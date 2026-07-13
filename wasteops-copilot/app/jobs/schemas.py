"""Safe job status schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobProgress(BaseModel):
    current: int = 0
    total: int = 0
    percentage: float = Field(default=0, ge=0, le=100)


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    progress: JobProgress = Field(default_factory=JobProgress)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    safe_error_message: str | None = None


class JobCreate(BaseModel):
    job_type: str
    reference_id: str = Field(pattern=r"^[A-Za-z0-9_.:/-]{1,255}$")
