"""Validated router and context-planning contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.decision.enums import DecisionType
from app.schemas.retrieval import RetrievalFilters


class PlannedAnalyticsCall(BaseModel):
    tool: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class PlannedDocumentQuery(BaseModel):
    query: str
    filters: RetrievalFilters | None = None


class DecisionRouteResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_type: DecisionType
    scope: dict[str, Any] = Field(default_factory=dict)
    required_analytics_tools: list[str] = Field(default_factory=list)
    required_document_queries: list[str] = Field(default_factory=list)
    requires_data_science: bool = False
    requires_optimization: bool = False
    unsupported_reason: str | None = None


class DecisionContextPlan(BaseModel):
    decision_type: DecisionType
    analytics_calls: list[PlannedAnalyticsCall]
    document_queries: list[PlannedDocumentQuery]
    required_evidence_categories: list[str]
    missing_requirements: list[str] = Field(default_factory=list)
    requires_data_science: bool = False
    requires_optimization: bool = False
    unsupported_reason: str | None = None
