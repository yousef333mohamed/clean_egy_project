"""Offline fake-provider regression execution."""

from pathlib import Path

from app.core.config import Settings
from app.evaluation.enums import EvaluationMode
from app.evaluation.regression_runner import RegressionRunner


def settings(**updates):
    values = {"database_url": "postgresql+asyncpg://x:x@db/x", "database_sync_url": "postgresql+psycopg://x:x@db/x"}
    values.update(updates)
    return Settings(**values)


async def test_rag_fake_dataset_runs_without_provider_or_database():
    path = Path("evaluation_datasets/rag/wasteops_rag_v1.json")
    result = await RegressionRunner(settings=settings(), write_report_files=False).run(path, mode=EvaluationMode.FAKE_PROVIDERS)
    assert len(result.results) == 3 and result.critical_failures == 0
    assert result.metrics["retrieval_recall_at_5"] == 1


async def test_live_mode_is_disabled():
    path = Path("evaluation_datasets/rag/wasteops_rag_v1.json")
    try:
        await RegressionRunner(settings=settings(), write_report_files=False).run(path, mode=EvaluationMode.LIVE_PROVIDERS)
    except ValueError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("Live evaluation unexpectedly ran")
