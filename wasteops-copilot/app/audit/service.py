"""Append-only audit persistence."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent


async def record_audit_event(session: AsyncSession, **values: object) -> None:
    """Append an event. Deliberately no update/delete service exists."""
    session.add(AuditEvent(**values))
    await session.commit()
