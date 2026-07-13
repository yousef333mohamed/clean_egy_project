"""Grounded RAG request and response contracts."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.citation import Citation
from app.schemas.retrieval import RetrievalFilters


class RAGRequest(BaseModel):
    question: str = Field(min_length=1)
    filters: RetrievalFilters | None = None
    top_k: int = Field(default=8, ge=1, le=100)
    debug: bool = False


class RAGResponse(BaseModel):
    answer: str
    grounded: bool
    insufficient_context: bool
    citations: list[Citation]
    retrieved_evidence_count: int
    used_evidence_count: int
    warnings: list[str]
    query: str
    rewritten_query: str | None
    filters_applied: dict[str, Any]
    request_id: uuid.UUID
    debug: dict[str, Any] | None = None
