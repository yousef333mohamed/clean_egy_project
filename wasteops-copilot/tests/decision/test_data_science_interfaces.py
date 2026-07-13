"""Future prediction providers remain disabled or explicitly synthetic."""

import pytest

from app.integrations.data_science.interfaces import DisabledDataScienceProvider
from app.integrations.data_science.mock_provider import MockDataScienceProvider


async def test_disabled_provider_never_fabricates_model_evidence():
    provider = DisabledDataScienceProvider()
    assert await provider.predict_overflow(["BIN-1"], 24) == []
    assert await provider.detect_anomalies(["TRK-1"]) == []


def test_mock_provider_requires_explicit_nonproduction_enablement(decision_settings):
    with pytest.raises(RuntimeError):
        MockDataScienceProvider(decision_settings.model_copy(update={"allow_mock_data_science": False}))


async def test_mock_results_are_synthetic(decision_settings):
    provider = MockDataScienceProvider(decision_settings.model_copy(update={"allow_mock_data_science": True, "data_science_provider": "mock"}))
    results = await provider.predict_overflow(["BIN-1"], 24)
    assert results[0].is_synthetic is True
