"""Typed ingestion API contracts."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ingestion_run import IngestionStatus


class IngestionRequest(BaseModel):
    """Options for one dataset ingestion."""

    force: bool = False


class IngestAllRequest(IngestionRequest):
    """Options shared by an ordered multi-dataset run."""

    dry_run: bool = False


class IngestionResult(BaseModel):
    """Stable summary returned by the service, CLI, and API."""

    run_id: uuid.UUID
    dataset: str
    source_filename: str
    status: IngestionStatus
    dry_run: bool
    total_rows: int = 0
    valid_rows: int = 0
    inserted_rows: int = 0
    duplicate_rows: int = 0
    rejected_rows: int = 0
    failed_rows: int = 0
    warnings: list[str] = Field(default_factory=list)
    rejection_report: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    error_message: str | None = None


class DiscoveredFileResponse(BaseModel):
    """Availability of one allow-listed dataset file."""

    dataset: str
    filename: str | None
    size_bytes: int | None
    available: bool


class IngestionRunResponse(BaseModel):
    """Persisted ingestion history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_name: str
    source_filename: str
    file_hash: str
    file_size_bytes: int
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime | None
    total_rows: int
    valid_rows: int
    inserted_rows: int
    duplicate_rows: int
    rejected_rows: int
    failed_rows: int
    dry_run: bool
    error_message: str | None
    metadata_json: dict


class IngestionRunPage(BaseModel):
    """Paginated ingestion history."""

    items: list[IngestionRunResponse]
    total: int
    limit: int
    offset: int
