"""Injection contracts for future real Data Science providers; no execution integration yet."""

from typing import Protocol

from pydantic import BaseModel, Field


class PredictionBase(BaseModel):
    entity_id: str
    score: float = Field(ge=0, le=1)
    model_version: str
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
    async def predict_overflow(self, bin_ids: list[str], horizon_hours: int) -> list[BinOverflowPrediction]: ...


class CollectionPriorityProvider(Protocol):
    async def calculate_priority(self, bin_ids: list[str]) -> list[CollectionPriorityPrediction]: ...


class TruckAnomalyPredictionProvider(Protocol):
    async def detect_anomalies(self, truck_ids: list[str]) -> list[TruckAnomalyPrediction]: ...


class MissedCollectionPredictionProvider(Protocol):
    async def predict_missed_collections(self, region: str | None, horizon_hours: int) -> list[MissedCollectionPrediction]: ...


class DisabledDataScienceProvider:
    """Return no model evidence; callers must keep predictive decisions unsupported."""

    async def predict_overflow(self, bin_ids, horizon_hours):
        return []

    async def calculate_priority(self, bin_ids):
        return []

    async def detect_anomalies(self, truck_ids):
        return []

    async def predict_missed_collections(self, region, horizon_hours):
        return []
