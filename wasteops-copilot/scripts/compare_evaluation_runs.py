"""Compare two persisted evaluation runs without activating prompts."""

import argparse
import asyncio
import json
from uuid import UUID

from app.core.database import AsyncSessionLocal
from app.evaluation.evaluation_service import EvaluationService


async def main(baseline: str, candidate: str) -> None:
    async with AsyncSessionLocal() as session:
        print(json.dumps(await EvaluationService(session).compare(UUID(baseline), UUID(candidate)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.baseline, args.candidate))
