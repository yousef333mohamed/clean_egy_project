"""CLI for retrieval diagnostics and grounded RAG questions."""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import AsyncSessionLocal, async_engine  # noqa: E402
from app.retrieval.factory import build_rag_service, build_retrieval_service  # noqa: E402
from app.schemas.chat import RAGRequest  # noqa: E402
from app.schemas.retrieval import RetrievalFilters, RetrievalRequest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query the WasteOps document knowledge base")
    parser.add_argument("--question", required=True)
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--document-type", action="append")
    parser.add_argument("--department", action="append")
    parser.add_argument("--asset-type", action="append")
    parser.add_argument("--region", action="append")
    parser.add_argument("--language", action="append")
    parser.add_argument("--source-filename", action="append")
    parser.add_argument("--synthetic", action=argparse.BooleanOptionalAction, default=None)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    settings = get_settings()
    filters = RetrievalFilters(
        document_type=args.document_type,
        department=args.department,
        asset_type=args.asset_type,
        region=args.region,
        language=args.language,
        source_filename=args.source_filename,
        is_synthetic=args.synthetic,
    )
    async with AsyncSessionLocal() as session:
        if args.retrieval_only:
            response = await build_retrieval_service(session, settings).search(RetrievalRequest(query=args.question, top_k=args.top_k, filters=filters))
            for index, item in enumerate(response.evidence, start=1):
                print(f"S{index}: {item.document_title} | {item.source_filename} | score={item.final_score:.3f}")
                print(f"  {item.content_preview}")
            for warning in response.warnings:
                print(f"warning: {warning}")
        else:
            response = await build_rag_service(session, settings).answer(RAGRequest(question=args.question, top_k=args.top_k, filters=filters))
            print(response.answer)
            if response.citations:
                print("\nCitations:")
                for citation in response.citations:
                    print(f"[{citation.citation_id}] {citation.document_title} ({citation.source_filename})")
            for warning in response.warnings:
                print(f"warning: {warning}")
    await async_engine.dispose()
    return 0


def main() -> int:
    try:
        return asyncio.run(run(parse_args()))
    except Exception as exc:
        print(f"RAG query failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
