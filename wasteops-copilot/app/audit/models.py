"""Append-only audit event model."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditEvent(Base):
    """Security-relevant action without request bodies or credentials."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_actor_created", "actor_subject_hash", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor_subject_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    actor_roles: Mapped[list[str]] = mapped_column(JSONB, default=list)
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    route: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int]
    resource_type: Mapped[str | None] = mapped_column(String(80))
    resource_id_hash: Mapped[str | None] = mapped_column(String(64))
    source_ip_hash: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
