# filepath: backend/app/models/flashcard.py
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
    from .curriculum import Grade, Lesson, Topic
    from .user import User


class GlossaryTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class TermType(str, enum.Enum):
    KEYWORD = "KEYWORD"
    SYNTAX = "SYNTAX"
    ALGORITHM = "ALGORITHM"
    NETWORK_HARDWARE = "NETWORK_HARDWARE"


class DeckTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_glossary_slug"),
        Index("ft_glossary_search", "term_name", "short_definition", mysql_prefix="FULLTEXT"),
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
    grade_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grades.id", ondelete="RESTRICT", name="fk_glossary_grade"),
        nullable=False,
    )
    topic_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("topics.id", ondelete="SET NULL", name="fk_glossary_topic"),
        nullable=True,
        default=None,
    )
    lesson_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("lessons.id", ondelete="SET NULL", name="fk_glossary_lesson"),
        nullable=True,
        default=None,
    )
    term_name: Mapped[str] = mapped_column(
        VARCHAR(150),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(160),
        nullable=False,
    )
    short_definition: Mapped[str] = mapped_column(
        VARCHAR(300),
        nullable=False,
    )
    full_explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    syntax_payload: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="template, parameters, return, examples",
    )
    track: Mapped[GlossaryTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="glossary_track_enum"),
        nullable=False,
        default=GlossaryTrack.COMMON,
    )
    term_type: Mapped[TermType] = mapped_column(
        ENUM("KEYWORD", "SYNTAX", "ALGORITHM", "NETWORK_HARDWARE", name="term_type_enum"),
        nullable=False,
        default=TermType.KEYWORD,
    )
    is_published: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )
    view_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
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

    grade: Mapped[Grade] = relationship(
        "Grade",
        foreign_keys=[grade_id],
    )
    topic: Mapped[Optional[Topic]] = relationship(
        "Topic",
        foreign_keys=[topic_id],
    )
    lesson: Mapped[Optional[Lesson]] = relationship(
        "Lesson",
        foreign_keys=[lesson_id],
    )
    user_bookmarks: Mapped[List[UserTermBookmark]] = relationship(
        "UserTermBookmark",
        back_populates="term",
        cascade="all, delete-orphan",
    )


class UserTermBookmark(Base):
    __tablename__ = "user_term_bookmarks"
    __table_args__ = (
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    term_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("glossary_terms.id", ondelete="CASCADE", name="fk_utb_term"),
        primary_key=True,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_utb_user"),
        primary_key=True,
    )
    note: Mapped[str | None] = mapped_column(
        VARCHAR(300),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    term: Mapped[GlossaryTerm] = relationship(
        "GlossaryTerm",
        back_populates="user_bookmarks",
        foreign_keys=[term_id],
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )


class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_flashcard_decks_slug"),
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
    grade_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("grades.id", ondelete="RESTRICT", name="fk_decks_grade"),
        nullable=False,
    )
    topic_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("topics.id", ondelete="SET NULL", name="fk_decks_topic"),
        nullable=True,
        default=None,
    )
    title: Mapped[str] = mapped_column(
        VARCHAR(200),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(220),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    track: Mapped[DeckTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="deck_track_enum"),
        nullable=False,
        default=DeckTrack.COMMON,
    )
    card_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_published: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_decks_creator"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    grade: Mapped[Grade] = relationship(
        "Grade",
        foreign_keys=[grade_id],
    )
    topic: Mapped[Optional[Topic]] = relationship(
        "Topic",
        foreign_keys=[topic_id],
    )
    creator: Mapped[User] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    cards: Mapped[List[Flashcard]] = relationship(
        "Flashcard",
        back_populates="deck",
        cascade="all, delete-orphan",
        order_by="Flashcard.order_index",
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
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
    deck_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("flashcard_decks.id", ondelete="CASCADE", name="fk_cards_deck"),
        nullable=False,
    )
    front_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    back_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    hint: Mapped[str | None] = mapped_column(
        VARCHAR(300),
        nullable=True,
        default=None,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    deck: Mapped[FlashcardDeck] = relationship(
        "FlashcardDeck",
        back_populates="cards",
        foreign_keys=[deck_id],
    )
    reviews: Mapped[List[UserCardReview]] = relationship(
        "UserCardReview",
        back_populates="card",
        cascade="all, delete-orphan",
    )


class UserCardReview(Base):
    __tablename__ = "user_card_reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_user_card"),
        Index("idx_user_card_due", "user_id", "next_review_at"),
        CheckConstraint("ease_factor >= 1.30", name="ck_ucr_ease_factor"),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_ucr_user"),
        nullable=False,
    )
    card_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("flashcards.id", ondelete="CASCADE", name="fk_ucr_card"),
        nullable=False,
    )
    repetition_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    ease_factor: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 2),
        nullable=False,
        default=Decimal("2.50"),
    )
    interval_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_quality: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="Điểm đánh giá lần gần nhất (1, 3, 4, 5)",
    )
    reviewed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_reviewed_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    next_review_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
    )
    card: Mapped[Flashcard] = relationship(
        "Flashcard",
        back_populates="reviews",
        foreign_keys=[card_id],
    )

