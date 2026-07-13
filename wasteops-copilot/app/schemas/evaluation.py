"""Public and internal evaluation contracts."""

import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.evaluation.enums import EvaluationMode, Severity


class EvaluationCase(BaseModel):
    case_id: str
    category: str
    question: str
    expected_route: str | None = None
    expected_tool: str | None = None
    expected_documents: list[str] = Field(default_factory=list)
    expected_citation_types: list[str] = Field(default_factory=list)
    expected_concepts: list[str] = Field(default_factory=list)
    forbidden_concepts: list[str] = Field(default_factory=list)
    expected_insufficient_context: bool = False
    expected_human_approval: bool | None = None
    severity: Severity = Severity.MEDIUM
    language: str = "en"
    expected: dict[str, Any] = Field(default_factory=dict)
    recorded_response: dict[str, Any] | None = None


class EvaluationActualResult(BaseModel):
    route: str | None = None
    domain: str | None = None
    tool: str | None = None
    metrics: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    date_range: dict[str, Any] = Field(default_factory=dict)
    retrieved_documents: list[str] = Field(default_factory=list)
    retrieved_items: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any] | str] = Field(default_factory=list)
    supplied_source_ids: list[str] = Field(default_factory=list)
    answer: str = ""
    insufficient_context: bool = False
    decision_type: str | None = None
    action_category: str | None = None
    required_tools: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool | None = None
    scores: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    numeric_values: list[float | int | None] = Field(default_factory=list)
    expected_numeric_values: list[float | int | None] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    duration_ms: float = 0
    token_usage: int = 0
    modified_database: bool = False
    executed_action: bool = False
    exposed_secret: bool = False
    used_mock_prediction_as_real: bool = False


class EvaluatorResult(BaseModel):
    passed: bool
    score: float = Field(ge=0, le=1)
    metrics: dict[str, Any] = Field(default_factory=dict)
    failure_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    critical: bool = False


class EvaluationCaseResult(BaseModel):
    case_id: str
    category: str
    passed: bool
    score: float
    metrics: dict[str, Any] = Field(default_factory=dict)
    failure_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    critical_failure: bool = False
    duration_ms: float = 0
    language: str = "en"


class EvaluationDataset(BaseModel):
    name: str
    version: str = "1.0.0"
    evaluation_type: str
    cases: list[EvaluationCase]
    path: Path | None = None


class EvaluationRunResult(BaseModel):
    run_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    evaluation_type: str
    dataset_name: str
    dataset_version: str
    mode: EvaluationMode
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_configuration: dict[str, Any] = Field(default_factory=dict)
    results: list[EvaluationCaseResult] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    critical_failures: int = 0
    duration_ms: float = 0


class StartEvaluationRequest(BaseModel):
    dataset: str
    mode: EvaluationMode = EvaluationMode.FAKE_PROVIDERS
    prompt_overrides: dict[str, str] | None = None


class CompareRunsRequest(BaseModel):
    baseline: uuid.UUID
    candidate: uuid.UUID


class QualityGateFailure(BaseModel):
    metric: str
    required: float | int | str
    actual: float | int | None


class QualityGateResult(BaseModel):
    passed: bool
    metrics: dict[str, float]
    failed_rules: list[QualityGateFailure] = Field(default_factory=list)
    critical_failures: int
