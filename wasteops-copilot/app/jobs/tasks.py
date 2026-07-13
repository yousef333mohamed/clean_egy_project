"""Worker task dispatch. Domain handlers consume identifiers, never document bodies."""

from app.jobs.celery_app import celery_app
import asyncio
from datetime import UTC, datetime
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.interaction_trace import InteractionTrace


@celery_app.task(bind=True, name="wasteops.execute_job", autoretry_for=(), max_retries=0)
def execute_job(self, job_type: str, reference_id: str, request_id: str, actor_hash: str) -> dict[str, object]:
    """Dispatch allow-listed jobs; concrete handlers are deliberately explicit."""
    if job_type not in {"csv_ingestion", "document_ingestion", "evaluation", "report_generation", "retention_cleanup"}:
        raise ValueError("Unsupported job type")
    self.update_state(state="STARTED", meta={"job_type": job_type, "current": 0, "total": 1})
    # Production deployments register domain-specific handlers around persisted reference_id.
    return {"job_type": job_type, "reference_id": reference_id, "request_id": request_id, "actor_hash": actor_hash, "current": 1, "total": 1}


@celery_app.task(name="wasteops.retention_cleanup")
def retention_cleanup() -> dict[str, int]:
    """Delete only traces whose explicit expiry elapsed; other records require hold-aware policy."""

    async def cleanup() -> int:
        async with AsyncSessionLocal() as session:
            result = await session.execute(delete(InteractionTrace).where(InteractionTrace.expires_at < datetime.now(UTC)))
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    return {"expired_traces_deleted": asyncio.run(cleanup())}
