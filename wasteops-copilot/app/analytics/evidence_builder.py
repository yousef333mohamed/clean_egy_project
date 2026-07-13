"""Create stable, lossless D-prefixed operational evidence."""

from datetime import UTC, datetime

from app.schemas.analytics_tools import AnalyticsToolResult
from app.schemas.operational_evidence import DataPeriod, OperationalEvidence
from app.utils.numeric_formatting import json_safe


class EvidenceBuilder:
    def build(self, results: list[AnalyticsToolResult]) -> list[OperationalEvidence]:
        evidence = []
        for index, result in enumerate(results, start=1):
            evidence.append(
                OperationalEvidence(
                    evidence_id=f"D{index}",
                    tool_name=result.tool_name,
                    metric=result.metric,
                    description=result.description,
                    filters=json_safe(result.filters),
                    columns=result.columns,
                    rows=json_safe(result.rows),
                    record_count=len(result.rows),
                    data_period=DataPeriod(start=json_safe(result.data_period_start), end=json_safe(result.data_period_end)),
                    generated_at=datetime.now(UTC),
                    notes=result.notes,
                    aggregation_definitions=result.aggregation_definitions,
                )
            )
        return evidence
