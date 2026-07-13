"""Queue facade that passes only database IDs and private object references."""

from datetime import UTC, datetime
from typing import Any
import uuid

from app.jobs.celery_app import celery_app

ALLOWED_JOB_TYPES = {"csv_ingestion", "document_ingestion", "evaluation", "report_generation", "retention_cleanup"}


def enqueue_job(job_type: str, *, reference_id: str, request_id: str, actor_hash: str) -> str:
    if job_type not in ALLOWED_JOB_TYPES:
        raise ValueError("Unsupported job type")
    job_id = str(uuid.uuid4())
    celery_app.backend.store_result(
        job_id,
        {"job_type": job_type, "current": 0, "total": 0, "created_at": datetime.now(UTC).isoformat(), "actor_hash": actor_hash},
        state="PENDING",
    )
    celery_app.send_task(
        "wasteops.execute_job",
        task_id=job_id,
        kwargs={"job_type": job_type, "reference_id": reference_id, "request_id": request_id, "actor_hash": actor_hash},
    )
    return job_id


def safe_job_metadata(result: Any) -> dict[str, Any]:
    metadata = result.info if isinstance(result.info, dict) else {}
    return {key: metadata[key] for key in ("job_type", "current", "total", "created_at", "started_at", "completed_at") if key in metadata}
