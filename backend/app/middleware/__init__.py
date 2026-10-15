# filepath: backend/app/middleware/__init__.py
from __future__ import annotations

from fastapi import FastAPI

from .correlation import CorrelationIdMiddleware, get_correlation_id
from .exception_handler import register_exception_handlers
from .rate_limit import GlobalRateLimitMiddleware, get_client_ip, rate_limit
from .security import SecurityHeadersMiddleware

__all__ = [
    "CorrelationIdMiddleware",
    "SecurityHeadersMiddleware",
    "GlobalRateLimitMiddleware",
    "get_correlation_id",
    "get_client_ip",
    "rate_limit",
    "register_exception_handlers",
    "setup_middlewares",
]


def setup_middlewares(app: FastAPI) -> None:
    """
    Cấu hình toàn bộ hệ thống Middleware và Exception Handlers theo chuẩn kiến trúc:
    Thứ tự thực thi trong Starlette: Middleware thêm sau sẽ bọc bên ngoài Middleware thêm trước!
    Thứ tự dòng chảy request:
    Request -> [CorrelationId] -> [SecurityHeaders] -> [GlobalRateLimit] -> Router/Endpoints -> Response
    """
    # 1. Đăng ký các bộ xử lý lỗi toàn cục (Global Exception Handlers)
    register_exception_handlers(app)

    # 2. Giới hạn tần suất gọi API công khai (Chống DDoS / Brute-force)
    app.add_middleware(GlobalRateLimitMiddleware)

    # 3. Gắn các Security Headers chuẩn OWASP Top 10
    app.add_middleware(SecurityHeadersMiddleware)

    # 4. Gắn Correlation-ID và đo lường hiệu năng thời gian xử lý (Lớp ngoài cùng)
    app.add_middleware(CorrelationIdMiddleware)

