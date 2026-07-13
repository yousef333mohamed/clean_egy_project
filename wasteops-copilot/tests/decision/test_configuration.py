"""Decision weight and human-approval configuration safety."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def values(**updates):
    data = {"database_url": "postgresql+asyncpg://x:x@x/x", "database_sync_url": "postgresql+psycopg://x:x@x/x"}
    data.update(updates)
    return data


def test_human_approval_default_and_option_bounds():
    settings = Settings(**values())
    assert settings.decision_require_human_approval is True
    assert 2 <= settings.decision_max_options <= 10


@pytest.mark.parametrize(
    "updates",
    [
        {"decision_service_impact_weight": 0.9},
        {"confidence_source_quality_weight": 0.9},
        {"decision_max_options": 1},
        {"app_environment": "production", "decision_require_human_approval": False},
        {"data_science_provider": "mock", "allow_mock_data_science": False},
    ],
)
def test_invalid_safety_configuration_rejected(updates):
    with pytest.raises(ValidationError):
        Settings(**values(**updates))
