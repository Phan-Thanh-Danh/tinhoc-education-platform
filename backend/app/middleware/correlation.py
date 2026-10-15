# filepath: backend/app/middleware/correlation.py
from __future__ import annotations

import logging
import re
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar giúp truy vết correlation_id xuyên suốt mọi tầng (Service, Repository, Logger, Audit)
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

logger = logging.getLogger("middleware.correlation")

# Regex chỉ chấp nhận các ký tự chữ, số, gạch ngang, gạch dưới (độ dài 1-64) để chống CRLF Log Injection
CORRELATION_ID_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")


def get_correlation_id(request: Optional[Request] = None) -> str:
    """
    Lấy correlation_id của request hiện tại trong ngữ cảnh thực thi:
    - Đọc từ ContextVar (xuyên suốt các tầng Service, Repository, Logger).
    - Dự phòng đọc từ request.state.correlation_id khi ContextVar bị reset (ví dụ khi văng ngoại lệ 500
      ra ngoài ServerErrorMiddleware).
    """
    cid = correlation_id_ctx.get()
    if cid:
        return cid
    if request is not None and hasattr(request, "state"):
        return getattr(request.state, "correlation_id", "") or ""
    return ""


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware gắn mã định danh tương quan (X-Correlation-ID) và đo lường thời gian xử lý:
    - Tiếp nhận hoặc tự động sinh UUID v4 cho mỗi request đến.
    - Làm sạch và xác thực chuỗi ID chống tấn công Log Injection (CRLF).
    - Gắn Correlation-ID vào contextvars và request.state.
    - Trả về X-Correlation-ID và X-Process-Time trong Response Headers.
    - Ghi log có cấu trúc (Structured Logging) thời gian thực thi (Performance tracking).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Lấy Correlation ID từ header của client nếu có, kiểm tra hợp lệ để chống Log Injection
        raw_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        if raw_id and CORRELATION_ID_REGEX.match(raw_id):
            req_correlation_id = raw_id
        else:
            req_correlation_id = str(uuid.uuid4())

        # Lưu vào contextvars và request.state
        token = correlation_id_ctx.set(req_correlation_id)
        request.state.correlation_id = req_correlation_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Ghi nhận lỗi có gắn correlation_id trước khi đẩy lên Exception Handler
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"[{req_correlation_id}] {request.method} {request.url.path} "
                f"gặp lỗi nghiêm trọng sau {process_time_ms}ms"
            )
            raise
        finally:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            correlation_id_ctx.reset(token)

        # Gắn các Header theo dõi vào Response
        response.headers["X-Correlation-ID"] = req_correlation_id
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"

        # Ghi log structured chuẩn hiệu năng
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"[{req_correlation_id}] {request.method} {request.url.path} "
            f"| Status: {response.status_code} | Time: {process_time_ms}ms | IP: {client_ip}"
        )

        return response

