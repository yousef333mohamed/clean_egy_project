"""Asynchronous database engine, sessions, and connectivity checks."""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


settings = get_settings()
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.app_environment == "development" and settings.log_level.upper() == "DEBUG",
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=settings.database_pool_recycle_seconds,
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session, rolling back failures and always closing it."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_database_connection() -> None:
    """Raise the underlying database error when a connectivity check fails."""
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
