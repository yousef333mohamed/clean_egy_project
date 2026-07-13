"""Retrieval contracts."""

from enum import StrEnum
from pydantic import BaseModel, Field


class Intent(StrEnum):
    SQL_DATA_QUERY = "SQL_DATA_QUERY"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    INCIDENT_INVESTIGATION = "INCIDENT_INVESTIGATION"
    DECISION_RECOMMENDATION = "DECISION_RECOMMENDATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


class IntentEntities(BaseModel):
    bin_id: str | None = None
    truck_id: str | None = None
    worker_id: str | None = None
    region: str | None = None
    date_range: str | None = None


class IntentResult(BaseModel):
    intent: Intent
    entities: IntentEntities = Field(default_factory=IntentEntities)
    requires_sql: bool = False
    requires_vector_search: bool = False


class Evidence(BaseModel):
    content: str
    source_type: str
    source_name: str
    record_reference: str
    relevance_score: float = Field(ge=0, le=1)
