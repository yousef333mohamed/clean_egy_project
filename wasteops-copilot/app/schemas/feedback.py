"""Sanitized feedback request and aggregate response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user_feedback import FeedbackType


class FeedbackCreate(BaseModel):
    request_id: str | None = Field(default=None, max_length=64)
    rating: int = Field(ge=1, le=5)
    feedback_type: FeedbackType
    comment: str | None = Field(default=None, max_length=2000)
    expected_answer: str | None = Field(default=None, max_length=2000)


class FeedbackCreated(BaseModel):
    id: uuid.UUID
    request_id: str | None
    rating: int
    feedback_type: FeedbackType
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackSummary(BaseModel):
    total: int
    by_rating: dict[str, int]
    by_type: dict[str, int]
