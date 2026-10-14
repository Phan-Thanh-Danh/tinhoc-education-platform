# filepath: backend/app/models/forum.py
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
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, LONGTEXT, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base

if TYPE_CHECKING:
    from .curriculum import Lesson
    from .question import Question
    from .user import User


class ForumPostTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class ForumPostStatus(str, enum.Enum):
    Published = "Published"
    PendingReview = "PendingReview"
    Locked = "Locked"
    Hidden = "Hidden"


class ForumAnswerStatus(str, enum.Enum):
    Published = "Published"
    Hidden = "Hidden"
    Deleted = "Deleted"


class ForumVoteTargetType(str, enum.Enum):
    POST = "POST"
    ANSWER = "ANSWER"


class ForumCategory(Base):
    __tablename__ = "forum_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_forum_categories_code"),
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
    icon_url: Mapped[str | None] = mapped_column(
        VARCHAR(500),
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

    posts: Mapped[List[ForumPost]] = relationship(
        "ForumPost",
        back_populates="category",
    )


class ForumPost(Base):
    __tablename__ = "forum_posts"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_forum_posts_slug"),
        Index("idx_forum_posts_feed", "category_id", "status", "last_activity_at"),
        Index("ft_forum_posts_title", "title", mysql_prefix="FULLTEXT"),
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
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("forum_categories.id", ondelete="RESTRICT", name="fk_posts_category"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_posts_creator"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(280),
        nullable=False,
    )
    content_markdown: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
    )
    code_snippet: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    track: Mapped[ForumPostTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="forum_post_track_enum"),
        nullable=False,
        default=ForumPostTrack.COMMON,
    )
    context_lesson_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="SET NULL", name="fk_posts_lesson"),
        nullable=True,
        default=None,
    )
    context_question_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="SET NULL", name="fk_posts_question"),
        nullable=True,
        default=None,
    )
    status: Mapped[ForumPostStatus] = mapped_column(
        ENUM("Published", "PendingReview", "Locked", "Hidden", name="forum_post_status_enum"),
        nullable=False,
        default=ForumPostStatus.Published,
    )
    is_resolved: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    accepted_answer_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        nullable=True,
        default=None,
        comment="Single Source of Truth cho câu trả lời được chấp nhận",
    )
    vote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    answer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    category: Mapped[ForumCategory] = relationship(
        "ForumCategory",
        back_populates="posts",
        foreign_keys=[category_id],
    )
    creator: Mapped[User] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    context_lesson: Mapped[Optional[Lesson]] = relationship(
        "Lesson",
        foreign_keys=[context_lesson_id],
    )
    context_question: Mapped[Optional[Question]] = relationship(
        "Question",
        foreign_keys=[context_question_id],
    )
    answers: Mapped[List[ForumAnswer]] = relationship(
        "ForumAnswer",
        back_populates="post",
        cascade="all, delete-orphan",
        foreign_keys="[ForumAnswer.post_id]",
    )
    tags: Mapped[List[ForumTag]] = relationship(
        "ForumTag",
        secondary="forum_post_tags",
        back_populates="posts",
        viewonly=True,
    )
    post_tags: Mapped[List[ForumPostTag]] = relationship(
        "ForumPostTag",
        back_populates="post",
        cascade="all, delete-orphan",
    )


class ForumAnswer(Base):
    __tablename__ = "forum_answers"
    __table_args__ = (
        Index("idx_answers_post", "post_id", "vote_count"),
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
    post_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("forum_posts.id", ondelete="CASCADE", name="fk_answers_post"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_answers_creator"),
        nullable=False,
    )
    content_markdown: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
    )
    code_snippet: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    vote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_accepted: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
        comment="Trường suy diễn, cập nhật đồng bộ cùng forum_posts.accepted_answer_id",
    )
    is_teacher_answer: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    status: Mapped[ForumAnswerStatus] = mapped_column(
        ENUM("Published", "Hidden", "Deleted", name="forum_answer_status_enum"),
        nullable=False,
        default=ForumAnswerStatus.Published,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        onupdate=func.now(),
    )

    post: Mapped[ForumPost] = relationship(
        "ForumPost",
        back_populates="answers",
        foreign_keys=[post_id],
    )
    creator: Mapped[User] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    comments: Mapped[List[ForumComment]] = relationship(
        "ForumComment",
        back_populates="answer",
        cascade="all, delete-orphan",
    )


class ForumComment(Base):
    __tablename__ = "forum_comments"
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
    answer_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("forum_answers.id", ondelete="CASCADE", name="fk_comments_answer"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_comments_user"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        VARCHAR(1000),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    answer: Mapped[ForumAnswer] = relationship(
        "ForumAnswer",
        back_populates="comments",
        foreign_keys=[answer_id],
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class ForumVote(Base):
    __tablename__ = "forum_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_user_vote_target"),
        CheckConstraint("vote_value IN (1, -1)", name="ck_forum_votes_value"),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_forum_votes_user"),
        nullable=False,
    )
    target_type: Mapped[ForumVoteTargetType] = mapped_column(
        ENUM("POST", "ANSWER", name="forum_vote_target_type_enum"),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
        comment="UUID của post hoặc answer, kiểm soát toàn vẹn bằng Application Transaction",
    )
    vote_value: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="+1 hoặc -1",
    )
    voted_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class ForumTag(Base):
    __tablename__ = "forum_tags"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_forum_tags_slug"),
        UniqueConstraint("tag_name", name="uq_forum_tags_name"),
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
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    tag_mappings: Mapped[List[ForumPostTag]] = relationship(
        "ForumPostTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    posts: Mapped[List[ForumPost]] = relationship(
        "ForumPost",
        secondary="forum_post_tags",
        back_populates="tags",
        viewonly=True,
    )


class ForumPostTag(Base):
    __tablename__ = "forum_post_tags"
    __table_args__ = (
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    post_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("forum_posts.id", ondelete="CASCADE", name="fk_fpt_post"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("forum_tags.id", ondelete="CASCADE", name="fk_fpt_tag"),
        primary_key=True,
    )

    post: Mapped[ForumPost] = relationship(
        "ForumPost",
        back_populates="post_tags",
        foreign_keys=[post_id],
    )
    tag: Mapped[ForumTag] = relationship(
        "ForumTag",
        back_populates="tag_mappings",
        foreign_keys=[tag_id],
    )
