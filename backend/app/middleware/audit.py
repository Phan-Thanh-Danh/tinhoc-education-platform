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

# Danh sách từ khóa/chuỗi con nhạy cảm bắt buộc phải che giấu (Masking) chuẩn OWASP
SENSITIVE_SUBSTRINGS = (
    "pass",        # password, mat_khau, old_password, new_password
    "pwd",
    "token",       # access_token, refresh_token, token
    "secret",      # secret_key, client_secret
    "otp",         # otp, verification_otp
    "pin",         # pin_code
    "cvv",         # cvv, cvc
    "cvc",
    "cccd",        # cccd, cmnd
    "cmnd",
    "credential",
    "auth",        # authorization, auth_token
    "private",
)


def is_sensitive_key(key: Any) -> bool:
    """
    Kiểm tra xem tên trường có chứa thông tin nhạy cảm hay không.
    Sử dụng so khớp mẫu substring và lọc chính xác cho từ khóa 'key'.
    """
    k = str(key).lower()
    if any(pattern in k for pattern in SENSITIVE_SUBSTRINGS):
        return True
    if k == "key" or "_key" in k or "key_" in k or "apikey" in k:
        return True
    return False


def mask_sensitive_data(data: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
    """
    Đệ quy duyệt qua Dictionary / List và che giấu các thông tin nhạy cảm
    như mật khẩu, mã OTP, Token bí mật trước khi lưu vào bảng CSDL audit_logs.
    Giới hạn độ sâu tối đa (max_depth=10) để chống Stack Overflow DoS từ payload lồng nhau.
    """
    if current_depth > max_depth:
        return "***MAX_DEPTH_EXCEEDED***"

    if isinstance(data, dict):
        masked_dict = {}
        for key, value in data.items():
            if is_sensitive_key(key):
                masked_dict[key] = "***REDACTED***"
            else:
                masked_dict[key] = mask_sensitive_data(
                    value, max_depth=max_depth, current_depth=current_depth + 1
                )
        return masked_dict
    elif isinstance(data, list):
        return [
            mask_sensitive_data(item, max_depth=max_depth, current_depth=current_depth + 1)
            for item in data
        ]
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
        user_id = str(getattr(u, "id", "")) or None
        user_name = (
            getattr(u, "full_name", None)
            or getattr(u, "username", None)
            or getattr(u, "email", "Người dùng")
        )
        return user_id, str(user_name)

    if hasattr(request.state, "user_id") and request.state.user_id:
        return str(request.state.user_id), str(getattr(request.state, "user_name", "Người dùng"))

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
            return str(user_id) if user_id else None, str(user_name)
        except Exception:
            # Token lỗi hoặc không hợp lệ -> Coi như khách
            pass

    return None, "Khách (Anonymous)"


class ComprehensiveAuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware tự động ghi nhật ký kiểm toán cho TẤT CẢ các API vào Bảng 45 (audit_logs):
    - IP thực tế (ip_address) chống giả mạo proxy qua danh sách TRUSTED_PROXIES.
    - ID người dùng (user_id) & Tên người dùng / Email (user_name).
    - API đã gọi: Method + Endpoint URL path (action).
    - Chi tiết JSON (details):
        + query_params: Tham số tìm kiếm, lọc (đã tự động che giấu token/otp nhạy cảm).
        + request_body: Gói tin JSON gửi lên (bảo vệ chống OOM DoS, che giấu mật khẩu/token).
        + status_code: Mã phản hồi HTTP (200, 201, 400, 401, 403, 404, 500).
        + process_time_ms: Thời gian máy chủ xử lý xong request.
        + correlation_id: Mã định danh truy vết tương quan xuyên suốt hệ thống.
    - Cơ chế ghi bất đồng bộ (Non-blocking): Hoàn toàn không làm chậm phản hồi cho client.
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

        # Xử lý Request Body an toàn chống OOM DoS & Stream Deadlock
        parsed_body: Any = None
        content_type = request.headers.get("content-type", "").lower()
        content_length_header = request.headers.get("content-length")
        try:
            content_length = int(content_length_header) if content_length_header else 0
        except ValueError:
            content_length = 0

        max_size = getattr(settings, "MAX_AUDIT_BODY_SIZE", 65536)

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if "multipart/form-data" in content_type:
                # Tuyệt đối không đọc stream file upload vào memory để tránh OOM DoS
                parsed_body = {
                    "notice": "Multipart/form-data stream, nội dung file được bỏ qua để tối ưu bộ nhớ",
                    "content_type": content_type,
                    "size_bytes": content_length,
                }
            elif "application/json" in content_type:
                if content_length > max_size:
                    parsed_body = {
                        "notice": f"Payload vượt quá ngưỡng cho phép ({content_length} bytes > {max_size} bytes), bỏ qua chi tiết",
                        "size_bytes": content_length,
                    }
                else:
                    try:
                        # Starlette tự động lưu cache body vào request._body
                        # Các endpoint phía sau có thể gọi request.body() / request.json() bình thường
                        # Không cần tạo lại ASGI Request(scope, receive) gây deadlock hoặc mất state!
                        body_bytes = await request.body()
                        if len(body_bytes) > max_size:
                            parsed_body = {
                                "notice": f"Payload thực tế vượt quá {max_size} bytes",
                                "size_bytes": len(body_bytes),
                            }
                        elif body_bytes:
                            try:
                                raw_json = json.loads(body_bytes.decode("utf-8"))
                                parsed_body = mask_sensitive_data(raw_json)
                            except Exception:
                                parsed_body = {
                                    "raw_sample": body_bytes[:256].decode("utf-8", errors="replace"),
                                    "parse_error": "Dữ liệu JSON không hợp lệ",
                                }
                    except Exception as exc:
                        parsed_body = {"body_read_error": str(exc)}
            elif content_length > 0:
                parsed_body = {
                    "content_type": content_type,
                    "size_bytes": content_length,
                }

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

            # Che giấu các tham số nhạy cảm trong query params (ví dụ ?token=..., ?otp=...)
            masked_query_params = mask_sensitive_data(dict(request.query_params))

            # Lấy correlation_id an toàn từ ContextVar hoặc request.state
            cid = get_correlation_id(request)

            # Gom toàn bộ dữ liệu kiểm toán vào trường details JSON
            audit_details: Dict[str, Any] = {
                "user_name": user_name,
                "method": request.method,
                "path": request.url.path,
                "query_params": masked_query_params,
                "request_body": parsed_body,
                "status_code": status_code,
                "process_time_ms": process_time_ms,
                "correlation_id": cid,
            }

            # Ghi vào bảng audit_logs qua background task bất đồng bộ (hoàn toàn không chặn luồng)
            log_audit_background(
                action=action_name,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                details=audit_details,
            )
