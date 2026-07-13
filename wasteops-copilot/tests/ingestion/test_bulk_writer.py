"""Batch conflict accounting tests."""

from types import SimpleNamespace

import pytest

from app.ingestion.bulk_writer import write_batch
from app.ingestion.registry import get_dataset


class NestedTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_args: object) -> None:
        return None


class FakeWriterSession:
    def __init__(self, inserted: int) -> None:
        self.inserted = inserted
        self.commits = 0

    def begin_nested(self) -> NestedTransaction:
        return NestedTransaction()

    async def execute(self, _statement: object) -> SimpleNamespace:
        return SimpleNamespace(fetchall=lambda: [object()] * self.inserted)

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_batch_insert_counts_conflicts() -> None:
    session = FakeWriterSession(inserted=1)
    records = [
        {"truck_id": "T1", "region": "Cairo", "capacity_kg": 1, "model_year": 2020, "fuel_type": "Diesel"},
        {"truck_id": "T2", "region": "Cairo", "capacity_kg": 1, "model_year": 2020, "fuel_type": "Diesel"},
    ]
    result = await write_batch(session, get_dataset("trucks"), records)
    assert result.inserted == 1
    assert result.duplicates == 1
    assert session.commits == 1
