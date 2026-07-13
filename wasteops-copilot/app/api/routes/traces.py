"""Administrative safe trace summaries; never returns content, prompts, SQL, or embeddings."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.models.interaction_trace import InteractionTrace
from app.observability.sanitization import sanitize
from app.schemas.tracing import TracePage, TraceSummary

router = APIRouter(prefix="/traces", tags=["traces"])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _enabled(settings: Settings) -> None:
    if not settings.enable_trace_api:
        raise HTTPException(status_code=403, detail="Trace API is disabled")


def _summary(item: InteractionTrace) -> TraceSummary:
    return TraceSummary(id=item.id, request_id=item.request_id, parent_trace_id=item.parent_trace_id, trace_type=item.trace_type, route=item.route,
        status=item.status, started_at=item.started_at, duration_ms=item.duration_ms, provider=item.provider, model=item.model, prompt_key=item.prompt_key,
        prompt_version=item.prompt_version, metrics=sanitize(item.metrics_json), error_category=item.error_category)


@router.get("", response_model=TracePage)
async def list_traces(session: DatabaseSession, settings: AppSettings, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    _enabled(settings)
    items = list((await session.execute(select(InteractionTrace).order_by(InteractionTrace.started_at.desc()).offset(offset).limit(limit))).scalars())
    return TracePage(items=[_summary(item) for item in items], offset=offset, limit=limit)


@router.get("/{request_id}", response_model=list[TraceSummary])
async def traces_for_request(request_id: str, session: DatabaseSession, settings: AppSettings):
    _enabled(settings)
    items = list((await session.execute(select(InteractionTrace).where(InteractionTrace.request_id == request_id).order_by(InteractionTrace.started_at))).scalars())
    if not items:
        raise HTTPException(status_code=404, detail="Trace not found")
    return [_summary(item) for item in items]
