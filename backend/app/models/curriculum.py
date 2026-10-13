# filepath: backend/app/models/curriculum.py
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
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

