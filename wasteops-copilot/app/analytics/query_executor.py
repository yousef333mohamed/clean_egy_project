"""Read-only bounded execution for internally constructed SQLAlchemy statements."""

import asyncio
import time
from typing import Any

from sqlalchemy import Select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.utils.numeric_formatting import json_safe

logger = get_logger(__name__)


class AnalyticsDatabaseError(RuntimeError):
    """Safe database failure without raw driver details."""


class AnalyticsQueryTimeout(AnalyticsDatabaseError):
    """The configured analytics deadline was exceeded."""


class QueryExecutor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def execute(self, session: AsyncSession, statement: Select[Any], *, tool_name: str, limit: int) -> list[dict[str, Any]]:
        safe_limit = min(limit, self.settings.analytics_max_limit)
        started = time.perf_counter()
        try:
            bind = session.get_bind()
            if bind and bind.dialect.name == "postgresql":
                if not session.info.get("analytics_read_only_applied"):
                    await session.execute(text("SET TRANSACTION READ ONLY"))
                    session.info["analytics_read_only_applied"] = True
                await session.execute(
                    text("SELECT set_config('statement_timeout', :timeout, true)"),
                    {"timeout": f"{self.settings.analytics_query_timeout_seconds * 1000}ms"},
                )
            async with asyncio.timeout(self.settings.analytics_query_timeout_seconds + 1):
                result = await session.execute(statement.limit(safe_limit))
            rows = [json_safe(dict(row)) for row in result.mappings().all()]
            logger.info("analytics_query_completed", tool_name=tool_name, row_count=len(rows), duration_seconds=time.perf_counter() - started)
            return rows
        except TimeoutError as exc:
            await session.rollback()
            logger.warning("analytics_query_failed", tool_name=tool_name, error_category="timeout")
            raise AnalyticsQueryTimeout("Analytics query timed out") from exc
        except SQLAlchemyError as exc:
            await session.rollback()
            logger.warning("analytics_query_failed", tool_name=tool_name, error_category=type(exc).__name__)
            raise AnalyticsDatabaseError("Operational database unavailable") from exc
