"""Safe background-job status and cancellation APIs."""

from datetime import UTC, datetime

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth.dependencies import CurrentUser, require_any_permission
from app.jobs.celery_app import celery_app
from app.audit.sanitization import safe_hash
from app.jobs.queue import enqueue_job, safe_job_metadata
from app.jobs.schemas import JobCreate, JobProgress, JobResponse, JobStatus

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_any_permission("datasets:read", "documents:read", "evaluations:read", "analytics:read", "system:configure"))],
)
JOB_PERMISSION = {
    "csv_ingestion": "datasets:read",
    "document_ingestion": "documents:read",
    "evaluation": "evaluations:read",
    "report_generation": "analytics:read",
    "retention_cleanup": "system:configure",
}


def _response(job_id: str) -> JobResponse:
    result = AsyncResult(job_id, app=celery_app)
    metadata = safe_job_metadata(result)
    state = {"STARTED": JobStatus.RUNNING, "SUCCESS": JobStatus.COMPLETED, "FAILURE": JobStatus.FAILED, "REVOKED": JobStatus.CANCELLED}.get(
        result.state, JobStatus.PENDING
    )
    current, total = int(metadata.get("current", 0)), int(metadata.get("total", 0))
    return JobResponse(
        job_id=job_id,
        job_type=str(metadata.get("job_type", "unknown")),
        status=state,
        progress=JobProgress(current=current, total=total, percentage=(current / total * 100) if total else 0),
        created_at=datetime.now(UTC),
        safe_error_message="Job failed; use the request ID when contacting support." if state == JobStatus.FAILED else None,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, user: CurrentUser) -> JobResponse:
    if len(job_id) > 100 or not all(char.isalnum() or char in "-_" for char in job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    response = _response(job_id)
    required = JOB_PERMISSION.get(response.job_type, "system:configure")
    if required not in user.permissions:
        raise HTTPException(status_code=404, detail="Job not found")
    return response


@router.get("", response_model=list[JobResponse])
async def list_jobs(_: CurrentUser, job_ids: str = Query(default="", max_length=1000)) -> list[JobResponse]:
    """Return only explicitly requested IDs; the queue backend is not an authorization index."""
    return [_response(item) for item in job_ids.split(",")[:50] if item and len(item) <= 100]


@router.post("", response_model=JobResponse, status_code=202)
async def create_job(payload: JobCreate, request: Request, user: CurrentUser) -> JobResponse:
    required = JOB_PERMISSION.get(payload.job_type)
    if not required or required not in user.permissions:
        raise HTTPException(status_code=403, detail="Job type is not permitted")
    job_id = enqueue_job(
        payload.job_type,
        reference_id=payload.reference_id,
        request_id=getattr(request.state, "request_id", "unknown"),
        actor_hash=safe_hash(user.subject) or "unknown",
    )
    return JobResponse(job_id=job_id, job_type=payload.job_type, status=JobStatus.PENDING, created_at=datetime.now(UTC))


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str, user: CurrentUser) -> JobResponse:
    response = _response(job_id)
    required = JOB_PERMISSION.get(response.job_type, "system:configure")
    if required not in user.permissions:
        raise HTTPException(status_code=404, detail="Job not found")
    celery_app.control.revoke(job_id, terminate=False)
    return response
