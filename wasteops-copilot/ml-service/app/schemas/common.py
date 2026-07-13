"""Shared strict prediction metadata."""

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExplanationFactor(StrictModel):
    feature: str
    direction: Literal["increases_risk", "decreases_risk", "increases_forecast", "decreases_forecast"]
    contribution: float = Field(ge=-1, le=1)


class PredictionMetadata(StrictModel):
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prediction_timestamp: datetime
    feature_timestamp: datetime
    data_age_seconds: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("prediction_timestamp", "feature_timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return value


class EntityBatchRequest(StrictModel):
    as_of_timestamp: datetime | None = None

    def prediction_time(self) -> datetime:
        return self.as_of_timestamp or datetime.now(timezone.utc)


class DateScope(StrictModel):
    start: date
    end: date

    @field_validator("end")
    @classmethod
    def _end_present(cls, value: date) -> date:
        return value
