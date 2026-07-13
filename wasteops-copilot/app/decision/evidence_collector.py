"""Collect and namespace database, document, rule, and future-model evidence."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from numbers import Number

from app.decision.enums import DecisionEvidenceType, DecisionType
from app.schemas.decision_evidence import DecisionEvidence
from app.schemas.retrieval import RetrievalRequest
from app.integrations.data_science.errors import DataScienceError
from app.integrations.data_science.interfaces import DisabledDataScienceProvider

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
    def __init__(self, analytics_service, retrieval_service, context_builder, session, settings, *, data_science_provider=None) -> None:
        self.analytics_service = analytics_service
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.session = session
        self.settings = settings
        self.data_science_provider = data_science_provider or DisabledDataScienceProvider()

    async def collect(self, request, plan, *, request_id: str = "unassigned") -> CollectedDecisionEvidence:
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
        if plan.requires_data_science:
            await self._add_model_evidence(request, plan, collected, request_id)
        self._add_rules(plan.decision_type, collected)
        collected.warnings = list(dict.fromkeys(collected.warnings))
        return collected

    async def _add_model_evidence(self, request, plan, collected: CollectedDecisionEvidence, request_id: str) -> None:
        horizon = next((value for value in (6, 12, 24) if str(value) in request.question), 24)
        bin_ids = list(dict.fromkeys([*request.scope.bin_ids, *self._planned_ids(plan, "bin_id")]))
        truck_ids = list(dict.fromkeys([*request.scope.truck_ids, *self._planned_ids(plan, "truck_id")]))
        region = request.scope.region or next((str(call.parameters["region"]) for call in plan.analytics_calls if call.parameters.get("region")), None)
        predictions = []
        try:
            if plan.decision_type == DecisionType.BIN_ATTENTION_PRIORITY and bin_ids:
                predictions.extend(await self.data_science_provider.predict_overflow(bin_ids, horizon, request_id=request_id))
                predictions.extend(await self.data_science_provider.calculate_priority(bin_ids, horizon, request_id=request_id))
            elif plan.decision_type == DecisionType.TRUCK_PERFORMANCE_RESPONSE and truck_ids:
                predictions.extend(await self.data_science_provider.detect_anomalies(truck_ids, request_id=request_id))
            elif plan.decision_type == DecisionType.MISSED_COLLECTION_RESPONSE and region:
                predictions.extend(await self.data_science_provider.predict_missed_collections(region, horizon, request_id=request_id))
            elif plan.decision_type == DecisionType.WORKFORCE_OPERATIONAL_RESPONSE and region:
                forecast_date = request.scope.end_date or date.today() + timedelta(days=1)
                predictions.extend(await self.data_science_provider.forecast_workforce_requirement(region, "Morning", forecast_date, request_id=request_id))
        except DataScienceError:
            collected.warnings.append("Predictive models are unavailable; no model evidence was returned and no mock prediction was substituted.")
            return
        if not predictions:
            collected.warnings.append("Predictive model context is unavailable for the requested assets or scope.")
            return
        for index, prediction in enumerate(predictions, start=1):
            values, description, factors = self._model_values(prediction)
            warnings = list(getattr(prediction, "warnings", []))
            version = str(prediction.model_version)
            production_approved = version not in {"unregistered", "synthetic-test"} and not any("baseline used" in item.casefold() for item in warnings)
            values.update(
                {
                    "model_name": prediction.model_name,
                    "model_version": version,
                    "prediction_timestamp": prediction.prediction_timestamp.isoformat(),
                    "feature_timestamp": prediction.feature_timestamp.isoformat(),
                    "prediction_horizon": values.get("prediction_horizon"),
                    "warnings": warnings,
                    "explanation_factors": factors,
                    "production_approved": production_approved,
                    "feature_fresh": not any("stale" in item.casefold() for item in warnings),
                    "drift_status": "unknown",
                    "has_data": True,
                }
            )
            collected.evidence.append(
                DecisionEvidence(
                    evidence_id=f"M{index}",
                    source_type=DecisionEvidenceType.MODEL,
                    category="model_prediction",
                    description=description,
                    data_period_start=prediction.feature_timestamp.isoformat(),
                    data_period_end=prediction.prediction_timestamp.isoformat(),
                    authority_level="model",
                    recency="current" if values["feature_fresh"] else "stale",
                    completeness_notes=[*warnings, "Feature contributions are associations, not causes; model evidence is not policy."],
                    supporting_values=values,
                    is_synthetic=getattr(prediction, "is_synthetic", False),
                )
            )
            collected.warnings.extend(warnings)

    @staticmethod
    def _planned_ids(plan, field: str) -> list[str]:
        return [str(call.parameters[field]) for call in plan.analytics_calls if call.parameters.get(field)]

    @staticmethod
    def _model_values(prediction) -> tuple[dict[str, object], str, list[dict[str, object]]]:
        factors = [item.model_dump(mode="json") for item in getattr(prediction, "top_factors", getattr(prediction, "model_factors", []))]
        if hasattr(prediction, "score"):
            return (
                {"entity_id": prediction.entity_id, "prediction_value": prediction.score, "threshold": None, "prediction_horizon": None},
                f"Synthetic test model score for {prediction.entity_id}",
                factors,
            )
        if hasattr(prediction, "overflow_probability") and hasattr(prediction, "decision_threshold"):
            return (
                {
                    "entity_id": prediction.bin_id,
                    "prediction_value": prediction.overflow_probability,
                    "threshold": prediction.decision_threshold,
                    "prediction_horizon": prediction.horizon_hours,
                },
                f"Bin overflow probability for {prediction.bin_id}",
                factors,
            )
        if hasattr(prediction, "priority_score"):
            return (
                {
                    "entity_id": prediction.bin_id,
                    "prediction_value": prediction.priority_score,
                    "threshold": None,
                    "prediction_horizon": getattr(prediction, "horizon_hours", 24),
                    "score_components": prediction.score_components,
                },
                f"Collection priority score for {prediction.bin_id}",
                factors,
            )
        if hasattr(prediction, "anomaly_score"):
            return (
                {
                    "entity_id": prediction.truck_id,
                    "prediction_value": prediction.anomaly_score,
                    "threshold": None,
                    "prediction_horizon": None,
                    "triggered_rules": prediction.triggered_rules,
                },
                f"ML-detected truck anomaly for {prediction.truck_id}",
                factors,
            )
        if hasattr(prediction, "missed_collection_probability"):
            return (
                {
                    "entity_id": prediction.scope_id,
                    "prediction_value": prediction.missed_collection_probability,
                    "threshold": None,
                    "prediction_horizon": prediction.horizon_hours,
                },
                f"Missed-collection probability for {prediction.scope_id}",
                factors,
            )
        return (
            {
                "entity_id": f"{prediction.region}:{prediction.shift}",
                "prediction_value": prediction.required_workers,
                "threshold": None,
                "prediction_horizon": prediction.forecast_date.isoformat(),
                "prediction_interval": prediction.prediction_interval,
            },
            f"Workforce requirement forecast for {prediction.region} {prediction.shift}",
            factors,
        )

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
