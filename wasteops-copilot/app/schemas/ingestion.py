"""Ingestion contracts."""

from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    filenames: list[str] | None = None


class DocumentIngestionRequest(BaseModel):
    filenames: list[str] | None = None
    department: str | None = None
    asset_type: str | None = None
    region: str | None = None
    effective_date: str | None = None
    version: str | None = None


class FileIngestionSummary(BaseModel):
    filename: str
    total_rows: int = 0
    inserted_rows: int = 0
    duplicate_rows: int = 0
    failed_rows: int = 0
    errors: list[str] = Field(default_factory=list)


class IngestionSummary(BaseModel):
    files: list[FileIngestionSummary]
    inserted_rows: int
    duplicate_rows: int
    failed_rows: int
