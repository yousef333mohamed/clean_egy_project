"""Ask controlled structured or hybrid WasteOps questions from the command line."""

from __future__ import annotations

import argparse
import asyncio
import sys
import traceback

from app.analytics.factory import build_analytics_stack, build_hybrid_service
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.schemas.hybrid_answer import HybridQuestionRequest


def arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Query approved WasteOps analytics tools.",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="The operational question to ask.",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Combine structured analytics with document retrieval.",
    )
    parser.add_argument(
        "--route-only",
        action="store_true",
        help="Show the selected route and parameters without executing the query.",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    """Run the requested analytics or hybrid workflow."""

    settings = get_settings()

    if args.route_only:
        async with AsyncSessionLocal() as session:
            analytics_stack = build_analytics_stack(session, settings)
            analytics_router = analytics_stack[1]
            decision = await analytics_router.route(args.question)

        print(decision.model_dump_json(indent=2))
        return

    async with AsyncSessionLocal() as session:
        hybrid_service = build_hybrid_service(session, settings)

        response = await hybrid_service.answer(
            HybridQuestionRequest(
                question=args.question,
            )
        )

    print("\nAnswer\n")
    print(response.answer)

    if response.database_evidence:
        print("\nDatabase evidence")
        for evidence in response.database_evidence:
            print(
                f"[{evidence.evidence_id}] "
                f"{evidence.description}"
            )

    if response.document_citations:
        print("\nDocument citations")
        for citation in response.document_citations:
            print(
                f"[{citation.citation_id}] "
                f"{citation.document_title} — "
                f"{citation.source_filename}"
            )

    if response.warnings:
        print("\nWarnings")
        for warning in response.warnings:
            print(f"- {warning}")


def main() -> int:
    """Application entry point."""

    try:
        asyncio.run(run(arguments()))
    except KeyboardInterrupt:
        print("\nOperation cancelled by the user.", file=sys.stderr)
        return 130
    except Exception:
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())