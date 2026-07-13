"""Collect and namespace database, document, rule, and future-model evidence."""

from dataclasses import dataclass, field
from datetime import date
from numbers import Number

from app.decision.enums import DecisionEvidenceType, DecisionType
from app.schemas.decision_evidence import DecisionEvidence
from app.schemas.retrieval import RetrievalRequest

TOOL_CATEGORIES = {
    "list_critical_bins": "latest_bin_status",
    "list_low_battery_bins": "latest_bin_status",
    "list_sensor_fault_bins": "latest_sensor_status",
    "get_bin_status_summary": "latest_bin_status",
    "get_operations_summary": "operations_outcomes",
    "rank_regions_by_operations_metric": "operations_outcomes",
    "get_truck_performance_summary": "truck_performance",
    "rank_trucks_by_metric": "truck_performance",
    "detect_truck_rule_anomalies": "rule_anomalies",
    "get_workforce_summary": "attendance_coverage",
    "rank_workforce_groups": "workload_evidence",
    "get_environmental_summary": "environment_context",
    "get_operational_overview": "operational_overview",
}


@dataclass
class CollectedDecisionEvidence:
    evidence: list[DecisionEvidence] = field(default_factory=list)
    database_evidence: list = field(default_factory=list)
    document_citations: list = field(default_factory=list)
    document_context: str = ""
    warnings: list[str] = field(default_factory=list)


