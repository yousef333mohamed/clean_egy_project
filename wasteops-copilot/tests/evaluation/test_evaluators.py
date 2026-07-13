"""Ranking, citation, numeric, and safety checks avoid exact wording."""

from app.evaluation.evaluators import CitationEvaluator, NumericPreservationEvaluator, SafetyEvaluator
from app.evaluation.retrieval_evaluator import RetrievalEvaluator
from app.schemas.evaluation import EvaluationActualResult, EvaluationCase


def case(**updates):
    values = {"case_id": "X-1", "category": "test", "question": "question"}
    values.update(updates)
    return EvaluationCase(**values)


def test_retrieval_metrics():
    metrics = RetrievalEvaluator.metrics(["A", "B"], ["X", "A", "Y", "B"])
    assert metrics["retrieval_recall_at_3"] == 0.5
    assert metrics["retrieval_recall_at_5"] == 1
    assert metrics["mean_reciprocal_rank"] == 0.5


async def test_citations_must_be_supplied():
    result = await CitationEvaluator().evaluate(
        case(expected_citation_types=["document"]), EvaluationActualResult(citations=["S1", "S9"], supplied_source_ids=["S1"])
    )
    assert not result.passed and result.metrics["citation_validity"] == 0.5


async def test_numbers_and_nulls_are_exact():
    result = await NumericPreservationEvaluator().evaluate(case(), EvaluationActualResult(expected_numeric_values=[12, None], numeric_values=[12, 0]))
    assert not result.passed and result.metrics["numeric_error_rate"] == 0.5


async def test_secret_or_write_is_critical():
    result = await SafetyEvaluator().evaluate(case(), EvaluationActualResult(answer="safe", exposed_secret=True, modified_database=True))
    assert result.critical and result.metrics["critical_failures"] == 2
