import pytest
import os
import json
from unittest.mock import patch, MagicMock
import httpx

from backend.app.services.ai_service import (
    ScopeAIEngine,
    DeterministicScopeEngine,
    GeminiProvider,
    RequestAnalysisResult,
    ai_engine,
)
from backend.app.config import settings

def test_default_model_and_thinking_configuration():
    """Verify that gemini-3.8-flash is the explicit default model and thinking level is low."""
    provider = GeminiProvider(api_key="test-key")
    assert provider.model == "gemini-3.8-flash"
    assert provider.thinking_level == "low"
    assert "gemini-3.8-flash" in provider.api_url

    # Test thinking level validation: supported: low, medium, high; minimal falls back to low
    p_med = GeminiProvider(api_key="test-key", thinking_level="medium")
    assert p_med.thinking_level == "medium"

    p_high = GeminiProvider(api_key="test-key", thinking_level="high")
    assert p_high.thinking_level == "high"

    # 'minimal' is explicitly unsupported for gemini-3.8-flash; should fall back to 'low'
    p_minimal = GeminiProvider(api_key="test-key", thinking_level="minimal")
    assert p_minimal.thinking_level == "low"


@pytest.mark.asyncio
async def test_gemini_provider_payload_and_header_formatting():
    """Verify headers use x-goog-api-key, key is omitted from URL, and legacy sampling params are removed."""
    provider = GeminiProvider(api_key="secret-key-12345", model="gemini-3.8-flash")
    
    captured_request = {}

    async def mock_post(url, json=None, headers=None):
        captured_request["url"] = str(url)
        captured_request["headers"] = headers
        captured_request["json"] = json
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"status": "ok"}'}]
                    }
                }
            ]
        }
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        result, err = await provider.call_gemini_json("Test prompt", "Test instruction")
        assert err is None
        assert result == {"status": "ok"}

    # 1. Secret key must NOT appear in URL query string
    assert "secret-key-12345" not in captured_request["url"]
    assert "?key=" not in captured_request["url"]
    assert captured_request["url"] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"

    # 2. Key must be passed securely in x-goog-api-key header
    assert captured_request["headers"].get("x-goog-api-key") == "secret-key-12345"

    # 3. Payload must contain thinkingConfig and responseMimeType
    gen_config = captured_request["json"].get("generationConfig", {})
    assert gen_config.get("responseMimeType") == "application/json"
    assert gen_config.get("thinkingConfig", {}).get("thinkingLevel") == "low"

    # 4. Unsupported legacy sampling parameters must be completely absent
    assert "temperature" not in gen_config
    assert "top_p" not in gen_config
    assert "top_k" not in gen_config


@pytest.mark.asyncio
async def test_mocked_gemini_live_success_with_thinking_parts():
    """Verify live Gemini response with thinking parts is parsed and attributed as gemini_live."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "scope-1",
            "item_type": "exclusion",
            "description": "Payment gateway and checkout workflows are excluded.",
            "source_clause_id": "Exclusion 4.1",
            "source_quote": "Payment gateway and checkout workflows are excluded.",
        }
    ]

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        # First part: model reasoning (thinking)
                        {
                            "thought": True,
                            "text": "The contract explicitly excludes payment gateways in Exclusion 4.1. Therefore, Stripe is out of scope."
                        },
                        # Second part: actual structured JSON output
                        {
                            "text": json.dumps({
                                "classification": "likely_out_of_scope",
                                "explanation": "Stripe checkout constitutes payment integration, excluded under Exclusion 4.1.",
                                "confidence": 0.95,
                                "matched_scope_item_id": "scope-1",
                                "matched_clause_id": "Exclusion 4.1",
                                "supporting_quote": "Payment gateway and checkout workflows are excluded.",
                                "estimated_extra_hours": 8.0,
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_gemini_response

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await engine.analyze_request(
            message_text="Can we add Stripe checkout?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

        assert isinstance(res, RequestAnalysisResult)
        assert res.provider_source == "gemini_live"
        assert res.classification == "likely_out_of_scope"
        assert res.matched_scope_item_id == "scope-1"
        assert res.matched_clause_id == "Exclusion 4.1"
        assert res.estimated_extra_hours == 8.0


@pytest.mark.asyncio
async def test_mocked_gemini_api_errors_fallback():
    """Verify that provider 503, 429, or network errors fall back truthfully to deterministic engine."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

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

    # Test 1: HTTP 503 Service Unavailable (Demand spike)
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.text = '{"error": {"code": 503, "message": "High demand spike", "status": "UNAVAILABLE"}}'

    with patch("httpx.AsyncClient.post", return_value=mock_503), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request("Can we add Stripe checkout?", sample_scope_items, 2000.0)
        assert res.provider_source == "deterministic_fallback"
        assert res.classification == "likely_out_of_scope"
        assert "deterministic" in (res.missing_evidence_notes or "").lower()
        assert "503" in (res.missing_evidence_notes or "")

    # Test 2: Network Timeout
    with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Read timed out")), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request("Can we add Stripe checkout?", sample_scope_items, 2000.0)
        assert res.provider_source == "deterministic_fallback"
        assert res.classification == "likely_out_of_scope"
        assert "timeout" in (res.missing_evidence_notes or "").lower() or "readtimeout" in (res.missing_evidence_notes or "").lower()


