"""Ingestion endpoints."""

from fastapi import APIRouter
from app.api.dependencies import SessionDep, SettingsDep
from app.ingestion.csv_loader import CSVLoader
from app.ingestion.embeddings import DocumentIngestor
from app.schemas.ingestion import DocumentIngestionRequest, IngestionRequest, IngestionSummary

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/csv", response_model=IngestionSummary)
async def ingest_csv(request: IngestionRequest, session: SessionDep, settings: SettingsDep) -> IngestionSummary:
    """Load selected raw CSV datasets idempotently."""
    return await CSVLoader(session, settings.data_dir / "raw").ingest(request.filenames)


@router.post("/documents", response_model=IngestionSummary)
async def ingest_documents(request: DocumentIngestionRequest, session: SessionDep, settings: SettingsDep) -> IngestionSummary:
    """Extract, embed, and store selected knowledge documents."""
    return await DocumentIngestor(session, settings).ingest(request)
