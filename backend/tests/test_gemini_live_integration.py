import os
import pytest
from backend.app.services.ai_service import GeminiProvider, ScopeAIEngine, RequestAnalysisResult
from backend.app.config import settings

@pytest.mark.asyncio
async def test_live_gemini_3_8_flash_integration():
    """
    Opt-in live integration test for Gemini 3.8 Flash.
    
    Requires both:
    1. RUN_LIVE_GEMINI_TESTS=1 in environment
    2. GEMINI_API_KEY populated in environment
    
    Never reports passed unless a real network request to gemini-3.8-flash succeeds.
    """
    run_live = os.getenv("RUN_LIVE_GEMINI_TESTS", "").strip() == "1"
    api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY).strip()

    if not run_live or not api_key:
        pytest.skip(
            "Skipping live Gemini 3.8 Flash test. To run, set RUN_LIVE_GEMINI_TESTS=1 and ensure GEMINI_API_KEY is configured."
        )

    provider = GeminiProvider(api_key=api_key, model="gemini-3.8-flash", timeout=45.0)
    assert provider.model == "gemini-3.8-flash"
    assert provider.is_configured() is True

    # Real inference test with gemini-3.8-flash (with retry for transient 503 demand spikes)
    import asyncio

    prompt = (
        'Analyze this client request: "Can you add Stripe payment gateway?" '
        'Respond in JSON: {"classification": "likely_out_of_scope", "reason": "Payment gateway", "confidence": 0.95}'
    )
    system_instruction = "You are a legal scope change detector. Always respond with valid JSON."

    data = None
    err = None
    for attempt in range(3):
        data, err = await provider.call_gemini_json(prompt, system_instruction)
        if not err and data:
            break
        if "503" in str(err):
            await asyncio.sleep(2)
            continue
        break

    if err:
        pytest.fail(f"Live Gemini 3.8 Flash API request failed: {err}")

    assert data is not None, "Live Gemini 3.8 Flash returned None data"
    assert "classification" in data, f"Live Gemini 3.8 Flash response missing 'classification': {data}"
    assert data["classification"] == "likely_out_of_scope"
