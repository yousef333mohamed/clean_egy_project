"""Decision fixtures."""

import pytest

from app.analytics.tool_registry import build_tool_registry
from app.core.config import Settings
from app.decision.decision_registry import build_decision_registry
from app.decision.enums import DecisionEvidenceType
from app.schemas.decision_evidence import DecisionEvidence


@pytest.fixture
def decision_settings():
    return Settings(database_url="postgresql+asyncpg://test:test@db/test", database_sync_url="postgresql+psycopg://test:test@db/test", llm_api_key="fake")


@pytest.fixture
def decision_registry():
    return build_decision_registry()


@pytest.fixture
def analytics_registry(decision_settings):
    return build_tool_registry(decision_settings)


@pytest.fixture
def evidence_factory():
    def build(
        evidence_id="D1",
        source_type=DecisionEvidenceType.DATABASE,
        category="latest_bin_status",
        description="Critical bins",
        authority_level="database",
        recency="latest_available",
        supporting_values=None,
        completeness_notes=None,
        is_synthetic=False,
    ):
        return DecisionEvidence(
            evidence_id=evidence_id,
            source_type=source_type,
            category=category,
            description=description,
            authority_level=authority_level,
            recency=recency,
            supporting_values=supporting_values or {"has_data": True, "result_row_count": 3},
            completeness_notes=completeness_notes or [],
            is_synthetic=is_synthetic,
        )

    return build
