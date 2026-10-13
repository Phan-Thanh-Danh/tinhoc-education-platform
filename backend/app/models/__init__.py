# filepath: backend/app/models/__init__.py
from __future__ import annotations

from .base import AuditMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin
from .curriculum import Grade, Lesson, LessonContent, Topic, TrackType
from .exam import (
    Exam,
    ExamQuestion,
    ExamQuestionType,
    ExamSubmission,
    ExamSubmissionAnswer,
    ExamTrack,
    ExamType,
    SubmissionStatus,
    UserWrongQuestion,
)
from .question import (
    DifficultyLevel,
    Question,
    QuestionStatus,
    QuestionTag,
    QuestionTagMapping,
    QuestionTrack,
    QuestionType,
)
from .user import (
    RefreshToken,
    Role,
    TrackPreference,
    User,
    UserRole,
    UserStatus,
    VerificationCode,
    VerificationCodeType,
)

__all__ = [
    # Base & Mixins
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "AuditMixin",
    # User & Auth
    "User",
    "Role",
    "UserRole",
    "RefreshToken",
    "VerificationCode",
    "TrackPreference",
    "UserStatus",
    "VerificationCodeType",
    # Curriculum
    "Grade",
    "Topic",
    "Lesson",
    "LessonContent",
    "TrackType",
    # Question Bank
    "Question",
    "QuestionTag",
    "QuestionTagMapping",
    "QuestionType",
    "QuestionTrack",
    "DifficultyLevel",
    "QuestionStatus",
    # Exam & Submissions
    "Exam",
    "ExamQuestion",
    "ExamSubmission",
    "ExamSubmissionAnswer",
    "UserWrongQuestion",
    "ExamTrack",
    "ExamType",
    "SubmissionStatus",
    "ExamQuestionType",
]

