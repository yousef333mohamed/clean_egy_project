"""Deterministic evidence-quality score; not a correctness probability."""

from app.decision.enums import ConfidenceLevel, DecisionEvidenceType
from app.schemas.confidence import ConfidenceComponents, DecisionConfidence


class ConfidenceCalculator:
    def __init__(self, settings) -> None:
        self.settings = settings

    def calculate(self, evidence, required_categories: list[str], *, explicitly_historical: bool = False) -> DecisionConfidence:
        found = {item.category for item in evidence if item.supporting_values.get("has_data", True)}
        coverage = len(found & set(required_categories)) / len(required_categories) if required_categories else 1.0
        quality = self._source_quality(evidence)
        completeness = self._completeness(evidence)
        agreement = self._agreement(evidence)
        recency = self._recency(evidence, explicitly_historical)
        components = ConfidenceComponents(
            retrieval_coverage=coverage,
            source_quality=quality,
            data_completeness=completeness,
            source_agreement=agreement,
            recency=recency,
        )
        score = (
            coverage * self.settings.confidence_retrieval_coverage_weight
            + quality * self.settings.confidence_source_quality_weight
            + completeness * self.settings.confidence_data_completeness_weight
            + agreement * self.settings.confidence_source_agreement_weight
            + recency * self.settings.confidence_recency_weight
        )
        level = ConfidenceLevel.LOW if score < 0.4 else ConfidenceLevel.MEDIUM if score < 0.7 else ConfidenceLevel.HIGH
        return DecisionConfidence(
            score=round(max(0.0, min(1.0, score)), 6),
            level=level,
            components=components,
            explanation="Evidence-quality score based on coverage, source authority, completeness, agreement, and recency; it is not a probability of correctness.",
        )

    @staticmethod
    def _source_quality(evidence) -> float:
        scores = []
        seen = set()
        for item in evidence:
            identity = (item.source_type, item.description)
            if identity in seen:
                continue
            seen.add(identity)
            if item.source_type == DecisionEvidenceType.DATABASE:
                scores.append(0.9)
            elif item.source_type == DecisionEvidenceType.RULE:
                scores.append(0.7)
            elif item.source_type == DecisionEvidenceType.MODEL:
                scores.append(0.0 if item.is_synthetic else 0.8)
            elif item.is_synthetic:
                scores.append(0.25)
            elif item.authority_level == "official":
                scores.append(1.0 if item.recency == "current" else 0.4)
            elif item.authority_level == "unknown":
                scores.append(0.5)
            else:
                scores.append(0.7)
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def _completeness(evidence) -> float:
        if not evidence:
            return 0.0
        penalties = 0.0
        for item in evidence:
            if not item.supporting_values.get("has_data", True):
                penalties += 1.0
            if item.completeness_notes:
                text = " ".join(item.completeness_notes).casefold()
                if any(term in text for term in ("missing", "excluded", "no valid", "unknown")):
                    penalties += 0.5
        return max(0.0, 1.0 - penalties / len(evidence))

    @staticmethod
    def _agreement(evidence) -> float:
        useful = [item for item in evidence if item.supporting_values.get("has_data", True)]
        if not useful:
            return 0.0
        categories = {item.category for item in useful}
        sources = {item.source_type for item in useful}
        conflicts = any("conflict" in " ".join(item.completeness_notes).casefold() for item in useful)
        if conflicts:
            return 0.25
        if len(categories) >= 2 and len(sources) >= 2:
            return 0.85
        if len(categories) >= 2:
            return 0.7
        return 0.5

    @staticmethod
    def _recency(evidence, explicitly_historical: bool) -> float:
        if not evidence:
            return 0.0
        if explicitly_historical:
            return 0.9
        scores = []
        for item in evidence:
            if item.recency in {"latest_available", "current", "current_configuration"}:
                scores.append(1.0)
            elif item.recency in {"requested_historical_period", "dated"}:
                scores.append(0.8)
            else:
                scores.append(0.5)
        return sum(scores) / len(scores)
