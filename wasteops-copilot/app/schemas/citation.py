"""Citation mapping and validation contracts."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    source_filename: str
    document_title: str
    page_number: int | None
    section_title: str | None
    chunk_number: int
    content_preview: str
    is_synthetic: bool


class CitationValidationResult(BaseModel):
    answer: str
    citations: list[Citation]
    valid_citation_ids: list[str] = Field(default_factory=list)
    invalid_citation_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
