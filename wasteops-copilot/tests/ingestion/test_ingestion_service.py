"""Service-level dry-run, foreign-key, and idempotency tests without PostgreSQL."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.ingestion.ingestion_service import IngestionService
from app.models import IngestionStatus


class FakeSession:
    """Minimal session surface used by dry runs and duplicate skips."""

    def __init__(self, parent_ids: list[str] | None = None) -> None:
        self.added = []
        self.parent_ids = parent_ids or []

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: list[object]) -> None:
        self.added.extend(values)

    async def commit(self) -> None:
        for value in self.added:
            if getattr(value, "id", "missing") is None:
                value.id = uuid.uuid4()

    async def rollback(self) -> None:
        return None

    async def scalars(self, _statement: object) -> SimpleNamespace:
        return SimpleNamespace(all=lambda: self.parent_ids)


def settings(data_dir: Path) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@database/test",
        database_sync_url="postgresql+psycopg://test:test@database/test",
        data_dir=str(data_dir),
    )


async def no_success(_dataset: str, _file_hash: str) -> None:
    return None


@pytest.mark.asyncio
async def test_parent_dry_run_validates_without_inserting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "smart_bins.csv").write_text(
        "bin_id,governorate,region,latitude,longitude,capacity_liters,primary_waste_type,install_date\nB1,القاهرة,Cairo,30,31,100,Mixed,2026-01-01\n",
        encoding="utf-8",
    )
    service = IngestionService(FakeSession(), settings=settings(tmp_path))
    monkeypatch.setattr(service, "_successful_run", no_success)
    result = await service.ingest_dataset("smart_bins", dry_run=True)
    assert result.status == IngestionStatus.DRY_RUN_COMPLETED
    assert result.total_rows == result.valid_rows == 1
    assert result.inserted_rows == 0


@pytest.mark.asyncio
async def test_missing_foreign_key_is_rejected_and_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "workforce_attendance.csv").write_text(
        "worker_id,date,present,completed_tasks,overtime_hours,performance_score\nW-missing,2026-01-01,true,1,0,90\n",
        encoding="utf-8",
    )
    service = IngestionService(FakeSession(parent_ids=["W-existing"]), settings=settings(tmp_path))
    monkeypatch.setattr(service, "_successful_run", no_success)
    result = await service.ingest_dataset("workforce_attendance", dry_run=True)
    assert result.rejected_rows == 1
    assert result.valid_rows == 0
    assert result.rejection_report is not None
    assert Path(result.rejection_report).exists()


@pytest.mark.asyncio
async def test_successful_file_hash_is_skipped_and_audited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "trucks.csv").write_text("truck_id,region,capacity_kg,model_year,fuel_type\n", encoding="utf-8")
    session = FakeSession()
    service = IngestionService(session, settings=settings(tmp_path))
    prior = SimpleNamespace(id=uuid.uuid4(), total_rows=17, valid_rows=17, started_at=datetime.now(UTC))

    async def successful(_dataset: str, _file_hash: str) -> SimpleNamespace:
        return prior

    monkeypatch.setattr(service, "_successful_run", successful)
    result = await service.ingest_dataset("trucks")
    assert result.status == IngestionStatus.SKIPPED_DUPLICATE
    assert result.inserted_rows == 0
    assert result.duplicate_rows == 17
    assert any(getattr(item, "status", None) == IngestionStatus.SKIPPED_DUPLICATE for item in session.added)
