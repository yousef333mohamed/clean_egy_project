"""Command-line entry point for production CSV ingestion."""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import AsyncSessionLocal, async_engine  # noqa: E402
from app.ingestion.ingestion_service import IngestionService  # noqa: E402
from app.ingestion.registry import DATASET_REGISTRY  # noqa: E402
from app.models import IngestionStatus  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse mutually exclusive dataset selection and validation options."""
    parser = argparse.ArgumentParser(description="Validate and ingest WasteOps CSV files")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--all", action="store_true", help="process every available dataset in dependency order")
    target.add_argument("--dataset", choices=sorted(DATASET_REGISTRY), help="process one registered dataset")
    parser.add_argument("--dry-run", action="store_true", help="validate without inserting source records")
    parser.add_argument("--force", action="store_true", help="process a previously ingested file with conflict-safe inserts")
    parser.add_argument("--batch-size", type=int, help="override the configured chunk size")
    parser.add_argument("--strict-columns", action="store_true", default=None, help="reject unexpected columns")
    args = parser.parse_args()
    if args.batch_size is not None and args.batch_size < 1:
        parser.error("--batch-size must be greater than zero")
    return args


async def run(args: argparse.Namespace) -> int:
    """Execute ingestion and return a process exit code."""
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = IngestionService(session, settings=settings, batch_size=args.batch_size, strict_columns=args.strict_columns)
        results = (
            await service.ingest_all(dry_run=args.dry_run, force=args.force)
            if args.all
            else [await service.ingest_dataset(args.dataset, dry_run=args.dry_run, force=args.force)]
        )
    await async_engine.dispose()
    print("Dataset                  Status                    Total    Inserted  Duplicate  Rejected  Failed")
    for result in results:
        print(
            f"{result.dataset:<24} {result.status.value:<25} {result.total_rows:>8} {result.inserted_rows:>11} "
            f"{result.duplicate_rows:>10} {result.rejected_rows:>9} {result.failed_rows:>7}"
        )
        for warning in result.warnings:
            print(f"  warning: {warning}")
        if result.rejection_report:
            print(f"  rejection report: {result.rejection_report}")
        if result.error_message:
            print(f"  error: {result.error_message}")
    return 1 if any(result.status == IngestionStatus.FAILED for result in results) else 0


def main() -> int:
    """Run the asynchronous command safely from a synchronous shell."""
    try:
        return asyncio.run(run(parse_args()))
    except Exception as exc:
        print(f"Ingestion failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
