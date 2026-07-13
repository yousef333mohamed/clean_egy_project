"""Translate a validated decision route into minimal approved evidence calls."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.decision.enums import DecisionType
from app.schemas.decision import DecisionRequest
from app.schemas.decision_context import DecisionContextPlan, PlannedAnalyticsCall, PlannedDocumentQuery
from app.schemas.retrieval import RetrievalFilters


class DecisionContextPlanner:
    def __init__(self, decision_registry, analytics_registry, settings) -> None:
        self.decision_registry = decision_registry
        self.analytics_registry = analytics_registry
        self.settings = settings

    def plan(self, request: DecisionRequest, route) -> DecisionContextPlan:
        if route.unsupported_reason or route.requires_optimization:
            return DecisionContextPlan(
                decision_type=route.decision_type,
                analytics_calls=[],
                document_queries=[],
                required_evidence_categories=[],
                requires_data_science=route.requires_data_science,
                requires_optimization=route.requires_optimization,
                unsupported_reason=route.unsupported_reason,
            )
        definition = self.decision_registry.get(route.decision_type)
        if route.requires_data_science and self.settings.data_science_provider == "disabled":
            return DecisionContextPlan(
                decision_type=route.decision_type,
                analytics_calls=[],
                document_queries=[],
                required_evidence_categories="model_prediction".split(),
                requires_data_science=True,
            )
        extracted = {key: route.scope[key] for key in ("region", "governorate", "bin_ids", "truck_ids", "worker_ids") if route.scope.get(key)}
        effective_request = request.model_copy(update={"scope": request.scope.model_copy(update=extracted)})
        calls: list[PlannedAnalyticsCall] = []
        for tool_name in route.required_analytics_tools:
            tool = self.analytics_registry.get(tool_name)
            base = self._tool_defaults(tool_name, self._base_parameters(effective_request, tool.allowed_parameters))
            id_field = self._id_field(tool.allowed_parameters)
            identifiers = self._identifiers(effective_request, id_field)
            if identifiers:
                calls.extend(PlannedAnalyticsCall(tool=tool_name, parameters={**base, id_field: identifier}) for identifier in identifiers)
            else:
                calls.append(PlannedAnalyticsCall(tool=tool_name, parameters=base))
        filters = request.document_filters or RetrievalFilters(document_type=list(definition.recommended_document_types))
        document_queries = [PlannedDocumentQuery(query=query, filters=filters) for query in route.required_document_queries]
        missing: list[str] = []
        if (
            route.decision_type == DecisionType.TRUCK_PERFORMANCE_RESPONSE
            and not effective_request.scope.truck_ids
            and "truck" not in request.question.casefold()
        ):
            missing.append("Truck identifier or an explicit fleet-wide scope")
        if request.scope.start_date and not request.scope.end_date:
            missing.append("End date for the requested historical period")
        return DecisionContextPlan(
            decision_type=route.decision_type,
            analytics_calls=calls,
            document_queries=document_queries,
            required_evidence_categories=[*definition.required_evidence_categories, *(["model_prediction"] if route.requires_data_science else [])],
            missing_requirements=missing,
            requires_data_science=route.requires_data_science,
        )

    def _base_parameters(self, request: DecisionRequest, allowed: tuple[str, ...]) -> dict[str, object]:
        scope = request.scope
        parameters: dict[str, object] = {}
        for name in ("region", "governorate"):
            value = getattr(scope, name)
            if value and name in allowed:
                parameters[name] = value
        if "latest_available" in allowed and scope.use_latest_available_data and not scope.start_date and not scope.end_date:
            parameters["latest_available"] = True
        if "start_date" in allowed and scope.start_date:
            parameters["start_date"] = scope.start_date
        if "end_date" in allowed and scope.end_date:
            parameters["end_date"] = scope.end_date
        if "start_timestamp" in allowed and scope.start_date:
            parameters["start_timestamp"] = datetime.combine(scope.start_date, datetime.min.time(), ZoneInfo(self.settings.source_timezone))
        if "end_timestamp" in allowed and scope.end_date:
            parameters["end_timestamp"] = datetime.combine(scope.end_date, datetime.max.time(), ZoneInfo(self.settings.source_timezone))
        return parameters

    @staticmethod
    def _id_field(allowed: tuple[str, ...]) -> str | None:
        return next((field for field in ("bin_id", "truck_id", "worker_id") if field in allowed), None)

    @staticmethod
    def _identifiers(request: DecisionRequest, field: str | None) -> list[str]:
        return {"bin_id": request.scope.bin_ids, "truck_id": request.scope.truck_ids, "worker_id": request.scope.worker_ids}.get(field, [])

    @staticmethod
    def _tool_defaults(tool_name: str, parameters: dict[str, object]) -> dict[str, object]:
        defaults = {
            "rank_regions_by_operations_metric": {"metric": "missed_collection_count", "limit": 5},
            "rank_trucks_by_metric": {"metric": "total_fuel_consumed_l", "limit": 10},
            "rank_workforce_groups": {"metric": "attendance_rate_pct", "group_by": "region", "limit": 10},
        }
        return {**parameters, **defaults.get(tool_name, {})}
