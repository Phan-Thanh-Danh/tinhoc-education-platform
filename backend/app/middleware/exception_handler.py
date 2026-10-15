# filepath: backend/app/middleware/exception_handler.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.middleware.correlation import get_correlation_id

logger = logging.getLogger("middleware.exception_handler")


def format_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Định dạng cấu trúc phản hồi lỗi chuẩn hóa cho toàn bộ hệ thống API."""
    content: dict[str, Any] = {
        "success": False,
        "error": error_type,
        "message": message,
        "correlation_id": get_correlation_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký các bộ xử lý lỗi toàn cục cho FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Xử lý các lỗi nghiệp vụ định nghĩa qua HTTPException."""
        error_names = {
            status.HTTP_400_BAD_REQUEST: "BadRequest",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized",
            status.HTTP_403_FORBIDDEN: "Forbidden",
            status.HTTP_404_NOT_FOUND: "NotFound",
            status.HTTP_409_CONFLICT: "Conflict",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "UnprocessableEntity",
            status.HTTP_429_TOO_MANY_REQUESTS: "RateLimitExceeded",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "InternalServerError",
        }
        error_type = error_names.get(exc.status_code, "HttpError")

        # Chuẩn hóa thông báo lỗi dạng string
        message = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không thể thực hiện."
        details = exc.detail if not isinstance(exc.detail, str) else None

        logger.warning(
            f"[{get_correlation_id()}] HTTP {exc.status_code} trên {request.method} {request.url.path}: {message}"
        )
        return format_error_response(exc.status_code, error_type, message, details)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Xử lý lỗi kiểm tra tính hợp lệ của tham số đầu vào (Pydantic v2)."""
        friendly_errors = []
        for err in exc.errors():
            field = " -> ".join(str(loc) for loc in err.get("loc", []))
            msg = err.get("msg", "Dữ liệu không hợp lệ")
            err_type = err.get("type", "value_error")

            # Việt hóa các thông báo lỗi cơ bản phổ biến
            if "missing" in err_type:
                msg = "Trường này là bắt buộc không được bỏ trống"
            elif "string_too_short" in err_type:
                msg = "Độ dài chuỗi quá ngắn"
            elif "string_too_long" in err_type:
                msg = "Độ dài chuỗi vượt quá giới hạn cho phép"
            elif "value_error" in err_type and "email" in field.lower():
                msg = "Địa chỉ email không đúng định dạng"

            friendly_errors.append({"field": field, "message": msg, "type": err_type})

        logger.info(
            f"[{get_correlation_id()}] Lỗi xác thực dữ liệu trên {request.method} {request.url.path}: {friendly_errors}"
        )

        return format_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="ValidationError",
            message="Dữ liệu gửi lên không đúng định dạng. Vui lòng kiểm tra lại các trường thông tin.",
            details=friendly_errors,
        )

    @app.exception_handler(Exception)
    async def global_unexpected_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Bắt toàn bộ các lỗi ngoại lệ chưa được xử lý (Unhandled 500).
        Bảo vệ an ninh tuyệt đối: Ghi đầy đủ Stack Trace vào Server Log nhưng
        KHÔNG BAO GIỜ để lộ Stack Trace ra ngoài Client.
        """
        correlation_id = get_correlation_id()
        logger.critical(
            f"[{correlation_id}] Lỗi nghiêm trọng chưa xử lý trên {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )

        return format_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="InternalServerError",
            message="Đã xảy ra sự cố nội bộ trên máy chủ. Vui lòng liên hệ ban quản trị kèm theo mã hỗ trợ này.",
            details={"support_id": correlation_id},
        )
