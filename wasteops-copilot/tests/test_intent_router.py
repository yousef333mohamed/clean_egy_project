import pytest
from app.retrieval.intent_router import IntentRouter
from app.schemas.retrieval import Intent


@pytest.mark.asyncio
async def test_fallback_routes_incident_and_extracts_truck() -> None:
    result = await IntentRouter().route("Why was collection missed by TRK-GRE-01?")
    assert result.intent == Intent.INCIDENT_INVESTIGATION
    assert result.entities.truck_id == "TRK-GRE-01"
    assert result.requires_sql and result.requires_vector_search
