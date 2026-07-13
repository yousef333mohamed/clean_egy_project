"""Ask controlled structured or hybrid WasteOps questions from the command line."""

import argparse
import asyncio
import sys

from app.analytics.factory import build_analytics_stack, build_hybrid_service
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.schemas.hybrid_answer import HybridQuestionRequest


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query approved WasteOps analytics tools")
    parser.add_argument("--question", required=True)
    parser.add_argument("--hybrid", action="store_true")
    parser.add_argument("--route-only", action="store_true")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        if args.route_only:
            decision = await build_analytics_stack(session, settings)[1].route(args.question)
            print(decision.model_dump_json(indent=2))
            return
        response = await build_hybrid_service(session, settings).answer(HybridQuestionRequest(question=args.question))
        print(response.answer)
        for evidence in response.database_evidence:
            print(f"[{evidence.evidence_id}] {evidence.description}")
        for citation in response.document_citations:
            print(f"[{citation.citation_id}] {citation.document_title} — {citation.source_filename}")
        for warning in response.warnings:
            print(f"Warning: {warning}")


if __name__ == "__main__":
    try:
        asyncio.run(run(arguments()))
    except Exception as exc:
        print(f"System failure: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1) from exc
