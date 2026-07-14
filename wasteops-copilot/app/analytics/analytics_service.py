"""Validate, execute, and evidence-wrap approved analytics tools."""

import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.evidence_builder import EvidenceBuilder
from app.analytics.parameter_parser import ParameterParser
from app.core.logging import get_logger
from app.analytics.query_executor import QueryExecutor
from app.models.environmental_daily import EnvironmentalDaily
from app.models.operational_daily import OperationalDaily
from app.models.smart_bin_reading import SmartBinReading
from app.models.smart_bin import SmartBin
from app.models.truck_trip_log import TruckTripLog
from app.models.worker import Worker
from app.models.workforce_attendance import WorkforceAttendance
from app.observability.tracer import Tracer
from app.core.database import AsyncSessionLocal

logger = get_logger(__name__)


class AnalyticsService:
    def __init__(self, registry, settings, *, tracer: Tracer | None = None) -> None:
        self.registry = registry
        self.parser = ParameterParser(registry, settings)
        self.evidence_builder = EvidenceBuilder()
        self.executor = QueryExecutor(settings)
        self.tracer = tracer or Tracer(session_factory=AsyncSessionLocal, settings=settings)

    async def _resolve_latest(self, tool_name, params, session):
        if not params.latest_available:
            return params
        date_columns = {
            "get_operations_summary": OperationalDaily.date,
            "rank_regions_by_operations_metric": OperationalDaily.date,
            "get_truck_performance_summary": TruckTripLog.date,
            "rank_trucks_by_metric": TruckTripLog.date,
            "detect_truck_rule_anomalies": TruckTripLog.date,
            "get_workforce_summary": WorkforceAttendance.date,
            "rank_workforce_groups": WorkforceAttendance.date,
            "get_environmental_summary": EnvironmentalDaily.date,
        }
        timestamp_tools = {"get_bin_status_summary": SmartBinReading.timestamp}
        column = date_columns.get(tool_name)
        if column is None:
            column = timestamp_tools.get(tool_name)
        if column is None:
            return params
        statement = select(func.max(column).label("latest_value"))
        if tool_name in {"get_operations_summary", "rank_regions_by_operations_metric"}:
            if params.region:
                statement = statement.where(func.lower(OperationalDaily.region) == params.region.casefold())
            if params.governorate:
                statement = statement.where(func.lower(OperationalDaily.governorate) == params.governorate.casefold())
            if params.bin_id:
                statement = statement.where(OperationalDaily.bin_id == params.bin_id)
        elif tool_name in {"get_truck_performance_summary", "rank_trucks_by_metric", "detect_truck_rule_anomalies"}:
            if params.region:
                statement = statement.where(func.lower(TruckTripLog.region) == params.region.casefold())
            if params.truck_id:
                statement = statement.where(TruckTripLog.truck_id == params.truck_id)
            if params.trip_status:
                statement = statement.where(func.lower(TruckTripLog.status) == params.trip_status.casefold())
        elif tool_name in {"get_workforce_summary", "rank_workforce_groups"}:
            statement = statement.join(Worker, Worker.worker_id == WorkforceAttendance.worker_id)
            if params.region:
                statement = statement.where(func.lower(Worker.region) == params.region.casefold())
            if params.governorate:
                statement = statement.where(func.lower(Worker.governorate) == params.governorate.casefold())
            if params.shift:
                statement = statement.where(func.lower(Worker.shift) == params.shift.casefold())
            if params.worker_id:
                statement = statement.where(WorkforceAttendance.worker_id == params.worker_id)
        elif tool_name == "get_environmental_summary":
            if params.region:
                statement = statement.where(func.lower(EnvironmentalDaily.region) == params.region.casefold())
            if params.traffic_level:
                statement = statement.where(func.lower(EnvironmentalDaily.traffic_level) == params.traffic_level.casefold())
            if params.holiday is not None:
                statement = statement.where(EnvironmentalDaily.is_holiday == params.holiday)
            if params.festival is not None:
                statement = statement.where(EnvironmentalDaily.is_festival == params.festival)
            if params.weekend is not None:
                statement = statement.where(EnvironmentalDaily.is_weekend == params.weekend)
        elif tool_name == "get_bin_status_summary":
            statement = statement.join(SmartBin, SmartBin.bin_id == SmartBinReading.bin_id)
            if params.region:
                statement = statement.where(func.lower(SmartBin.region) == params.region.casefold())
            if params.governorate:
                statement = statement.where(func.lower(SmartBin.governorate) == params.governorate.casefold())
            if params.bin_id:
                statement = statement.where(SmartBinReading.bin_id == params.bin_id)
            if params.waste_type:
                statement = statement.where(func.lower(SmartBinReading.waste_type) == params.waste_type.casefold())
            if params.sensor_status:
                statement = statement.where(func.lower(SmartBinReading.sensor_status) == params.sensor_status.casefold())
        rows = await self.executor.execute(session, statement, tool_name=f"{tool_name}:latest", limit=1)
        latest = rows[0].get("latest_value") if rows else None
        if latest is None:
            return params
        update = {"latest_available": True}
        if tool_name in timestamp_tools:
            update.update({"start_timestamp": latest, "end_timestamp": latest})
        else:
            update.update({"start_date": latest, "end_date": latest})
        return params.model_copy(update=update)

    async def execute(self, tool_name: str, parameters, session: AsyncSession):
        async with self.tracer.span("ANALYTICS_TOOL", {"tool_name": tool_name}) as span:
            evidence = await self._execute(tool_name, parameters, session)
            span.set_metric("row_count", evidence.record_count)
            span.set_metric("no_data", not evidence.rows)
            return evidence

    async def _execute(self, tool_name: str, parameters, session: AsyncSession):
        started = time.perf_counter()
        tool = self.registry.get(tool_name)
        params = self.parser.parse(tool_name, parameters)
        params = await self._resolve_latest(tool_name, params, session)
        result = await tool.execute(params, session)
        evidence = self.evidence_builder.build([result])
        logger.info(
            "analytics_tool_completed",
            tool_name=tool.name,
            domain=tool.domain,
            row_count=len(result.rows),
            no_data=not result.rows,
            duration_seconds=time.perf_counter() - started,
        )
        return evidence[0]
