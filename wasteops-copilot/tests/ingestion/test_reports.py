"""Rejected-record report tests."""

from pathlib import Path

from app.ingestion.reports import RejectedRecord, write_rejection_report


def test_rejected_report_contains_safe_row_details(tmp_path: Path) -> None:
    path = write_rejection_report(
        tmp_path,
        "smart_bins",
        "run-id",
        [RejectedRecord(2, "OUT_OF_RANGE", "latitude must be between -90 and 90", {"bin_id": "B1", "latitude": "999"})],
    )
    assert path is not None
    content = path.read_text(encoding="utf-8-sig")
    assert "source_row_number,error_code,error_message,bin_id,latitude" in content
    assert "OUT_OF_RANGE" in content
    assert "B1" in content
