"""Normalized evidence metadata for deterministic decision logic."""

from typing import Any

from pydantic import BaseModel, Field

from app.decision.enums import DecisionEvidenceType


class DecisionEvidence(BaseModel):
    evidence_id: str
    source_type: DecisionEvidenceType
    category: str
    description: str
    data_period_start: str | None = None
    data_period_end: str | None = None
    authority_level: str
    recency: str
    completeness_notes: list[str] = Field(default_factory=list)
    supporting_values: dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = False