@pytest.mark.asyncio
async def test_transient_503_retry_and_success():
    """Simulate a 503 high-demand error on attempt 1 followed by 200 OK on attempt 2."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-scope-42",
            "item_type": "exclusion",
            "description": "Customer accounts, authentication, and order history functionality are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included.",
        }
    ]

    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.text = '{"error": {"code": 503, "message": "High demand spike", "status": "UNAVAILABLE"}}'

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "likely_out_of_scope",
                                "explanation": "Customer order history is explicitly excluded under Exclusion 4.2.",
                                "confidence": 0.95,
                                "matched_scope_item_id": "item-scope-42",
                                "matched_clause_id": "Exclusion 4.2",
                                "supporting_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included.",
                                "estimated_extra_hours": 5.0,
                            })
                        }
                    ]
                }
            }
        ]
    }

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_503
        return mock_200

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    assert call_count == 2
    assert res.provider_source == "gemini_live"
    assert res.classification == "likely_out_of_scope"
    assert res.matched_scope_item_id == "item-scope-42"
    assert res.matched_clause_id == "Exclusion 4.2"
    assert res.estimated_extra_hours == 5.0


@pytest.mark.asyncio
async def test_persistent_503_honest_fallback():
    """Simulate persistent 503 errors across all retries, verifying honest deterministic fallback with preserved error."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-scope-42",
            "item_type": "exclusion",
            "description": "Customer accounts, authentication, and order history functionality are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
        }
    ]

    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.text = '{"error": {"code": 503, "message": "High demand spike", "status": "UNAVAILABLE"}}'

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return mock_503

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    assert call_count == 4  # All max_attempts exhausted
    assert res.provider_source == "deterministic_fallback"
    assert res.classification == "likely_out_of_scope"
    assert res.matched_scope_item_id == "item-scope-42"
    assert "503" in (res.missing_evidence_notes or "")


