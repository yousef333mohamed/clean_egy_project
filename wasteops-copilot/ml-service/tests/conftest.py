from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest


@pytest.fixture
def as_of():
    return datetime(2026, 3, 10, 12, tzinfo=timezone.utc)


@pytest.fixture
def bin_readings(as_of):
    rows = []
    for bin_id, base in (("BIN-1", 40), ("BIN-2", 70)):
        for hours in (24, 12, 6, 3, 0):
            rows.append(
                {
                    "bin_id": bin_id,
                    "reading_timestamp": as_of - timedelta(hours=hours),
                    "fill_level_pct": base + (24 - hours) * 1.2,
                    "sensor_status": "Operational",
                    "was_collected": hours == 24,
                    "last_collected_at": as_of - timedelta(hours=24),
                    "region": "Cairo",
                }
            )
    return pd.DataFrame(rows)
