"""Generate distinct candidates only from the selected registered strategy."""

from app.decision.enums import ActionCategory
from app.schemas.decision_option import CandidateDecisionOption


class OptionGenerator:
    def __init__(self, decision_registry, settings) -> None:
        self.decision_registry = decision_registry
        self.settings = settings

    def generate(self, request, decision_type, evidence) -> list[CandidateDecisionOption]:
        definition = self.decision_registry.get(decision_type)
        maximum = min(request.constraints.maximum_actions or self.settings.decision_max_options, self.settings.decision_max_options)
        has_operational_condition = any(item.source_type == "database" and item.supporting_values.get("has_data") for item in evidence)
        templates = list(definition.action_templates)
        if has_operational_condition:
            templates.sort(key=lambda item: item.category == ActionCategory.CONTINUE_MONITORING)
        else:
            templates.sort(key=lambda item: item.category != ActionCategory.CONTINUE_MONITORING)
        selected = templates[:maximum]
        if len(selected) < 2:
            selected = templates[:2]
        evidence_ids = [item.evidence_id for item in evidence if item.source_type != "model"]
        options = []
        seen = set()
        for index, template in enumerate(selected, start=1):
            if template.category in seen:
                continue
            seen.add(template.category)
            assumptions = [
                "Resource availability has not been assumed and must be confirmed by an authorized manager.",
                "Configured thresholds are operational rules unless current official guidance confirms them.",
            ]
            options.append(
                CandidateDecisionOption(
                    option_id=f"O{index}",
                    action_category=template.category,
                    title=template.title,
                    action=template.action,
                    supporting_evidence_ids=evidence_ids,
                    assumptions=assumptions,
                    operational_requirements=list(template.operational_requirements),
                    expected_impact=list(template.expected_impact),
                    possible_risks=["The action may require resources whose current availability is not established by the evidence."],
                )
            )
        return options
