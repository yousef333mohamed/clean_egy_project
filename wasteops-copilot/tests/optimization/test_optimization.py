from datetime import UTC, date, datetime
from types import SimpleNamespace

import httpx
import pytest

from app.api.routes.optimization import _deterministic_explanation, _numbers_are_grounded
from app.integrations.optimization.client import OptimizationClient, OptimizationUnavailable
from app.integrations.optimization.schemas import BinInput, Constraints, Location, OptimizePayload, OptimizeResponse, TruckInput


def payload() -> OptimizePayload:
    depot = Location(latitude=30.04, longitude=31.23)
    return OptimizePayload(
        bins=[
            BinInput(
                bin_id="B1",
                location=Location(latitude=30.05, longitude=31.24),
                estimated_load_kg=250,
                priority_score=0.9,
                overflow_probability=0.8,
                feature_timestamp=datetime.now(UTC),
                model_versions={"bin-overflow": "v1", "collection-priority": "v1"},
            )
        ],
        trucks=[TruckInput(truck_id="T1", capacity_kg=1000, depot=depot)],
        constraints=Constraints(
            plan_date=date.today(),
            available_workers=2,
            workers_per_route=2,
            average_speed_kmh=25,
            traffic_multiplier=1,
            environmental_duration_multiplier=1,
        ),
    )


def response_json() -> dict:
    return {
        "plan_id": "plan-1",
        "status": "FEASIBLE",
        "generated_at": datetime.now(UTC).isoformat(),
        "solver_name": "Google OR-Tools",
        "solver_version": "9.15",
        "primary_plan": {
            "routes": [],
            "unassigned_bin_ids": ["B1"],
            "total_distance_km": 0,
            "total_duration_minutes": 0,
            "total_load_kg": 0,
            "total_fuel_liters": 0,
            "objective_value": 10,
        },
        "alternatives": [],
        "warnings": ["Manager review required."],
        "assumptions": ["Distance is approximate."],
        "requires_human_approval": True,
        "executes_operations": False,
    }


@pytest.mark.asyncio
async def test_client_authenticates_and_validates_advisory_contract():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret"
        assert request.headers["X-Request-ID"] == "request-1"
        return httpx.Response(200, json=response_json())

    settings = SimpleNamespace(
        optimization_service_base_url="http://optimizer",
        optimization_timeout_seconds=2,
        optimization_service_token="secret",
    )
    result = await OptimizationClient(settings, httpx.MockTransport(handler)).optimize(payload(), "request-1")
    assert result.requires_human_approval is True
    assert result.executes_operations is False


@pytest.mark.asyncio
async def test_client_rejects_unsafe_or_invalid_response():
    body = response_json()
    body["executes_operations"] = True
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    settings = SimpleNamespace(
        optimization_service_base_url="http://optimizer",
        optimization_timeout_seconds=2,
        optimization_service_token="secret",
    )
    with pytest.raises(OptimizationUnavailable):
        await OptimizationClient(settings, transport).optimize(payload(), "request-1")


def test_explanation_guard_rejects_invented_numbers():
    result = OptimizeResponse.model_validate(response_json())
    fallback = _deterministic_explanation(result)
    assert "[O1]" in fallback
    assert _numbers_are_grounded("There are 0 routes [O1].", str(response_json()))
    assert not _numbers_are_grounded("There are 999 routes [O1].", str(response_json()))
