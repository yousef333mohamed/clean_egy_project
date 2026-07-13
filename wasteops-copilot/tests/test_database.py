"""Configuration and async session unit tests."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core import database
from app.core.database import AsyncSessionLocal, async_engine


def test_database_settings_load_from_environment(monkeypatch) -> None:
    """Async and sync database URLs are independently configurable."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@database:5432/test_db")
    monkeypatch.setenv("DATABASE_SYNC_URL", "postgresql+psycopg://test:test@database:5432/test_db")
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.database_sync_url.startswith("postgresql+psycopg://")


async def test_async_session_factory_creates_session() -> None:
    """The exported factory constructs SQLAlchemy AsyncSession objects."""
    assert isinstance(async_engine, AsyncEngine)
    assert isinstance(AsyncSessionLocal, async_sessionmaker)
    session = AsyncSessionLocal()
    try:
        assert isinstance(session, AsyncSession)
    finally:
        await session.close()


async def test_session_dependency_rolls_back_and_closes(monkeypatch) -> None:
    """Exceptions are re-raised after rollback and unconditional cleanup."""

    class FakeSession:
        def __init__(self) -> None:
            self.rolled_back = False
            self.closed = False

        async def rollback(self) -> None:
            self.rolled_back = True

        async def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: session)
    dependency = database.get_db_session()
    assert await anext(dependency) is session

    error = RuntimeError("database operation failed")
    try:
        await dependency.athrow(error)
    except RuntimeError as exc:
        assert exc is error
    else:
        raise AssertionError("The dependency silently hid the database error")

    assert session.rolled_back
    assert session.closed
