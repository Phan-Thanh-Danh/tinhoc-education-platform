# filepath: backend/app/services/audit.py
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.middleware.correlation import get_correlation_id
from app.models.platform import AuditLog

logger = logging.getLogger("service.audit")


class AuditAction:
    """Danh mục các hành động kiểm toán an ninh chuẩn hóa theo Tài liệu Đặc tả."""

    # Xác thực & Phiên làm việc
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"
    AUTH_PASSWORD_RESET_REQUEST = "AUTH_PASSWORD_RESET_REQUEST"
    AUTH_PASSWORD_RESET_SUCCESS = "AUTH_PASSWORD_RESET_SUCCESS"
    AUTH_ACCOUNT_LOCKOUT = "AUTH_ACCOUNT_LOCKOUT"

    # Quản trị Người dùng & Phân quyền
    USER_ROLE_ASSIGNED = "USER_ROLE_ASSIGNED"
    USER_ROLE_REVOKED = "USER_ROLE_REVOKED"
    USER_STATUS_SUSPENDED = "USER_STATUS_SUSPENDED"
    USER_STATUS_BANNED = "USER_STATUS_BANNED"
    USER_STATUS_ACTIVATED = "USER_STATUS_ACTIVATED"

    # Ngân hàng Đề thi & Khảo thí
    EXAM_SUBMISSION_STARTED = "EXAM_SUBMISSION_STARTED"
    EXAM_SUBMISSION_COMPLETED = "EXAM_SUBMISSION_COMPLETED"
    EXAM_SUBMISSION_CANCELLED = "EXAM_SUBMISSION_CANCELLED"
    QUESTION_EDITED = "QUESTION_EDITED"
    QUESTION_DELETED = "QUESTION_DELETED"

    # Kiểm duyệt Tài liệu & Sổ cái Cống hiến
    DOCUMENT_APPROVED = "DOCUMENT_APPROVED"
    DOCUMENT_REVISION_REQUIRED = "DOCUMENT_REVISION_REQUIRED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    DOCUMENT_TAKEDOWN = "DOCUMENT_TAKEDOWN"
    CONTRIBUTOR_POINTS_ADJUSTED = "CONTRIBUTOR_POINTS_ADJUSTED"

    # An ninh & Cảnh báo Vi phạm
    SECURITY_RATE_LIMIT_EXCEEDED = "SECURITY_RATE_LIMIT_EXCEEDED"
    SECURITY_UNAUTHORIZED_ACCESS = "SECURITY_UNAUTHORIZED_ACCESS"
    SECURITY_SUSPICIOUS_PAYLOAD = "SECURITY_SUSPICIOUS_PAYLOAD"


async def log_audit_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Ghi một bản ghi nhật ký kiểm toán trực tiếp vào CSDL (bảng audit_logs - Bảng 45).
    Tự động kèm mã correlation_id để phục vụ điều tra, truy vết toàn diện.
    """
    payload = details or {}
    correlation_id = get_correlation_id()
    if correlation_id and "correlation_id" not in payload:
        payload["correlation_id"] = correlation_id

    # Cắt ngắn user_agent nếu quá dài so với giới hạn cột 500 ký tự
    safe_user_agent = (user_agent[:495] + "...") if user_agent and len(user_agent) > 500 else user_agent

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=safe_user_agent,
        details=payload,
    )

    db.add(audit_entry)
    await db.flush()

    logger.info(
        f"[{correlation_id}] AUDIT LOG: Action={action} | User={user_id or 'Anonymous'} | IP={ip_address or 'Unknown'}"
    )
    return audit_entry


def log_audit_background(
    action: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Ghi nhật ký kiểm toán bất đồng bộ dưới dạng Background Task.
    Mở một AsyncSession độc lập để không làm chậm thời gian phản hồi (Response Time) của người dùng.
    """
    async def _async_task():
        try:
            async with AsyncSessionLocal() as session:
                await log_audit_event(
                    db=session,
                    action=action,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=details,
                )
                await session.commit()
        except Exception as exc:
            logger.error(f"Không thể ghi nhật ký audit log trong background task: {exc}", exc_info=True)

    # Chạy tác vụ nền mà không chặn luồng chính
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_async_task())
    except RuntimeError:
        # Nếu chưa có event loop (trường hợp chạy sync), bỏ qua an toàn
        pass

