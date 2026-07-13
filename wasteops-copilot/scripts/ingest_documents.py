"""Ingest all supported documents with optional metadata."""

import argparse
import asyncio
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.ingestion.embeddings import DocumentIngestor
from app.schemas.ingestion import DocumentIngestionRequest


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--department")
    parser.add_argument("--asset-type")
    parser.add_argument("--region")
    parser.add_argument("--effective-date")
    parser.add_argument("--version")
    args = parser.parse_args()
    request = DocumentIngestionRequest(
        department=args.department, asset_type=args.asset_type, region=args.region, effective_date=args.effective_date, version=args.version
    )
    async with SessionLocal() as session:
        print((await DocumentIngestor(session, get_settings()).ingest(request)).model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
