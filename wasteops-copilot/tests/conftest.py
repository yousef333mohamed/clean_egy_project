"""Isolated test configuration set before application modules are imported."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@database:5432/wasteops_test")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql+psycopg://test:test@database:5432/wasteops_test")
