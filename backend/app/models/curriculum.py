# filepath: backend/app/models/curriculum.py
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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, LONGTEXT, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .question import Question
    from .user import User


class TrackType(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class LessonProgressStatus(str, enum.Enum):
    InProgress = "InProgress"
    Completed = "Completed"


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("code", name="uq_grades_code"),
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
        VARCHAR(10),
        nullable=False,
        comment="K10, K11, K12",
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(50),
        nullable=False,
        comment="Tin học Lớp 10, Tin học Lớp 11, Tin học Lớp 12",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    topics: Mapped[List[Topic]] = relationship(
        "Topic",
        back_populates="grade",
        cascade="all, delete-orphan",
        order_by="Topic.order_index",
    )


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("grade_id", "code", name="uq_topics_grade_id_code"),
        UniqueConstraint("id", "grade_id", name="uq_topics_id_grade_id"),
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
    grade_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grades.id", ondelete="RESTRICT", name="fk_topics_grade"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        VARCHAR(20),
        nullable=False,
        comment="CS_A, ICT_B...",
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(150),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    grade: Mapped[Grade] = relationship(
        "Grade",
        back_populates="topics",
    )
    lessons: Mapped[List[Lesson]] = relationship(
        "Lesson",
        back_populates="topic",
        order_by="Lesson.order_index",
    )
    questions: Mapped[List[Question]] = relationship(
        "Question",
        back_populates="topic",
        primaryjoin="and_(Topic.id == foreign(Question.topic_id), Topic.grade_id == foreign(Question.grade_id))",
    )


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_lessons_slug"),
        Index("idx_lessons_topic_track", "topic_id", "track", "is_published"),
        CheckConstraint("estimated_duration_minutes > 0", name="ck_lessons_duration"),
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
        ForeignKey("topics.id", ondelete="RESTRICT", name="fk_lessons_topic"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        VARCHAR(250),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(250),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    track: Mapped[TrackType] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="lesson_track_enum"),
        nullable=False,
        default=TrackType.COMMON,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )
    is_published: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    is_free_preview: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    view_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    author_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_lessons_author"),
        nullable=False,
    )

    topic: Mapped[Topic] = relationship(
        "Topic",
        back_populates="lessons",
    )
    author: Mapped[User] = relationship(
        "User",
        back_populates="created_lessons",
        foreign_keys=[author_id],
    )
    content: Mapped[Optional[LessonContent]] = relationship(
        "LessonContent",
        back_populates="lesson",
        uselist=False,
        cascade="all, delete-orphan",
    )
    questions: Mapped[List[Question]] = relationship(
        "Question",
        back_populates="lesson",
        foreign_keys="[Question.lesson_id]",
    )
    attachments: Mapped[List[LessonAttachment]] = relationship(
        "LessonAttachment",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    mini_quiz_questions: Mapped[List[MiniQuizQuestion]] = relationship(
        "MiniQuizQuestion",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="MiniQuizQuestion.order_index",
    )
    user_progresses: Mapped[List[UserLessonProgress]] = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )


class LessonContent(Base):
    __tablename__ = "lesson_contents"
    __table_args__ = (
        UniqueConstraint("lesson_id", name="uq_lesson_contents_lesson"),
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
    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", name="fk_lesson_contents_lesson"),
        nullable=False,
    )
    markdown_body: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
    )
    html_compiled: Mapped[str | None] = mapped_column(
        LONGTEXT,
        nullable=True,
        default=None,
        comment="Bản HTML đã qua làm sạch Bleach",
    )
    key_takeaways: Mapped[Dict[str, Any] | List[Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Mảng JSON chứa các ý cốt lõi",
    )
    last_edited_by: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", name="fk_lesson_contents_editor"),
        nullable=True,
        default=None,
    )

    lesson: Mapped[Lesson] = relationship(
        "Lesson",
        back_populates="content",
    )
    last_editor: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="edited_lesson_contents",
        foreign_keys=[last_edited_by],
    )


class LessonAttachment(Base):
    __tablename__ = "lesson_attachments"
    __table_args__ = (
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
    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", name="fk_attachments_lesson"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(
        VARCHAR(500),
        nullable=False,
    )
    file_extension: Mapped[str] = mapped_column(
        VARCHAR(10),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lesson: Mapped[Lesson] = relationship(
        "Lesson",
        back_populates="attachments",
    )


class MiniQuizQuestion(Base):
    __tablename__ = "mini_quiz_questions"
    __table_args__ = (
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
    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", name="fk_mini_quiz_lesson"),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_image: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    lesson: Mapped[Lesson] = relationship(
        "Lesson",
        back_populates="mini_quiz_questions",
    )
    answers: Mapped[List[MiniQuizAnswer]] = relationship(
        "MiniQuizAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="MiniQuizAnswer.order_index",
    )


class MiniQuizAnswer(Base):
    __tablename__ = "mini_quiz_answers"
    __table_args__ = (
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
        ForeignKey("mini_quiz_questions.id", ondelete="CASCADE", name="fk_mini_quiz_answers_q"),
        nullable=False,
    )
    answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    question: Mapped[MiniQuizQuestion] = relationship(
        "MiniQuizQuestion",
        back_populates="answers",
    )


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
        CheckConstraint(
            "quiz_score IS NULL OR (quiz_score >= 0.00 AND quiz_score <= 100.00)",
            name="ck_ulp_score",
        ),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_ulp_user"),
        nullable=False,
    )
    lesson_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="CASCADE", name="fk_ulp_lesson"),
        nullable=False,
    )
    status: Mapped[LessonProgressStatus] = mapped_column(
        ENUM("InProgress", "Completed", name="lesson_progress_status_enum"),
        nullable=False,
        default=LessonProgressStatus.InProgress,
    )
    quiz_score: Mapped[Decimal | None] = mapped_column(
        DECIMAL(5, 2),
        nullable=True,
        default=None,
    )
    quiz_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_reading_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    lesson: Mapped[Lesson] = relationship(
        "Lesson",
        back_populates="user_progresses",
        foreign_keys=[lesson_id],
    )
