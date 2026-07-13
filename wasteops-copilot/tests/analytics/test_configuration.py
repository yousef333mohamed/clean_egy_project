"""Analytics safety defaults and cross-field validation."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def values(**updates):
    base = {"database_url": "postgresql+asyncpg://x:x@x/x", "database_sync_url": "postgresql+psycopg://x:x@x/x"}
    base.update(updates)
    return base


def test_raw_sql_is_disabled_by_default():
    settings = Settings(**values())
    assert settings.analytics_allow_raw_sql is False
    assert settings.analytics_query_timeout_seconds > 0


def test_maximum_limit_must_cover_default():
    with pytest.raises(ValidationError):
        Settings(**values(analytics_default_limit=100, analytics_max_limit=50))
