"""Preview or request a human-approved WasteOps recommendation."""

import argparse
import asyncio
import sys

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.decision.factory import build_decision_preview, build_decision_service
from app.schemas.decision import DecisionRequest, DecisionScope


def arguments():
    parser = argparse.ArgumentParser(description="WasteOps Decision Intelligence CLI")
    parser.add_argument("--question", required=True)
    parser.add_argument("--region")
    parser.add_argument("--preview", action="store_true")
    return parser.parse_args()


async def run(args) -> None:
    settings = get_settings()
    request = DecisionRequest(question=args.question, scope=DecisionScope(region=args.region) if args.region else DecisionScope())
    if args.preview:
        _registry, _analytics, router, planner, _llm = build_decision_preview(settings)
        route = await router.route(request)
        print(planner.plan(request, route).model_dump_json(indent=2))
        return
    async with AsyncSessionLocal() as session:
        response = await build_decision_service(session, settings).recommend(request)
    print(response.situation_summary)
    if response.recommended_option:
        option = response.recommended_option
        print(f"Recommended: [{option.option_id}] {option.title} — {option.action}")
        print(f"Score: {option.score} {option.score_breakdown.model_dump_json()}")
        for risk in option.risks:
            print(f"Risk {risk.risk_id}: {risk.description} Mitigation: {risk.mitigation}")
    for option in response.alternative_options:
        print(f"Alternative [{option.option_id}]: {option.title} (score {option.score})")
    print(f"Confidence: {response.confidence.score} {response.confidence.components.model_dump_json()}")
    for evidence in response.database_evidence:
        print(f"[{evidence.evidence_id}] {evidence.description}")
    for citation in response.document_citations:
        print(f"[{citation.citation_id}] {citation.document_title} — {citation.source_filename}")
    for item in response.missing_information:
        print(f"Missing: {item}")
    for warning in response.warnings:
        print(f"Warning: {warning}")
    print("Human approval required: yes")


if __name__ == "__main__":
    try:
        asyncio.run(run(arguments()))
    except Exception as exc:
        print(f"System failure: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1) from exc
