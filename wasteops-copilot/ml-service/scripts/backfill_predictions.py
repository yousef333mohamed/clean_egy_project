"""Controlled resumable backfill validation entry point."""

import argparse
from datetime import date
from pathlib import Path
from app.registry.model_registry import ALLOWED_MODELS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=sorted(ALLOWED_MODELS), required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--resume-file", type=Path, default=Path("artifacts/backfill.resume"))
    args = parser.parse_args()
    if args.start_date > args.end_date:
        parser.error("start-date must not follow end-date")
    if not 1 <= args.batch_size <= 1000:
        parser.error("batch-size must be between 1 and 1000")
    raise SystemExit("Backfill validation passed, but execution requires a configured historical as-of feature store. No predictions were written.")


if __name__ == "__main__":
    main()
