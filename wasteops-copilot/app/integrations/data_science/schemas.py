"""Strict backend view of ML service contracts."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Factor(StrictModel):
    feature: str
    direction: str
    contribution: float = Field(ge=-1, le=1)


class PredictionBase(StrictModel):
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prediction_timestamp: datetime
    feature_timestamp: datetime
    data_age_seconds: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    is_synthetic: bool = False


class BinOverflowPrediction(PredictionBase):
    bin_id: str
    horizon_hours: Literal[6, 12, 24]
    overflow_probability: float = Field(ge=0, le=1)
    predicted_class: bool
    decision_threshold: float = Field(ge=0, le=1)
    risk_level: str
    top_factors: list[Factor] = Field(default_factory=list)


class CollectionPriorityPrediction(PredictionBase):
    bin_id: str
    priority_score: float = Field(ge=0, le=1)
    priority_level: str
    overflow_probability: float = Field(ge=0, le=1)
    recommended_review_window_hours: int
    score_components: dict[str, float]
    top_factors: list[Factor] = Field(default_factory=list)


class TruckAnomalyPrediction(PredictionBase):
    truck_id: str
    trip_date: date
    is_anomalous: bool
    anomaly_score: float = Field(ge=0, le=1)
    severity: str
    triggered_rules: list[str]
    model_factors: list[Factor]
    recommended_action_category: str


class MissedCollectionPrediction(PredictionBase):
    scope_type: str
    scope_id: str
    horizon_hours: Literal[6, 12, 24]
    missed_collection_probability: float = Field(ge=0, le=1)
    risk_level: str
    top_factors: list[Factor] = Field(default_factory=list)


class WorkforceRequirementPrediction(PredictionBase):
    region: str
    shift: str
    forecast_date: date
    required_workers: int = Field(ge=0)
    prediction_interval: dict[str, int]
    top_factors: list[Factor] = Field(default_factory=list)


class PredictionEnvelope(StrictModel):
    request_id: str
    predictions: list[dict]


class ActiveModel(StrictModel):
    model_name: str
    version: str
    stage: str
    feature_version: str
    approval_status: str
    metrics: dict[str, float]
    training_period: dict[str, str]


class ModelVersion(ActiveModel):
    created_at: datetime
    promoted_at: datetime | None = None
    promoted_by: str | None = None


class MonitoringReportEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")
    reports: list[dict] = Field(default_factory=list)
