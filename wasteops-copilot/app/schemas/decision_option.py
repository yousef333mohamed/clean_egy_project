"""Candidate actions, deterministic scores, and evidence-based risks."""

from pydantic import BaseModel, Field

from app.decision.enums import ActionCategory, DecisionPriority, RiskCategory, RiskLikelihood, RiskSeverity


class DecisionRisk(BaseModel):
    risk_id: str
    category: RiskCategory
    description: str
    severity: RiskSeverity
    likelihood: RiskLikelihood
    supporting_evidence_ids: list[str]
    mitigation: str


class CandidateDecisionOption(BaseModel):
    option_id: str
    action_category: ActionCategory
    title: str
    action: str
    supporting_evidence_ids: list[str]
    assumptions: list[str] = Field(default_factory=list)
    operational_requirements: list[str] = Field(default_factory=list)
    expected_impact: list[str] = Field(default_factory=list)
    possible_risks: list[str] = Field(default_factory=list)


class OptionScoreBreakdown(BaseModel):
    service_impact: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)
    risk_control: float = Field(ge=0, le=1)
    feasibility: float = Field(ge=0, le=1)
    policy_alignment: float = Field(ge=0, le=1)


class ScoredDecisionOption(CandidateDecisionOption):
    priority: DecisionPriority
    score: float = Field(ge=0, le=1)
    score_breakdown: OptionScoreBreakdown
    risks: list[DecisionRisk] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)
