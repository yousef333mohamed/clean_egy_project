"""Truck performance, ranking, and transparent rule-anomaly tools."""

from sqlalchemy import case, func, or_, select

from app.analytics.enums import AnalyticsDomain, SortDirection
from app.analytics.metric_registry import get_metric
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.truck import Truck
from app.models.truck_trip_log import TruckTripLog
from app.schemas.analytics_tools import AnalyticsToolResult

TRUCK_METRICS = (
    "total_distance_km",
    "total_fuel_consumed_l",
    "average_fuel_consumed_l",
    "average_load_kg",
    "average_trip_duration_min",
    "truck_utilization_pct",
    "fuel_efficiency_km_per_l",
)
TRUCK_PARAMS = ("start_date", "end_date", "region", "truck_id", "trip_status", "metric", "sort_direction", "limit", "latest_available")


def _scope(statement, params, *, columns=None):
    c = columns if columns is not None else TruckTripLog
    if params.start_date is not None:
        statement = statement.where(c.date >= params.start_date)
    if params.end_date is not None:
        statement = statement.where(c.date <= params.end_date)
    if params.region is not None:
        statement = statement.where(func.lower(c.region) == params.region.casefold())
    if params.truck_id is not None:
        statement = statement.where(c.truck_id == params.truck_id)
    if params.trip_status is not None:
        statement = statement.where(func.lower(c.status) == params.trip_status.casefold())
    return statement


class TruckPerformanceSummaryTool:
    name = "get_truck_performance_summary"
    description = "Summarize historical truck trips with valid-denominator counts."
    domain = AnalyticsDomain.TRUCKS
    supported_metrics = TRUCK_METRICS
    required_parameters = ()
    allowed_parameters = TRUCK_PARAMS
    allowed_groupings = ()
    maximum_result_size = 1
    example_questions = ("Show truck performance in Greater Cairo during the last 30 days.",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        valid_capacity = Truck.capacity_kg > 0
        valid_fuel = TruckTripLog.fuel_consumed_l > 0
        statement = _scope(
            select(
                func.count(TruckTripLog.id).label("trip_count"),
                func.coalesce(func.sum(TruckTripLog.distance_km), 0).label("total_distance_km"),
                func.coalesce(func.sum(TruckTripLog.fuel_consumed_l), 0).label("total_fuel_consumed_l"),
                func.avg(TruckTripLog.fuel_consumed_l).label("average_fuel_consumed_l"),
                func.avg(TruckTripLog.load_kg).label("average_load_kg"),
                func.avg(TruckTripLog.avg_speed_kmh).label("average_speed_kmh"),
                func.coalesce(func.sum(TruckTripLog.stops_completed), 0).label("total_stops_completed"),
                func.avg(TruckTripLog.trip_duration_min).label("average_trip_duration_min"),
                func.avg(case((valid_capacity, TruckTripLog.load_kg * 100.0 / Truck.capacity_kg), else_=None)).label("truck_utilization_pct"),
                func.avg(case((valid_fuel, TruckTripLog.distance_km / TruckTripLog.fuel_consumed_l), else_=None)).label("fuel_efficiency_km_per_l"),
                func.sum(case((valid_capacity, 1), else_=0)).label("utilization_records_included"),
                func.sum(case((~valid_capacity, 1), else_=0)).label("utilization_records_excluded"),
                func.sum(case((valid_fuel, 1), else_=0)).label("fuel_efficiency_records_included"),
                func.sum(case((~valid_fuel, 1), else_=0)).label("fuel_efficiency_records_excluded"),
                func.min(TruckTripLog.date).label("effective_start_date"),
                func.max(TruckTripLog.date).label("effective_end_date"),
            ).join(Truck, Truck.truck_id == TruckTripLog.truck_id),
            params,
        )
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=1)
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=["Utilization is load / capacity × 100 and is not capped at 100%.", "Fuel efficiency excludes trips with zero fuel."],
            aggregation_definitions={
                "truck_utilization_pct": "Mean trip load/capacity × 100 over utilization_records_included.",
                "fuel_efficiency_km_per_l": "Mean distance/fuel over positive-fuel trips.",
            },
        )


