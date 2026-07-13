"""Region-day environmental analytics tool."""

from sqlalchemy import case, func, select

from app.analytics.enums import AnalyticsDomain
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.environmental_daily import EnvironmentalDaily
from app.schemas.analytics_tools import AnalyticsToolResult


class EnvironmentalSummaryTool:
    name = "get_environmental_summary"
    description = "Summarize environmental records aggregated at region-day level."
    domain = AnalyticsDomain.ENVIRONMENT
    supported_metrics = (
        "average_temperature_c",
        "total_rainfall_mm",
        "holiday_day_count",
        "festival_day_count",
        "weekend_day_count",
        "traffic_level_distribution",
    )
    required_parameters = ()
    allowed_parameters = ("start_date", "end_date", "region", "traffic_level", "holiday", "festival", "weekend", "limit", "latest_available")
    allowed_groupings = ()
    maximum_result_size = 20
    example_questions = ("Summarize environmental conditions last month.",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        statement = select(
            func.avg(EnvironmentalDaily.temperature_c).label("average_temperature_c"),
            func.coalesce(func.sum(EnvironmentalDaily.rainfall_mm), 0).label("total_rainfall_mm"),
            func.sum(case((EnvironmentalDaily.is_holiday.is_(True), 1), else_=0)).label("holiday_day_count"),
            func.sum(case((EnvironmentalDaily.is_festival.is_(True), 1), else_=0)).label("festival_day_count"),
            func.sum(case((EnvironmentalDaily.is_weekend.is_(True), 1), else_=0)).label("weekend_day_count"),
            func.sum(case((func.lower(EnvironmentalDaily.traffic_level) == "low", 1), else_=0)).label("traffic_low_count"),
            func.sum(case((func.lower(EnvironmentalDaily.traffic_level) == "medium", 1), else_=0)).label("traffic_medium_count"),
            func.sum(case((func.lower(EnvironmentalDaily.traffic_level) == "high", 1), else_=0)).label("traffic_high_count"),
            func.count(EnvironmentalDaily.id).label("region_day_records_included"),
            func.min(EnvironmentalDaily.date).label("effective_start_date"),
            func.max(EnvironmentalDaily.date).label("effective_end_date"),
        )
        if params.start_date is not None:
            statement = statement.where(EnvironmentalDaily.date >= params.start_date)
        if params.end_date is not None:
            statement = statement.where(EnvironmentalDaily.date <= params.end_date)
        if params.region is not None:
            statement = statement.where(func.lower(EnvironmentalDaily.region) == params.region.casefold())
        if params.traffic_level is not None:
            statement = statement.where(func.lower(EnvironmentalDaily.traffic_level) == params.traffic_level.casefold())
        if params.holiday is not None:
            statement = statement.where(EnvironmentalDaily.is_holiday == params.holiday)
        if params.festival is not None:
            statement = statement.where(EnvironmentalDaily.is_festival == params.festival)
        if params.weekend is not None:
            statement = statement.where(EnvironmentalDaily.is_weekend == params.weekend)
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=1)
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=["Environmental records are aggregated at region-day level; day counts are region-day counts."],
            aggregation_definitions={"traffic_level_distribution": "Counts of region-day records per allow-listed traffic level."},
        )