class DecisionEvidenceCollector:
    def __init__(self, analytics_service, retrieval_service, context_builder, session, settings) -> None:
        self.analytics_service = analytics_service
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.session = session
        self.settings = settings

    async def collect(self, request, plan) -> CollectedDecisionEvidence:
        collected = CollectedDecisionEvidence()
        for index, call in enumerate(plan.analytics_calls, start=1):
            result = await self.analytics_service.execute(call.tool, call.parameters, self.session)
            result.evidence_id = f"D{index}"
            collected.database_evidence.append(result)
            completeness = self._quality_notes(result)
            has_data = self._has_data(result)
            values = self._supporting_values(result)
            values["has_data"] = has_data
            collected.evidence.append(
                DecisionEvidence(
                    evidence_id=result.evidence_id,
                    source_type=DecisionEvidenceType.DATABASE,
                    category=TOOL_CATEGORIES.get(call.tool, "database_evidence"),
                    description=result.description,
                    data_period_start=result.data_period.start,
                    data_period_end=result.data_period.end,
                    authority_level="database",
                    recency="latest_available" if request.scope.use_latest_available_data else "requested_historical_period",
                    completeness_notes=completeness,
                    supporting_values=values,
                )
            )
            collected.warnings.extend(result.notes)
            if not has_data:
                collected.warnings.append(f"No matching operational records were found for {call.tool}.")
            elif call.tool == "list_sensor_fault_bins":
                collected.warnings.append("Current sensor faults may make affected telemetry readings unreliable until inspection.")
        retrieved = []
        for query in plan.document_queries:
            response = await self.retrieval_service.search(
                RetrievalRequest(query=query.query, filters=query.filters, include_content=True, top_k=self.settings.retrieval_top_k)
            )
            collected.warnings.extend(response.warnings)
            retrieved.extend(response.evidence)
        unique = list({item.chunk_id: item for item in retrieved}.values())
        if unique:
            context = self.context_builder.build(unique, max_tokens=self.settings.retrieval_max_context_tokens)
            collected.document_context = context.context_text
            collected.document_citations = context.citations
            by_chunk = {item.chunk_id: item for item in unique}
            for citation in context.citations:
                source = by_chunk[citation.chunk_id]
                notes = []
                if source.is_synthetic:
                    notes.append("Synthetic demo document; not official policy.")
                    collected.warnings.append("The cited procedure is a synthetic demo document.")
                if source.authority_level == "unknown":
                    notes.append("Document authority is unknown.")
                    collected.warnings.append("A cited document has unknown authority.")
                collected.evidence.append(
                    DecisionEvidence(
                        evidence_id=citation.citation_id,
                        source_type=DecisionEvidenceType.DOCUMENT,
                        category=self._document_category(plan.decision_type, source.document_type),
                        description=f"{source.document_title}: {source.section_title or 'document excerpt'}",
                        data_period_start=source.effective_date.isoformat() if source.effective_date else None,
                        data_period_end=source.expiration_date.isoformat() if source.expiration_date else None,
                        authority_level=source.authority_level,
                        recency=self._document_recency(source, request),
                        completeness_notes=notes,
                        supporting_values={"document_type": source.document_type, "version": source.version},
                        is_synthetic=source.is_synthetic,
                    )
                )
            collected.warnings.extend(context.warnings)
        elif plan.document_queries:
            collected.warnings.append("No useful document guidance was retrieved.")
        self._add_rules(plan.decision_type, collected)
        collected.warnings = list(dict.fromkeys(collected.warnings))
        return collected

    @staticmethod
    def _has_data(evidence) -> bool:
        if not evidence.rows:
            return False
        row = evidence.rows[0]
        count_keys = [key for key in row if key in {"records_included", "trip_count", "attendance_record_count", "region_day_records_included"}]
        return not count_keys or any((row.get(key) or 0) > 0 for key in count_keys)

    @staticmethod
    def _quality_notes(evidence) -> list[str]:
        notes = list(evidence.notes)
        for row in evidence.rows:
            for key, value in row.items():
                if any(term in key for term in ("missing", "excluded", "without_valid")) and isinstance(value, Number) and value > 0:
                    notes.append(f"{key}: {value}")
        return list(dict.fromkeys(notes))

    @staticmethod
    def _supporting_values(evidence) -> dict[str, object]:
        values: dict[str, object] = {"result_row_count": len(evidence.rows)}
        for row in evidence.rows:
            for key, value in row.items():
                if isinstance(value, (Number, bool)) and value is not None:
                    if key.endswith("_count") or key in {"records_included", "trip_count", "attendance_rate_pct", "utilization_pct"}:
                        existing = values.get(key)
                        values[key] = value if existing is None else existing + value
        return values

    @staticmethod
    def _add_rules(decision_type: DecisionType, collected: CollectedDecisionEvidence) -> None:
        rules: list[tuple[str, str, dict[str, object]]] = []
        if decision_type in {DecisionType.BIN_ATTENTION_PRIORITY, DecisionType.SENSOR_MAINTENANCE_RESPONSE, DecisionType.GENERAL_OPERATIONAL_PRIORITY}:
            rules.extend(
                [
                    ("Configured critical-fill rule", "latest fill level >= 80%; not marked as official policy", {"threshold_pct": 80}),
                    ("Configured low-battery rule", "latest battery level < 20%; not marked as official policy", {"threshold_pct": 20}),
                    ("Current sensor-fault rule", "latest sensor status indicates Fault", {}),
                ]
            )
        if decision_type in {DecisionType.TRUCK_PERFORMANCE_RESPONSE, DecisionType.GENERAL_OPERATIONAL_PRIORITY}:
            rules.append(("Configured truck anomaly rules", "Transparent historical-average and invalid-value rules; not predictions", {}))
        start = 1
        for offset, (description, note, values) in enumerate(rules, start=start):
            collected.evidence.append(
                DecisionEvidence(
                    evidence_id=f"R{offset}",
                    source_type=DecisionEvidenceType.RULE,
                    category="configured_rules",
                    description=description,
                    authority_level="configured",
                    recency="current_configuration",
                    completeness_notes=[note],
                    supporting_values=values,
                )
            )
            collected.warnings.append(note)

    @staticmethod
    def _document_category(decision_type: DecisionType, document_type: str | None) -> str:
        if decision_type == DecisionType.MISSED_COLLECTION_RESPONSE:
            return "response_guidance"
        if decision_type == DecisionType.SENSOR_MAINTENANCE_RESPONSE:
            return "maintenance_guidance"
        if decision_type == DecisionType.TRUCK_PERFORMANCE_RESPONSE:
            return "inspection_guidance"
        return "document_guidance" if "procedure" not in (document_type or "").casefold() else "response_guidance"

    @staticmethod
    def _document_recency(source, request) -> str:
        reference = request.scope.end_date or date.today()
        if source.expiration_date and source.expiration_date < reference:
            return "expired"
        if source.effective_date and source.effective_date > reference:
            return "not_yet_effective"
        return "current"