@pytest.mark.asyncio
async def test_permanent_401_no_retries():
    """Permanent errors like HTTP 401 must fail immediately on attempt 1 without retry."""
    provider = GeminiProvider(api_key="invalid-api-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-1",
            "item_type": "exclusion",
            "description": "Payment gateway integration is excluded.",
            "source_clause_id": "Exclusion 4.1",
            "source_quote": "Payment gateway integration is strictly out of scope.",
        }
    ]

    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.text = '{"error": {"code": 401, "message": "API key not valid", "status": "UNAUTHENTICATED"}}'

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return mock_401

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request(
            message_text="Can we add Stripe checkout?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    assert call_count == 1  # Exactly 1 attempt! No retries!
    assert res.provider_source == "deterministic_fallback"
    assert "401" in (res.missing_evidence_notes or "")


@pytest.mark.asyncio
async def test_clause_id_grounding_resolution_from_clause_name():
    """Verify that when Gemini cites clause name (e.g. Exclusion 4.2) rather than UUID, it resolves to the real UUID."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "real-uuid-clause-4-2",
            "item_type": "exclusion",
            "description": "Customer accounts and order history are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included.",
            "section_reference": "Section 4 - Exclusions",
        }
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "likely_out_of_scope",
                                "explanation": "Order history is excluded per Exclusion 4.2.",
                                "confidence": 0.95,
                                "matched_scope_item_id": "Exclusion 4.2",  # Clause label instead of DB UUID
                                "matched_clause_id": "Exclusion 4.2",
                                "supporting_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included.",
                                "estimated_extra_hours": 5.0,
                            })
                        }
                    ]
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    assert res.provider_source == "gemini_live"
    # Grounding must resolve the real DB UUID!
    assert res.matched_scope_item_id == "real-uuid-clause-4-2"
    assert res.matched_clause_id == "Exclusion 4.2"
    assert res.section_reference == "Section 4 - Exclusions"


def test_customer_account_deterministic_semantic_matching():
    """Test customer order-history semantic matching against exclusions, deliverables, and empty baseline."""
    # Case 1: Baseline with explicit Exclusion 4.2
    scope_with_exclusion = [
        {
            "id": "scope-ex-42",
            "item_type": "exclusion",
            "description": "Customer accounts & order history excluded",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
        }
    ]
    res1 = DeterministicScopeEngine.analyze_request("Can we also add a customer order-history page?", scope_with_exclusion)
    assert res1.classification == "likely_out_of_scope"
    assert res1.matched_scope_item_id == "scope-ex-42"
    assert res1.matched_clause_id == "Exclusion 4.2"
    assert res1.estimated_extra_hours == 5.0

    # Case 2: Baseline without exclusion, but with marketing website deliverable
    scope_marketing_only = [
        {
            "id": "scope-del-21",
            "item_type": "deliverable",
            "description": "Five-page marketing website",
            "source_clause_id": "Clause 2.1",
            "source_quote": "Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact.",
        }
    ]
    res2 = DeterministicScopeEngine.analyze_request("Can we add a customer account login dashboard?", scope_marketing_only)
    assert res2.classification == "likely_out_of_scope"
    assert res2.matched_scope_item_id == "scope-del-21"
    assert res2.estimated_extra_hours == 5.0

    # Case 3: Empty baseline
    res3 = DeterministicScopeEngine.analyze_request("Can we also add a customer order-history page?", [])
    assert res3.classification == "ambiguous"
    assert res3.matched_scope_item_id is None
    assert res3.estimated_extra_hours is None
    assert "lacks explicit language" in (res3.missing_evidence_notes or "")


@pytest.mark.asyncio
async def test_mocked_gemini_hallucinated_clause_id_rejection():
    """Verify that hallucinated scope item IDs returned by the model are rejected."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "valid-scope-1",
            "item_type": "deliverable",
            "description": "Five page marketing website",
        }
    ]

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "likely_out_of_scope",
                                "explanation": "Hallucinated item citation",
                                "confidence": 0.85,
                                "matched_scope_item_id": "nonexistent-fake-id-9999",
                                "matched_clause_id": "Fake Clause 99",
                                "estimated_extra_hours": 4.0,
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_gemini_response

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await engine.analyze_request(
            message_text="Add external API",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

        assert res.provider_source == "gemini_live"
        # The hallucinated ID was not in valid_ids, so it must be stripped to None
        assert res.matched_scope_item_id is None


@pytest.mark.asyncio
async def test_ai_provider_configuration_and_fallback():
    """Verify that absent credentials trigger truthful fallback without fabrication."""
    engine = ScopeAIEngine()
    # Force provider unconfigured
    engine.provider.api_key = ""

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
    engine.provider.api_key = ""
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
    engine.provider.api_key = ""
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


def test_parse_error_response_hard_quota_distinction():
    """Verify GeminiProvider.parse_error_response identifies Google's exact quota exhaustion response as hard quota."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.headers = {}
    mock_resp.text = '{"error": {"code": 429, "message": "You exceeded your current quota, please check your plan and billing details.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_resp.json.return_value = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota, please check your plan and billing details. For more information, see https://cloud.google.com/docs/quota.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RESOURCE_EXHAUSTED",
                    "domain": "googleapis.com",
                }
            ],
        }
    }

    parsed = GeminiProvider.parse_error_response(mock_resp)
    assert parsed["status_code"] == 429
    assert parsed["status"] == "RESOURCE_EXHAUSTED"
    assert parsed["is_hard_quota"] is True
    assert "exceeded your current quota" in parsed["message"]


def test_parse_error_response_temporary_rate_limit_with_retry_info():
    """Verify parse_error_response identifies temporary rate limits with RetryInfo retryDelay."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "3"}
    mock_resp.text = '{"error": {"code": 429, "message": "Too many requests per minute.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_resp.json.return_value = {
        "error": {
            "code": 429,
            "message": "Resource has been exhausted (e.g. check quota). Too many requests per minute.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RATE_LIMIT_EXCEEDED",
                    "domain": "googleapis.com",
                },
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "2.5s",
                },
            ],
        }
    }

    parsed = GeminiProvider.parse_error_response(mock_resp)
    assert parsed["status_code"] == 429
    assert parsed["is_hard_quota"] is False
    assert parsed["retry_delay"] == 2.5
    assert "RATE_LIMIT_EXCEEDED" in parsed["reasons"]


