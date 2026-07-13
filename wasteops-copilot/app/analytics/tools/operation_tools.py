"""Daily-operations summary and regional ranking tools."""

from sqlalchemy import case, func, select

from app.analytics.enums import AnalyticsDomain, SortDirection
from app.analytics.metric_registry import get_metric
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.operational_daily import OperationalDaily
from app.schemas.analytics_tools import AnalyticsToolParameters, AnalyticsToolResult

OPERATION_METRICS = ("missed_collection_count", "emergency_request_count", "complaint_count", "illegal_dumping_count", "average_service_completion_time_min")
FILTERS = ("start_date", "end_date", "region", "governorate", "bin_id", "metric", "sort_direction", "limit", "latest_available")


def _filters(statement, params):
    for value, column, op in [
        (params.start_date, OperationalDaily.date, "ge"),
        (params.end_date, OperationalDaily.date, "le"),
        (params.region, OperationalDaily.region, "eq"),
        (params.governorate, OperationalDaily.governorate, "eq"),
        (params.bin_id, OperationalDaily.bin_id, "eq"),
    ]:
        if value is not None:
            statement = statement.where(getattr(column, f"__{op}__")(value))
    return statement


class OperationsSummaryTool:
    name = "get_operations_summary"
    description = "Summarize historical daily operational outcomes."
    domain = AnalyticsDomain.OPERATIONS
    supported_metrics = OPERATION_METRICS
    required_parameters = ()
    allowed_parameters = FILTERS
    allowed_groupings = ()
    maximum_result_size = 1
    example_questions = ("How many missed collections occurred in March?",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        statement = select(
            func.coalesce(get_metric("missed_collection_count").expression_builder(), 0).label("missed_collection_count"),
            func.coalesce(get_metric("emergency_request_count").expression_builder(), 0).label("emergency_request_count"),
            func.coalesce(get_metric("complaint_count").expression_builder(), 0).label("complaint_count"),
            func.coalesce(get_metric("illegal_dumping_count").expression_builder(), 0).label("illegal_dumping_count"),
            get_metric("average_service_completion_time_min").expression_builder().label("average_service_completion_time_min"),
            func.count(OperationalDaily.id).label("records_included"),
            func.count(OperationalDaily.service_completion_time_min).label("completion_time_records_included"),
            func.sum(case((OperationalDaily.service_completion_time_min.is_(None), 1), else_=0)).label("records_missing_completion_time"),
            func.min(OperationalDaily.date).label("effective_start_date"),
            func.max(OperationalDaily.date).label("effective_end_date"),
        )
        rows = await self.executor.execute(session, _filters(statement, params), tool_name=self.name, limit=1)
        return AnalyticsToolResult(
            tool_name=self.name,
            description=self.description,
            columns=list(rows[0]) if rows else [],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=["Null service-completion times are excluded from the average, not converted to zero."],
            aggregation_definitions={"average_service_completion_time_min": "Mean over completion_time_records_included non-null records."},
        )


class RegionalOperationsRankingTool:
    name = "rank_regions_by_operations_metric"
    description = "Rank regions by one approved operations metric."
    domain = AnalyticsDomain.OPERATIONS
    supported_metrics = OPERATION_METRICS
    required_parameters = ("metric",)
    allowed_parameters = FILTERS
    allowed_groupings = ("region",)
    maximum_result_size = 200
    example_questions = ("Which region had the most complaints in March 2026?",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params: AnalyticsToolParameters, session):
        metric_id = params.metric or "missed_collection_count"
        expression = get_metric(metric_id).expression_builder().label(metric_id)
        statement = _filters(select(OperationalDaily.region.label("region"), expression).group_by(OperationalDaily.region), params)
        statement = statement.order_by(expression.asc() if params.sort_direction == SortDirection.ASC else expression.desc(), OperationalDaily.region.asc())
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=params.limit or 50)
        notes = ["Null service-completion times are excluded from averages."] if metric_id.startswith("average_") else []
        return AnalyticsToolResult(
            tool_name=self.name,
            metric=metric_id,
            description=f"{get_metric(metric_id).name} grouped by region",
            columns=["region", metric_id],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=notes,
            aggregation_definitions={metric_id: get_metric(metric_id).description},
        )
