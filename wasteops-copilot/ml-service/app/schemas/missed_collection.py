from typing import Literal
from pydantic import Field

from app.schemas.common import EntityBatchRequest, ExplanationFactor, PredictionMetadata, StrictModel


class MissedCollectionRequest(EntityBatchRequest):
    scope_type: Literal["region", "bin_group", "operational_period"] = "region"
    scope_ids: list[str] = Field(min_length=1)
    horizon_hours: Literal[6, 12, 24] = 24


class MissedCollectionPrediction(PredictionMetadata):
    scope_type: Literal["region", "bin_group", "operational_period"]
    scope_id: str
    horizon_hours: Literal[6, 12, 24]
    missed_collection_probability: float = Field(ge=0, le=1)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    top_factors: list[ExplanationFactor] = Field(default_factory=list, max_length=5)


class MissedCollectionResponse(StrictModel):
    request_id: str
    predictions: list[MissedCollectionPrediction]
