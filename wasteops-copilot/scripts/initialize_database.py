"""Initialize database schema without Alembic (development convenience)."""

import asyncio
from app.core.database import create_schema

if __name__ == "__main__":
    asyncio.run(create_schema())
