# filepath: backend/app/models/base.py
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.mysql import CHAR, DATETIME
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """
    Lớp cơ sở trừu tượng cho toàn bộ các Entity Models trong hệ thống.
    Kế thừa AsyncAttrs để hỗ trợ truy cập thuộc tính lazy-loading an toàn trong môi trường Asyncio.
    """


class TimestampMixin:
    """
    Mixin cung cấp 2 trường kiểm toán thời gian tự động:
    - created_at: Mốc thời gian bản ghi được tạo (mặc định CURRENT_TIMESTAMP).
    - updated_at: Mốc thời gian cập nhật gần nhất (NULL khi tạo mới, tự động cập nhật).
    """
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
        onupdate=func.now(),
    )


class UUIDPrimaryKeyMixin:
    """
    Mixin cung cấp khóa chính dạng UUID v4 chuẩn quốc tế, lưu trữ dưới dạng CHAR(36) trong MySQL 8.0.
    """
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


class AuditMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Mixin kết hợp khóa chính UUID và kiểm toán thời gian toàn diện.
    """
