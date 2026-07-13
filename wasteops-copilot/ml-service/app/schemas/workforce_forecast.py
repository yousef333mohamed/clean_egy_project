from datetime import date
from pydantic import Field

from app.schemas.common import EntityBatchRequest, ExplanationFactor, PredictionMetadata, StrictModel


class WorkforceForecastRequest(EntityBatchRequest):
    regions: list[str] = Field(min_length=1)
    shifts: list[str] = Field(min_length=1)
    forecast_date: date


class PredictionInterval(StrictModel):
    lower: int = Field(ge=0)
    upper: int = Field(ge=0)


class WorkforceForecast(PredictionMetadata):
    region: str
    shift: str
    forecast_date: date
    required_workers: int = Field(ge=0)
    prediction_interval: PredictionInterval
    top_factors: list[ExplanationFactor] = Field(default_factory=list, max_length=5)


class WorkforceForecastResponse(StrictModel):
    request_id: str
    predictions: list[WorkforceForecast]
