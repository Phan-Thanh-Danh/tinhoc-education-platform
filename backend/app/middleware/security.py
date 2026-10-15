# filepath: backend/app/middleware/security.py
from __future__ import annotations

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware áp dụng các Security Headers chuẩn OWASP Top 10 (Defence in Depth Lớp 2):
    - Chống Clickjacking (X-Frame-Options: DENY).
    - Chống MIME Type Sniffing (X-Content-Type-Options: nosniff).
    - Chống rò rỉ phiên bản hệ điều hành / runtime (gỡ Server, X-Powered-By).
    - Cấu hình Content Security Policy (CSP), Referrer-Policy và Permissions-Policy.
    - Cấu hình HSTS (Strict-Transport-Security) cho môi trường Production.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 1. Ẩn thông tin công nghệ máy chủ (Information Disclosure Prevention)
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        # 2. Ngăn chặn nhúng trang vào iframe để chống tấn công Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 3. Ngăn trình duyệt tự ý đoán định dạng tệp tin (MIME Sniffing)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 4. Tắt bộ lọc XSS lỗi thời của trình duyệt (theo chuẩn OWASP 2025/2026 chống lỗ hổng XS-Search)
        response.headers["X-XSS-Protection"] = "0"

        # 5. Ngăn rò rỉ cửa sổ và tài nguyên chéo nguồn (Cross-Origin Opener Policy)
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # 6. Kiểm soát thông tin Referrer để bảo vệ quyền riêng tư
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Giới hạn quyền truy cập phần cứng nhạy cảm (Microphone, Camera, Vị trí)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )

        # 8. Content Security Policy (CSP)
        is_prod = settings.ENVIRONMENT.lower() == "production"
        docs_paths = {"/docs", "/redoc", "/openapi.json"}

        if request.url.path in docs_paths:
            # Cho phép Swagger UI và Redoc tải thư viện CSS/JS từ CDN jsdelivr và render API docs bình thường
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "img-src 'self' data: blob: https: https://fastapi.tiangolo.com; "
                "connect-src 'self' *; "
                "frame-ancestors 'none';"
            )
        else:
            connect_src = "'self'" if is_prod else "'self' http://localhost:8000 http://localhost:5173 ws:"
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "img-src 'self' data: blob: https:; "
                f"connect-src {connect_src}; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        response.headers["Content-Security-Policy"] = csp_policy

        # 8. Bắt buộc kết nối HTTPS với HSTS nếu chạy trên môi trường Production
        if is_prod:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response

