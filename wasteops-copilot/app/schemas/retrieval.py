"""Typed query processing and retrieval contracts."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.citation import Citation


class RetrievalFilters(BaseModel):
    """Allow-listed database metadata filters; lists are ORed per field."""

    model_config = ConfigDict(extra="forbid")

    document_type: list[str] | None = None
    department: list[str] | None = None
    asset_type: list[str] | None = None
    region: list[str] | None = None
    language: list[str] | None = None
    version: list[str] | None = None
    source_filename: list[str] | None = None
    effective_date_from: date | None = None
    effective_date_to: date | None = None
    is_synthetic: bool | None = None

    @field_validator("document_type", "department", "asset_type", "region", "language", "version", "source_filename", mode="before")
    @classmethod
    def normalize_list(cls, value: Any) -> Any:
        if value is None:
            return None
        values = [value] if isinstance(value, str) else value
        if not isinstance(values, list) or not values:
            raise ValueError("filter values must be a non-empty string or list")
        normalized = [str(item).strip() for item in values]
        if any(not item for item in normalized):
            raise ValueError("filter values must not be blank")
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_dates(self) -> "RetrievalFilters":
        if self.effective_date_from and self.effective_date_to and self.effective_date_from > self.effective_date_to:
            raise ValueError("effective_date_from must not be after effective_date_to")
        return self

    def applied(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class QueryEntities(BaseModel):
    bin_ids: list[str] = Field(default_factory=list)
    truck_ids: list[str] = Field(default_factory=list)
    worker_ids: list[str] = Field(default_factory=list)
    policy_codes: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)


class ProcessedQuery(BaseModel):
    original_query: str
    normalized_query: str
    rewritten_query: str | None = None
    language: str
    entities: QueryEntities
    rewrite_hints: dict[str, list[str]] = Field(default_factory=dict)

    @property
    def retrieval_query(self) -> str:
        return self.rewritten_query or self.normalized_query


class RetrievedEvidence(BaseModel):
    """Ranked chunk metadata; embeddings are intentionally absent."""

    chunk_id: str
    document_id: str
    source_filename: str
    document_title: str
    document_type: str | None = None
    department: str | None = None
    asset_type: str | None = None
    region: str | None = None
    language: str
    version: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    authority_level: str = "unknown"
    page_number: int | None = None
    section_title: str | None = None
    chunk_number: int
    content: str | None = None
    content_preview: str
    vector_score: float = Field(default=0, ge=0, le=1)
    keyword_score: float = Field(default=0, ge=0, le=1)
    rerank_score: float = Field(default=0, ge=0, le=1)
    final_score: float = Field(default=0, ge=0, le=1)
    is_synthetic: bool = False
    content_hash: str = Field(default="", exclude=True)


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=100)
    filters: RetrievalFilters | None = None
    include_content: bool = False
    debug: bool = False


class RetrievalResponse(BaseModel):
    query: str
    rewritten_query: str | None
    language: str
    evidence: list[RetrievedEvidence]
    filters_applied: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    debug: dict[str, Any] | None = None


class BuiltContext(BaseModel):
    context_text: str
    citations: list[Citation]
    included_chunk_ids: list[str]
    excluded_chunk_ids: list[str]
    estimated_tokens: int
    truncated: bool
    warnings: list[str] = Field(default_factory=list)
