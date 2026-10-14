# filepath: backend/app/models/exam.py
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import CHAR, DATETIME, ENUM, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .base import Base

if TYPE_CHECKING:
    from .question import Question
    from .user import User


class ExamTrack(str, enum.Enum):
    COMMON = "COMMON"
    ICT = "ICT"
    CS = "CS"


class ExamType(str, enum.Enum):
    MOCK_EXAM = "MOCK_EXAM"
    TOPIC_PRACTICE = "TOPIC_PRACTICE"


class SubmissionStatus(str, enum.Enum):
    InProgress = "InProgress"
    Submitted = "Submitted"
    TimedOut = "TimedOut"
    Cancelled = "Cancelled"


class RoomStatus(str, enum.Enum):
    Scheduled = "Scheduled"
    Opening = "Opening"
    Closed = "Closed"


class ExamQuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_exams_slug"),
        CheckConstraint("duration_minutes > 0", name="ck_exams_duration"),
        CheckConstraint("total_questions > 0", name="ck_exams_total_questions"),
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
    title: Mapped[str] = mapped_column(
        VARCHAR(250),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        VARCHAR(250),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(500),
        nullable=True,
        default=None,
    )
    track: Mapped[ExamTrack] = mapped_column(
        ENUM("COMMON", "ICT", "CS", name="exam_track_enum"),
        nullable=False,
        default=ExamTrack.COMMON,
    )
    exam_type: Mapped[ExamType] = mapped_column(
        ENUM("MOCK_EXAM", "TOPIC_PRACTICE", name="exam_type_enum"),
        nullable=False,
        default=ExamType.MOCK_EXAM,
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=28,
    )
    max_score: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 2),
        nullable=False,
        default=Decimal("10.00"),
    )
    is_published: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
    )
    created_by: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_exams_creator"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    creator: Mapped[User] = relationship(
        "User",
        back_populates="created_exams",
        foreign_keys=[created_by],
    )
    exam_questions: Mapped[List[ExamQuestion]] = relationship(
        "ExamQuestion",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="ExamQuestion.order_index",
    )
    submissions: Mapped[List[ExamSubmission]] = relationship(
        "ExamSubmission",
        back_populates="exam",
    )
    virtual_rooms: Mapped[List[VirtualExamRoom]] = relationship(
        "VirtualExamRoom",
        back_populates="exam",
    )


class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "order_index", name="uq_exam_questions_order"),
        CheckConstraint("order_index >= 1", name="ck_exam_questions_order"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_0900_ai_ci",
        },
    )

    exam_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("exams.id", ondelete="CASCADE", name="fk_exam_questions_exam"),
        primary_key=True,
    )
    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="RESTRICT", name="fk_exam_questions_question"),
        primary_key=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Thứ tự từ 1 đến 28",
    )
    point_weight: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2),
        nullable=False,
        default=Decimal("0.25"),
    )

    exam: Mapped[Exam] = relationship(
        "Exam",
        back_populates="exam_questions",
    )
    question: Mapped[Question] = relationship(
        "Question",
        back_populates="exam_questions",
    )


