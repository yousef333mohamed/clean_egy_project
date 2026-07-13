"""Analytics fixtures."""

from types import SimpleNamespace

import pytest
from sqlalchemy.dialects import postgresql

from app.core.config import Settings


@pytest.fixture
def analytics_settings():
    return Settings(database_url="postgresql+asyncpg://test:test@db/test", database_sync_url="postgresql+psycopg://test:test@db/test", llm_api_key="fake")


class RecordingExecutor:
    def __init__(self, rows=None):
        self.rows = rows if rows is not None else [{"records_included": 1}]
        self.statements = []

    async def execute(self, _session, statement, *, tool_name, limit):
        self.statements.append((tool_name, limit, str(statement.compile(dialect=postgresql.dialect()))))
        return self.rows


@pytest.fixture
def recording_executor():
    return RecordingExecutor()


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.statements = []
        self.rolled_back = False

    def get_bind(self):
        return SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    async def execute(self, statement, *_args):
        self.statements.append(statement)
        return FakeResult(self.rows)

    async def rollback(self):
        self.rolled_back = True
