from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.common import EntityBatchRequest, ExplanationFactor, PredictionMetadata, StrictModel


class TruckAnomalyRequest(EntityBatchRequest):
    truck_ids: list[str] = Field(min_length=1)


class TruckAnomalyPrediction(PredictionMetadata):
    truck_id: str
    trip_date: date
    is_anomalous: bool
    anomaly_score: float = Field(ge=0, le=1)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    triggered_rules: list[str] = Field(default_factory=list)
    model_factors: list[ExplanationFactor] = Field(default_factory=list, max_length=5)
    recommended_action_category: Literal["MONITOR", "MANAGER_REVIEW", "INSPECTION_REVIEW"] = "MANAGER_REVIEW"


class TruckAnomalyResponse(StrictModel):
    request_id: str
    predictions: list[TruckAnomalyPrediction]
