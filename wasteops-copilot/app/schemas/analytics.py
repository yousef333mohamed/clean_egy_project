"""Routing and natural-language analytics API schemas."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.analytics.enums import AnalyticsDomain, AnalyticsRoute
from app.schemas.analytics_tools import AnalyticsToolParameters
from app.schemas.operational_evidence import OperationalEvidence


class AnalyticsQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    debug: bool = False


class AnalyticsRouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: AnalyticsRoute
    domain: AnalyticsDomain | None = None
    tool_name: str | None = None
    parameters: AnalyticsToolParameters = Field(default_factory=AnalyticsToolParameters)
    requires_document_retrieval: bool = False
    document_query: str | None = None
    clarification_required: bool = False
    unsupported_reason: str | None = None


class DatabaseCitation(BaseModel):
    citation_id: str
    source_type: str = "database"
    tool_name: str
    description: str


class AnalyticsResponse(BaseModel):
    answer: str
    route: AnalyticsRoute
    tool_name: str | None = None
    domain: AnalyticsDomain | None = None
    grounded: bool
    insufficient_data: bool
    database_evidence: list[OperationalEvidence]
    citations: list[DatabaseCitation]
    warnings: list[str]
    request_id: uuid.UUID
    debug: dict[str, Any] | None = None
