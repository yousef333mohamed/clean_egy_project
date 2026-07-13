"""Decision request and response contracts."""

from pydantic import BaseModel, Field
from app.schemas.retrieval import Evidence


class DecisionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class ExpectedImpact(BaseModel):
    service_impact: str = "Unknown"
    fuel_impact: str = "Unknown"
    overflow_impact: str = "Unknown"


class DecisionResponse(BaseModel):
    situation_summary: str
    recommended_decision: str
    supporting_evidence: list[Evidence]
    expected_impact: ExpectedImpact
    risks: list[str]
    alternative_decisions: list[str]
    confidence_score: float = Field(ge=0, le=1)
    missing_information: list[str]
    retrieved_facts: list[str] = Field(default_factory=list)
    model_assumptions: list[str] = Field(default_factory=list)
