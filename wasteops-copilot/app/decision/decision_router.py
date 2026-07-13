"""Rules-first classification of recommendation requests without execution."""

import re
from typing import Any

from app.analytics.tool_registry import UnknownAnalyticsTool
from app.decision.enums import DecisionType
from app.schemas.decision import DecisionRequest
from app.schemas.decision_context import DecisionRouteResult

PREDICTIVE = ("predict", "forecast", "will overflow", "tomorrow", "غدا", "غدًا", "ستمتلئ")
AUTONOMOUS = (
    "automatically dispatch",
    "dispatch automatically",
    "auto dispatch",
    "execute now",
    "delete ",
    "drop ",
    "update records",
    "ignore company policy",
    "ignore policy",
    "نفذ تلقائيا",
    "احذف",
)
OPTIMIZATION = ("optimize", "route optimization", "best route", "shortest route", "تحسين المسار", "أفضل مسار")
KNOWN_REGIONS = ("Greater Cairo", "Upper Egypt", "Coastal & Red Sea", "Canal & Sinai", "Delta")


class DecisionRouter:
    def __init__(self, decision_registry, analytics_registry, *, llm_service=None) -> None:
        self.decision_registry = decision_registry
        self.analytics_registry = analytics_registry
        self.llm_service = llm_service

    async def route(self, request: DecisionRequest) -> DecisionRouteResult:
        question = " ".join(request.question.split())
        lowered = question.casefold()
        scope = request.scope.model_dump(mode="json", exclude_none=True)
        self._extract(question, scope)
        if any(term in lowered for term in AUTONOMOUS):
            return DecisionRouteResult(
                decision_type=DecisionType.UNSUPPORTED_AUTONOMOUS_ACTION,
                scope=scope,
                unsupported_reason="Operational execution, database modification, and safety bypass requests are prohibited.",
            )
        if any(term in lowered for term in OPTIMIZATION):
            return DecisionRouteResult(
                decision_type=DecisionType.UNSUPPORTED_OPTIMIZATION,
                scope=scope,
                requires_optimization=True,
                unsupported_reason="Route optimization is not implemented in this step.",
            )
        if any(term in lowered for term in PREDICTIVE):
            return DecisionRouteResult(
                decision_type=DecisionType.UNSUPPORTED_PREDICTIVE_DECISION,
                scope=scope,
                requires_data_science=True,
                unsupported_reason="The request requires a future Data Science prediction provider.",
            )
        decision_type = request.decision_type or self._deterministic_type(lowered, scope)
        if decision_type in {
            DecisionType.UNSUPPORTED_PREDICTIVE_DECISION,
            DecisionType.UNSUPPORTED_AUTONOMOUS_ACTION,
            DecisionType.UNSUPPORTED_OPTIMIZATION,
        }:
            return DecisionRouteResult(
                decision_type=decision_type,
                scope=scope,
                requires_data_science=decision_type == DecisionType.UNSUPPORTED_PREDICTIVE_DECISION,
                requires_optimization=decision_type == DecisionType.UNSUPPORTED_OPTIMIZATION,
                unsupported_reason="The explicitly selected decision type is unsupported in this step.",
            )
        if decision_type:
            return self._registered(decision_type, scope)
        if self.llm_service:
            try:
                raw = await self.llm_service.route_decision(
                    question=question,
                    decision_types=[item.value for item in DecisionType],
                    tool_catalog=self.analytics_registry.catalog(),
                )
                return self._validate_llm(raw, scope)
            except Exception:
                pass
        return self._registered(DecisionType.GENERAL_OPERATIONAL_PRIORITY, scope)

    def _deterministic_type(self, lowered: str, scope: dict[str, Any]) -> DecisionType | None:
        if scope.get("bin_ids") or any(
            term in lowered
            for term in ("critical bin", "critical-fill", "which bins", "bin attention", "critical-fill bins", "fill data", "fill level", "حاويات", "الحاويات")
        ):
            return DecisionType.BIN_ATTENTION_PRIORITY
        if any(term in lowered for term in ("sensor", "battery", "maintenance", "connectivity", "مستشعر", "حساس", "بطارية", "صيانة")):
            return DecisionType.SENSOR_MAINTENANCE_RESPONSE
        if scope.get("truck_ids") or any(term in lowered for term in ("truck", "fuel", "trip duration", "شاحن", "وقود", "رحلة")):
            return DecisionType.TRUCK_PERFORMANCE_RESPONSE
        if any(term in lowered for term in ("missed collection", "missed collections", "collection missed", "جمع فائت", "الجمع الفائت")):
            return DecisionType.MISSED_COLLECTION_RESPONSE
        if any(term in lowered for term in ("workforce", "worker", "attendance", "absence", "overtime", "عامل", "عمال", "حضور", "غياب")):
            return DecisionType.WORKFORCE_OPERATIONAL_RESPONSE
        if scope.get("region") and any(term in lowered for term in ("complaint", "emergency", "regional", "region", "شكوى", "طوارئ", "منطقة")):
            return DecisionType.REGIONAL_OPERATIONAL_RESPONSE
        if any(term in lowered for term in ("prioritize", "priority", "best operational action", "latest available", "overview", "أفضل إجراء", "الأولوية")):
            return DecisionType.GENERAL_OPERATIONAL_PRIORITY
        return None

    def _registered(self, decision_type: DecisionType, scope: dict[str, Any]) -> DecisionRouteResult:
        definition = self.decision_registry.get(decision_type)
        for tool in (*definition.required_analytics_tools, *definition.optional_analytics_tools):
            self.analytics_registry.get(tool)
        return DecisionRouteResult(
            decision_type=decision_type,
            scope=scope,
            required_analytics_tools=list(definition.required_analytics_tools),
            required_document_queries=list(definition.document_queries),
        )

    def _validate_llm(self, raw: dict[str, Any], fallback_scope: dict[str, Any]) -> DecisionRouteResult:
        try:
            result = DecisionRouteResult.model_validate(raw)
            if result.decision_type == DecisionType.UNSUPPORTED_PREDICTIVE_DECISION:
                return result.model_copy(
                    update={"requires_data_science": True, "unsupported_reason": result.unsupported_reason or "Prediction provider required."}
                )
            if result.decision_type == DecisionType.UNSUPPORTED_OPTIMIZATION:
                return result.model_copy(
                    update={"requires_optimization": True, "unsupported_reason": result.unsupported_reason or "Optimization service required."}
                )
            if result.decision_type == DecisionType.UNSUPPORTED_AUTONOMOUS_ACTION:
                return result.model_copy(update={"unsupported_reason": result.unsupported_reason or "Autonomous execution is prohibited."})
            definition = self.decision_registry.get(result.decision_type)
            allowed = set(definition.required_analytics_tools) | set(definition.optional_analytics_tools)
            if not set(result.required_analytics_tools).issubset(allowed):
                raise UnknownAnalyticsTool("LLM selected a tool outside the strategy")
            for tool in result.required_analytics_tools:
                self.analytics_registry.get(tool)
            selected_optional = [tool for tool in result.required_analytics_tools if tool in definition.optional_analytics_tools]
            tools = [*definition.required_analytics_tools, *selected_optional]
            return result.model_copy(update={"scope": result.scope or fallback_scope, "required_analytics_tools": list(dict.fromkeys(tools))})
        except Exception:
            return DecisionRouteResult(
                decision_type=DecisionType.UNSUPPORTED_AUTONOMOUS_ACTION,
                scope=fallback_scope,
                unsupported_reason="The decision router returned an unknown tool or invalid plan.",
            )

    @staticmethod
    def _extract(question: str, scope: dict[str, Any]) -> None:
        mappings = {"bin_ids": r"\bBIN-[A-Z0-9-]+\b", "truck_ids": r"\b(?:TRK|TRUCK)-[A-Z0-9-]+\b", "worker_ids": r"\b(?:WRK|WORKER)-[A-Z0-9-]+\b"}
        for field, pattern in mappings.items():
            found = re.findall(pattern, question, re.IGNORECASE)
            if found:
                scope[field] = list(dict.fromkeys([*scope.get(field, []), *found]))
        for region in KNOWN_REGIONS:
            if region.casefold() in question.casefold():
                scope["region"] = region
                break
