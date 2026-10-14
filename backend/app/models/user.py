# filepath: backend/app/models/user.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .curriculum import Lesson, LessonContent
    from .exam import Exam, ExamRoomParticipant, ExamSubmission, UserWrongQuestion
    from .question import Question


class TrackPreference(str, enum.Enum):
    ICT = "ICT"
    CS = "CS"


class UserStatus(str, enum.Enum):
    PendingActivation = "PendingActivation"
    Active = "Active"
    Suspended = "Suspended"
    Banned = "Banned"


class VerificationCodeType(str, enum.Enum):
    RegisterActivation = "RegisterActivation"
    PasswordReset = "PasswordReset"
    ChangeEmail = "ChangeEmail"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("google_id", name="uq_users_google_id"),
        CheckConstraint("target_score >= 0.0 AND target_score <= 10.0", name="ck_users_target_score"),
        CheckConstraint("failed_login_attempts >= 0", name="ck_users_failed_attempts"),
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
    email: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    password_hash: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        default=None,
        comment="Băm BCrypt/Argon2id, NULL nếu chỉ dùng Google SSO",
    )
    full_name: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
    )
    phone_number: Mapped[str | None] = mapped_column(
        VARCHAR(20),
        nullable=True,
        default=None,
    )
    avatar_url: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    track_preference: Mapped[TrackPreference | None] = mapped_column(
        ENUM("ICT", "CS", name="user_track_preference_enum"),
        nullable=True,
        default=None,
        comment="Phân luồng định hướng thi tốt nghiệp THPT",
    )
    target_score: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 1),
        nullable=False,
        default=Decimal("8.0"),
        comment="Mục tiêu điểm số từ 0.0 đến 10.0",
    )
    reputation_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Điểm uy tín tích lũy từ diễn đàn",
    )
    contributor_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Giá trị tổng hợp điểm cống hiến tài liệu (Read-Cache từ Ledger)",
    )
    status: Mapped[UserStatus] = mapped_column(
        ENUM("PendingActivation", "Active", "Suspended", "Banned", name="user_status_enum"),
        nullable=False,
        default=UserStatus.PendingActivation,
        comment="Trạng thái vòng đời của tài khoản",
    )
    email_confirmed: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    google_id: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        default=None,
        comment="Google Subject ID (sub claim duy nhất vĩnh viễn), không lưu ID Token",
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    lockout_end: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )

    # Quan hệ RBAC
    user_roles: Mapped[List[UserRole]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[UserRole.user_id]",
    )
    roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.id == UserRole.user_id",
        secondaryjoin="Role.id == UserRole.role_id",
        back_populates="users",
        viewonly=True,
    )

    # Quan hệ Phiên & Xác thực
    refresh_tokens: Mapped[List[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verification_codes: Mapped[List[VerificationCode]] = relationship(
        "VerificationCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Quan hệ Nội dung & Khảo thí
    created_lessons: Mapped[List[Lesson]] = relationship(
        "Lesson",
        back_populates="author",
        foreign_keys="[Lesson.author_id]",
    )
    edited_lesson_contents: Mapped[List[LessonContent]] = relationship(
        "LessonContent",
        back_populates="last_editor",
        foreign_keys="[LessonContent.last_edited_by]",
    )
    created_questions: Mapped[List[Question]] = relationship(
        "Question",
        back_populates="creator",
        foreign_keys="[Question.created_by]",
    )
    created_exams: Mapped[List[Exam]] = relationship(
        "Exam",
        back_populates="creator",
        foreign_keys="[Exam.created_by]",
    )
    exam_submissions: Mapped[List[ExamSubmission]] = relationship(
        "ExamSubmission",
        back_populates="user",
        foreign_keys="[ExamSubmission.user_id]",
    )
    wrong_questions: Mapped[List[UserWrongQuestion]] = relationship(
        "UserWrongQuestion",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[UserWrongQuestion.user_id]",
    )
    room_participations: Mapped[List[ExamRoomParticipant]] = relationship(
        "ExamRoomParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[ExamRoomParticipant.user_id]",
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
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
    name: Mapped[str] = mapped_column(
        VARCHAR(50),
        nullable=False,
        comment="Tên vai trò: Student, Instructor, Admin, Reviewer",
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user_roles: Mapped[List[UserRole]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
        foreign_keys="[UserRole.role_id]",
    )
    users: Mapped[List[User]] = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == UserRole.role_id",
        secondaryjoin="User.id == UserRole.user_id",
        back_populates="roles",
        viewonly=True,
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_user_roles_user"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE", name="fk_user_roles_role"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    assigned_by: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_user_roles_assigned_by"),
        nullable=True,
        default=None,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="user_roles",
        foreign_keys=[user_id],
    )
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="user_roles",
        foreign_keys=[role_id],
    )
    assigner: Mapped[Optional[User]] = relationship(
        "User",
        foreign_keys=[assigned_by],
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_hash"),
        Index("idx_refresh_tokens_user", "user_id", "is_revoked", "expires_at"),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_refresh_tokens_user"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        VARCHAR(128),
        nullable=False,
        comment="Băm SHA-256 của Refresh Token",
    )
    jwt_id: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
        comment="Khóa jti của Access Token đi kèm",
    )
    is_used: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    is_revoked: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    created_by_ip: Mapped[str | None] = mapped_column(
        VARCHAR(45),
        nullable=True,
        default=None,
    )
    replaced_by_token_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("refresh_tokens.id", ondelete="SET NULL", name="fk_refresh_tokens_replaced"),
        nullable=True,
        default=None,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="refresh_tokens",
    )
    replaced_by: Mapped[Optional[RefreshToken]] = relationship(
        "RefreshToken",
        remote_side=[id],
        back_populates="replaced_tokens",
        foreign_keys=[replaced_by_token_id],
    )
    replaced_tokens: Mapped[List[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="replaced_by",
        foreign_keys=[replaced_by_token_id],
    )


class VerificationCode(Base):
    __tablename__ = "verification_codes"
    __table_args__ = (
        Index("idx_verification_codes_lookup", "user_id", "type", "is_used", "expires_at"),
        CheckConstraint("attempt_count >= 0", name="ck_verification_codes_attempts"),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_verification_codes_user"),
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(
        VARCHAR(128),
        nullable=False,
        comment="HMAC-SHA256(OTP, Server_Secret_Pepper) chống dò quét không gian 6 số",
    )
    type: Mapped[VerificationCodeType] = mapped_column(
        ENUM("RegisterActivation", "PasswordReset", "ChangeEmail", name="verification_code_type_enum"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Quá 5 lần nhập sai sẽ vô hiệu hóa",
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="verification_codes",
    )
