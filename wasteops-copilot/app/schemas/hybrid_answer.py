"""Combined database and document intelligence contracts."""

import uuid

from pydantic import BaseModel, Field

from app.analytics.enums import AnalyticsRoute
from app.schemas.citation import Citation
from app.schemas.operational_evidence import OperationalEvidence
from app.schemas.retrieval import RetrievalFilters


class HybridQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_filters: RetrievalFilters | None = None
    debug: bool = False


class HybridQuestionResponse(BaseModel):
    answer: str
    route: AnalyticsRoute
    grounded: bool
    insufficient_data: bool
    insufficient_context: bool
    database_evidence: list[OperationalEvidence]
    document_citations: list[Citation]
    warnings: list[str]
    request_id: uuid.UUID
