from typing import Literal

from pydantic import Field

from app.schemas.common import EntityBatchRequest, ExplanationFactor, PredictionMetadata, StrictModel


class OverflowPredictionRequest(EntityBatchRequest):
    bin_ids: list[str] = Field(min_length=1)
    horizon_hours: Literal[6, 12, 24] = 24


class OverflowPrediction(PredictionMetadata):
    bin_id: str
    horizon_hours: Literal[6, 12, 24]
    overflow_probability: float = Field(ge=0, le=1)
    predicted_class: bool
    decision_threshold: float = Field(ge=0, le=1)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    top_factors: list[ExplanationFactor] = Field(default_factory=list, max_length=5)


class OverflowPredictionResponse(StrictModel):
    request_id: str
    predictions: list[OverflowPrediction]
