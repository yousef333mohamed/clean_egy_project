"""Sanitized user-feedback submission and administrative aggregates."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.models.user_feedback import UserFeedback
from app.observability.sanitization import sanitize_text
from app.schemas.feedback import FeedbackCreate, FeedbackCreated, FeedbackSummary

router = APIRouter(prefix="/feedback", tags=["feedback"])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _enabled(settings: Settings) -> None:
    if not settings.enable_feedback_api:
        raise HTTPException(status_code=403, detail="Feedback API is disabled")


@router.post("", response_model=FeedbackCreated, status_code=201)
async def submit_feedback(request: FeedbackCreate, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    record = UserFeedback(request_id=request.request_id, rating=request.rating, feedback_type=request.feedback_type,
        comment=sanitize_text(request.comment, max_length=2000, reject_html=True) if request.comment else None,
        expected_answer=sanitize_text(request.expected_answer, max_length=2000, reject_html=True) if request.expected_answer else None)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/summary", response_model=FeedbackSummary)
async def feedback_summary(session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    total = (await session.execute(select(func.count(UserFeedback.id)))).scalar_one()
    ratings = (await session.execute(select(UserFeedback.rating, func.count(UserFeedback.id)).group_by(UserFeedback.rating))).all()
    types = (await session.execute(select(UserFeedback.feedback_type, func.count(UserFeedback.id)).group_by(UserFeedback.feedback_type))).all()
    return FeedbackSummary(total=total, by_rating={str(key): count for key, count in ratings}, by_type={key.value: count for key, count in types})
