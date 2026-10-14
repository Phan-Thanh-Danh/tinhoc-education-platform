# filepath: backend/app/models/question.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, VARCHAR
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .curriculum import Lesson, Topic
    from .exam import ExamQuestion, ExamSubmissionAnswer, UserWrongQuestion
    from .user import User


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"


class QuestionTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class DifficultyLevel(str, enum.Enum):
    RECOGNITION = "RECOGNITION"
    COMPREHENSION = "COMPREHENSION"
    APPLICATION = "APPLICATION"
    ADVANCED_APPLICATION = "ADVANCED_APPLICATION"


class QuestionStatus(str, enum.Enum):
    Draft = "Draft"
    PendingReview = "PendingReview"
    Approved = "Approved"
    Archived = "Archived"


class Question(Base, TimestampMixin):
    __tablename__ = "questions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["topic_id", "grade_id"],
            ["topics.id", "topics.grade_id"],
            name="fk_questions_topic_grade",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name="fk_questions_lesson",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_questions_creator",
            ondelete="RESTRICT",
        ),
        Index(
            "idx_questions_matrix",
            "grade_id",
            "topic_id",
            "question_type",
            "track",
            "difficulty_level",
            "status",
        ),
        CheckConstraint("usage_count >= 0", name="ck_questions_usage"),
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
    topic_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    grade_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    lesson_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        nullable=True,
        default=None,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        ENUM("MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER", name="question_type_enum"),
        nullable=False,
    )
    track: Mapped[QuestionTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="question_track_enum"),
        nullable=False,
        default=QuestionTrack.COMMON,
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        ENUM(
            "RECOGNITION",
            "COMPREHENSION",
            "APPLICATION",
            "ADVANCED_APPLICATION",
            name="question_difficulty_enum",
        ),
        nullable=False,
        default=DifficultyLevel.COMPREHENSION,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Phiên bản câu hỏi, tăng lên khi có hiệu đính",
    )
    content_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Đề bài, code, options (A/B/C/D) hoặc statements (a/b/c/d) - KHÔNG chứa đáp án đúng",
    )
    solution_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Khóa đáp án, regex, giải thích từng bước, tracing table",
    )
    status: Mapped[QuestionStatus] = mapped_column(
        ENUM("Draft", "PendingReview", "Approved", "Archived", name="question_status_enum"),
        nullable=False,
        default=QuestionStatus.Draft,
        comment="Mặc định Draft an toàn",
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
    )

    # Quan hệ thực thể
    topic: Mapped[Topic] = relationship(
        "Topic",
        back_populates="questions",
        primaryjoin="and_(foreign(Question.topic_id) == Topic.id, foreign(Question.grade_id) == Topic.grade_id)",
    )
    lesson: Mapped[Optional[Lesson]] = relationship(
        "Lesson",
        back_populates="questions",
        foreign_keys=[lesson_id],
    )
    creator: Mapped[User] = relationship(
        "User",
        back_populates="created_questions",
        foreign_keys=[created_by],
    )

    # Thẻ phân loại Tag (N-N)
    tag_mappings: Mapped[List[QuestionTagMapping]] = relationship(
        "QuestionTagMapping",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    tags: Mapped[List[QuestionTag]] = relationship(
        "QuestionTag",
        secondary="question_tag_mappings",
        back_populates="questions",
        viewonly=True,
    )

    # Liên kết Khảo thí & Lịch sử
    exam_questions: Mapped[List[ExamQuestion]] = relationship(
        "ExamQuestion",
        back_populates="question",
    )
    submission_answers: Mapped[List[ExamSubmissionAnswer]] = relationship(
        "ExamSubmissionAnswer",
        back_populates="question",
    )
    wrong_questions: Mapped[List[UserWrongQuestion]] = relationship(
        "UserWrongQuestion",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List[QuestionAuditLog]] = relationship(
        "QuestionAuditLog",
        back_populates="question",
    )


class QuestionTag(Base):
    __tablename__ = "question_tags"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_question_tags_slug"),
        UniqueConstraint("tag_name", name="uq_question_tags_name"),
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
    tag_name: Mapped[str] = mapped_column(
        VARCHAR(50),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(60),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    tag_mappings: Mapped[List[QuestionTagMapping]] = relationship(
        "QuestionTagMapping",
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    questions: Mapped[List[Question]] = relationship(
        "Question",
        secondary="question_tag_mappings",
        back_populates="tags",
        viewonly=True,
    )


class QuestionTagMapping(Base):
    __tablename__ = "question_tag_mappings"
    __table_args__ = (
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="CASCADE", name="fk_qtm_question"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question_tags.id", ondelete="CASCADE", name="fk_qtm_tag"),
        primary_key=True,
    )

    question: Mapped[Question] = relationship(
        "Question",
        back_populates="tag_mappings",
    )
    tag: Mapped[QuestionTag] = relationship(
        "QuestionTag",
        back_populates="tag_mappings",
    )


class QuestionAuditLog(Base):
    __tablename__ = "question_audit_logs"
    __table_args__ = (
        Index("idx_qal_question", "question_id", "version"),
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
    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="RESTRICT", name="fk_qal_question"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    old_content_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    old_solution_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    change_reason: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    changed_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_qal_editor"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    question: Mapped[Question] = relationship(
        "Question",
        back_populates="audit_logs",
    )
    editor: Mapped[User] = relationship(
        "User",
        foreign_keys=[changed_by],
    )


