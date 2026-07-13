"""Decision request, response, preview, and debug API schemas."""

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.decision.enums import DecisionType
from app.schemas.citation import Citation
from app.schemas.confidence import DecisionConfidence
from app.schemas.decision_context import DecisionContextPlan, DecisionRouteResult
from app.schemas.decision_option import ScoredDecisionOption
from app.schemas.operational_evidence import OperationalEvidence
from app.schemas.retrieval import RetrievalFilters
from app.utils.safe_identifiers import validate_safe_value


class DecisionScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: str | None = None
    governorate: str | None = None
    bin_ids: list[str] = Field(default_factory=list)
    truck_ids: list[str] = Field(default_factory=list)
    worker_ids: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    use_latest_available_data: bool = True

    @field_validator("region", "governorate")
    @classmethod
    def safe_location(cls, value: str | None) -> str | None:
        return validate_safe_value(value) if value else value

    @field_validator("bin_ids", "truck_ids", "worker_ids")
    @classmethod
    def safe_ids(cls, values: list[str]) -> list[str]:
        if len(values) > 200:
            raise ValueError("too many identifiers")
        return list(dict.fromkeys(validate_safe_value(value) for value in values))

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "DecisionScope":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        if self.start_date and self.end_date and (self.end_date - self.start_date).days + 1 > 366:
            raise ValueError("decision date range exceeds 366 days")
        return self


class DecisionConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    maximum_actions: int | None = Field(default=None, ge=2, le=10)
    prioritize_service_continuity: bool = True
    prioritize_safety: bool = True
    prioritize_cost_reduction: bool = False


class DecisionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    decision_type: DecisionType | None = None
    scope: DecisionScope = Field(default_factory=DecisionScope)
    constraints: DecisionConstraints = Field(default_factory=DecisionConstraints)
    document_filters: RetrievalFilters | None = None


class DecisionResponse(BaseModel):
    request_id: uuid.UUID
    decision_type: DecisionType
    situation_summary: str
    recommended_option: ScoredDecisionOption | None
    alternative_options: list[ScoredDecisionOption]
    database_evidence: list[OperationalEvidence]
    document_citations: list[Citation]
    confidence: DecisionConfidence
    missing_information: list[str]
    warnings: list[str]
    requires_human_approval: Literal[True] = True
    grounded: bool
    insufficient_context: bool


class DecisionPreviewResponse(BaseModel):
    route: DecisionRouteResult
    plan: DecisionContextPlan


class DecisionDebugResponse(BaseModel):
    request_id: uuid.UUID
    router_output: DecisionRouteResult
    evidence_summary: list[dict[str, Any]]
    option_scores: list[dict[str, Any]]
    confidence: DecisionConfidence
    insufficient_context: bool
