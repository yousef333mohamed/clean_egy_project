from datetime import UTC, date, datetime
from app.engine.solver import optimize
from app.schemas.plans import OptimizeRequest


def request(workers=4):
    return OptimizeRequest.model_validate(
        {
            "bins": [
                {
                    "bin_id": "B1",
                    "location": {"latitude": 30.05, "longitude": 31.24},
                    "estimated_load_kg": 300,
                    "priority_score": 0.95,
                    "overflow_probability": 0.9,
                    "feature_timestamp": datetime.now(UTC),
                    "model_versions": {"overflow": "3"},
                },
                {
                    "bin_id": "B2",
                    "location": {"latitude": 30.06, "longitude": 31.25},
                    "estimated_load_kg": 250,
                    "priority_score": 0.7,
                    "overflow_probability": 0.6,
                    "feature_timestamp": datetime.now(UTC),
                },
            ],
            "trucks": [
                {"truck_id": "T1", "capacity_kg": 1000, "depot": {"latitude": 30.04, "longitude": 31.23}},
                {"truck_id": "T2", "capacity_kg": 1000, "depot": {"latitude": 30.04, "longitude": 31.23}},
            ],
            "constraints": {"plan_date": date.today(), "available_workers": workers, "workers_per_route": 2},
        }
    )


def test_feasible_plan_orders_and_estimates():
    result = optimize(request(), 1, 1)
    assert result.status == "FEASIBLE" and result.primary_plan
    assert sum(len(route.stops) for route in result.primary_plan.routes) == 2
    assert result.primary_plan.total_distance_km > 0 and result.requires_human_approval and not result.executes_operations


def test_no_workers_is_infeasible():
    result = optimize(request(0), 1, 0)
    assert result.status == "INFEASIBLE" and result.primary_plan is None
    assert result.alternatives and result.alternatives[0].scenario == "Add 2 available workers"


def test_alternative_excludes_used_truck():
    result = optimize(request(), 1, 1)
    assert result.alternatives and "unavailable" in result.alternatives[0].scenario


def test_high_priority_stop_is_scheduled_first():
    body = request()
    body.bins[0].location = body.bins[1].location
    result = optimize(body, 1, 0)
    assert result.primary_plan
    assert result.primary_plan.routes[0].stops[0].bin_id == "B1"
