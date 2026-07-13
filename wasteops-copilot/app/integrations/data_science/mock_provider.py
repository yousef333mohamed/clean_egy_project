"""Synthetic test-only provider that cannot be enabled accidentally in production."""

from app.integrations.data_science.interfaces import (
    BinOverflowPrediction,
    CollectionPriorityPrediction,
    MissedCollectionPrediction,
    TruckAnomalyPrediction,
)


class MockDataScienceProvider:
    def __init__(self, settings) -> None:
        if settings.app_environment.casefold() == "production" or not settings.allow_mock_data_science:
            raise RuntimeError("Mock Data Science is test-only and explicitly disabled")

    async def predict_overflow(self, bin_ids, horizon_hours, *, request_id="unassigned"):
        return [BinOverflowPrediction(entity_id=item, score=0.5, model_version="synthetic-test", is_synthetic=True) for item in bin_ids]

    async def calculate_priority(self, bin_ids, horizon_hours=24, *, request_id="unassigned"):
        return [CollectionPriorityPrediction(entity_id=item, score=0.5, model_version="synthetic-test", is_synthetic=True) for item in bin_ids]

    async def detect_anomalies(self, truck_ids, *, request_id="unassigned"):
        return [TruckAnomalyPrediction(entity_id=item, score=0.5, model_version="synthetic-test", is_synthetic=True) for item in truck_ids]

    async def predict_missed_collections(self, region, horizon_hours, *, request_id="unassigned"):
        return [MissedCollectionPrediction(entity_id=region or "all", score=0.5, model_version="synthetic-test", is_synthetic=True)]

    async def forecast_workforce_requirement(self, region, shift, forecast_date, *, request_id="unassigned"):
        return []
