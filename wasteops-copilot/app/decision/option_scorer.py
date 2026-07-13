"""Transparent deterministic scoring of registered decision options."""

from app.decision.enums import ActionCategory, DecisionEvidenceType, DecisionPriority
from app.schemas.decision_option import OptionScoreBreakdown, ScoredDecisionOption


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


class OptionScorer:
    """Weighted score; confidence and candidate wording never affect this formula."""

    def __init__(self, settings) -> None:
        self.settings = settings

    def score(self, options, evidence, constraints) -> list[ScoredDecisionOption]:
        affected = self._affected_count(evidence)
        urgent = self._urgency_signal(evidence)
        policy = self._policy_alignment(evidence)
        scored = []
        for option in options:
            service_impact = _bounded(affected / 10)
            if option.action_category in {ActionCategory.PRIORITIZE_COLLECTION_REVIEW, ActionCategory.COMBINED_OPERATIONAL_REVIEW} and urgent >= 0.7:
                service_impact = max(service_impact, 0.8)
            urgency = urgent if option.action_category != ActionCategory.CONTINUE_MONITORING else _bounded(1 - urgent)
            risk_control = self._risk_control(option.action_category, constraints)
            feasibility = self._feasibility(option.action_category)
            policy_alignment = policy
            breakdown = OptionScoreBreakdown(
                service_impact=service_impact,
                urgency=urgency,
                risk_control=risk_control,
                feasibility=feasibility,
                policy_alignment=policy_alignment,
            )
            final = (
                breakdown.service_impact * self.settings.decision_service_impact_weight
                + breakdown.urgency * self.settings.decision_urgency_weight
                + breakdown.risk_control * self.settings.decision_risk_weight
                + breakdown.feasibility * self.settings.decision_feasibility_weight
                + breakdown.policy_alignment * self.settings.decision_policy_alignment_weight
            )
            priority = DecisionPriority.HIGH if final >= 0.7 else DecisionPriority.MEDIUM if final >= 0.4 else DecisionPriority.LOW
            scored.append(ScoredDecisionOption(**option.model_dump(), score=round(final, 6), priority=priority, score_breakdown=breakdown))
        return sorted(scored, key=lambda item: (-item.score, item.option_id))

    @staticmethod
    def _affected_count(evidence) -> float:
        counts = []
        for item in evidence:
            if item.source_type != DecisionEvidenceType.DATABASE or not item.supporting_values.get("has_data"):
                continue
            numeric = [float(value) for key, value in item.supporting_values.items() if key.endswith("_count") or key in {"result_row_count", "trip_count"}]
            if numeric:
                counts.append(max(numeric))
        return max(counts, default=0.0)

    @staticmethod
    def _urgency_signal(evidence) -> float:
        signal = 0.0
        for item in evidence:
            text = f"{item.category} {item.description}".casefold()
            if item.supporting_values.get("has_data"):
                if any(term in text for term in ("critical", "fault", "emergency", "anomal")):
                    signal = max(signal, 0.9)
                elif any(term in text for term in ("low-battery", "battery", "missed")):
                    signal = max(signal, 0.7)
                else:
                    signal = max(signal, 0.4)
        return signal

    @staticmethod
    def _risk_control(category: ActionCategory, constraints) -> float:
        values = {
            ActionCategory.REQUEST_INSPECTION: 0.85,
            ActionCategory.PRIORITIZE_COLLECTION_REVIEW: 0.85,
            ActionCategory.COMBINED_OPERATIONAL_REVIEW: 0.8,
            ActionCategory.ESCALATE_FOR_MANAGER_REVIEW: 0.8,
            ActionCategory.REQUEST_BATTERY_REPLACEMENT: 0.75,
            ActionCategory.VALIDATE_CONNECTIVITY: 0.7,
            ActionCategory.CONTINUE_MONITORING: 0.3,
        }
        value = values.get(category, 0.65)
        if constraints.prioritize_safety and category in {ActionCategory.REQUEST_INSPECTION, ActionCategory.ESCALATE_FOR_MANAGER_REVIEW}:
            value = max(value, 0.9)
        if constraints.prioritize_service_continuity and category in {ActionCategory.PRIORITIZE_COLLECTION_REVIEW, ActionCategory.COMBINED_OPERATIONAL_REVIEW}:
            value = max(value, 0.9)
        return value

    @staticmethod
    def _feasibility(category: ActionCategory) -> float:
        if category in {
            ActionCategory.CONTINUE_MONITORING,
            ActionCategory.REVIEW_SERVICE_RECORDS,
            ActionCategory.REVIEW_FUEL_RECORDS,
            ActionCategory.REVIEW_LOAD_AND_DURATION,
            ActionCategory.REVIEW_ATTENDANCE_COVERAGE,
            ActionCategory.REVIEW_WORKLOAD_DISTRIBUTION,
            ActionCategory.REVIEW_OVERTIME,
            ActionCategory.VALIDATE_CONNECTIVITY,
        }:
            return 0.9
        if category in {ActionCategory.REQUEST_INSPECTION, ActionCategory.ESCALATE_FOR_MANAGER_REVIEW}:
            return 0.7
        if category == ActionCategory.REQUEST_BATTERY_REPLACEMENT:
            return 0.6
        if category == ActionCategory.COMBINED_OPERATIONAL_REVIEW:
            return 0.55
        if category == ActionCategory.REVIEW_OPERATIONAL_CAPACITY:
            return 0.4
        return 0.7

    def _policy_alignment(self, evidence) -> float:
        documents = [item for item in evidence if item.source_type == DecisionEvidenceType.DOCUMENT]
        if not documents:
            return 0.0 if self.settings.decision_require_document_guidance else 0.5
        scores = []
        for item in documents:
            if item.is_synthetic:
                scores.append(0.25)
            elif item.authority_level == "official":
                scores.append(1.0 if item.recency == "current" else 0.4)
            elif item.authority_level == "unknown":
                scores.append(0.5)
            else:
                scores.append(0.7)
        return max(scores)
