"""CSV header and chunk behavior tests."""

from pathlib import Path

import pytest

from app.ingestion.csv_reader import CsvSchemaError, inspect_schema, read_csv_chunks
from app.ingestion.registry import get_dataset


HEADER = "bin_id,governorate,region,latitude,longitude,capacity_liters,primary_waste_type,install_date"


def test_missing_required_columns_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "smart_bins.csv"
    path.write_text("bin_id,region\nB1,Cairo\n", encoding="utf-8")
    with pytest.raises(CsvSchemaError, match="missing required"):
        inspect_schema(path, get_dataset("smart_bins"))


def test_duplicate_normalized_columns_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "smart_bins.csv"
    path.write_text(f"{HEADER},Bin ID\n", encoding="utf-8")
    with pytest.raises(CsvSchemaError, match="duplicate columns"):
        inspect_schema(path, get_dataset("smart_bins"))


def test_unexpected_columns_warn_or_fail_in_strict_mode(tmp_path: Path) -> None:
    path = tmp_path / "smart_bins.csv"
    path.write_text(f"{HEADER},extra\nB1,القاهرة,Cairo,30,31,100,Mixed,2026-01-01,x\n", encoding="utf-8")
    assert inspect_schema(path, get_dataset("smart_bins")).warnings
    with pytest.raises(CsvSchemaError, match="unexpected columns"):
        inspect_schema(path, get_dataset("smart_bins"), strict_columns=True)


def test_chunk_reader_preserves_source_row_numbers(tmp_path: Path) -> None:
    path = tmp_path / "smart_bins.csv"
    path.write_text(
        f"{HEADER}\nB1,القاهرة,Cairo,30,31,100,Mixed,2026-01-01\nB2,الجيزة,Cairo,30,31,100,Mixed,2026-01-01\n",
        encoding="utf-8",
    )
    _, chunks = read_csv_chunks(path, get_dataset("smart_bins"), 1)
    assert [int(chunk.iloc[0]["__source_row_number__"]) for chunk in chunks] == [2, 3]
