# filepath: backend/app/models/platform.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base

if TYPE_CHECKING:
    from .user import User


class ReportTargetType(str, enum.Enum):
    QUESTION = "QUESTION"
    FORUM_POST = "FORUM_POST"
    FORUM_ANSWER = "FORUM_ANSWER"
    SHARED_DOCUMENT = "SHARED_DOCUMENT"


class ReportStatus(str, enum.Enum):
    Pending = "Pending"
    Resolved = "Resolved"
    Dismissed = "Dismissed"


class NotificationType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    FORUM = "FORUM"
    RESOURCE = "RESOURCE"
    EXAM = "EXAM"


class SystemReport(Base):
    __tablename__ = "system_reports"
    __table_args__ = (
        Index("idx_system_reports_target", "target_type", "target_id", "status"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    reporter_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_reports_reporter"),
        nullable=False,
    )
    target_type: Mapped[ReportTargetType] = mapped_column(
        ENUM("QUESTION", "FORUM_POST", "FORUM_ANSWER", "SHARED_DOCUMENT", name="report_target_type_enum"),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
        comment="UUID đối tượng bị tố cáo, kiểm tra tồn tại qua Application Logic",
    )
    reason_category: Mapped[str] = mapped_column(
        VARCHAR(50),
        nullable=False,
        comment="WRONG_ANSWER, CODE_ERROR, COPYRIGHT, SPAM, OFFENSIVE",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[ReportStatus] = mapped_column(
        ENUM("Pending", "Resolved", "Dismissed", name="report_status_enum"),
        nullable=False,
        default=ReportStatus.Pending,
    )
    admin_note: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    resolved_by: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_reports_resolver"),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )

    reporter: Mapped[User] = relationship(
        "User",
        foreign_keys=[reporter_id],
    )
    resolver: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[resolved_by],
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read", "created_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_notifications_user"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        VARCHAR(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    type: Mapped[NotificationType] = mapped_column(
        ENUM("SYSTEM", "FORUM", "RESOURCE", "EXAM", name="notification_type_enum"),
        nullable=False,
    )
    action_url: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    is_read: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_action", "action", "created_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_audit_logs_user"),
        nullable=True,
        default=None,
        comment="SET NULL khi tài khoản bị xóa, giữ nguyên dấu vết kiểm toán",
    )
    action: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        VARCHAR(45),
        nullable=True,
        default=None,
    )
    user_agent: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    details: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[user_id],
    )

