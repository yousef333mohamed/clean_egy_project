"""Attach situation-specific qualitative risks without probability claims."""

from app.decision.enums import ActionCategory, DecisionEvidenceType, RiskCategory, RiskLikelihood, RiskSeverity
from app.schemas.decision_option import DecisionRisk


class RiskAnalyzer:
    def analyze(self, option, evidence) -> list[DecisionRisk]:
        risks: list[DecisionRisk] = []
        evidence_ids = option.supporting_evidence_ids
        has_urgent = any(
            item.source_type == DecisionEvidenceType.DATABASE
            and item.supporting_values.get("has_data")
            and any(term in f"{item.category} {item.description}".casefold() for term in ("critical", "fault", "missed", "anomal", "emergency"))
            for item in evidence
        )
        quality_ids = [item.evidence_id for item in evidence if item.completeness_notes]
        weak_policy = [
            item.evidence_id
            for item in evidence
            if item.source_type == DecisionEvidenceType.DOCUMENT and (item.is_synthetic or item.authority_level == "unknown")
        ]
        safety_ids = [item.evidence_id for item in evidence if "safety" in f"{item.description} {' '.join(item.completeness_notes)}".casefold()]
        if option.operational_requirements:
            risks.append(
                self._risk(
                    "RESOURCE",
                    RiskCategory.RESOURCE,
                    "Required operational resources or availability are not confirmed by the evidence.",
                    RiskSeverity.MEDIUM,
                    evidence_ids,
                    "An authorized manager should confirm resources before execution.",
                )
            )
        if quality_ids:
            risks.append(
                self._risk(
                    "DATA",
                    RiskCategory.DATA_QUALITY,
                    "Missing or incomplete source values may affect prioritization.",
                    RiskSeverity.MEDIUM,
                    quality_ids,
                    "Verify incomplete records and latest timestamps before approval.",
                )
            )
        if weak_policy:
            risks.append(
                self._risk(
                    "POLICY",
                    RiskCategory.POLICY_AUTHORITY,
                    "Available document guidance is synthetic or has uncertain authority.",
                    RiskSeverity.HIGH,
                    weak_policy,
                    "Confirm a current official procedure before treating guidance as policy.",
                )
            )
        if safety_ids:
            risks.append(
                self._risk(
                    "SAFETY",
                    RiskCategory.SAFETY,
                    "The supplied evidence identifies a safety-related condition requiring authorized review.",
                    RiskSeverity.HIGH,
                    safety_ids,
                    "Follow current official safety guidance and obtain authorized approval.",
                )
            )
        if option.action_category == ActionCategory.CONTINUE_MONITORING and has_urgent:
            risks.append(
                self._risk(
                    "NO_ACTION",
                    RiskCategory.NO_ACTION,
                    "Monitoring alone may leave a supported urgent operational condition unresolved.",
                    RiskSeverity.HIGH,
                    evidence_ids,
                    "Set an explicit review deadline and escalation trigger.",
                )
            )
        elif has_urgent:
            risks.append(
                self._risk(
                    "NO_ACTION",
                    RiskCategory.NO_ACTION,
                    "Taking no action may leave the supported operational condition unresolved.",
                    RiskSeverity.MEDIUM,
                    evidence_ids,
                    "Complete the recommended manager review and define a follow-up deadline.",
                )
            )
        if option.action_category in {ActionCategory.PRIORITIZE_COLLECTION_REVIEW, ActionCategory.COMBINED_OPERATIONAL_REVIEW}:
            risks.append(
                self._risk(
                    "CONTINUITY",
                    RiskCategory.SERVICE_CONTINUITY,
                    "Delayed review may prolong a supported collection-service condition.",
                    RiskSeverity.MEDIUM,
                    evidence_ids,
                    "Complete manager review promptly while confirming capacity.",
                )
            )
        elif option.action_category in {ActionCategory.REQUEST_INSPECTION, ActionCategory.REQUEST_BATTERY_REPLACEMENT, ActionCategory.VALIDATE_CONNECTIVITY}:
            risks.append(
                self._risk(
                    "OPERATIONAL",
                    RiskCategory.OPERATIONAL,
                    "Unverified telemetry or equipment condition may make the initial diagnosis incomplete.",
                    RiskSeverity.MEDIUM,
                    evidence_ids,
                    "Validate the latest reading and inspection findings before further action.",
                )
            )
        return risks

    @staticmethod
    def _risk(identifier, category, description, severity, evidence_ids, mitigation) -> DecisionRisk:
        return DecisionRisk(
            risk_id=f"K-{identifier}",
            category=category,
            description=description,
            severity=severity,
            likelihood=RiskLikelihood.POSSIBLE,
            supporting_evidence_ids=list(dict.fromkeys(evidence_ids)),
            mitigation=mitigation,
        )
