"""Rules-first safe router for structured, document, hybrid, and unsupported questions."""

import re
from datetime import datetime
from typing import Any

from app.analytics.date_range_parser import DateRangeError, DateRangeParser
from app.analytics.enums import AnalyticsDomain, AnalyticsRoute, SortDirection
from app.analytics.parameter_parser import AnalyticsParameterError, ParameterParser
from app.schemas.analytics import AnalyticsRouteDecision

PREDICTION_TERMS = ("will overflow", "tomorrow", "predict", "forecast", "يتنبأ", "غدا", "غدًا", "ستمتلئ")
PROHIBITED_TERMS = ("delete", "drop", "truncate", "update database", "insert into", "password", "credential", "api key", "احذف", "كلمة المرور")
DOCUMENT_TERMS = ("procedure", "policy", "sop", "guidance", "escalat", "according to", "إجراء", "اجراء", "سياسة", "تصعيد", "وفقاً", "وفقا")

METRIC_TERMS = {
    "missed_collection_count": ("missed collection", "missed collections", "عمليات الجمع الفائتة", "جمع فائت"),
    "complaint_count": ("complaint", "complaints", "شكوى", "شكاوى"),
    "emergency_request_count": ("emergency request", "emergency requests", "طلبات الطوارئ", "طلب طوارئ"),
    "illegal_dumping_count": ("illegal dumping", "dumping flags", "إلقاء غير قانوني", "القاء غير قانوني"),
    "average_service_completion_time_min": ("completion time", "service time", "وقت إكمال", "زمن الخدمة"),
    "total_fuel_consumed_l": ("fuel use", "fuel consumed", "most fuel", "استهلاك الوقود", "وقود"),
    "truck_utilization_pct": ("utilization", "capacity use", "استغلال", "الحمولة"),
    "average_trip_duration_min": ("trip duration", "مدة الرحلة"),
    "attendance_rate_pct": ("attendance rate", "attendance", "الحضور"),
    "average_performance_score": ("performance score", "performance", "درجة الأداء", "اداء العمال"),
    "average_temperature_c": ("temperature", "درجة الحرارة"),
    "total_rainfall_mm": ("rainfall", "rain", "الأمطار", "المطر"),
}
KNOWN_REGIONS = ("Greater Cairo", "Upper Egypt", "Coastal & Red Sea", "Canal & Sinai", "Delta")


