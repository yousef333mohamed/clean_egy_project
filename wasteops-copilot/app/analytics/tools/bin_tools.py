"""Smart-bin telemetry summaries and deterministic latest-status tools."""

from sqlalchemy import case, func, select

from app.analytics.enums import AnalyticsDomain
from app.analytics.metric_registry import CRITICAL_FILL_THRESHOLD_PCT, LOW_BATTERY_THRESHOLD_PCT, get_metric
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.smart_bin import SmartBin
from app.models.smart_bin_reading import SmartBinReading
from app.schemas.analytics_tools import AnalyticsToolResult

BIN_PARAMS = ("start_timestamp", "end_timestamp", "region", "governorate", "bin_id", "waste_type", "sensor_status", "limit", "latest_available")


def _scope(statement, params):
    if params.start_timestamp is not None:
        statement = statement.where(SmartBinReading.timestamp >= params.start_timestamp)
    if params.end_timestamp is not None:
        statement = statement.where(SmartBinReading.timestamp <= params.end_timestamp)
    if params.region is not None:
        statement = statement.where(func.lower(SmartBin.region) == params.region.casefold())
    if params.governorate is not None:
        statement = statement.where(func.lower(SmartBin.governorate) == params.governorate.casefold())
    if params.bin_id is not None:
        statement = statement.where(SmartBinReading.bin_id == params.bin_id)
    if params.waste_type is not None:
        statement = statement.where(func.lower(SmartBinReading.waste_type) == params.waste_type.casefold())
    if params.sensor_status is not None:
        statement = statement.where(func.lower(SmartBinReading.sensor_status) == params.sensor_status.casefold())
    return statement


def _latest_subquery(params):
    ranked = _scope(
        select(
            SmartBinReading.bin_id,
            SmartBinReading.fill_level_pct,
            SmartBinReading.battery_level_pct,
            SmartBinReading.sensor_status,
            SmartBinReading.timestamp,
            SmartBin.region,
            SmartBin.governorate,
            func.row_number().over(partition_by=SmartBinReading.bin_id, order_by=SmartBinReading.timestamp.desc()).label("rn"),
        ).join(SmartBin, SmartBin.bin_id == SmartBinReading.bin_id),
        params,
    )
    return ranked.subquery("latest_bin_readings")


class BinStatusSummaryTool:
    name = "get_bin_status_summary"
    description = "Summarize telemetry with null-aware fill and weight calculations."
    domain = AnalyticsDomain.BINS
    supported_metrics = (
        "average_fill_level_pct",
        "maximum_fill_level_pct",
        "average_battery_level_pct",
        "sensor_fault_reading_count",
        "collection_event_count",
        "critical_fill_reading_count",
        "low_battery_reading_count",
    )
    required_parameters = ()
    allowed_parameters = BIN_PARAMS
    allowed_groupings = ()
    maximum_result_size = 1
    example_questions = ("How many bin readings have low batteries?",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        statement = _scope(
            select(
                get_metric("average_fill_level_pct").expression_builder().label("average_fill_level_pct"),
                get_metric("maximum_fill_level_pct").expression_builder().label("maximum_fill_level_pct"),
                get_metric("average_battery_level_pct").expression_builder().label("average_battery_level_pct"),
                func.coalesce(get_metric("sensor_fault_reading_count").expression_builder(), 0).label("sensor_fault_reading_count"),
                func.coalesce(get_metric("collection_event_count").expression_builder(), 0).label("collection_event_count"),
                func.coalesce(get_metric("critical_fill_reading_count").expression_builder(), 0).label("critical_fill_reading_count"),
                func.coalesce(get_metric("low_battery_reading_count").expression_builder(), 0).label("low_battery_reading_count"),
                func.count(SmartBinReading.id).label("records_included"),
                func.count(SmartBinReading.fill_level_pct).label("fill_records_included"),
                func.sum(case((SmartBinReading.fill_level_pct.is_(None), 1), else_=0)).label("fill_records_excluded_null"),
                func.count(SmartBinReading.waste_weight_kg).label("weight_records_included"),
                func.sum(case((SmartBinReading.waste_weight_kg.is_(None), 1), else_=0)).label("weight_records_excluded_null"),
                func.min(SmartBinReading.timestamp).label("effective_start_timestamp"),
                func.max(SmartBinReading.timestamp).label("effective_end_timestamp"),
            ).join(SmartBin, SmartBin.bin_id == SmartBinReading.bin_id),
            params,
        )
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=1)
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_timestamp,
            data_period_end=params.end_timestamp,
            notes=[
                "Configured rules: critical fill >= 80%; low battery < 20%. These are not marked as official policy.",
                "Null measurements are excluded from averages and counted separately.",
            ],
            aggregation_definitions={"average_fill_level_pct": "Mean over fill_records_included non-null readings."},
        )