class ExamSubmission(Base):
    __tablename__ = "exam_submissions"
    __table_args__ = (
        Index("idx_submissions_user_exam", "user_id", "exam_id", "status"),
        CheckConstraint(
            "(total_score IS NULL) OR "
            "(total_score >= 0.00 AND total_score <= 10.00 AND (score_part1 + score_part2 + COALESCE(score_part3, 0.00) = total_score))",
            name="ck_submissions_scores",
        ),
        CheckConstraint("expires_at > started_at", name="ck_submissions_timer"),
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
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_submissions_user"),
        nullable=False,
    )
    exam_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("exams.id", ondelete="RESTRICT", name="fk_submissions_exam"),
        nullable=False,
    )
    room_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        nullable=True,
        default=None,
        comment="NULL nếu tự luyện tập, có giá trị nếu thi tại phòng thi ảo",
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        ENUM("InProgress", "Submitted", "TimedOut", "Cancelled", name="submission_status_enum"),
        nullable=False,
        default=SubmissionStatus.InProgress,
    )
    started_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        comment="Thời hạn đóng máy chủ = started_at + duration + 15 giây dung sai mạng",
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DATETIME,
        nullable=True,
        default=None,
    )
    score_part1: Mapped[Decimal | None] = mapped_column(
        DECIMAL(4, 2),
        nullable=True,
        default=None,
        comment="Phần I: MCQ (Tối đa 6.00)",
    )
    score_part2: Mapped[Decimal | None] = mapped_column(
        DECIMAL(4, 2),
        nullable=True,
        default=None,
        comment="Phần II: Đúng/Sai lũy tiến (Tối đa 4.00)",
    )
    score_part3: Mapped[Decimal | None] = mapped_column(
        DECIMAL(4, 2),
        nullable=True,
        default=None,
        comment="Phần III: Trả lời ngắn (Nếu đề thi mở rộng)",
    )
    total_score: Mapped[Decimal | None] = mapped_column(
        DECIMAL(4, 2),
        nullable=True,
        default=None,
        comment="Tổng điểm chuẩn 10.00",
    )
    content_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Bản chụp đề bài phát cho thí sinh (Không có đáp án)",
    )
    grading_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="ĐÓNG BĂNG ĐÁP ÁN CHUẨN, VERSION VÀ CÔNG THỨC CHẤM TẠI THỜI ĐIỂM THI",
    )
    ip_address: Mapped[str | None] = mapped_column(
        VARCHAR(45),
        nullable=True,
        default=None,
    )
    violation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Số lần rời màn hình thi",
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="exam_submissions",
        foreign_keys=[user_id],
    )
    exam: Mapped[Exam] = relationship(
        "Exam",
        back_populates="submissions",
        foreign_keys=[exam_id],
    )
    answers: Mapped[List[ExamSubmissionAnswer]] = relationship(
        "ExamSubmissionAnswer",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ExamSubmissionAnswer.order_index",
    )
    wrong_questions: Mapped[List[UserWrongQuestion]] = relationship(
        "UserWrongQuestion",
        back_populates="last_submission",
    )
    room_participant: Mapped[Optional[ExamRoomParticipant]] = relationship(
        "ExamRoomParticipant",
        back_populates="submission",
        uselist=False,
    )


class ExamSubmissionAnswer(Base):
    __tablename__ = "exam_submission_answers"
    __table_args__ = (
        UniqueConstraint("submission_id", "order_index", name="uq_sub_answers_question"),
        Index("idx_sub_answers_lookup", "submission_id", "is_correct"),
        CheckConstraint("earned_score >= 0.00", name="ck_sub_answers_score"),
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
    submission_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("exam_submissions.id", ondelete="CASCADE", name="fk_sub_answers_submission"),
        nullable=False,
    )
    question_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="SET NULL", name="fk_sub_answers_question"),
        nullable=True,
        default=None,
        comment="SET NULL nếu câu hỏi gốc bị dọn dẹp vật lý, toàn bộ dữ liệu đối soát nằm ở snapshot",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    question_type: Mapped[ExamQuestionType] = mapped_column(
        ENUM("MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER", name="submission_answer_type_enum"),
        nullable=False,
    )
    student_answer: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment='Dữ liệu chọn: "A" hoặc {"a":true,"b":false,"c":true,"d":false} hoặc "2000"',
    )
    is_correct: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
        comment="1: Đúng tuyệt đối, 0: Sai hoặc đúng một phần",
    )
    earned_score: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    grading_details: Mapped[Dict[str, Any] | List[Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
        comment="Chi tiết đối soát từng ý (a,b,c,d) phục vụ xem lại bài thi",
    )

    submission: Mapped[ExamSubmission] = relationship(
        "ExamSubmission",
        back_populates="answers",
    )
    question: Mapped[Optional[Question]] = relationship(
        "Question",
        back_populates="submission_answers",
    )


class UserWrongQuestion(Base):
    __tablename__ = "user_wrong_questions"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_user_wrong_question"),
        Index("idx_user_wrong_resolved", "user_id", "is_resolved"),
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
        ForeignKey("users.id", ondelete="CASCADE", name="fk_uwq_user"),
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("questions.id", ondelete="CASCADE", name="fk_uwq_question"),
        nullable=False,
    )
    last_submission_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("exam_submissions.id", ondelete="SET NULL", name="fk_uwq_submission"),
        nullable=True,
        default=None,
        comment="SET NULL khi bài nộp bị xóa, không làm mất sổ tay câu sai",
    )
    question_type: Mapped[ExamQuestionType] = mapped_column(
        ENUM("MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER", name="wrong_question_type_enum"),
        nullable=False,
    )
    lowest_score: Mapped[Decimal] = mapped_column(
        DECIMAL(4, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Điểm thấp nhất từng bị mất",
    )
    is_resolved: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=False,
        comment="1: Đã làm lại đúng hoàn toàn trong phiên luyện tập",
    )
    wrong_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Số lần làm sai trong lịch sử",
    )
    last_practiced_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="wrong_questions",
        foreign_keys=[user_id],
    )
    question: Mapped[Question] = relationship(
        "Question",
        back_populates="wrong_questions",
        foreign_keys=[question_id],
    )
    last_submission: Mapped[Optional[ExamSubmission]] = relationship(
        "ExamSubmission",
        back_populates="wrong_questions",
        foreign_keys=[last_submission_id],
    )


