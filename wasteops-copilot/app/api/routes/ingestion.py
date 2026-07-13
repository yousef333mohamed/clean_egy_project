"""Development CSV ingestion and audit-history endpoints."""

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.dependencies import DatabaseSession
from app.core.config import Settings, get_settings
from app.ingestion.file_discovery import discover_files
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.registry import DATASET_REGISTRY
from app.models import IngestionRun, IngestionStatus
from app.schemas.ingestion import (
    DiscoveredFileResponse,
    IngestAllRequest,
    IngestionRequest,
    IngestionResult,
    IngestionRunPage,
    IngestionRunResponse,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
AppSettings = Annotated[Settings, Depends(get_settings)]


def _require_dataset(dataset_name: str) -> None:
    if dataset_name not in DATASET_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown dataset")


def _require_enabled(settings: Settings) -> None:
    if not settings.enable_ingestion_api:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ingestion API is disabled")


@router.get("/files", response_model=list[DiscoveredFileResponse])
async def list_files(settings: AppSettings) -> list[DiscoveredFileResponse]:
    """Discover registry-approved canonical filenames and aliases."""
    return [
        DiscoveredFileResponse(
            dataset=item.dataset,
            filename=item.filename,
            size_bytes=item.size_bytes,
            available=item.available,
        )
        for item in discover_files(Path(settings.data_dir) / "raw")
    ]


@router.post("/validate/{dataset_name}", response_model=IngestionResult)
async def validate_dataset(dataset_name: str, session: DatabaseSession, settings: AppSettings) -> IngestionResult:
    """Run full validation without inserting source records."""
    _require_enabled(settings)
    _require_dataset(dataset_name)
    try:
        return await IngestionService(session, settings=settings).ingest_dataset(dataset_name, dry_run=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/csv/{dataset_name}", response_model=IngestionResult)
async def ingest_dataset(dataset_name: str, request: IngestionRequest, session: DatabaseSession, settings: AppSettings) -> IngestionResult:
    """Ingest one allow-listed dataset."""
    _require_enabled(settings)
    _require_dataset(dataset_name)
    try:
        result = await IngestionService(session, settings=settings).ingest_dataset(dataset_name, force=request.force)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if result.status == IngestionStatus.SKIPPED_DUPLICATE and not request.force:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dataset file was already ingested")
    return result


@router.post("/csv", response_model=list[IngestionResult])
async def ingest_all(request: IngestAllRequest, session: DatabaseSession, settings: AppSettings) -> list[IngestionResult]:
    """Ingest every available source in dependency order."""
    _require_enabled(settings)
    return await IngestionService(session, settings=settings).ingest_all(dry_run=request.dry_run, force=request.force)


@router.get("/runs/{run_id}", response_model=IngestionRunResponse)
async def get_run(run_id: uuid.UUID, session: DatabaseSession) -> IngestionRun:
    """Return one persisted ingestion attempt."""
    run = await session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion run not found")
    return run


@router.get("/runs", response_model=IngestionRunPage)
async def list_runs(
    session: DatabaseSession,
    dataset: str | None = None,
    run_status: Annotated[IngestionStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> IngestionRunPage:
    """List recent attempts with filters and bounded pagination."""
    filters = []
    if dataset is not None:
        _require_dataset(dataset)
        filters.append(IngestionRun.dataset_name == dataset)
    if run_status is not None:
        filters.append(IngestionRun.status == run_status)
    total = await session.scalar(select(func.count()).select_from(IngestionRun).where(*filters))
    statement = select(IngestionRun).where(*filters).order_by(IngestionRun.started_at.desc()).limit(limit).offset(offset)
    items = list((await session.scalars(statement)).all())
    return IngestionRunPage(items=items, total=total or 0, limit=limit, offset=offset)
