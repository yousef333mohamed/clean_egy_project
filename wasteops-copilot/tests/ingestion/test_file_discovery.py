"""Filename allow-list and alias discovery tests."""

from pathlib import Path

from app.ingestion.file_discovery import discover_dataset
from app.ingestion.registry import get_dataset


def test_canonical_filename_takes_precedence(tmp_path: Path) -> None:
    (tmp_path / "smart_bins.csv").write_text("bin_id\n", encoding="utf-8")
    (tmp_path / "smart_bins(1).csv").write_text("bin_id\n", encoding="utf-8")
    result = discover_dataset(tmp_path, get_dataset("smart_bins"))
    assert result.filename == "smart_bins.csv"


def test_uploaded_alias_is_supported(tmp_path: Path) -> None:
    (tmp_path / "smart_bins(1).csv").write_text("bin_id\n", encoding="utf-8")
    result = discover_dataset(tmp_path, get_dataset("smart_bins"))
    assert result.available is True
    assert result.filename == "smart_bins(1).csv"


def test_dataset_names_never_resolve_paths() -> None:
    try:
        get_dataset("../smart_bins")
    except KeyError:
        pass
    else:
        raise AssertionError("path traversal must not resolve as a dataset")