@pytest.mark.asyncio
async def test_gemini_hard_quota_429_stops_promptly_without_retries():
    """A confirmed quota exhaustion 429 must stop immediately on attempt 1 without retries and fall back honestly."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-scope-42",
            "item_type": "exclusion",
            "description": "Customer accounts and order history functionality are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
        }
    ]

    mock_429_quota = MagicMock(spec=httpx.Response)
    mock_429_quota.status_code = 429
    mock_429_quota.headers = {}
    mock_429_quota.text = '{"error": {"code": 429, "message": "You exceeded your current quota, please check your plan and billing details.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_429_quota.json.return_value = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota, please check your plan and billing details.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RESOURCE_EXHAUSTED",
                }
            ],
        }
    }

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return mock_429_quota

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    # CRITICAL INVARIANT: Hard quota must stop promptly after exactly 1 attempt (NO RETRIES!)
    assert call_count == 1
    assert res.provider_source == "deterministic_fallback"
    assert res.classification == "likely_out_of_scope"
    assert res.matched_scope_item_id == "item-scope-42"
    assert "quota exhausted / billing restriction" in (res.missing_evidence_notes or "")
    assert "exceeded your current quota" in (res.missing_evidence_notes or "")


@pytest.mark.asyncio
async def test_gemini_temporary_429_retries_and_succeeds():
    """Temporary rate limit 429 retries with delay and succeeds when attempt 2 returns 200 OK."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-scope-42",
            "item_type": "exclusion",
            "description": "Customer accounts and order history functionality are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
        }
    ]

    mock_429_transient = MagicMock(spec=httpx.Response)
    mock_429_transient.status_code = 429
    mock_429_transient.headers = {}
    mock_429_transient.text = '{"error": {"code": 429, "message": "Rate limit exceeded. Too many requests.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_429_transient.json.return_value = {
        "error": {
            "code": 429,
            "message": "Rate limit exceeded. Too many requests.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RATE_LIMIT_EXCEEDED",
                },
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "0.5s",
                },
            ],
        }
    }

    mock_200 = MagicMock(spec=httpx.Response)
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "classification": "likely_out_of_scope",
                                "explanation": "Order history is excluded per Exclusion 4.2.",
                                "confidence": 0.95,
                                "matched_scope_item_id": "item-scope-42",
                                "matched_clause_id": "Exclusion 4.2",
                                "supporting_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
                                "estimated_extra_hours": 5.0,
                            })
                        }
                    ]
                }
            }
        ]
    }

    call_count = 0
    sleep_calls = []

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_429_transient
        return mock_200

    async def mock_sleep(d):
        sleep_calls.append(d)

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", side_effect=mock_sleep):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    assert call_count == 2
    assert len(sleep_calls) == 1
    # Slept at least 0.5s retry delay + jitter
    assert sleep_calls[0] >= 0.5
    assert res.provider_source == "gemini_live"
    assert res.classification == "likely_out_of_scope"
    assert res.matched_scope_item_id == "item-scope-42"
    assert res.estimated_extra_hours == 5.0


