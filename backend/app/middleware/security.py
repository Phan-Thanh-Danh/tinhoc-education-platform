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

        # 4. Bật bộ lọc XSS trên các trình duyệt thế hệ cũ
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 5. Kiểm soát thông tin Referrer để bảo vệ quyền riêng tư
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Giới hạn quyền truy cập phần cứng nhạy cảm (Microphone, Camera, Vị trí)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )

        # 7. Content Security Policy (CSP) cho phép KaTeX, PrismJS và API nội bộ
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' http://localhost:8000 http://localhost:5173 ws:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # 8. Bắt buộc kết nối HTTPS với HSTS nếu chạy trên môi trường Production
        if settings.ENVIRONMENT.lower() == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response

