"""Deterministic evidence-quality confidence contract."""

from pydantic import BaseModel, Field

from app.decision.enums import ConfidenceLevel


class ConfidenceComponents(BaseModel):
    retrieval_coverage: float = Field(ge=0, le=1)
    source_quality: float = Field(ge=0, le=1)
    data_completeness: float = Field(ge=0, le=1)
    source_agreement: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)
    model_reliability: float = Field(default=1.0, ge=0, le=1)


class DecisionConfidence(BaseModel):
    score: float = Field(ge=0, le=1)
    level: ConfidenceLevel
    components: ConfidenceComponents
    explanation: str
