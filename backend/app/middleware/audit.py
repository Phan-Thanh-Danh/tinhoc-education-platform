# filepath: backend/app/middleware/audit.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.middleware.correlation import get_correlation_id
from app.middleware.rate_limit import get_client_ip
from app.services.audit import log_audit_background

logger = logging.getLogger("middleware.audit")

# Danh sách các từ khóa nhạy cảm bắt buộc phải che giấu (Masking) để bảo vệ quyền riêng tư & chuẩn OWASP
SENSITIVE_KEYS = {
    "password",
    "mat_khau",
    "old_password",
    "new_password",
    "confirm_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "otp",
    "verification_code",
    "code",
}


def mask_sensitive_data(data: Any) -> Any:
    """
    Đệ quy duyệt qua Dictionary / List và che giấu các thông tin nhạy cảm
    như mật khẩu, mã OTP, Token bí mật trước khi lưu vào bảng CSDL audit_logs.
    """
    if isinstance(data, dict):
        masked_dict = {}
        for key, value in data.items():
            if str(key).lower() in SENSITIVE_KEYS:
                masked_dict[key] = "***REDACTED***"
            else:
                masked_dict[key] = mask_sensitive_data(value)
        return masked_dict
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


def extract_user_info_from_token(request: Request) -> tuple[Optional[str], str]:
    """
    Trích xuất User ID và Tên hiển thị / Email từ JWT Token trong Header Authorization
    hoặc từ request.state (nếu route đã qua tầng xác thực).
    Trả về: (user_id, user_name)
    """
    # 1. Kiểm tra nếu request.state đã được tầng Auth gán
    if hasattr(request.state, "user") and request.state.user:
        u = request.state.user
        user_id = getattr(u, "id", None)
        user_name = getattr(u, "full_name", None) or getattr(u, "username", None) or getattr(u, "email", "Người dùng")
        return user_id, user_name

    if hasattr(request.state, "user_id") and request.state.user_id:
        return request.state.user_id, getattr(request.state, "user_name", "Người dùng")

    # 2. Giải mã token nhanh từ Header Authorization nếu có
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            from jose import jwt
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_exp": False},  # Vẫn trích xuất được danh tính kể cả token vừa hết hạn
            )
            user_id = payload.get("sub")
            user_name = (
                payload.get("name")
                or payload.get("full_name")
                or payload.get("username")
                or payload.get("email")
                or "Người dùng"
            )
            return user_id, str(user_name)
        except Exception:
            # Token lỗi hoặc không hợp lệ -> Coi như khách
            pass

    return None, "Khách (Anonymous)"


class ComprehensiveAuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware tự động ghi nhật ký kiểm toán cho TẤT CẢ các API vào Bảng 45 (audit_logs):
    - IP thực tế (ip_address) chống giả mạo proxy.
    - ID người dùng (user_id) & Tên người dùng / Email (user_name).
    - API đã gọi: Method + Endpoint URL path (action).
    - Chi tiết JSON (details):
        + query_params: Toàn bộ tham số tìm kiếm, phân trang.
        + request_body: Gói tin JSON gửi lên (đã tự động che giấu mật khẩu, OTP, Token).
        + status_code: Mã phản hồi HTTP (200, 201, 400, 401, 403, 404, 500).
        + process_time_ms: Thời gian máy chủ xử lý xong request.
        + correlation_id: Mã định danh truy vết tương quan.
    - Cơ chế ghi bất đồng bộ (Non-blocking): Không làm chậm tốc độ phản hồi API cho người dùng.
    """

    # Các đường dẫn hệ thống nội bộ bỏ qua để tránh gây phình to database
    EXEMPT_PATHS: set[str] = {
        "/health",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bỏ qua các request OPTIONS (CORS preflight) hoặc health check
        if request.url.path in self.EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        start_time = time.perf_counter()
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Đọc trước Request Body và thiết lập lại receive stream để Endpoint đọc bình thường
        parsed_body: Any = None
        content_type = request.headers.get("content-type", "").lower()

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                body_bytes = await request.body()
                # Cấp lại stream nhận dữ liệu cho các handler phía sau
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request = Request(request.scope, receive)

                if "application/json" in content_type and body_bytes:
                    raw_json = json.loads(body_bytes.decode("utf-8"))
                    # Che giấu mật khẩu và token trước khi lưu vào CSDL
                    parsed_body = mask_sensitive_data(raw_json)
                elif body_bytes:
                    # Với form-data / upload tệp: Chỉ ghi nhận kích thước, không lưu byte thô
                    parsed_body = {
                        "content_type": content_type,
                        "size_bytes": len(body_bytes),
                    }
            except Exception as e:
                parsed_body = {"parse_error": str(e)}

        # Chuyển tiếp request vào ứng dụng
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            user_id, user_name = extract_user_info_from_token(request)

            # Tạo action chuẩn: "METHOD /path" (giới hạn 100 ký tự theo cột DB)
            action_name = f"{request.method} {request.url.path}"[:100]

            # Gom toàn bộ dữ liệu kiểm toán vào trường details JSON
            audit_details: Dict[str, Any] = {
                "user_name": user_name,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "request_body": parsed_body,
                "status_code": status_code,
                "process_time_ms": process_time_ms,
                "correlation_id": get_correlation_id(),
            }

            # Ghi vào bảng audit_logs qua background task bất đồng bộ (hoàn toàn không chặn luồng)
            log_audit_background(
                action=action_name,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                details=audit_details,
            )
