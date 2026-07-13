from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Strict):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class PlanPreviewRequest(Strict):
    plan_date: date
    bin_ids: list[str] = Field(min_length=1, max_length=500)
    truck_ids: list[str] = Field(min_length=1, max_length=100)
    depot: Location
    workers_per_route: int = Field(default=2, ge=1, le=20)
    average_speed_kmh: float = Field(default=25, gt=0, le=120)
    traffic_multiplier: float = Field(default=1, ge=0.5, le=5)
    environmental_duration_multiplier: float = Field(default=1, ge=0.5, le=3)


class Factor(Strict):
    feature: str
    direction: str
    contribution: float


class BinInput(Strict):
    bin_id: str
    location: Location
    estimated_load_kg: int
    service_minutes: int = 10
    priority_score: float
    overflow_probability: float
    window_start_minute: int = 0
    window_end_minute: int = 480
    feature_timestamp: datetime
    model_versions: dict[str, str]


class TruckInput(Strict):
    truck_id: str
    capacity_kg: int
    available: bool = True
    depot: Location
    max_route_minutes: int = 480
    fuel_efficiency_km_per_l: float = 3


class Constraints(Strict):
    plan_date: date
    available_workers: int
    workers_per_route: int
    average_speed_kmh: float
    traffic_multiplier: float
    environmental_duration_multiplier: float
    working_day_minutes: int = 480


class OptimizePayload(Strict):
    bins: list[BinInput]
    trucks: list[TruckInput]
    constraints: Constraints


class Stop(Strict):
    sequence: int
    bin_id: str
    arrival_minute: int
    estimated_load_kg: int
    cumulative_load_kg: int
    priority_score: float
    overflow_probability: float


class Route(Strict):
    route_id: str
    truck_id: str
    required_workers: int
    stops: list[Stop]
    estimated_distance_km: float
    estimated_duration_minutes: int
    estimated_load_kg: int
    estimated_fuel_liters: float


class Summary(Strict):
    routes: list[Route]
    unassigned_bin_ids: list[str]
    total_distance_km: float
    total_duration_minutes: int
    total_load_kg: int
    total_fuel_liters: float
    objective_value: int


class Alternative(Strict):
    scenario: str
    summary: Summary


class OptimizeResponse(Strict):
    plan_id: str
    status: Literal["FEASIBLE", "INFEASIBLE", "TIME_LIMIT"]
    generated_at: datetime
    solver_name: str
    solver_version: str
    primary_plan: Summary | None
    alternatives: list[Alternative]
    warnings: list[str]
    assumptions: list[str]
    requires_human_approval: Literal[True]
    executes_operations: Literal[False]


class PlanReviewRequest(Strict):
    approved: bool
    review_notes: str = Field(min_length=10, max_length=1000)


class PlanExplanation(Strict):
    plan_id: str
    explanation: str
    evidence_id: Literal["O1"] = "O1"
    generated_by: Literal["llm", "deterministic"]
    requires_human_approval: Literal[True] = True
    executes_operations: Literal[False] = False
