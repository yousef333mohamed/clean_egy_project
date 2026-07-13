"""Read-only security audit API."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.dependencies import DatabaseSession
from app.audit.models import AuditEvent
from app.auth.dependencies import require_permission

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_permission("audit:read"))])


class AuditEventResponse(BaseModel):
    id: UUID
    event_type: str
    actor_subject_hash: str | None
    request_id: str | None
    route: str
    method: str
    status_code: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[AuditEventResponse])
async def list_audit_events(
    session: DatabaseSession,
    event_type: str | None = None,
    request_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditEvent]:
    query = select(AuditEvent)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if request_id:
        query = query.where(AuditEvent.request_id == request_id)
    return list((await session.execute(query.order_by(AuditEvent.created_at.desc()).limit(limit))).scalars())
