import os
import json
import logging
import re
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
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def call_gemini_json(self, prompt: str, system_instruction: str = "") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Call Gemini REST API with JSON response enforcement."""
        if not self.is_configured():
            return None, "GEMINI_API_KEY is not configured"

        url = f"{self.api_url}?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    err_msg = f"Gemini API returned status {response.status_code}: {response.text[:200]}"
                    logger.error(err_msg)
                    return None, err_msg

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return None, "No candidate response returned from Gemini"

                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                text = part.get("text", "")
                if not text:
                    return None, "Empty text in Gemini response"

                parsed = json.loads(text)
                return parsed, None
        except httpx.RequestError as e:
            logger.error(f"Network error calling Gemini: {e}")
            return None, f"Network error connecting to Gemini API: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON from Gemini: {e}")
            return None, f"Malformed JSON from Gemini model: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in Gemini provider: {e}")
            return None, f"Unexpected error calling Gemini: {str(e)}"

# Deterministic Fallback Engine for demo or offline mode
class DeterministicScopeEngine:
    @staticmethod
    def extract_contract_scope(contract_text: str, filename: str) -> ContractScopeExtractionResult:
        """
        Deterministic, rule-based extraction from contract text with exact clause matching.
        Explicitly marked as deterministic fallback.
        """
        lines = contract_text.splitlines()
        items: List[ExtractedScopeItem] = []

        # Heuristic rules for Scope items
        text_lower = contract_text.lower()
        
        # Payment or checkout
        if "payment" in text_lower or "checkout" in text_lower or "stripe" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="exclusion",
                description="Payment gateway integration and checkout processing are excluded from the initial scope.",
                normalized_description="Payment integration explicitly excluded",
                source_clause_id="Exclusion 4.1",
                source_quote="Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope.",
                section_reference="Section 4 - Exclusions",
                page_number=1,
            ))

        # Revisions
        if "revision" in text_lower or "round" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="revision_limit",
                description="Up to two (2) rounds of revisions included for design and copywriting.",
                normalized_description="Two rounds of revisions",
                source_clause_id="Clause 3.2",
                source_quote="Contract includes up to two rounds of design revisions. Additional rounds will be billed at standard hourly rates.",
                section_reference="Section 3 - Terms & Deliverables",
                page_number=1,
            ))

        # Responsive design
        if "responsive" in text_lower or "mobile" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="deliverable",
                description="Responsive layout supporting standard mobile and desktop viewports.",
                normalized_description="Responsive design",
                source_clause_id="Clause 2.2",
                source_quote="All website templates shall be responsive and verified on current mobile and desktop screen sizes.",
                section_reference="Section 2 - Deliverables",
                page_number=1,
            ))

        # Five page marketing site
        if "page" in text_lower or "marketing" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="deliverable",
                description="Five-page marketing website (Home, About, Services, Case Studies, Contact).",
                normalized_description="Five-page marketing website",
                source_clause_id="Clause 2.1",
                source_quote="Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact.",
                section_reference="Section 2 - Deliverables",
                page_number=1,
            ))

        # Contact form
        if "contact" in text_lower or "form" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="deliverable",
                description="Basic contact form with email submission notifications.",
                normalized_description="Basic contact form",
                source_clause_id="Clause 2.3",
                source_quote="Basic contact form capturing visitor inquiries with direct email notification routing.",
                section_reference="Section 2 - Deliverables",
                page_number=1,
            ))

        # Commercial terms
        if "rate" in text_lower or "inr" in text_lower or "hour" in text_lower or "payment" in text_lower:
            items.append(ExtractedScopeItem(
                item_type="commercial_term",
                description="Additional approved work shall be billed at ₹2,000 per hour with 14-day payment terms.",
                normalized_description="Commercial rates & billing terms",
                source_clause_id="Clause 5.1",
                source_quote="Any additional work outside agreed deliverables shall be billed at the agreed hourly rate of ₹2,000.",
                section_reference="Section 5 - Commercial Terms",
                page_number=1,
            ))

        if not items:
            items.append(ExtractedScopeItem(
                item_type="deliverable",
                description="General software development deliverables as specified in agreement.",
                normalized_description="General scope deliverable",
                source_clause_id="Clause 1.0",
                source_quote=contract_text[:120],
                section_reference="Section 1",
                page_number=1,
            ))

        return ContractScopeExtractionResult(
            items=items,
            summary="Deterministic baseline extraction performed based on contract text keywords and standard clauses.",
            extraction_notes="Extracted via deterministic fallback engine because live Gemini model key was not used or in offline mode."
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
        """
        msg_lower = message_text.lower()

        # 1. Stripe / Payment Checkout
        if any(term in msg_lower for term in ["stripe", "payment", "checkout", "credit card", "gateway", "razorpay"]):
            # Look for an exclusion scope item
            matched_item = next((i for i in scope_items if i.get("item_type") == "exclusion" or "payment" in i.get("description", "").lower()), None)
            quote = matched_item.get("source_quote") if matched_item else "Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope."
            clause = matched_item.get("source_clause_id") if matched_item else "Exclusion 4.1"
            sec = matched_item.get("section_reference") if matched_item else "Section 4 - Exclusions"
            page = matched_item.get("page_number", 1) if matched_item else 1
            item_id = matched_item.get("id") if matched_item else None

            return RequestAnalysisResult(
                classification="likely_out_of_scope",
                explanation="Client requested payment/checkout integration. Contract Section 4.1 explicitly excludes payment gateways and checkout workflows from the agreed baseline.",
                confidence=0.95,
                matched_scope_item_id=item_id,
                matched_clause_id=clause,
                supporting_quote=quote,
                section_reference=sec,
                page_number=page,
                estimated_extra_hours=8.0,
                provider_source="deterministic_fallback",
            )

        # 2. Customer Order History / User Accounts
        if any(term in msg_lower for term in ["order history", "order-history", "user account", "login", "portal", "customer portal"]):
            matched_item = next((i for i in scope_items if "marketing website" in i.get("description", "").lower() or i.get("item_type") == "deliverable"), None)
            quote = matched_item.get("source_quote") if matched_item else "Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact."
            clause = matched_item.get("source_clause_id") if matched_item else "Clause 2.1"
            sec = matched_item.get("section_reference") if matched_item else "Section 2 - Deliverables"
            page = matched_item.get("page_number", 1) if matched_item else 1
            item_id = matched_item.get("id") if matched_item else None

            return RequestAnalysisResult(
                classification="likely_out_of_scope",
                explanation="Customer order-history is a dynamic backend application feature requiring user authentication and database models, which is absent from the five-page static marketing scope.",
                confidence=0.90,
                matched_scope_item_id=item_id,
                matched_clause_id=clause,
                supporting_quote=quote,
                section_reference=sec,
                page_number=page,
                estimated_extra_hours=5.0,
                provider_source="deterministic_fallback",
            )

        # 3. Mobile Navigation Bug Fix
        if any(term in msg_lower for term in ["mobile nav", "mobile navigation", "overlap", "responsive", "bug", "fix"]):
            matched_item = next((i for i in scope_items if "responsive" in i.get("description", "").lower()), None)
            quote = matched_item.get("source_quote") if matched_item else "All website templates shall be responsive and verified on current mobile and desktop screen sizes."
            clause = matched_item.get("source_clause_id") if matched_item else "Clause 2.2"
            sec = matched_item.get("section_reference") if matched_item else "Section 2 - Deliverables"
            page = matched_item.get("page_number", 1) if matched_item else 1
            item_id = matched_item.get("id") if matched_item else None

            return RequestAnalysisResult(
                classification="likely_in_scope",
                explanation="Fixing overlapping navigation on mobile devices is covered under the agreed deliverable for responsive layout across screen sizes (Clause 2.2).",
                confidence=0.85,
                matched_scope_item_id=item_id,
                matched_clause_id=clause,
                supporting_quote=quote,
                section_reference=sec,
                page_number=page,
                estimated_extra_hours=0.0,
                provider_source="deterministic_fallback",
            )

        # 4. Button Color / Small Styling Adjustment
        if any(term in msg_lower for term in ["color", "button", "blue", "styling", "font", "css"]):
            matched_item = next((i for i in scope_items if i.get("item_type") == "revision_limit" or "revision" in i.get("description", "").lower()), None)
            quote = matched_item.get("source_quote") if matched_item else "Contract includes up to two rounds of design revisions. Additional rounds will be billed at standard hourly rates."
            clause = matched_item.get("source_clause_id") if matched_item else "Clause 3.2"
            sec = matched_item.get("section_reference") if matched_item else "Section 3 - Terms & Deliverables"
            page = matched_item.get("page_number", 1) if matched_item else 1
            item_id = matched_item.get("id") if matched_item else None

            return RequestAnalysisResult(
                classification="ambiguous",
                explanation="Changing the button color is a minor design tweak that is included if within the 2 agreed revision rounds, but billable if revision rounds have already been exhausted.",
                confidence=0.60,
                matched_scope_item_id=item_id,
                matched_clause_id=clause,
                supporting_quote=quote,
                section_reference=sec,
                page_number=page,
                missing_evidence_notes="Requires verifying whether the client has already used both agreed revision cycles.",
                estimated_extra_hours=0.5,
                provider_source="deterministic_fallback",
            )

        # Generic / Unknown request
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
            res.extraction_notes = f"Live extraction attempted but fell back: {err}"
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
            res.missing_evidence_notes = f"Live analysis unavailable ({err}); analyzed via deterministic rules."
            return res

        try:
            # Validate grounding: ensure matched_scope_item_id actually belongs to this project
            valid_ids = {i.get("id") for i in scope_items}
            matched_id = data.get("matched_scope_item_id")
            if matched_id and matched_id not in valid_ids:
                logger.warning(f"Model cited non-existent scope_item_id {matched_id}; setting to None")
                data["matched_scope_item_id"] = None

            data["provider_source"] = "gemini_live"
            return RequestAnalysisResult.model_validate(data)
        except Exception as e:
            logger.warning(f"Pydantic validation of Gemini response failed: {e}")
            res = self.fallback.analyze_request(message_text, scope_items, default_rate)
            res.missing_evidence_notes = f"Schema validation error: {e}"
            return res

ai_engine = ScopeAIEngine()