class VirtualExamRoom(Base):
    __tablename__ = "virtual_exam_rooms"
    __table_args__ = (
        CheckConstraint("close_time > open_time", name="ck_rooms_time"),
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
    exam_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("exams.id", ondelete="RESTRICT", name="fk_rooms_exam"),
        nullable=False,
    )
    room_name: Mapped[str] = mapped_column(
        VARCHAR(200),
        nullable=False,
    )
    open_time: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
    )
    close_time: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
    )
    status: Mapped[RoomStatus] = mapped_column(
        ENUM("Scheduled", "Opening", "Closed", name="room_status_enum"),
        nullable=False,
        default=RoomStatus.Scheduled,
    )
    is_leaderboard_public: Mapped[bool] = mapped_column(
        TINYINT(1),
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME,
        nullable=False,
        server_default=func.now(),
    )

    exam: Mapped[Exam] = relationship(
        "Exam",
        back_populates="virtual_rooms",
        foreign_keys=[exam_id],
    )
    participants: Mapped[List[ExamRoomParticipant]] = relationship(
        "ExamRoomParticipant",
        back_populates="room",
        cascade="all, delete-orphan",
    )


class ExamRoomParticipant(Base):
    __tablename__ = "exam_room_participants"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_user"),
        Index("idx_room_leaderboard", "room_id", "final_score", "completion_time_seconds"),
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
    room_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("virtual_exam_rooms.id", ondelete="CASCADE", name="fk_participants_room"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_participants_user"),
        nullable=False,
    )
    submission_id: Mapped[str | None] = mapped_column(
        CHAR(36),
        ForeignKey("exam_submissions.id", ondelete="SET NULL", name="fk_participants_sub"),
        nullable=True,
        default=None,
    )
    final_score: Mapped[Decimal | None] = mapped_column(
        DECIMAL(4, 2),
        nullable=True,
        default=None,
    )
    completion_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    leaderboard_rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="Cập nhật tự động sau khi phòng thi đóng hoặc khi nộp bài",
    )

    room: Mapped[VirtualExamRoom] = relationship(
        "VirtualExamRoom",
        back_populates="participants",
        foreign_keys=[room_id],
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="room_participations",
        foreign_keys=[user_id],
    )
    submission: Mapped[Optional[ExamSubmission]] = relationship(
        "ExamSubmission",
        back_populates="room_participant",
        foreign_keys=[submission_id],
    )

