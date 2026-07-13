"""Ingest all raw CSV datasets."""

import asyncio
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.ingestion.csv_loader import CSVLoader


async def main() -> None:
    async with SessionLocal() as session:
        print((await CSVLoader(session, get_settings().data_dir / "raw").ingest()).model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
