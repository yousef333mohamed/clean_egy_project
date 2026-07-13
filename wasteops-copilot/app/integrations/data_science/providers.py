"""Real provider implementations over the private ML service."""

from datetime import date

from app.integrations.data_science.schemas import (
    BinOverflowPrediction,
    CollectionPriorityPrediction,
    MissedCollectionPrediction,
    TruckAnomalyPrediction,
    WorkforceRequirementPrediction,
)


class RemoteDataScienceProvider:
    def __init__(self, client) -> None:
        self.client = client

    async def predict_overflow(self, bin_ids: list[str], horizon_hours: int, *, request_id: str = "unassigned") -> list[BinOverflowPrediction]:
        return await self.client.post(
            "/api/predictions/bin-overflow",
            {"bin_ids": bin_ids, "horizon_hours": horizon_hours, "as_of_timestamp": None},
            BinOverflowPrediction,
            request_id=request_id,
        )

    async def calculate_priority(self, bin_ids: list[str], horizon_hours: int = 24, *, request_id: str = "unassigned") -> list[CollectionPriorityPrediction]:
        return await self.client.post(
            "/api/predictions/collection-priority",
            {"bin_ids": bin_ids, "horizon_hours": horizon_hours, "as_of_timestamp": None},
            CollectionPriorityPrediction,
            request_id=request_id,
        )

    async def detect_anomalies(self, truck_ids: list[str], *, request_id: str = "unassigned") -> list[TruckAnomalyPrediction]:
        return await self.client.post(
            "/api/predictions/truck-anomalies", {"truck_ids": truck_ids, "as_of_timestamp": None}, TruckAnomalyPrediction, request_id=request_id
        )

    async def predict_missed_collections(self, region: str | None, horizon_hours: int, *, request_id: str = "unassigned") -> list[MissedCollectionPrediction]:
        return await self.client.post(
            "/api/predictions/missed-collections",
            {"scope_type": "region", "scope_ids": [region] if region else [], "horizon_hours": horizon_hours, "as_of_timestamp": None},
            MissedCollectionPrediction,
            request_id=request_id,
        )

    async def forecast_workforce_requirement(
        self, region: str, shift: str, forecast_date: date, *, request_id: str = "unassigned"
    ) -> list[WorkforceRequirementPrediction]:
        return await self.client.post(
            "/api/predictions/workforce-requirements",
            {"regions": [region], "shifts": [shift], "forecast_date": forecast_date.isoformat(), "as_of_timestamp": None},
            WorkforceRequirementPrediction,
            request_id=request_id,
        )
