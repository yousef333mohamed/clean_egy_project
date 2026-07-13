"""CLI for dry-running or ingesting knowledge-base documents."""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import AsyncSessionLocal, async_engine  # noqa: E402
from app.ingestion.document_ingestion_service import DocumentIngestionService  # noqa: E402
from app.models import DocumentStatus  # noqa: E402
from app.schemas.documents import DocumentMetadata  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse document target and optional metadata overrides."""
    parser = argparse.ArgumentParser(description="Validate and ingest WasteOps knowledge documents")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--all", action="store_true", help="process every supported document")
    target.add_argument("--file", help="safe path relative to DOCUMENTS_DIRECTORY")
    parser.add_argument("--dry-run", action="store_true", help="extract and chunk without embeddings or storage")
    parser.add_argument("--force", action="store_true", help="create a new version even when the file hash exists")
    parser.add_argument("--document-type")
    parser.add_argument("--department")
    parser.add_argument("--asset-type")
    parser.add_argument("--region")
    parser.add_argument("--effective-date")
    parser.add_argument("--version")
    parser.add_argument("--language", choices=["en", "ar", "mixed", "unknown"])
    parser.add_argument("--title")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    """Execute the selected workflow and print only safe aggregate metadata."""
    override_values = {
        key: getattr(args, key)
        for key in ("document_type", "department", "asset_type", "region", "effective_date", "version", "language", "title")
        if getattr(args, key) is not None
    }
    override = DocumentMetadata.model_validate(override_values) if override_values else None
    async with AsyncSessionLocal() as session:
        service = DocumentIngestionService(session, settings=get_settings())
        results = (
            await service.ingest_all_documents(force=args.force, dry_run=args.dry_run)
            if args.all
            else [
                await service.ingest_document(
                    args.file,
                    force=args.force,
                    dry_run=args.dry_run,
                    metadata_override=override,
                )
            ]
        )
    await async_engine.dispose()
    print("Document                                Status                     Tokens  Chunks  Embedded  Reused")
    for result in results:
        print(
            f"{result.relative_path:<39} {result.status.value:<26} {result.tokens_extracted:>7} "
            f"{result.chunks_created:>7} {result.chunks_embedded:>9} {result.embeddings_reused:>7}"
        )
        for warning in result.warnings:
            print(f"  warning: {warning}")
        if result.failure_report:
            print(f"  failure report: {result.failure_report}")
        if result.error_message:
            print(f"  error: {result.error_message}")
    return 1 if results and all(result.status == DocumentStatus.FAILED for result in results) else 0


def main() -> int:
    try:
        return asyncio.run(run(parse_args()))
    except Exception as exc:
        print(f"Document ingestion failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
