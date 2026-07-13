"""Deterministic RAG evaluator composition."""

import re

from app.evaluation.evaluators import CitationEvaluator, ConceptCoverageEvaluator, LanguageEvaluator, SafetyEvaluator
from app.evaluation.retrieval_evaluator import RetrievalEvaluator


class RAGEvaluator:
    name = "rag"
    evaluators = (RetrievalEvaluator(), CitationEvaluator(), ConceptCoverageEvaluator(), LanguageEvaluator(), SafetyEvaluator())

    async def evaluate(self, case, actual):
        results = [await evaluator.evaluate(case, actual) for evaluator in self.evaluators]
        evidence = case.expected.get("evidence_text", "")
        numeric_claims = re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", actual.answer)
        identifiers = re.findall(r"\b[A-Z]{2,}-\d+\b", actual.answer)
        grounded = all(value in evidence for value in numeric_claims + identifiers) if evidence else all(result.passed for result in results[:2])
        warning_text = " ".join(actual.warnings).casefold()
        synthetic_ok = not case.expected.get("synthetic_warning", False) or "synthetic" in warning_text
        unknown_ok = not case.expected.get("unknown_authority_warning", False) or "unknown authority" in warning_text
        expected_identifiers = case.expected.get("identifiers", [])
        identifiers_ok = all(identifier in actual.answer for identifier in expected_identifiers)
        metrics = {key: value for result in results for key, value in result.metrics.items()}
        metrics["groundedness"] = float(grounded)
        metrics.update(synthetic_warning=float(synthetic_ok), unknown_authority_warning=float(unknown_ok), identifier_preservation=float(identifiers_ok))
        reasons = [reason for result in results for reason in result.failure_reasons]
        if not grounded:
            reasons.append("Numeric claim or identifier is unsupported by evidence")
        if not synthetic_ok:
            reasons.append("Synthetic-document warning is missing")
        if not unknown_ok:
            reasons.append("Unknown-authority warning is missing")
        if not identifiers_ok:
            reasons.append("An operational identifier was changed or omitted")
        from app.schemas.evaluation import EvaluatorResult

        deterministic_checks = (grounded, synthetic_ok, unknown_ok, identifiers_ok)
        return EvaluatorResult(
            passed=all(result.passed for result in results) and all(deterministic_checks),
            score=(sum(result.score for result in results) + sum(deterministic_checks)) / (len(results) + len(deterministic_checks)),
            metrics=metrics,
            failure_reasons=reasons,
            warnings=[warning for result in results for warning in result.warnings],
            critical=any(result.critical for result in results),
        )
