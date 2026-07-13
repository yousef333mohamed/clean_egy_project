from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4
import ortools
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from app.engine.distance import haversine_meters
from app.schemas.plans import AlternativePlan, OptimizeRequest, OptimizeResponse, PlanSummary, PlannedRoute, PlannedStop


def optimize(request: OptimizeRequest, timeout: int = 10, max_alternatives: int = 2) -> OptimizeResponse:
    primary = _solve(request, timeout)
    alternatives: list[AlternativePlan] = []
    if primary:
        used = [route.truck_id for route in primary.routes]
        for truck_id in used[:max_alternatives]:
            changed = request.model_copy(
                update={"trucks": [truck.model_copy(update={"available": False}) if truck.truck_id == truck_id else truck for truck in request.trucks]}
            )
            candidate = _solve(changed, timeout)
            if candidate:
                alternatives.append(AlternativePlan(scenario=f"Truck {truck_id} unavailable", summary=candidate))
    status: Literal["FEASIBLE", "INFEASIBLE", "TIME_LIMIT"] = "FEASIBLE" if primary else "INFEASIBLE"
    if not primary and request.constraints.available_workers < request.constraints.workers_per_route:
        required = request.constraints.workers_per_route - request.constraints.available_workers
        changed = request.model_copy(
            update={"constraints": request.constraints.model_copy(update={"available_workers": request.constraints.workers_per_route})}
        )
        candidate = _solve(changed, timeout)
        if candidate:
            alternatives.append(
                AlternativePlan(
                    scenario=f"Add {required} available worker{'s' if required != 1 else ''}",
                    summary=candidate,
                )
            )
    if not primary and not any(truck.available for truck in request.trucks):
        for truck in request.trucks[:max_alternatives]:
            changed = request.model_copy(update={"trucks": [item.model_copy(update={"available": item.truck_id == truck.truck_id}) for item in request.trucks]})
            candidate = _solve(changed, timeout)
            if candidate:
                alternatives.append(
                    AlternativePlan(
                        scenario=f"Restore truck {truck.truck_id} to service",
                        summary=candidate,
                    )
                )
    warnings = [] if primary else ["No feasible plan satisfies current truck, capacity, time, and workforce constraints."]
    if primary and primary.unassigned_bin_ids:
        warnings.append("Some bins were unassigned; manager review or additional resources are required.")
    return OptimizeResponse(
        plan_id=str(uuid4()),
        status=status,
        generated_at=datetime.now(UTC),
        solver_version=ortools.__version__,
        primary_plan=primary,
        alternatives=alternatives,
        warnings=warnings,
        assumptions=[
            "Straight-line distance is used until a governed road-network matrix is configured.",
            "Traffic and environmental inputs are multipliers, not live navigation guarantees.",
            "The plan is advisory and cannot dispatch trucks or assign workers.",
        ],
    )


def _solve(request: OptimizeRequest, timeout: int) -> PlanSummary | None:
    trucks = [truck for truck in request.trucks if truck.available]
    max_routes = request.constraints.available_workers // request.constraints.workers_per_route
    trucks = trucks[:max_routes]
    if not trucks:
        return None
    bins = request.bins
    locations = [trucks[0].depot, *[item.location for item in bins]]
    matrix = [[haversine_meters(a, b) for b in locations] for a in locations]
    manager = pywrapcp.RoutingIndexManager(len(locations), len(trucks), 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance(i, j):
        return matrix[manager.IndexToNode(i)][manager.IndexToNode(j)]

    transit = routing.RegisterTransitCallback(distance)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    def demand(index):
        node = manager.IndexToNode(index)
        return 0 if node == 0 else bins[node - 1].estimated_load_kg

    demand_index = routing.RegisterUnaryTransitCallback(demand)
    routing.AddDimensionWithVehicleCapacity(demand_index, 0, [truck.capacity_kg for truck in trucks], True, "Capacity")
    speed = request.constraints.average_speed_kmh
    multiplier = request.constraints.traffic_multiplier * request.constraints.environmental_duration_multiplier

    def duration(i, j):
        source = manager.IndexToNode(i)
        target = manager.IndexToNode(j)
        service = 0 if source == 0 else bins[source - 1].service_minutes
        return round(matrix[source][target] / 1000 / speed * 60 * multiplier) + service

    time_index = routing.RegisterTransitCallback(duration)
    routing.AddDimension(time_index, 60, request.constraints.working_day_minutes, True, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for vehicle, truck in enumerate(trucks):
        time_dim.CumulVar(routing.End(vehicle)).SetMax(min(request.constraints.working_day_minutes, truck.max_route_minutes))
    for node, item in enumerate(bins, 1):
        index = manager.NodeToIndex(node)
        time_dim.CumulVar(index).SetRange(item.window_start_minute, min(item.window_end_minute, request.constraints.working_day_minutes))
        preferred_arrival = round((1 - max(item.priority_score, item.overflow_probability)) * 60)
        time_dim.SetCumulVarSoftUpperBound(index, max(item.window_start_minute, preferred_arrival), 1000)
        penalty = 100000 + round(900000 * max(item.priority_score, item.overflow_probability))
        routing.AddDisjunction([index], penalty)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = timeout
    solution = routing.SolveWithParameters(params)
    if not solution:
        return None
    routes: list[PlannedRoute] = []
    assigned: set[str] = set()
    for vehicle, truck in enumerate(trucks):
        index = routing.Start(vehicle)
        stops: list[PlannedStop] = []
        distance_m = 0
        load = 0
        while not routing.IsEnd(index):
            next_index = solution.Value(routing.NextVar(index))
            node = manager.IndexToNode(next_index)
            distance_m += distance(index, next_index)
            if node:
                item = bins[node - 1]
                load += item.estimated_load_kg
                assigned.add(item.bin_id)
                stops.append(
                    PlannedStop(
                        sequence=len(stops) + 1,
                        bin_id=item.bin_id,
                        arrival_minute=solution.Value(time_dim.CumulVar(next_index)),
                        estimated_load_kg=item.estimated_load_kg,
                        cumulative_load_kg=load,
                        priority_score=item.priority_score,
                        overflow_probability=item.overflow_probability,
                    )
                )
            index = next_index
        if stops:
            minutes = solution.Value(time_dim.CumulVar(routing.End(vehicle)))
            km = distance_m / 1000
            routes.append(
                PlannedRoute(
                    route_id=f"ROUTE-{len(routes) + 1}",
                    truck_id=truck.truck_id,
                    required_workers=request.constraints.workers_per_route,
                    stops=stops,
                    estimated_distance_km=round(km, 2),
                    estimated_duration_minutes=minutes,
                    estimated_load_kg=load,
                    estimated_fuel_liters=round(km / truck.fuel_efficiency_km_per_l, 2),
                )
            )
    unassigned = [item.bin_id for item in bins if item.bin_id not in assigned]
    return PlanSummary(
        routes=routes,
        unassigned_bin_ids=unassigned,
        total_distance_km=round(sum(x.estimated_distance_km for x in routes), 2),
        total_duration_minutes=sum(x.estimated_duration_minutes for x in routes),
        total_load_kg=sum(x.estimated_load_kg for x in routes),
        total_fuel_liters=round(sum(x.estimated_fuel_liters for x in routes), 2),
        objective_value=solution.ObjectiveValue(),
    )