@pytest.mark.asyncio
async def test_gemini_persistent_temporary_429_exhausts_retries_and_falls_back():
    """Persistent temporary 429 retries all max_attempts before falling back honestly to deterministic engine."""
    provider = GeminiProvider(api_key="valid-mock-key")
    engine = ScopeAIEngine()
    engine.provider = provider

    sample_scope_items = [
        {
            "id": "item-scope-42",
            "item_type": "exclusion",
            "description": "Customer accounts and order history functionality are excluded.",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
        }
    ]

    mock_429_transient = MagicMock(spec=httpx.Response)
    mock_429_transient.status_code = 429
    mock_429_transient.headers = {}
    mock_429_transient.text = '{"error": {"code": 429, "message": "Rate limit exceeded. Too many requests.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_429_transient.json.return_value = {
        "error": {
            "code": 429,
            "message": "Rate limit exceeded. Too many requests.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RATE_LIMIT_EXCEEDED",
                }
            ],
        }
    }

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return mock_429_transient

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("asyncio.sleep", return_value=None):
        res = await engine.analyze_request(
            message_text="Can we also add a customer order-history page?",
            scope_items=sample_scope_items,
            default_rate=2000.0,
        )

    # Invariant: retries all 4 attempts when error is temporary
    assert call_count == 4
    assert res.provider_source == "deterministic_fallback"
    assert res.classification == "likely_out_of_scope"
    assert res.matched_scope_item_id == "item-scope-42"
    assert "rate limit exceeded after 4 attempts" in (res.missing_evidence_notes or "").lower()


@pytest.mark.asyncio
async def test_api_endpoint_handles_hard_quota_gracefully():
    """Verify that the FastAPI analyze endpoint handles Gemini hard quota 429 gracefully with deterministic fallback."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # 1. Create a test project
    p_res = client.post("/api/projects", json={
        "name": "Quota Test Project",
        "client_name": "Quota Client",
        "currency": "USD",
        "default_hourly_rate": 150.0,
    })
    assert p_res.status_code == 201
    proj_id = p_res.json()["id"]

    # 2. Add an exclusion scope item
    s_res = client.post(f"/api/projects/{proj_id}/scope", json={
        "item_type": "exclusion",
        "description": "Payment gateways and checkout integrations are strictly excluded.",
        "source_clause_id": "Clause 3.1",
        "source_quote": "Payment gateways and checkout integrations are strictly excluded.",
        "review_status": "confirmed",
    })
    assert s_res.status_code == 201

    # 3. Add client request
    r_res = client.post(f"/api/projects/{proj_id}/requests", json={
        "message_text": "Please integrate Stripe checkout with Apple Pay.",
    })
    assert r_res.status_code == 201

    mock_429 = MagicMock(spec=httpx.Response)
    mock_429.status_code = 429
    mock_429.headers = {}
    mock_429.text = '{"error": {"code": 429, "message": "You exceeded your current quota, please check your plan and billing details.", "status": "RESOURCE_EXHAUSTED"}}'
    mock_429.json.return_value = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota, please check your plan and billing details.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "RESOURCE_EXHAUSTED",
                }
            ],
        }
    }

    call_count = 0

    async def mock_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return mock_429

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch.object(ai_engine.provider, "api_key", "test-mock-api-key"):
        analyze_res = client.post(f"/api/projects/{proj_id}/analyze")
        assert analyze_res.status_code == 200
        findings = analyze_res.json()
        assert len(findings) >= 1
        finding = findings[0]
        assert finding["provider_source"] == "deterministic_fallback"
        assert finding["classification"] == "likely_out_of_scope"
        notes = " ".join([str(ref.get("notes") or "") for ref in finding.get("evidence_references", [])])
        assert "quota" in notes.lower()
