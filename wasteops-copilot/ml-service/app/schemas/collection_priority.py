from pydantic import Field
from typing import Literal

from app.schemas.common import EntityBatchRequest, ExplanationFactor, PredictionMetadata, StrictModel


class CollectionPriorityRequest(EntityBatchRequest):
    bin_ids: list[str] = Field(min_length=1)
    horizon_hours: Literal[6, 12, 24] = 24


class PriorityComponents(StrictModel):
    overflow_risk: float = Field(ge=0, le=1)
    current_urgency: float = Field(ge=0, le=1)
    service_history: float = Field(ge=0, le=1)
    operational_context: float = Field(ge=0, le=1)
    sensor_reliability: float = Field(ge=0, le=1)


class CollectionPriorityPrediction(PredictionMetadata):
    bin_id: str
    priority_score: float = Field(ge=0, le=1)
    priority_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    overflow_probability: float = Field(ge=0, le=1)
    recommended_review_window_hours: int = Field(ge=1)
    score_components: PriorityComponents
    top_factors: list[ExplanationFactor] = Field(default_factory=list, max_length=5)


class CollectionPriorityResponse(StrictModel):
    request_id: str
    predictions: list[CollectionPriorityPrediction]
