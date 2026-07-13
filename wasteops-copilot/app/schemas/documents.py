"""Document metadata, ingestion, and API response schemas."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.knowledge_document import DocumentStatus


class DocumentMetadata(BaseModel):
    """Validated optional metadata from sidecars, CLI, or API overrides."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, max_length=500)
    document_type: str | None = Field(default=None, max_length=80)
    department: str | None = Field(default=None, max_length=120)
    asset_type: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    effective_date: date | None = None
    version: str | None = Field(default=None, max_length=40)
    language: Literal["en", "ar", "mixed", "unknown"] | None = None
    is_synthetic: bool | None = None
    authority_level: Literal["official", "demo_only", "unknown"] | None = None
    expiration_date: date | None = None

    @model_validator(mode="after")
    def validate_authority(self) -> "DocumentMetadata":
        if self.authority_level == "demo_only" and self.is_synthetic is not True:
            raise ValueError("demo_only metadata requires is_synthetic=true")
        if self.authority_level == "official" and self.is_synthetic is not False:
            raise ValueError("official metadata requires is_synthetic=false")
        return self


class DocumentPathRequest(BaseModel):
    """Safe relative document path for validation."""

    relative_path: str = Field(min_length=1, max_length=1024)


class DocumentIngestRequest(DocumentPathRequest):
    """One-document ingestion request."""

    force: bool = False
    metadata: DocumentMetadata | None = None


class DocumentIngestAllRequest(BaseModel):
    """Options for an ordered document-directory ingestion."""

    force: bool = False
    dry_run: bool = False


class DiscoveredDocumentResponse(BaseModel):
    """Public discovery metadata without an internal absolute path."""

    filename: str
    relative_path: str
    extension: str
    size_bytes: int
    modified_at: datetime
    supported: bool
    rejection_reason: str | None = None


class DocumentIngestionResult(BaseModel):
    """Detailed result for ingestion or dry-run validation."""

    document_id: str
    source_filename: str
    relative_path: str
    status: DocumentStatus
    dry_run: bool
    file_size_bytes: int
    pages_extracted: int = 0
    characters_extracted: int = 0
    tokens_extracted: int = 0
    chunks_created: int = 0
    chunks_embedded: int = 0
    embeddings_reused: int = 0
    warnings: list[str] = Field(default_factory=list)
    failure_report: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    error_message: str | None = None


class KnowledgeDocumentResponse(BaseModel):
    """Stored document metadata without filesystem internals or vectors."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str
    source_filename: str
    relative_path: str
    file_extension: str
    mime_type: str
    document_type: str | None
    department: str | None
    asset_type: str | None
    region: str | None
    effective_date: date | None
    version: str | None
    language: str
    is_synthetic: bool | None
    authority_level: str
    expiration_date: date | None
    title: str
    file_size_bytes: int
    status: DocumentStatus
    total_pages: int
    total_characters: int
    total_tokens: int
    total_chunks: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata_json: dict[str, Any]

    @classmethod
    def from_document(cls, document: Any) -> "KnowledgeDocumentResponse":
        data = {column: getattr(document, column) for column in cls.model_fields if column != "relative_path"}
        return cls(relative_path=document.original_path, **data)


class KnowledgeDocumentPage(BaseModel):
    items: list[KnowledgeDocumentResponse]
    total: int
    limit: int
    offset: int


class DocumentChunkResponse(BaseModel):
    """Safe chunk details that deliberately omit embeddings and full content."""

    chunk_number: int
    page_number: int | None
    section_title: str | None
    token_count: int
    content_preview: str
    metadata: dict[str, Any]


class DocumentChunkPage(BaseModel):
    items: list[DocumentChunkResponse]
    total: int
    limit: int
    offset: int
