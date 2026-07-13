"""Sanitized end-user feedback linked to a request identifier."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FeedbackType(str, enum.Enum):
    HELPFUL = "HELPFUL"
    NOT_HELPFUL = "NOT_HELPFUL"
    INCORRECT_DATA = "INCORRECT_DATA"
    MISSING_SOURCE = "MISSING_SOURCE"
    BAD_RECOMMENDATION = "BAD_RECOMMENDATION"
    UNSAFE = "UNSAFE"
    OTHER = "OTHER"


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_user_feedback_rating"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType, name="feedback_type"), nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text)
    expected_answer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
