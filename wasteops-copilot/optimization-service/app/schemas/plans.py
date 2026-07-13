from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Location(Strict):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BinStopInput(Strict):
    bin_id: str
    location: Location
    estimated_load_kg: int = Field(ge=0)
    service_minutes: int = Field(default=10, ge=1, le=120)
    priority_score: float = Field(ge=0, le=1)
    overflow_probability: float = Field(ge=0, le=1)
    window_start_minute: int = Field(default=0, ge=0, le=1440)
    window_end_minute: int = Field(default=480, ge=0, le=1440)
    feature_timestamp: datetime
    model_versions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def window(self):
        if self.window_start_minute >= self.window_end_minute:
            raise ValueError("Invalid stop time window")
        return self


class TruckInput(Strict):
    truck_id: str
    capacity_kg: int = Field(gt=0)
    available: bool = True
    depot: Location
    max_route_minutes: int = Field(default=480, ge=30, le=1440)
    fuel_efficiency_km_per_l: float = Field(default=3, gt=0, le=50)


class PlanConstraints(Strict):
    plan_date: date
    available_workers: int = Field(ge=0)
    workers_per_route: int = Field(default=2, ge=1, le=20)
    average_speed_kmh: float = Field(default=25, gt=0, le=120)
    traffic_multiplier: float = Field(default=1, ge=0.5, le=5)
    environmental_duration_multiplier: float = Field(default=1, ge=0.5, le=3)
    working_day_minutes: int = Field(default=480, ge=30, le=1440)


class OptimizeRequest(Strict):
    bins: list[BinStopInput] = Field(min_length=1)
    trucks: list[TruckInput] = Field(min_length=1)
    constraints: PlanConstraints

    @model_validator(mode="after")
    def single_depot(self):
        depots = {(truck.depot.latitude, truck.depot.longitude) for truck in self.trucks}
        if len(depots) != 1:
            raise ValueError("All trucks must use the same depot in this solver version")
        if any(item.window_start_minute >= self.constraints.working_day_minutes for item in self.bins):
            raise ValueError("Stop time windows must begin within the working day")
        return self


class PlannedStop(Strict):
    sequence: int
    bin_id: str
    arrival_minute: int
    estimated_load_kg: int
    cumulative_load_kg: int
    priority_score: float
    overflow_probability: float


class PlannedRoute(Strict):
    route_id: str
    truck_id: str
    required_workers: int
    stops: list[PlannedStop]
    estimated_distance_km: float
    estimated_duration_minutes: int
    estimated_load_kg: int
    estimated_fuel_liters: float


class PlanSummary(Strict):
    routes: list[PlannedRoute]
    unassigned_bin_ids: list[str]
    total_distance_km: float
    total_duration_minutes: int
    total_load_kg: int
    total_fuel_liters: float
    objective_value: int


class AlternativePlan(Strict):
    scenario: str
    summary: PlanSummary


class OptimizeResponse(Strict):
    plan_id: str
    status: Literal["FEASIBLE", "INFEASIBLE", "TIME_LIMIT"]
    generated_at: datetime
    solver_name: str = "Google OR-Tools"
    solver_version: str
    primary_plan: PlanSummary | None
    alternatives: list[AlternativePlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    requires_human_approval: Literal[True] = True
    executes_operations: Literal[False] = False
