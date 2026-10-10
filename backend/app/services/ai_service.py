import os
import json
import logging
import re
import time
import random
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field

from backend.app.config import settings

logger = logging.getLogger(__name__)

# Pydantic Schemas for AI Structured Extraction and Analysis
class ExtractedScopeItem(BaseModel):
    item_type: str = Field(..., description="deliverable, exclusion, revision_limit, milestone, commercial_term, ambiguous")
    description: str
    normalized_description: str
    source_clause_id: Optional[str] = None
    source_quote: Optional[str] = None
    page_number: Optional[int] = None
    section_reference: Optional[str] = None

class ContractScopeExtractionResult(BaseModel):
    items: List[ExtractedScopeItem]
    summary: str
    extraction_notes: Optional[str] = None

class RequestAnalysisResult(BaseModel):
    classification: str = Field(..., description="likely_in_scope, likely_out_of_scope, ambiguous")
    explanation: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    matched_scope_item_id: Optional[str] = None
    matched_clause_id: Optional[str] = None
    supporting_quote: Optional[str] = None
    section_reference: Optional[str] = None
    page_number: Optional[int] = None
    missing_evidence_notes: Optional[str] = None
    estimated_extra_hours: Optional[float] = None
    provider_source: str = "gemini_live"  # "gemini_live" or "deterministic_fallback"