class _LatestBinsTool:
    domain = AnalyticsDomain.BINS
    supported_metrics = ()
    required_parameters = ()
    allowed_parameters = BIN_PARAMS
    allowed_groupings = ()
    maximum_result_size = 200

    predicate = None
    measurement = "fill_level_pct"
    extra_notes: tuple[str, ...] = ()

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        latest = _latest_subquery(params)
        statement = select(
            latest.c.bin_id,
            latest.c.fill_level_pct,
            latest.c.battery_level_pct,
            latest.c.sensor_status,
            latest.c.timestamp.label("reading_timestamp"),
            latest.c.region,
            latest.c.governorate,
        ).where(latest.c.rn == 1, self.predicate(latest))
        rows = await self.executor.execute(
            session, statement.order_by(latest.c.timestamp.desc(), latest.c.bin_id), tool_name=self.name, limit=params.limit or 50
        )
        measurement = getattr(latest.c, self.measurement)
        stats_rows = await self.executor.execute(
            session,
            select(
                func.sum(case((measurement.is_(None), 1), else_=0)).label("bins_without_valid_latest_measurement"),
                func.max(latest.c.timestamp).label("latest_timestamp_available"),
            ).where(latest.c.rn == 1),
            tool_name=f"{self.name}:quality",
            limit=1,
        )
        stats = stats_rows[0] if stats_rows else {}
        timestamps = [row["reading_timestamp"] for row in rows if row.get("reading_timestamp")]
        notes = ["Uses the latest reading per bin inside the requested scope; historical statuses are not treated as current.", *self.extra_notes]
        if timestamps:
            notes.append(f"Latest returned timestamp: {max(timestamps)}")
        if stats.get("latest_timestamp_available"):
            notes.append(f"Latest timestamp available: {stats['latest_timestamp_available']}")
        notes.append(f"Bins with no valid latest measurement: {stats.get('bins_without_valid_latest_measurement', 0)}")
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_timestamp,
            data_period_end=params.end_timestamp,
            notes=notes,
        )


class CriticalBinsTool(_LatestBinsTool):
    name = "list_critical_bins"
    description = "List bins whose latest valid fill is at least the configured 80% rule."
    example_questions = ("Which bins are currently critical?",)
    predicate = staticmethod(lambda latest: latest.c.fill_level_pct.is_not(None) & (latest.c.fill_level_pct >= CRITICAL_FILL_THRESHOLD_PCT))
    extra_notes = ("The configured 80% fill threshold is not marked as an official policy.", "Bins with a null latest fill measurement are excluded.")


class LowBatteryBinsTool(_LatestBinsTool):
    name = "list_low_battery_bins"
    description = "List bins whose latest battery reading is below the configured 20% rule."
    example_questions = ("How many bins currently have low batteries?",)
    predicate = staticmethod(lambda latest: latest.c.battery_level_pct < LOW_BATTERY_THRESHOLD_PCT)
    measurement = "battery_level_pct"
    extra_notes = ("The configured 20% battery threshold is not marked as an official policy.",)


class SensorFaultBinsTool(_LatestBinsTool):
    name = "list_sensor_fault_bins"
    description = "List bins whose latest sensor status indicates a fault."
    example_questions = ("Which bins currently have sensor faults?",)
    predicate = staticmethod(lambda latest: func.lower(latest.c.sensor_status).like("%fault%"))
    measurement = "sensor_status"
