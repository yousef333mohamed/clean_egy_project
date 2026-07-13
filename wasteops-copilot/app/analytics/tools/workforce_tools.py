"""Workforce summary and allow-listed grouping tools."""

from sqlalchemy import case, func, select

from app.analytics.enums import AnalyticsDomain, SortDirection
from app.analytics.metric_registry import get_metric
from app.analytics.query_executor import QueryExecutor
from app.core.config import get_settings
from app.models.worker import Worker
from app.models.workforce_attendance import WorkforceAttendance
from app.schemas.analytics_tools import AnalyticsToolResult

WORKFORCE_METRICS = ("attendance_rate_pct", "total_completed_tasks", "average_completed_tasks", "total_overtime_hours", "average_performance_score")
WORKFORCE_PARAMS = (
    "start_date",
    "end_date",
    "region",
    "governorate",
    "shift",
    "worker_id",
    "group_by",
    "metric",
    "sort_direction",
    "limit",
    "latest_available",
)


def _scope(statement, params):
    if params.start_date is not None:
        statement = statement.where(WorkforceAttendance.date >= params.start_date)
    if params.end_date is not None:
        statement = statement.where(WorkforceAttendance.date <= params.end_date)
    if params.region is not None:
        statement = statement.where(func.lower(Worker.region) == params.region.casefold())
    if params.governorate is not None:
        statement = statement.where(func.lower(Worker.governorate) == params.governorate.casefold())
    if params.shift is not None:
        statement = statement.where(func.lower(Worker.shift) == params.shift.casefold())
    if params.worker_id is not None:
        statement = statement.where(WorkforceAttendance.worker_id == params.worker_id)
    return statement


class WorkforceSummaryTool:
    name = "get_workforce_summary"
    description = "Summarize attendance, tasks, overtime, and null-safe performance."
    domain = AnalyticsDomain.WORKFORCE
    supported_metrics = WORKFORCE_METRICS
    required_parameters = ()
    allowed_parameters = WORKFORCE_PARAMS
    allowed_groupings = ()
    maximum_result_size = 1
    example_questions = ("What was workforce attendance in March?",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        statement = _scope(
            select(
                func.count(func.distinct(WorkforceAttendance.worker_id)).label("worker_count"),
                func.count(WorkforceAttendance.id).label("attendance_record_count"),
                func.coalesce(get_metric("present_worker_count").expression_builder(), 0).label("present_worker_count"),
                func.coalesce(get_metric("absent_worker_count").expression_builder(), 0).label("absent_worker_count"),
                get_metric("attendance_rate_pct").expression_builder().label("attendance_rate_pct"),
                func.coalesce(get_metric("total_completed_tasks").expression_builder(), 0).label("total_completed_tasks"),
                func.coalesce(get_metric("total_overtime_hours").expression_builder(), 0).label("total_overtime_hours"),
                get_metric("average_performance_score").expression_builder().label("average_performance_score"),
                func.count(WorkforceAttendance.performance_score).label("performance_records_included"),
                func.sum(case((WorkforceAttendance.performance_score.is_(None), 1), else_=0)).label("records_missing_performance_score"),
                func.min(WorkforceAttendance.date).label("effective_start_date"),
                func.max(WorkforceAttendance.date).label("effective_end_date"),
            ).join(Worker, Worker.worker_id == WorkforceAttendance.worker_id),
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
            notes=["Missing performance scores are excluded from the average, not converted to zero."],
            aggregation_definitions={
                "attendance_rate_pct": "Present attendance records / all attendance records × 100.",
                "average_performance_score": "Mean over performance_records_included.",
            },
        )


class WorkforceRankingTool:
    name = "rank_workforce_groups"
    description = "Rank an approved workforce grouping by an approved metric."
    domain = AnalyticsDomain.WORKFORCE
    supported_metrics = WORKFORCE_METRICS
    required_parameters = ("group_by", "metric")
    allowed_parameters = WORKFORCE_PARAMS
    allowed_groupings = ("region", "governorate", "shift", "worker_id")
    maximum_result_size = 200
    example_questions = ("Rank shifts by attendance rate.",)

    def __init__(self, settings=None):
        self.executor = QueryExecutor(settings or get_settings())

    async def execute(self, params, session):
        grouping = params.group_by or "region"
        metric_id = params.metric or "attendance_rate_pct"
        group_column = {"region": Worker.region, "governorate": Worker.governorate, "shift": Worker.shift, "worker_id": WorkforceAttendance.worker_id}[grouping]
        expression = get_metric(metric_id).expression_builder().label(metric_id)
        statement = _scope(
            select(
                group_column.label(grouping),
                expression,
                func.count(WorkforceAttendance.id).label("records_included"),
                func.count(WorkforceAttendance.performance_score).label("performance_records_included"),
            )
            .join(Worker, Worker.worker_id == WorkforceAttendance.worker_id)
            .group_by(group_column),
            params,
        )
        statement = statement.order_by(expression.asc() if params.sort_direction == SortDirection.ASC else expression.desc(), group_column)
        rows = await self.executor.execute(session, statement, tool_name=self.name, limit=params.limit or 50)
        return AnalyticsToolResult(
            tool_name=self.name,
            metric=metric_id,
            description=f"{get_metric(metric_id).name} grouped by {grouping}",
            columns=list(rows[0]) if rows else [grouping, metric_id],
            rows=rows,
            filters=params.model_dump(mode="json", exclude_none=True),
            data_period_start=params.start_date,
            data_period_end=params.end_date,
            notes=["Missing performance scores are excluded from performance averages."],
            aggregation_definitions={metric_id: get_metric(metric_id).description},
        )