class AnalyticsRouterService:
    def __init__(self, registry, settings, *, llm_service=None, date_parser=None) -> None:
        self.registry = registry
        self.settings = settings
        self.llm_service = llm_service
        self.date_parser = date_parser or DateRangeParser(settings)
        self.parameter_parser = ParameterParser(registry, settings)

    async def route(self, question: str) -> AnalyticsRouteDecision:
        normalized = " ".join(question.split())
        lowered = normalized.casefold()
        if any(term in lowered for term in PROHIBITED_TERMS):
            return self._unsupported("Database modification and credential requests are prohibited.")
        if any(term in lowered for term in PREDICTION_TERMS):
            return self._unsupported("The question requires a future prediction model.")
        requires_docs = any(term in lowered for term in DOCUMENT_TERMS)
        try:
            structured = self._deterministic(normalized)
        except DateRangeError as exc:
            return self._unsupported(str(exc))
        if structured:
            if requires_docs:
                analytical_cue = any(
                    term in lowered for term in ("which", "how many", "most ", "highest", "count", "rank", "number", "كم", "أي", "أكبر", "عدد")
                )
                if not analytical_cue:
                    return AnalyticsRouteDecision(route=AnalyticsRoute.DOCUMENT_KNOWLEDGE, requires_document_retrieval=True, document_query=normalized)
                return structured.model_copy(
                    update={"route": AnalyticsRoute.HYBRID_ANALYSIS, "requires_document_retrieval": True, "document_query": normalized}
                )
            return structured
        if requires_docs:
            return AnalyticsRouteDecision(route=AnalyticsRoute.DOCUMENT_KNOWLEDGE, requires_document_retrieval=True, document_query=normalized)
        if self.llm_service:
            try:
                raw = await self.llm_service.route_analytics(question=normalized, tool_catalog=self.registry.catalog())
                return self._validate_llm(raw, normalized)
            except Exception:
                pass
        return self._unsupported("No approved analytics tool could safely answer this question.")

    def _deterministic(self, question: str) -> AnalyticsRouteDecision | None:
        lowered = question.casefold()
        params: dict[str, Any] = {}
        self._add_date(question, params)
        self._add_identifiers(question, params)
        for region in KNOWN_REGIONS:
            if region.casefold() in lowered:
                params["region"] = region
                break
        if "latest available data" in lowered or "أحدث بيانات متاحة" in lowered:
            params["latest_available"] = True
        metric = next((metric_id for metric_id, terms in METRIC_TERMS.items() if any(term in lowered for term in terms)), None)
        ranking = any(term in lowered for term in ("which region", "highest", "most ", "rank", "أكبر", "اكثر", "أكثر", "رتب"))
        if any(term in lowered for term in ("overview", "operational overview", "ملخص تشغيلي", "نظرة عامة")):
            return self._decision(AnalyticsDomain.OVERVIEW, "get_operational_overview", params)
        bin_attention = "bin" in lowered and any(
            term in lowered
            for term in ("which bins", "bins need attention", "bins should receive", "bin attention")
        )
        if bin_attention or any(term in lowered for term in ("critical bin", "critical bins", "fill >=", "ممتلئة", "حرجة")):
            return self._decision(AnalyticsDomain.BINS, "list_critical_bins", params)
        if any(term in lowered for term in ("low battery", "battery bins", "بطارية منخفضة", "البطارية")):
            return self._decision(AnalyticsDomain.BINS, "list_low_battery_bins", params)
        if any(term in lowered for term in ("sensor fault", "faulty sensor", "عطل المستشعر", "أعطال الحساس")):
            return self._decision(AnalyticsDomain.BINS, "list_sensor_fault_bins", params)
        if any(term in lowered for term in ("bin status", "fill level", "bin reading", "حالة الحاويات", "مستوى الامتلاء")):
            return self._decision(AnalyticsDomain.BINS, "get_bin_status_summary", params)
        if any(term in lowered for term in ("normal average", "anomal", "above 100%", "zero fuel", "أعلى من المتوسط", "شذوذ")) and any(
            term in lowered for term in ("truck", "fuel", "trip", "شاحن")
        ):
            return self._decision(AnalyticsDomain.TRUCKS, "detect_truck_rule_anomalies", params)
        if metric in {"total_fuel_consumed_l", "truck_utilization_pct", "average_trip_duration_min"} or any(
            term in lowered for term in ("truck", "trucks", "trip", "شاحن", "رحلة")
        ):
            if ranking:
                params["metric"] = metric or "total_fuel_consumed_l"
                return self._decision(AnalyticsDomain.TRUCKS, "rank_trucks_by_metric", params)
            return self._decision(AnalyticsDomain.TRUCKS, "get_truck_performance_summary", params)
        if metric in {"attendance_rate_pct", "average_performance_score"} or any(term in lowered for term in ("workforce", "worker", "shift", "عمال", "وردية")):
            if ranking:
                params.update({"metric": metric or "attendance_rate_pct", "group_by": "region"})
                return self._decision(AnalyticsDomain.WORKFORCE, "rank_workforce_groups", params)
            return self._decision(AnalyticsDomain.WORKFORCE, "get_workforce_summary", params)
        if metric in {"average_temperature_c", "total_rainfall_mm"} or any(
            term in lowered for term in ("environment", "traffic level", "holiday", "festival", "weather", "بيئة", "طقس")
        ):
            return self._decision(AnalyticsDomain.ENVIRONMENT, "get_environmental_summary", params)
        if metric in {"missed_collection_count", "complaint_count", "emergency_request_count", "illegal_dumping_count", "average_service_completion_time_min"}:
            if ranking:
                params.update({"metric": metric, "sort_direction": SortDirection.DESC, "limit": 5})
                return self._decision(AnalyticsDomain.OPERATIONS, "rank_regions_by_operations_metric", params)
            return self._decision(AnalyticsDomain.OPERATIONS, "get_operations_summary", params)
        return None

    def _add_date(self, question: str, params: dict[str, Any]) -> None:
        patterns = [
            r"from\s+\d{4}-\d{2}-\d{2}\s+to\s+\d{4}-\d{2}-\d{2}",
            r"(?:last\s+\d+\s+days|today|yesterday|this week|last week|this month|last month)",
            r"(?:(?:آخر|اخر)\s+\d+\s+(?:يوم|يوما|أيام))",
            r"(?:يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)\s+\d{4}",
            r"(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}",
            r"(?:january|february|march|april|may|june|july|august|september|october|november|december)",
        ]
        match = next((m for pattern in patterns if (m := re.search(pattern, question, re.IGNORECASE))), None)
        if match:
            parsed = self.date_parser.parse(match.group(0))
            params.update({"start_date": parsed.start_date, "end_date": parsed.end_date})

    @staticmethod
    def _add_identifiers(question: str, params: dict[str, Any]) -> None:
        for key, pattern in {"bin_id": r"\bBIN-[A-Z0-9-]+\b", "truck_id": r"\bTRUCK-[A-Z0-9-]+\b", "worker_id": r"\bWORKER-[A-Z0-9-]+\b"}.items():
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                params[key] = match.group(0)

    def _decision(self, domain, tool_name, params):
        if domain == AnalyticsDomain.BINS and ("start_date" in params or "end_date" in params):
            start_date = params.pop("start_date", None)
            end_date = params.pop("end_date", None)
            timezone = self.date_parser.timezone
            if start_date:
                params["start_timestamp"] = datetime.combine(start_date, datetime.min.time(), timezone)
            if end_date:
                params["end_timestamp"] = datetime.combine(end_date, datetime.max.time(), timezone)
        try:
            validated = self.parameter_parser.parse(tool_name, params)
        except AnalyticsParameterError:
            return self._unsupported("The extracted parameters are invalid for the selected tool.")
        return AnalyticsRouteDecision(route=AnalyticsRoute.STRUCTURED_DATA, domain=domain, tool_name=tool_name, parameters=validated)

    def _validate_llm(self, raw: dict[str, Any], question: str) -> AnalyticsRouteDecision:
        try:
            decision = AnalyticsRouteDecision.model_validate(raw)
            if decision.route in {AnalyticsRoute.STRUCTURED_DATA, AnalyticsRoute.HYBRID_ANALYSIS}:
                if not decision.tool_name:
                    raise ValueError("missing tool")
                tool = self.registry.get(decision.tool_name)
                params = self.parameter_parser.parse(tool.name, decision.parameters)
                decision = decision.model_copy(update={"domain": tool.domain, "parameters": params})
            if decision.route in {AnalyticsRoute.DOCUMENT_KNOWLEDGE, AnalyticsRoute.HYBRID_ANALYSIS}:
                decision = decision.model_copy(update={"requires_document_retrieval": True, "document_query": decision.document_query or question})
            return decision
        except Exception:
            return self._unsupported("The model returned an unknown tool or invalid parameters.")

    @staticmethod
    def _unsupported(reason: str) -> AnalyticsRouteDecision:
        return AnalyticsRouteDecision(route=AnalyticsRoute.UNSUPPORTED, unsupported_reason=reason)
