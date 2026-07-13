"""Immutable registry metadata used by loading and promotion gates."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModelMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_name: Literal["bin-overflow", "collection-priority", "truck-anomaly", "missed-collection", "workforce-forecast"]
    version: str
    stage: Literal["None", "Staging", "Production", "Archived"] = "None"
    training_period_start: str
    training_period_end: str
    feature_version: str
    code_commit: str
    parameters: dict[str, object] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)
    decision_threshold: float | None = Field(default=None, ge=0, le=1)
    artifact_file: str
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    approval_status: Literal["unreviewed", "approved", "rejected"] = "unreviewed"
    created_at: datetime
    promoted_at: datetime | None = None
    promoted_by: str | None = None
    leakage_checks_passed: bool = False
    validation_passed: bool = False
    baseline_comparison_passed: bool = False
    calibration_acceptable: bool = False
    critical_subgroup_failure: bool = False
    model_card_file: str = ""
