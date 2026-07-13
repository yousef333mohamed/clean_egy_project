"""Opt-in checks against a dedicated migrated PostgreSQL test database."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = [pytest.mark.integration, pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not configured")]


async def test_invalid_percentage_is_rejected_by_postgresql() -> None:
    """The migrated database rejects out-of-range telemetry percentages."""
    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """INSERT INTO smart_bins
                    (bin_id, governorate, region, latitude, longitude, capacity_liters, primary_waste_type, install_date)
                    VALUES ('TEST-BIN-CHECK', 'Test', 'Test', 30.0, 31.0, 100, 'Mixed', DATE '2026-01-01')
                    ON CONFLICT (bin_id) DO NOTHING"""
                )
            )
            with pytest.raises(IntegrityError):
                await connection.execute(
                    text(
                        """INSERT INTO smart_bin_readings
                        (bin_id, timestamp, fill_level_pct, waste_weight_kg, waste_type, temperature_c,
                         humidity_pct, battery_level_pct, sensor_status, was_collected)
                        VALUES ('TEST-BIN-CHECK', now(), 101, 0, 'Mixed', 20, 50, 50, 'OK', false)"""
                    )
                )
    finally:
        await engine.dispose()
