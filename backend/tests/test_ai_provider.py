import pytest
import os
from backend.app.services.ai_service import (
    ScopeAIEngine,
    DeterministicScopeEngine,
    GeminiProvider,
    RequestAnalysisResult,
)
from backend.app.config import settings

@pytest.mark.asyncio
async def test_ai_provider_configuration_and_fallback():
    """Verify that absent credentials trigger truthful fallback without fabrication."""
    engine = ScopeAIEngine()
    
    # If GEMINI_API_KEY is not in the environment, verify honest fallback reporting
    if not engine.provider.is_configured():
        assert engine.provider.is_configured() is False
        
        sample_scope_items = [
            {
                "id": "item-123",
                "item_type": "exclusion",
                "description": "Payment gateway and checkout workflows are excluded.",
                "source_clause_id": "Exclusion 4.1",
                "source_quote": "Payment gateway and checkout workflows are excluded.",
                "section_reference": "Exclusions",
                "page_number": 1,
            }
        ]
        
        result = await engine.analyze_request(
            message_text="Can we add Stripe checkout?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )
        
        assert isinstance(result, RequestAnalysisResult)
        assert result.provider_source == "deterministic_fallback"
        assert result.classification == "likely_out_of_scope"
        assert result.matched_scope_item_id == "item-123"
        assert result.supporting_quote == "Payment gateway and checkout workflows are excluded."
        assert result.estimated_extra_hours == 8.0

@pytest.mark.asyncio
async def test_grounding_rejects_nonexistent_ids():
    """Verify that references not present in the project baseline are rejected or flagged."""
    engine = ScopeAIEngine()
    
    # Empty baseline
    empty_scope_items = []
    
    result = await engine.analyze_request(
        message_text="Can you build a native VR metaverse game?",
        scope_items=empty_scope_items,
        default_rate=150.0,
    )
    
    assert result.classification == "ambiguous"
    assert result.matched_scope_item_id is None
    assert result.matched_clause_id is None
    assert result.supporting_quote is None
    assert result.missing_evidence_notes is not None
    assert "lacks explicit language" in result.missing_evidence_notes or "baseline" in result.missing_evidence_notes

@pytest.mark.asyncio
async def test_unrelated_request_not_classified_as_creep():
    """Verify that conversational or off-topic requests are not marked as out-of-scope creep."""
    engine = ScopeAIEngine()
    
    scope_items = [
        {
            "id": "item-1",
            "item_type": "deliverable",
            "description": "Five-page marketing website",
            "source_clause_id": "Clause 2.1",
            "source_quote": "Delivery of a five-page marketing website",
        }
    ]
    
    unrelated_messages = [
        "What is the weather today in San Francisco?",
        "Good morning team, hope you are having a great week!",
        "When is our sync call tomorrow afternoon?",
    ]
    
    for msg in unrelated_messages:
        result = await engine.analyze_request(
            message_text=msg,
            scope_items=scope_items,
            default_rate=2000.0,
        )
        assert result.classification == "ambiguous", f"Message '{msg}' was falsely classified as {result.classification}"
        assert result.estimated_extra_hours in (0.0, None)
        assert result.matched_scope_item_id is None
