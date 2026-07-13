"""Deterministic structured-analytics evaluator composition."""

from app.evaluation.evaluators import NumericPreservationEvaluator, RouteEvaluator, SafetyEvaluator, ToolSelectionEvaluator
from app.schemas.evaluation import EvaluatorResult


class AnalyticsEvaluator:
    name = "analytics"
    evaluators = (RouteEvaluator(), ToolSelectionEvaluator(), NumericPreservationEvaluator(), SafetyEvaluator())

    async def evaluate(self, case, actual):
        results = [await evaluator.evaluate(case, actual) for evaluator in self.evaluators]
        expected_domain = case.expected.get("domain")
        domain_ok = expected_domain is None or actual.domain == expected_domain
        expected_metrics = set(case.expected.get("metrics", []))
        metric_ok = expected_metrics.issubset(set(actual.metrics))
        filter_ok = all(actual.filters.get(key) == value for key, value in case.expected.get("filters", {}).items())
        date_ok = all(actual.date_range.get(key) == value for key, value in case.expected.get("date_range", {}).items())
        metrics = {key: value for result in results for key, value in result.metrics.items()}
        metrics.update(domain_accuracy=float(domain_ok), metric_accuracy=float(metric_ok), filter_accuracy=float(filter_ok), date_range_accuracy=float(date_ok))
        checks = all((domain_ok, metric_ok, filter_ok, date_ok)) and all(result.passed for result in results)
        reasons = [reason for result in results for reason in result.failure_reasons] + [f"Analytics check failed: {name}" for name, ok in (("domain", domain_ok), ("metric", metric_ok), ("filter", filter_ok), ("date_range", date_ok)) if not ok]
        return EvaluatorResult(passed=checks, score=sum(metrics.values()) / len(metrics), metrics=metrics, failure_reasons=reasons, critical=any(result.critical for result in results))
