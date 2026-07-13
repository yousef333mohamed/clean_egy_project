"""Cross-domain operational overview with explicitly labeled effective dates."""

from sqlalchemy import case, cast, Date, func, select

from app.analytics.enums import AnalyticsDomain
from app.analytics.metric_registry import CRITICAL_FILL_THRESHOLD_PCT, LOW_BATTERY_THRESHOLD_PCT
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.operational_daily import OperationalDaily
from app.models.smart_bin import SmartBin
from app.models.smart_bin_reading import SmartBinReading
from app.models.truck_trip_log import TruckTripLog
from app.models.workforce_attendance import WorkforceAttendance
from app.models.worker import Worker
from app.schemas.analytics_tools import AnalyticsToolResult


class OperationalOverviewTool:
    name = "get_operational_overview"
    description = "Small cross-domain snapshot with per-section effective dates."
    domain = AnalyticsDomain.OVERVIEW
    supported_metrics = ()
    required_parameters = ()
    allowed_parameters = ("start_date", "end_date", "region", "limit", "latest_available")
    allowed_groupings = ()
    maximum_result_size = 1
    example_questions = ("Give me an operational overview for March.",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    @staticmethod
    def _period(statement, column, params):
        if params.start_date:
            statement = statement.where(column >= params.start_date)
        if params.end_date:
            statement = statement.where(column <= params.end_date)
        return statement

    async def execute(self, params, session):
        bins = select(func.count(SmartBin.bin_id))
        if params.region:
            bins = bins.where(func.lower(SmartBin.region) == params.region.casefold())
        ranked = select(
            SmartBinReading.bin_id,
            SmartBinReading.fill_level_pct,
            SmartBinReading.battery_level_pct,
            SmartBinReading.sensor_status,
            SmartBinReading.timestamp,
            func.row_number().over(partition_by=SmartBinReading.bin_id, order_by=SmartBinReading.timestamp.desc()).label("rn"),
        )
        ranked = self._period(ranked, cast(SmartBinReading.timestamp, Date), params)
        if params.region:
            ranked = ranked.join(SmartBin, SmartBin.bin_id == SmartBinReading.bin_id).where(func.lower(SmartBin.region) == params.region.casefold())
        latest = ranked.subquery("overview_latest")
        operations = self._period(
            select(
                func.sum(case((OperationalDaily.missed_collection.is_(True), 1), else_=0)).label("missed"),
                func.sum(case((OperationalDaily.emergency_request.is_(True), 1), else_=0)).label("emergency"),
                func.sum(case((OperationalDaily.complaint_filed.is_(True), 1), else_=0)).label("complaints"),
                func.max(OperationalDaily.date).label("effective_date"),
            ),
            OperationalDaily.date,
            params,
        )
        if params.region:
            operations = operations.where(func.lower(OperationalDaily.region) == params.region.casefold())
        if params.latest_available and not params.start_date and not params.end_date:
            operations_max = select(func.max(OperationalDaily.date))
            if params.region:
                operations_max = operations_max.where(func.lower(OperationalDaily.region) == params.region.casefold())
            operations = operations.where(OperationalDaily.date == operations_max.scalar_subquery())
        ops = operations.subquery("overview_operations")
        trucks = self._period(
            select(
                func.count(func.distinct(TruckTripLog.truck_id)).label("active_trucks"),
                func.count(TruckTripLog.id).label("trips"),
                func.max(TruckTripLog.date).label("effective_date"),
            ),
            TruckTripLog.date,
            params,
        )
        if params.region:
            trucks = trucks.where(func.lower(TruckTripLog.region) == params.region.casefold())
        if params.latest_available and not params.start_date and not params.end_date:
            trucks_max = select(func.max(TruckTripLog.date))
            if params.region:
                trucks_max = trucks_max.where(func.lower(TruckTripLog.region) == params.region.casefold())
            trucks = trucks.where(TruckTripLog.date == trucks_max.scalar_subquery())
        truck = trucks.subquery("overview_trucks")
        workforce_statement = self._period(
            select(
                func.avg(case((WorkforceAttendance.present.is_(True), 100.0), else_=0.0)).label("attendance_rate"),
                func.max(WorkforceAttendance.date).label("effective_date"),
            ).join(Worker, Worker.worker_id == WorkforceAttendance.worker_id),
            WorkforceAttendance.date,
            params,
        )
        if params.region:
            workforce_statement = workforce_statement.where(func.lower(Worker.region) == params.region.casefold())
        if params.latest_available and not params.start_date and not params.end_date:
            workforce_max = select(func.max(WorkforceAttendance.date)).join(Worker, Worker.worker_id == WorkforceAttendance.worker_id)
            if params.region:
                workforce_max = workforce_max.where(func.lower(Worker.region) == params.region.casefold())
            workforce_statement = workforce_statement.where(WorkforceAttendance.date == workforce_max.scalar_subquery())
        workforce = workforce_statement.subquery("overview_workforce")
        statement = select(
            bins.scalar_subquery().label("total_bins"),
            select(func.count())
            .select_from(latest)
            .where(latest.c.rn == 1, latest.c.fill_level_pct >= CRITICAL_FILL_THRESHOLD_PCT)
            .scalar_subquery()
            .label("latest_critical_bins"),
            select(func.count())
            .select_from(latest)
            .where(latest.c.rn == 1, latest.c.battery_level_pct < LOW_BATTERY_THRESHOLD_PCT)
            .scalar_subquery()
            .label("latest_low_battery_bins"),
            select(func.count())
            .select_from(latest)
            .where(latest.c.rn == 1, func.lower(latest.c.sensor_status).like("%fault%"))
            .scalar_subquery()
            .label("latest_sensor_fault_bins"),
            select(func.max(latest.c.timestamp)).where(latest.c.rn == 1).scalar_subquery().label("bin_status_effective_timestamp"),
            ops.c.missed.label("missed_collection_count"),
            ops.c.emergency.label("emergency_request_count"),
            ops.c.complaints.label("complaint_count"),
            ops.c.effective_date.label("operations_effective_date"),
            truck.c.active_trucks.label("active_trucks_represented"),
            truck.c.trips.label("trip_count"),
            truck.c.effective_date.label("trucks_effective_date"),
            workforce.c.attendance_rate.label("attendance_rate_pct"),
            workforce.c.effective_date.label("workforce_effective_date"),
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
            notes=[
                "Each section includes its own effective date because source coverage may differ.",
                "Critical fill >= 80% and low battery < 20% are configured rules, not marked as official policy.",
            ],
            aggregation_definitions={"attendance_rate_pct": "Present records / attendance records × 100."},
        )