class TruckRankingTool:
    name = "rank_trucks_by_metric"
    description = "Rank trucks using one approved historical performance metric."
    domain = AnalyticsDomain.TRUCKS
    supported_metrics = TRUCK_METRICS
    required_parameters = ("metric",)
    allowed_parameters = TRUCK_PARAMS
    allowed_groupings = ("truck_id",)
    maximum_result_size = 200
    example_questions = ("Which trucks consumed the most fuel?",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        metric_id = params.metric or "total_fuel_consumed_l"
        expression = get_metric(metric_id).expression_builder().label(metric_id)
        statement = _scope(
            select(TruckTripLog.truck_id, expression, func.count(TruckTripLog.id).label("records_included"))
            .join(Truck, Truck.truck_id == TruckTripLog.truck_id)
            .group_by(TruckTripLog.truck_id),
            params,
        )
        statement = statement.order_by(expression.asc() if params.sort_direction == SortDirection.ASC else expression.desc(), TruckTripLog.truck_id)
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=params.limit or 50)
        return AnalyticsToolResult(
            tool_name=self.name,
            metric=metric_id,
            description=f"{get_metric(metric_id).name} grouped by truck",
            columns=list(rows[0]) if rows else ["truck_id", metric_id],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=[get_metric(metric_id).interpretation_notes],
            aggregation_definitions={metric_id: get_metric(metric_id).description},
        )


class TruckAnomalyTool:
    name = "detect_truck_rule_anomalies"
    description = "Detect transparent deterministic truck rules; this is not an ML prediction."
    domain = AnalyticsDomain.TRUCKS
    supported_metrics = ()
    required_parameters = ()
    allowed_parameters = tuple(item for item in TRUCK_PARAMS if item not in {"metric", "sort_direction"})
    allowed_groupings = ()
    maximum_result_size = 200
    example_questions = ("Which trucks consumed more fuel than their normal average?",)

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.executor = QueryExecutor(self.settings)

    async def execute(self, params, session):
        history = (
            select(
                TruckTripLog.id,
                TruckTripLog.truck_id,
                TruckTripLog.date,
                TruckTripLog.region,
                TruckTripLog.status,
                TruckTripLog.distance_km,
                TruckTripLog.fuel_consumed_l,
                TruckTripLog.load_kg,
                TruckTripLog.trip_duration_min,
                Truck.capacity_kg,
                func.avg(TruckTripLog.fuel_consumed_l).over(partition_by=TruckTripLog.truck_id).label("historical_average_fuel_l"),
                func.avg(TruckTripLog.trip_duration_min).over(partition_by=TruckTripLog.truck_id).label("historical_average_duration_min"),
            )
            .join(Truck, Truck.truck_id == TruckTripLog.truck_id)
            .subquery("truck_history")
        )
        utilization = history.c.load_kg * 100.0 / func.nullif(history.c.capacity_kg, 0)
        fuel_rule = history.c.fuel_consumed_l > history.c.historical_average_fuel_l * self.settings.truck_fuel_anomaly_multiplier
        duration_rule = history.c.trip_duration_min > history.c.historical_average_duration_min * self.settings.truck_duration_anomaly_multiplier
        zero_fuel_rule = (history.c.fuel_consumed_l == 0) & (history.c.distance_km > 0)
        zero_distance_rule = (history.c.load_kg > 0) & (history.c.distance_km == 0)
        utilization_rule = utilization > 100
        rule = func.concat_ws(
            "; ",
            case((utilization_rule, "Utilization exceeded 100%: load_kg / capacity_kg x 100 > 100."), else_=None),
            case((fuel_rule, f"Fuel exceeded {self.settings.truck_fuel_anomaly_multiplier} x this truck's historical average."), else_=None),
            case((duration_rule, f"Duration exceeded {self.settings.truck_duration_anomaly_multiplier} x this truck's historical average."), else_=None),
            case((zero_fuel_rule, "Fuel was zero while trip distance was positive."), else_=None),
            case((zero_distance_rule, "Load was positive while trip distance was zero."), else_=None),
        ).label("triggered_rules")
        statement = select(
            history.c.truck_id,
            history.c.date,
            history.c.distance_km,
            history.c.fuel_consumed_l,
            history.c.load_kg,
            history.c.trip_duration_min,
            utilization.label("utilization_pct"),
            history.c.historical_average_fuel_l,
            history.c.historical_average_duration_min,
            rule,
        ).where(or_(utilization_rule, fuel_rule, duration_rule, zero_fuel_rule, zero_distance_rule))
        statement = _scope(statement, params, columns=history.c).order_by(history.c.date.desc(), history.c.truck_id)
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=params.limit or 50)
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=["These are configured deterministic rules, not AI predictions.", "Historical averages use all available records for each truck."],
            aggregation_definitions={"utilization_pct": "load_kg / capacity_kg x 100; values are not capped."},
        )
