"""Safe failed-document report generation."""

import json
from datetime import UTC, datetime
from pathlib import Path


def write_document_failure_report(
    rejected_root: Path,
    *,
    source_filename: str,
    relative_path: str,
    document_id: str,
    error_type: str,
    error_message: str,
    warnings: list[str],
    stage: str,
) -> Path:
    """Write failure metadata without content, secrets, tracebacks, or absolute paths."""
    target_dir = rejected_root / "documents"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{Path(source_filename).stem}_{document_id}_failed.json"
    payload = {
        "source_filename": source_filename,
        "relative_path": relative_path,
        "error_type": error_type,
        "error_message": error_message,
        "warnings": warnings,
        "processing_stage": stage,
        "created_at": datetime.now(UTC).isoformat(),
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target
