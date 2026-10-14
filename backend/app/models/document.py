# filepath: backend/app/models/document.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base

if TYPE_CHECKING:
    from .curriculum import Grade
    from .user import User


class DocumentTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class DocumentStatus(str, enum.Enum):
    PendingReview = "PendingReview"
    UnderReview = "UnderReview"
    RevisionRequired = "RevisionRequired"
    Published = "Published"
    Rejected = "Rejected"
    Abandoned = "Abandoned"


class ModerationDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    REJECTED = "REJECTED"


class PointTransactionType(str, enum.Enum):
    DOC_APPROVED = "DOC_APPROVED"
    DOC_FEATURED = "DOC_FEATURED"
    DOC_REMOVED_PENALTY = "DOC_REMOVED_PENALTY"
    SYSTEM_ADJUSTMENT = "SYSTEM_ADJUSTMENT"


class DocumentCategory(Base):
    __tablename__ = "document_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_doc_categories_code"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    code: Mapped[str] = mapped_column(
        VARCHAR(30),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        default=None,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_active: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )

    documents: Mapped[List[SharedDocument]] = relationship(
        "SharedDocument",
        back_populates="category",
    )


class SharedDocument(Base):
    __tablename__ = "shared_documents"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_shared_docs_slug"),
        Index("idx_shared_docs_search", "grade_id", "track", "category_id", "status"),
        Index("ft_shared_docs_text", "title", "description", mysql_prefix="FULLTEXT"),
        CheckConstraint("file_size_bytes > 0 AND file_size_bytes <= 52428800", name="ck_shared_docs_size"),
        CheckConstraint("average_rating IS NULL OR (average_rating >= 1.00 AND average_rating <= 5.00)", name="ck_shared_docs_rating"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    contributor_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_shared_docs_contributor"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document_categories.id", ondelete="RESTRICT", name="fk_shared_docs_category"),
        nullable=False,
    )
    assigned_reviewer_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_shared_docs_reviewer"),
        nullable=True,
        default=None,
    )
    title: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(280),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grades.id", ondelete="RESTRICT", name="fk_shared_docs_grade"),
        nullable=False,
    )
    track: Mapped[DocumentTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="document_track_enum"),
        nullable=False,
        default=DocumentTrack.COMMON,
    )
    storage_path: Mapped[str] = mapped_column(
        VARCHAR(500),
        nullable=False,
    )
    original_file_name: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    file_extension: Mapped[str] = mapped_column(
        VARCHAR(10),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
    )
    file_hash_sha256: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
        comment="Mã băm kiểm tra tính toàn vẹn và ngăn chặn trùng tệp",
    )
    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    thumbnail_url: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        ENUM("PendingReview", "UnderReview", "RevisionRequired", "Published", "Rejected", "Abandoned", name="document_status_enum"),
        nullable=False,
        default=DocumentStatus.PendingReview,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    has_answer_key: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )
    is_downloadable: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )
    view_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    download_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    average_rating: Mapped[Decimal | None] = mapped_column(
        DECIMAL(3, 2),
        nullable=True,
        default=None,
        comment="MẶC ĐỊNH NULL KHI CHƯA CÓ ĐÁNH GIÁ (Tránh 5 sao ảo)",
    )
    total_reviews: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )

    category: Mapped[DocumentCategory] = relationship(
        "DocumentCategory",
        back_populates="documents",
        foreign_keys=[category_id],
    )
    contributor: Mapped[User] = relationship(
        "User",
        foreign_keys=[contributor_id],
    )
    assigned_reviewer: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[assigned_reviewer_id],
    )
    grade: Mapped[Grade] = relationship(
        "Grade",
        foreign_keys=[grade_id],
    )
    moderation_logs: Mapped[List[DocumentModerationLog]] = relationship(
        "DocumentModerationLog",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    ratings: Mapped[List[DocumentRating]] = relationship(
        "DocumentRating",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    download_logs: Mapped[List[DocumentDownloadLog]] = relationship(
        "DocumentDownloadLog",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentModerationLog(Base):
    __tablename__ = "document_moderation_logs"
    __table_args__ = (
        Index("idx_mod_logs_doc", "document_id", "document_version"),
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
    document_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("shared_documents.id", ondelete="CASCADE", name="fk_mod_logs_doc"),
        nullable=False,
    )
    document_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Gắn chặt với phiên bản tệp được thẩm định",
    )
    reviewer_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_mod_logs_reviewer"),
        nullable=False,
    )
    decision: Mapped[ModerationDecision] = mapped_column(
        ENUM("APPROVED", "REVISION_REQUIRED", "REJECTED", name="moderation_decision_enum"),
        nullable=False,
    )
    feedback_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    checklist_scores_json: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Chấm điểm 4 tiêu chuẩn GDPT",
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[SharedDocument] = relationship(
        "SharedDocument",
        back_populates="moderation_logs",
        foreign_keys=[document_id],
    )
    reviewer: Mapped[User] = relationship(
        "User",
        foreign_keys=[reviewer_id],
    )


class DocumentRating(Base):
    __tablename__ = "document_ratings"
    __table_args__ = (
        UniqueConstraint("document_id", "user_id", name="uq_doc_user_rating"),
        CheckConstraint("rating_stars >= 1 AND rating_stars <= 5", name="ck_doc_ratings_stars"),
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
    document_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("shared_documents.id", ondelete="CASCADE", name="fk_doc_ratings_doc"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_doc_ratings_user"),
        nullable=False,
    )
    rating_stars: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    comment_text: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[SharedDocument] = relationship(
        "SharedDocument",
        back_populates="ratings",
        foreign_keys=[document_id],
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class ContributorPointsHistory(Base):
    __tablename__ = "contributor_points_history"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_cph_idempotency"),
        Index("idx_cph_user", "user_id", "created_at"),
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
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_cph_user"),
        nullable=False,
        comment="SỔ CÁI BẤT BIẾN - KHÔNG XÓA KHI USER BỊ XÓA",
    )
    document_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("shared_documents.id", ondelete="SET NULL", name="fk_cph_document"),
        nullable=True,
        default=None,
    )
    points_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="+200, +100, -50",
    )
    transaction_type: Mapped[PointTransactionType] = mapped_column(
        ENUM("DOC_APPROVED", "DOC_FEATURED", "DOC_REMOVED_PENALTY", "SYSTEM_ADJUSTMENT", name="point_transaction_type_enum"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
        comment="Quy tắc: DOC_APPROVE_{doc_id}_v{version} chống cộng trùng",
    )
    reason: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    created_by: Mapped[str | None] = mapped_column(
        CHAR(36),
        nullable=True,
        default=None,
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
    document: Mapped[Optional[SharedDocument]] = relationship(
        "SharedDocument",
        foreign_keys=[document_id],
    )


class DocumentDownloadLog(Base):
    __tablename__ = "document_download_logs"
    __table_args__ = (
        Index("idx_download_logs_rate_limit", "ip_address", "downloaded_at"),
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
    document_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("shared_documents.id", ondelete="CASCADE", name="fk_downloads_doc"),
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_downloads_user"),
        nullable=True,
        default=None,
        comment="NULL nếu tải vãng lai",
    )
    ip_address: Mapped[str] = mapped_column(
        VARCHAR(45),
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        default=None,
    )
    downloaded_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[SharedDocument] = relationship(
        "SharedDocument",
        back_populates="download_logs",
        foreign_keys=[document_id],
    )
    user: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[user_id],
    )

