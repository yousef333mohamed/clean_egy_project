import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, async_engine
from app.ingestion.ingestion_service import IngestionService


async def main() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        service = IngestionService(session, settings=settings)
        result = await service.ingest_dataset("smart_bin_readings")
        print(result)
    await async_engine.dispose()


asyncio.run(main())