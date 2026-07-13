"""Injection contracts for disabled, test-only, and real Data Science providers."""

from datetime import UTC, date, datetime
from typing import Protocol

from pydantic import BaseModel, Field


class PredictionBase(BaseModel):
    entity_id: str
    score: float = Field(ge=0, le=1)
    model_version: str
    model_name: str = "synthetic-test"
    prediction_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    feature_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=lambda: ["Synthetic test prediction; not operational evidence."])
    is_synthetic: bool = False


class BinOverflowPrediction(PredictionBase):
    pass


class CollectionPriorityPrediction(PredictionBase):
    pass


class TruckAnomalyPrediction(PredictionBase):
    pass


class MissedCollectionPrediction(PredictionBase):
    pass


class BinOverflowPredictionProvider(Protocol):
    async def predict_overflow(self, bin_ids: list[str], horizon_hours: int, *, request_id: str = "unassigned") -> list: ...


class CollectionPriorityProvider(Protocol):
    async def calculate_priority(self, bin_ids: list[str], horizon_hours: int = 24, *, request_id: str = "unassigned") -> list: ...


class TruckAnomalyPredictionProvider(Protocol):
    async def detect_anomalies(self, truck_ids: list[str], *, request_id: str = "unassigned") -> list: ...


class MissedCollectionPredictionProvider(Protocol):
    async def predict_missed_collections(self, region: str | None, horizon_hours: int, *, request_id: str = "unassigned") -> list: ...


class WorkforceRequirementProvider(Protocol):
    async def forecast_workforce_requirement(self, region: str, shift: str, forecast_date: date, *, request_id: str = "unassigned") -> list: ...


class DisabledDataScienceProvider:
    """Return no model evidence; callers must keep predictive decisions unsupported."""

    async def predict_overflow(self, bin_ids, horizon_hours, *, request_id="unassigned"):
        return []

    async def calculate_priority(self, bin_ids, horizon_hours=24, *, request_id="unassigned"):
        return []

    async def detect_anomalies(self, truck_ids, *, request_id="unassigned"):
        return []

    async def predict_missed_collections(self, region, horizon_hours, *, request_id="unassigned"):
        return []

    async def forecast_workforce_requirement(self, region, shift, forecast_date, *, request_id="unassigned"):
        return []