class GeminiProvider:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        thinking_level: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = float(timeout or settings.GEMINI_TIMEOUT_SECONDS)
        # Validate thinking level: supported values for gemini-3.8-flash are 'low', 'medium', 'high'; 'minimal' is unsupported
        raw_level = (thinking_level or settings.GEMINI_THINKING_LEVEL or "low").strip().lower()
        if raw_level in ("low", "medium", "high"):
            self.thinking_level = raw_level
        else:
            self.thinking_level = "low"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    @staticmethod
    def _parse_duration(val: Any) -> Optional[float]:
        """Parse duration strings like '2.5s', '10s' or numbers into seconds."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            v = val.strip().lower()
            if v.endswith("s"):
                v = v[:-1]
            try:
                return float(v)
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def parse_error_response(response: httpx.Response) -> Dict[str, Any]:
        """
        Parses Google Gemini API's structured error response and HTTP headers.
        Extracts code, status, message, detailed reasons, retryDelay, and determines
        if the error represents hard quota exhaustion / billing restrictions vs temporary rate limiting.
        Never exposes API keys or sensitive authorization headers.
        """
        status_code = response.status_code
        error_code = status_code
        status_str = ""
        message = ""
        reasons = []
        retry_delay = None

        # Check standard Retry-After header
        retry_after_hdr = response.headers.get("Retry-After")
        if retry_after_hdr:
            try:
                retry_delay = float(retry_after_hdr.strip())
            except (ValueError, TypeError):
                pass

        # Try parsing JSON error structure
        try:
            body = response.json()
            if isinstance(body, dict):
                err = body.get("error", {})
                if isinstance(err, dict):
                    error_code = err.get("code", status_code)
                    message = err.get("message", "")
                    status_str = err.get("status", "")
                    details = err.get("details", [])
                    if isinstance(details, list):
                        for detail in details:
                            if not isinstance(detail, dict):
                                continue
                            dtype = str(detail.get("@type", ""))
                            # ErrorInfo (contains reason, domain, metadata)
                            if "ErrorInfo" in dtype:
                                r = detail.get("reason")
                                if r:
                                    reasons.append(str(r))
                            # RetryInfo (contains retryDelay duration string like '2.5s')
                            elif "RetryInfo" in dtype:
                                raw_delay = detail.get("retryDelay")
                                if raw_delay is not None:
                                    parsed_d = GeminiProvider._parse_duration(raw_delay)
                                    if parsed_d is not None:
                                        retry_delay = parsed_d
                            # QuotaFailure (contains violations)
                            elif "QuotaFailure" in dtype:
                                violations = detail.get("violations", [])
                                for v in violations:
                                    if isinstance(v, dict) and v.get("description"):
                                        reasons.append(str(v["description"]))
        except Exception:
            # Fallback to plain text if not valid JSON
            message = response.text[:300] if response.text else f"HTTP {status_code}"

        if not message:
            message = response.text[:300] if response.text else f"HTTP {status_code}"

        # Clean / sanitize message
        sanitized_msg = message.replace("\n", " ").strip()

        # Hard quota & billing restriction indicators
        msg_lower = sanitized_msg.lower()
        hard_quota_keywords = [
            "exceeded your current quota",
            "check your plan and billing",
            "billing details",
            "quota exceeded",
            "insufficient quota",
            "billing not enabled",
            "account has been disabled",
            "quota has been exhausted",
            "daily quota",
            "free tier quota",
        ]
        hard_quota_reasons = {
            "QUOTA_EXCEEDED",
            "BILLING_DISABLED",
            "BILLING_NOT_FOUND",
            "BILLING_ACCOUNT_DISABLED",
            "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
        }

        is_hard_quota = False
        if any(kw in msg_lower for kw in hard_quota_keywords):
            is_hard_quota = True
        elif any(r.upper() in hard_quota_reasons for r in reasons):
            is_hard_quota = True

        return {
            "status_code": status_code,
            "error_code": error_code,
            "status": status_str,
            "message": sanitized_msg,
            "reasons": reasons,
            "is_hard_quota": is_hard_quota,
            "retry_delay": retry_delay,
        }

    async def call_gemini_json(self, prompt: str, system_instruction: str = "") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Call Gemini REST API with JSON response enforcement and thinkingConfig for Gemini 3.8 Flash.
        Implements bounded retries with exponential backoff and jitter for transient errors:
        - HTTP 503 (High demand spikes / Service Unavailable)
        - HTTP 429 (Temporary rate limiting, respecting RetryInfo.retryDelay or Retry-After)
        - HTTP 502 / 504 (Bad Gateway / Gateway Timeout)
        - httpx.TimeoutException / httpx.ConnectError
        
        Permanent errors fail immediately without retrying:
        - Confirmed quota exhaustion / billing restriction (HTTP 429 with hard quota)
        - HTTP 400, 401, 403, 404
        - JSON decode errors
        
        Safely logs HTTP status and attempt counts without logging API keys or headers.
        """
        if not self.is_configured():
            return None, "GEMINI_API_KEY is not configured"

        # Pass API key strictly in header to avoid exposing credentials in URLs or proxy logs
        url = self.api_url
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        # Build generationConfig: remove legacy sampling parameters (temperature, top_p, top_k)
        # Configure thinkingConfig with validated thinking level ('low', 'medium', or 'high')
        generation_config: Dict[str, Any] = {
            "responseMimeType": "application/json",
            "thinkingConfig": {
                "thinkingLevel": self.thinking_level,
            },
        }

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        max_attempts = 4
        base_delay = 1.0
        max_delay = 8.0
        start_time = time.monotonic()

        for attempt in range(max_attempts):
            elapsed = time.monotonic() - start_time
            remaining_time = max(0.0, self.timeout - elapsed)
            if remaining_time <= 1.0:
                logger.warning(
                    f"Gemini API request timed out before attempt {attempt + 1}: "
                    f"elapsed {elapsed:.1f}s reached timeout budget of {self.timeout}s"
                )
                return None, f"Gemini API request deadline exceeded ({elapsed:.1f}s >= {self.timeout}s)"

            req_timeout = min(self.timeout, remaining_time)

            try:
                logger.info(f"Gemini API request attempt {attempt + 1}/{max_attempts} for model '{self.model}'...")
                async with httpx.AsyncClient(timeout=req_timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                # HTTP 429: Distinguish hard quota / billing restriction from temporary rate limit
                if response.status_code == 429:
                    err_info = self.parse_error_response(response)
                    if err_info["is_hard_quota"]:
                        # Confirmed hard quota or billing restriction -> halt retries immediately
                        msg_snippet = err_info["message"][:180]
                        logger.warning(
                            f"Gemini API quota exhausted / billing restriction confirmed on attempt {attempt + 1}/{max_attempts} "
                            f"(status={err_info['status'] or 'RESOURCE_EXHAUSTED'}, message='{msg_snippet}'). "
                            f"Halting retries immediately to preserve responsiveness."
                        )
                        return None, f"Gemini API quota exhausted / billing restriction: {msg_snippet}"
                    else:
                        # Temporary rate limiting -> retry with bounded backoff respecting retryDelay
                        logger.warning(
                            f"Transient rate limit (HTTP 429) received from Gemini API on attempt {attempt + 1}/{max_attempts} "
                            f"for model '{self.model}'. Reasons: {err_info['reasons'] or ['RATE_LIMIT_EXCEEDED']}, "
                            f"retryDelay: {err_info['retry_delay']}s."
                        )
                        if attempt < max_attempts - 1:
                            calculated_backoff = base_delay * (2 ** attempt)
                            if err_info["retry_delay"] is not None and err_info["retry_delay"] > 0:
                                backoff = min(max(err_info["retry_delay"], calculated_backoff), max_delay)
                            else:
                                backoff = min(calculated_backoff, max_delay)
                            jitter = random.uniform(0.1, 0.4)
                            delay = backoff + jitter

                            now_elapsed = time.monotonic() - start_time
                            if (self.timeout - now_elapsed) <= (delay + 1.0):
                                logger.warning(
                                    f"Insufficient time budget for retry ({self.timeout - now_elapsed:.1f}s remaining, need {delay:.1f}s). Aborting retries."
                                )
                                return None, f"Gemini API rate limit exceeded timeout budget ({err_info['message'][:180]})"

                            logger.info(f"Retrying Gemini API in {delay:.2f}s (backoff={backoff:.1f}s, jitter={jitter:.2f}s)...")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            err_msg = f"Gemini API rate limit exceeded after {max_attempts} attempts: {err_info['message'][:180]}"
                            logger.error(err_msg)
                            return None, err_msg

                # Transient retriable HTTP server statuses (503 high demand spike, 502/504 gateway)
                if response.status_code in (503, 502, 504):
                    logger.warning(
                        f"Transient HTTP {response.status_code} received from Gemini API on attempt {attempt + 1}/{max_attempts} "
                        f"for model '{self.model}'."
                    )
                    if attempt < max_attempts - 1:
                        backoff = min(base_delay * (2 ** attempt), max_delay)
                        jitter = random.uniform(0.1, 0.4)
                        delay = backoff + jitter

                        now_elapsed = time.monotonic() - start_time
                        if (self.timeout - now_elapsed) <= (delay + 1.0):
                            logger.warning(
                                f"Insufficient time budget for retry ({self.timeout - now_elapsed:.1f}s remaining, need {delay:.1f}s). Aborting retries."
                            )
                            return None, f"Gemini API transient HTTP {response.status_code}: demand spike exceeded timeout budget ({response.text[:200]})"

                        logger.info(f"Retrying Gemini API in {delay:.2f}s (backoff={backoff:.1f}s, jitter={jitter:.2f}s)...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        err_msg = f"Gemini API returned persistent status {response.status_code} after {max_attempts} attempts: {response.text[:200]}"
                        logger.error(err_msg)
                        return None, err_msg

                # Non-retriable client errors (400, 401, 403, 404, etc.)
                if response.status_code != 200:
                    err_msg = f"Gemini API returned non-retriable status {response.status_code}: {response.text[:200]}"
                    logger.error(err_msg)
                    return None, err_msg

                # HTTP 200 OK - Process response
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return None, "No candidate response returned from Gemini"

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return None, "Empty content parts returned from Gemini"

                # Extract the non-thought text part (or last text part)
                text = ""
                for p in parts:
                    if not p.get("thought", False) and "text" in p:
                        text = p["text"]
                        break
                if not text:
                    text = parts[-1].get("text", "")

                if not text:
                    return None, "Empty text in Gemini response"

                # Strip possible markdown code fences if model wrapped JSON
                cleaned_text = text.strip()
                if cleaned_text.startswith("```"):
                    lines = cleaned_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    cleaned_text = "\n".join(lines).strip()

                parsed = json.loads(cleaned_text)
                logger.info(f"Gemini API successfully returned valid JSON response on attempt {attempt + 1}")
                return parsed, None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                err_detail = type(e).__name__
                logger.warning(
                    f"Transient network/timeout error ({err_detail}) on attempt {attempt + 1}/{max_attempts} calling Gemini: {e}"
                )
                if attempt < max_attempts - 1:
                    backoff = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0.1, 0.4)
                    delay = backoff + jitter
                    now_elapsed = time.monotonic() - start_time
                    if (self.timeout - now_elapsed) <= (delay + 1.0):
                        logger.warning("Insufficient time budget for retry after network timeout. Aborting retries.")
                        return None, f"Network timeout calling Gemini API exceeded timeout budget: {err_detail}"
                    logger.info(f"Retrying Gemini API after network/timeout in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    return None, f"Network error calling Gemini API after {max_attempts} attempts: {err_detail}"

            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON from Gemini: {e}")
                return None, f"Malformed JSON from Gemini model: {str(e)}"

            except Exception as e:
                logger.error(f"Unexpected error in Gemini provider: {e}")
                return None, f"Unexpected error calling Gemini: {str(e)}"

        return None, "Exceeded maximum retry attempts calling Gemini API"

# Deterministic Fallback Engine for demo or offline mode
class DeterministicScopeEngine:
    @staticmethod
    def extract_contract_scope(contract_text: str, filename: str) -> ContractScopeExtractionResult:
        """
        Deterministic, rule-based extraction from contract text with exact clause matching.
        Parses actual sections and clauses directly from the input text, extracting
        verbatim quotes from contract_text so all evidence is verifiably grounded.
        """
        lines = [line.strip() for line in contract_text.splitlines() if line.strip()]
        items: List[ExtractedScopeItem] = []
        current_section: Optional[str] = None

        clause_regex = re.compile(
            r'^(?:(?:(?:Section|Clause|Article|Exclusion|Deliverable|Item)\s*([\d\.]+)|([\d\.]+[\d\.]*))\s*[:\.\-]?\s*)(.*)$',
            re.IGNORECASE
        )
        section_regex = re.compile(
            r'^(?:(?:\d+[\.:]|\bSection|\bClause|\bArticle|\bSchedule)\s*[\d\.]*[:\.\-]?\s*)([A-Za-z0-9\s&/,\-]+)$',
            re.IGNORECASE
        )

        for line in lines:
            # Check for section header
            sec_match = section_regex.match(line)
            if sec_match and len(line) < 80 and not line.endswith("."):
                current_section = line
                continue

            # Check for numbered clause
            c_match = clause_regex.match(line)
            if c_match:
                clause_num = c_match.group(1) or c_match.group(2)
                body = c_match.group(3).strip()

                # Determine clause label
                if re.match(r'^(Section|Clause|Article|Exclusion|Deliverable|Item)', line, re.IGNORECASE):
                    prefix = line.split()[0].capitalize()
                    source_clause_id = f"{prefix} {clause_num}"
                else:
                    source_clause_id = f"Clause {clause_num}"

                # Extract title and quote
                if ":" in body:
                    title, desc_body = body.split(":", 1)
                    title = title.strip()
                    desc_body = desc_body.strip()
                    normalized_desc = title
                    description = f"{title}: {desc_body}" if desc_body else title
                    # verbatim quote is the actual text
                    source_quote = desc_body if desc_body else body
                else:
                    normalized_desc = body[:50]
                    description = body
                    source_quote = body

                line_lower = (line + " " + (current_section or "")).lower()
                if any(w in line_lower for w in ["exclusion", "out of scope", "strictly out of scope", "not included", "prohibited", "strictly excluded"]):
                    item_type = "exclusion"
                elif any(w in line_lower for w in ["revision", "revision round", "feedback round", "rounds of revision"]):
                    item_type = "revision_limit"
                elif any(w in line_lower for w in ["rate", "commercial", "hourly", "inr", "usd", "payment terms", "deposit", "billing"]):
                    item_type = "commercial_term"
                elif any(w in line_lower for w in ["milestone", "timeline", "schedule"]):
                    item_type = "milestone"
                else:
                    item_type = "deliverable"

                items.append(ExtractedScopeItem(
                    item_type=item_type,
                    description=description,
                    normalized_description=normalized_desc,
                    source_clause_id=source_clause_id,
                    source_quote=source_quote,
                    section_reference=current_section or "Contract Scope",
                    page_number=1,
                ))

        # Fallback if no structured numbered clauses were detected
        if not items:
            text_lower = contract_text.lower()
            sentences = [s.strip() for s in re.split(r'[.\n]+', contract_text) if len(s.strip()) > 15]

            for s in sentences:
                s_lower = s.lower()
                if any(w in s_lower for w in ["excluded", "out of scope", "not included"]):
                    items.append(ExtractedScopeItem(
                        item_type="exclusion",
                        description=s,
                        normalized_description="Excluded feature",
                        source_clause_id="Exclusion",
                        source_quote=s,
                        section_reference="Exclusions",
                        page_number=1,
                    ))
                elif any(w in s_lower for w in ["revision", "round"]):
                    items.append(ExtractedScopeItem(
                        item_type="revision_limit",
                        description=s,
                        normalized_description="Revision limit",
                        source_clause_id="Revision Terms",
                        source_quote=s,
                        section_reference="Terms",
                        page_number=1,
                    ))
                elif any(w in s_lower for w in ["deliver", "deliverable", "website", "application", "portal", "responsive"]):
                    items.append(ExtractedScopeItem(
                        item_type="deliverable",
                        description=s,
                        normalized_description="Agreed deliverable",
                        source_clause_id="Deliverables",
                        source_quote=s,
                        section_reference="Deliverables",
                        page_number=1,
                    ))

        # Default fallback if contract text is entirely unstructured
        if not items:
            items.append(ExtractedScopeItem(
                item_type="deliverable",
                description="General software development deliverables as specified in agreement.",
                normalized_description="General scope deliverable",
                source_clause_id="Clause 1.0",
                source_quote=contract_text[:120].strip(),
                section_reference="General Terms",
                page_number=1,
            ))

        return ContractScopeExtractionResult(
            items=items,
            summary=f"Extracted {len(items)} baseline scope items directly from {filename} text.",
            extraction_notes="Extracted via deterministic grounded parser with verbatim quotes from contract text."
        )

    @staticmethod
    def analyze_request(
        message_text: str,
        scope_items: List[Dict[str, Any]],
        default_rate: float = 2000.0,
    ) -> RequestAnalysisResult:
        """
        Deterministic, rule-based classification against project scope items.
        Returns verifiable evidence references and explicit confidence.
        Never fabricates nonexistent clauses or IDs.
        """
        msg_lower = message_text.lower()

        # 1. Unrelated / Conversational messages:
        # Check if the message is general talk, greetings, or off-topic without technical keywords
        conversational_phrases = ["weather", "how are you", "hello", "hi there", "good morning", "good afternoon", "coffee", "lunch", "meeting time", "call tomorrow", "when is our sync"]
        tech_keywords = ["stripe", "payment", "checkout", "card", "gateway", "bug", "fix", "nav", "mobile", "button", "color", "design", "page", "portal", "api", "auth", "login", "feature", "build", "create", "database", "backend", "frontend", "form", "revision"]
        
        is_conversational = any(p in msg_lower for p in conversational_phrases)
        has_tech_keyword = any(k in msg_lower for k in tech_keywords)

        if is_conversational and not has_tech_keyword:
            return RequestAnalysisResult(
                classification="ambiguous",
                explanation=f"Client message '{message_text}' is an unrelated communication or general question that does not request technical features or modify contract scope.",
                confidence=0.95,
                matched_scope_item_id=None,
                matched_clause_id=None,
                supporting_quote=None,
                section_reference=None,
                page_number=None,
                missing_evidence_notes="Not a technical project scope change request.",
                estimated_extra_hours=0.0,
                provider_source="deterministic_fallback",
            )

        # 2. Stripe / Payment Checkout
        if any(term in msg_lower for term in ["stripe", "payment", "checkout", "credit card", "gateway", "razorpay", "paypal"]):
            # Look for an exclusion scope item matching payment
            matched_item = next(
                (i for i in scope_items if i.get("item_type") == "exclusion" and any(t in (i.get("description", "") + " " + (i.get("source_quote") or "")).lower() for t in ["payment", "stripe", "checkout", "card", "gateway", "e-commerce", "ecommerce", "merchant"])),
                None
            )
            if matched_item:
                clause_ref = matched_item.get("source_clause_id") or matched_item.get("section_reference") or "Contract Baseline Scope"
                return RequestAnalysisResult(
                    classification="likely_out_of_scope",
                    explanation=f"Client requested payment/checkout integration. Contract {clause_ref} explicitly excludes this: '{matched_item.get('description')}'.",
                    confidence=0.95,
                    matched_scope_item_id=matched_item.get("id"),
                    matched_clause_id=clause_ref,
                    supporting_quote=matched_item.get("source_quote"),
                    section_reference=matched_item.get("section_reference"),
                    page_number=matched_item.get("page_number", 1),
                    estimated_extra_hours=8.0,
                    provider_source="deterministic_fallback",
                )
            else:
                # No payment exclusion found in baseline! Check deliverables or mark ambiguous
                return RequestAnalysisResult(
                    classification="ambiguous",
                    explanation="Client requested payment/checkout functionality, but the confirmed baseline contains neither an inclusion deliverable nor an explicit exclusion clause for payment gateways.",
                    confidence=0.60,
                    matched_scope_item_id=None,
                    matched_clause_id=None,
                    supporting_quote=None,
                    section_reference=None,
                    page_number=None,
                    missing_evidence_notes="No matching contract clause or exclusion found in project baseline; human clarification required.",
                    estimated_extra_hours=None,
                    provider_source="deterministic_fallback",
                )

        # 3. Customer Order History / Dynamic User Portals
        if any(term in msg_lower for term in [
            "order history", "order-history", "user account", "customer account",
            "account page", "profile page", "customer portal", "user portal",
            "login", "portal", "authentication", "dashboard", "sign in", "sign up", "orders"
        ]):
            # Check for exclusion first
            matched_item = next(
                (i for i in scope_items if i.get("item_type") == "exclusion" and any(
                    t in (i.get("description", "") + " " + (i.get("source_quote") or "")).lower()
                    for t in ["portal", "account", "accounts", "history", "login", "user", "users", "auth", "dashboard", "authentication"]
                )),
                None
            )
            if matched_item:
                clause_ref = matched_item.get("source_clause_id") or matched_item.get("section_reference") or "Contract Baseline Scope"
                return RequestAnalysisResult(
                    classification="likely_out_of_scope",
                    explanation=f"Client requested dynamic customer portal/account features, which is explicitly excluded under {clause_ref}: '{matched_item.get('description')}'.",
                    confidence=0.92,
                    matched_scope_item_id=matched_item.get("id"),
                    matched_clause_id=clause_ref,
                    supporting_quote=matched_item.get("source_quote"),
                    section_reference=matched_item.get("section_reference"),
                    page_number=matched_item.get("page_number", 1),
                    estimated_extra_hours=5.0,
                    provider_source="deterministic_fallback",
                )
            # Check for marketing / static deliverable
            deliverable_item = next(
                (i for i in scope_items if any(
                    term in i.get("description", "").lower()
                    for term in ["marketing website", "marketing portal", "five-page", "static website", "brochure", "landing page", "corporate website"]
                )),
                None
            )
            if deliverable_item:
                clause_ref = deliverable_item.get("source_clause_id") or deliverable_item.get("section_reference") or "Contract Baseline Scope"
                return RequestAnalysisResult(
                    classification="likely_out_of_scope",
                    explanation=f"Customer order-history and dynamic account features are dynamic backend functionality absent from the agreed marketing/static website scope ({clause_ref}).",
                    confidence=0.85,
                    matched_scope_item_id=deliverable_item.get("id"),
                    matched_clause_id=clause_ref,
                    supporting_quote=deliverable_item.get("source_quote"),
                    section_reference=deliverable_item.get("section_reference"),
                    page_number=deliverable_item.get("page_number", 1),
                    estimated_extra_hours=5.0,
                    provider_source="deterministic_fallback",
                )
            return RequestAnalysisResult(
                classification="ambiguous",
                explanation="Client requested customer portal/accounts, but no matching deliverable or exclusion clause exists in the baseline.",
                confidence=0.55,
                matched_scope_item_id=None,
                matched_clause_id=None,
                supporting_quote=None,
                missing_evidence_notes="Contract lacks explicit language addressing customer portals.",
                estimated_extra_hours=None,
                provider_source="deterministic_fallback",
            )

        # 4. Mobile Navigation Bug Fix / Responsive Layout
        if any(term in msg_lower for term in ["mobile nav", "mobile navigation", "overlap", "responsive", "bug", "fix", "mobile screen"]):
            matched_item = next((i for i in scope_items if "responsive" in i.get("description", "").lower() or "mobile" in i.get("description", "").lower()), None)
            if matched_item:
                clause_ref = matched_item.get("source_clause_id") or matched_item.get("section_reference") or "Contract Baseline Scope"
                return RequestAnalysisResult(
                    classification="likely_in_scope",
                    explanation=f"Fixing overlapping navigation on mobile devices is covered under the agreed deliverable for responsive layout across screen sizes ({clause_ref}).",
                    confidence=0.85,
                    matched_scope_item_id=matched_item.get("id"),
                    matched_clause_id=clause_ref,
                    supporting_quote=matched_item.get("source_quote"),
                    section_reference=matched_item.get("section_reference"),
                    page_number=matched_item.get("page_number", 1),
                    estimated_extra_hours=0.0,
                    provider_source="deterministic_fallback",
                )
            return RequestAnalysisResult(
                classification="ambiguous",
                explanation="Client requested mobile navigation fix, but responsive deliverables are not explicitly specified in the baseline.",
                confidence=0.60,
                matched_scope_item_id=None,
                matched_clause_id=None,
                supporting_quote=None,
                missing_evidence_notes="No responsive deliverable explicitly found in project baseline.",
                estimated_extra_hours=None,
                provider_source="deterministic_fallback",
            )

        # 5. Button Color / Small Styling Adjustment
        if any(term in msg_lower for term in ["color", "button", "blue", "styling", "font", "css"]):
            matched_item = next((i for i in scope_items if i.get("item_type") == "revision_limit" or "revision" in i.get("description", "").lower()), None)
            if matched_item:
                clause_ref = matched_item.get("source_clause_id") or matched_item.get("section_reference") or "Contract Baseline Scope"
                return RequestAnalysisResult(
                    classification="ambiguous",
                    explanation=f"Changing styling is covered if within agreed revision rounds ({clause_ref}), but billable if revision rounds have been exhausted.",
                    confidence=0.60,
                    matched_scope_item_id=matched_item.get("id"),
                    matched_clause_id=clause_ref,
                    supporting_quote=matched_item.get("source_quote"),
                    section_reference=matched_item.get("section_reference"),
                    page_number=matched_item.get("page_number", 1),
                    missing_evidence_notes="Requires verifying whether the client has already used both agreed revision cycles.",
                    estimated_extra_hours=0.5,
                    provider_source="deterministic_fallback",
                )
            return RequestAnalysisResult(
                classification="ambiguous",
                explanation="Minor design tweak submitted, but contract contains no explicit revision limit clause.",
                confidence=0.55,
                matched_scope_item_id=None,
                matched_clause_id=None,
                supporting_quote=None,
                missing_evidence_notes="Contract lacks explicit revision limit terms.",
                estimated_extra_hours=0.5,
                provider_source="deterministic_fallback",
            )

        # 6. Generic / Unknown request (e.g. "Can you build a native VR game?")
        return RequestAnalysisResult(
            classification="ambiguous",
            explanation=f"Request '{message_text}' cannot be definitively mapped to baseline deliverables or exclusions without additional details.",
            confidence=0.50,
            matched_scope_item_id=None,
            matched_clause_id=None,
            supporting_quote=None,
            section_reference=None,
            missing_evidence_notes="Contract lacks explicit language addressing this specific request; reviewer clarification recommended.",
            estimated_extra_hours=None,
            provider_source="deterministic_fallback",
        )


class ScopeAIEngine:
    def __init__(self):
        self.provider = GeminiProvider()
        self.fallback = DeterministicScopeEngine()

    async def extract_contract_scope(self, contract_text: str, filename: str) -> ContractScopeExtractionResult:
        """
        Extract scope deliverables, exclusions, revisions, and milestones with source quotes.
        Uses Gemini if configured, otherwise falls back to deterministic extraction.
        """
        if not self.provider.is_configured():
            logger.info("Gemini API key not configured; using deterministic baseline extraction.")
            return self.fallback.extract_contract_scope(contract_text, filename)

        prompt = f"""
Analyze the following contract document and extract all scope items into structured JSON.
Filename: {filename}

Contract Content:
\"\"\"
{contract_text[:8000]}
\"\"\"

Extract every item with:
- item_type: exactly one of ["deliverable", "exclusion", "revision_limit", "milestone", "commercial_term", "ambiguous"]
- description: concise description of the commitment or exclusion
- normalized_description: short normalized title
- source_clause_id: e.g. "Clause 2.1" or "Section 4.1" if visible, or null
- source_quote: the exact verbatim sentence from the contract text
- page_number: integer page if discernible, or null
- section_reference: e.g. "Section 2 - Deliverables" or null

Output JSON format:
{{
  "summary": "Brief summary of contract scope",
  "extraction_notes": "Notes on extraction precision",
  "items": [
    {{
      "item_type": "...",
      "description": "...",
      "normalized_description": "...",
      "source_clause_id": "...",
      "source_quote": "...",
      "page_number": 1,
      "section_reference": "..."
    }}
  ]
}}
"""
        system_instruction = "You are an expert legal and scope-change evidence analyst for software contracts. Only quote text that exists verbatim in the contract. Never fabricate clauses or quotations."

        data, err = await self.provider.call_gemini_json(prompt, system_instruction)
        if err or not data or "items" not in data:
            logger.warning(f"Live Gemini extraction failed ({err}); falling back to deterministic extraction.")
            res = self.fallback.extract_contract_scope(contract_text, filename)
            fallback_note = f"Live extraction attempted but fell back: {err}"
            if res.extraction_notes:
                res.extraction_notes = f"{fallback_note} | {res.extraction_notes}"
            else:
                res.extraction_notes = fallback_note
            return res

        try:
            return ContractScopeExtractionResult.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to validate Gemini extraction schema: {e}")
            res = self.fallback.extract_contract_scope(contract_text, filename)
            res.extraction_notes = f"Model output schema validation failed: {e}"
            return res

    async def analyze_request(
        self,
        message_text: str,
        scope_items: List[Dict[str, Any]],
        default_rate: float = 2000.0,
    ) -> RequestAnalysisResult:
        """
        Classify client request against baseline scope items.
        Ensures all cited IDs exist and source references are verifiable.
        """
        if not self.provider.is_configured():
            return self.fallback.analyze_request(message_text, scope_items, default_rate)

        # Prepare scope items context
        scope_context = json.dumps([
            {
                "id": item.get("id"),
                "item_type": item.get("item_type"),
                "description": item.get("description"),
                "source_clause_id": item.get("source_clause_id"),
                "source_quote": item.get("source_quote"),
                "section_reference": item.get("section_reference"),
                "page_number": item.get("page_number"),
            }
            for item in scope_items
        ], indent=2)

        prompt = f"""
Compare the following client message against the confirmed project contract scope baseline.

Client Message:
\"{message_text}\"

Agreed Contract Scope Items:
{scope_context}

Perform an evidence-backed scope analysis:
1. Determine classification: "likely_in_scope", "likely_out_of_scope", or "ambiguous"
2. Provide a clear, objective rationale.
3. Identify which specific scope item (if any) it connects to.
4. If out of scope, estimate additional hours if sensible, or leave null.
5. If ambiguous or missing contract terms, explicitly state missing evidence.

Output JSON format:
{{
  "classification": "likely_in_scope | likely_out_of_scope | ambiguous",
  "explanation": "Clear rationale connecting client message to contract baseline",
  "confidence": 0.85,
  "matched_scope_item_id": "Exact ID from the scope list above, or null",
  "matched_clause_id": "Clause identifier or null",
  "supporting_quote": "Exact verbatim quote from contract or null",
  "section_reference": "Section reference or null",
  "page_number": 1,
  "missing_evidence_notes": "Any missing information or ambiguity, or null",
  "estimated_extra_hours": 5.0
}}
"""
        system_instruction = "You are a deterministic evidence evaluation assistant for freelance software developers. Never invent contract terms or clause identifiers."

        data, err = await self.provider.call_gemini_json(prompt, system_instruction)
        if err or not data:
            logger.warning(f"Live Gemini request analysis failed ({err}); using deterministic fallback.")
            res = self.fallback.analyze_request(message_text, scope_items, default_rate)
            fallback_note = f"Upstream Gemini unavailable ({err}); evaluated via deterministic fallback engine."
            if res.missing_evidence_notes:
                res.missing_evidence_notes = f"{fallback_note} | {res.missing_evidence_notes}"
            else:
                res.missing_evidence_notes = fallback_note
            res.provider_source = "deterministic_fallback"
            return res

        try:
            # Grounding resolution and verification against confirmed project baseline
            valid_id_map = {item["id"]: item for item in scope_items if item.get("id")}
            matched_id = data.get("matched_scope_item_id")

            if matched_id and matched_id in valid_id_map:
                # Direct match by confirmed DB UUID
                matched_item = valid_id_map[matched_id]
                clause_ref = matched_item.get("source_clause_id") or matched_item.get("section_reference") or "Contract Baseline Scope"
                if not data.get("matched_clause_id"):
                    data["matched_clause_id"] = clause_ref
                if not data.get("supporting_quote"):
                    data["supporting_quote"] = matched_item.get("source_quote") or matched_item.get("description")
                if not data.get("section_reference"):
                    data["section_reference"] = matched_item.get("section_reference")
            else:
                # Model may have cited clause identifier, section reference, or verbatim quote rather than DB UUID
                resolved_item = None
                target_clause = data.get("matched_clause_id") or matched_id
                if target_clause:
                    t_str = str(target_clause).strip().lower()
                    resolved_item = next(
                        (i for i in scope_items if (
                            (i.get("source_clause_id") and i.get("source_clause_id").strip().lower() == t_str) or
                            (i.get("section_reference") and i.get("section_reference").strip().lower() == t_str) or
                            (i.get("section_reference") and t_str in i.get("section_reference").strip().lower())
                        )),
                        None
                    )
                if not resolved_item and data.get("supporting_quote"):
                    quote_snippet = data["supporting_quote"].strip().lower()
                    resolved_item = next(
                        (i for i in scope_items if (
                            (i.get("source_quote") and quote_snippet in i["source_quote"].lower()) or
                            (i.get("description") and quote_snippet in i["description"].lower())
                        )),
                        None
                    )

                if resolved_item:
                    clause_ref = resolved_item.get("source_clause_id") or resolved_item.get("section_reference") or "Contract Baseline Scope"
                    data["matched_scope_item_id"] = resolved_item.get("id")
                    data["matched_clause_id"] = clause_ref
                    data["supporting_quote"] = resolved_item.get("source_quote") or resolved_item.get("description")
                    data["section_reference"] = resolved_item.get("section_reference")
                else:
                    if matched_id or data.get("matched_clause_id"):
                        logger.warning(
                            f"Model cited ungrounded scope reference (id={matched_id}, clause={data.get('matched_clause_id')}); setting to None"
                        )
                    data["matched_scope_item_id"] = None
                    data["matched_clause_id"] = None
                    data["supporting_quote"] = None

            data["provider_source"] = "gemini_live"
            return RequestAnalysisResult.model_validate(data)
        except Exception as e:
            logger.warning(f"Pydantic validation of Gemini response failed: {e}")
            res = self.fallback.analyze_request(message_text, scope_items, default_rate)
            res.missing_evidence_notes = f"Schema validation error: {e}"
            res.provider_source = "deterministic_fallback"
            return res

ai_engine = ScopeAIEngine()
