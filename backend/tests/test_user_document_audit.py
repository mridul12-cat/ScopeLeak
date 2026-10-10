import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.project import Project
from backend.app.models.contract import Contract
from backend.app.models.scope_item import ScopeItem
from backend.app.models.client_request import ClientRequest
from backend.app.models.finding import Finding
from backend.app.models.change_order import ChangeOrder

client = TestClient(app)

SYNTHETIC_CONTRACT_TEXT = """MASTER SERVICES AGREEMENT - ACME WEB PORTAL
Client: Acme Global
Contractor: Apex Development Labs
Date: October 10, 2026

1. DELIVERABLES
1.1 Marketing Portal: Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact.
1.2 Responsive Layout: All website templates shall be responsive and verified on current mobile and desktop screen sizes.

2. REVISIONS & LIMITS
2.1 Feedback Rounds: Contract includes up to two (2) rounds of design revisions. Additional rounds will be billed at standard hourly rates.

3. EXCLUSIONS
3.1 Payment Processing: Payment gateway integration, Stripe checkout, credit card handling, and merchant accounts are strictly excluded from the scope of work.
3.2 Native Applications: Native iOS and Android application binaries are not included in agreed deliverables.

4. COMMERCIAL TERMS
4.1 Hourly Rate: Any additional approved work outside agreed deliverables shall be billed at the agreed hourly rate of $150.
4.2 Payment Terms: Net 14 calendar days upon invoice issuance.
"""

def test_user_document_audit_lifecycle():
    """
    Complete audit test simulating user-provided synthetic contract and client requests
    on a brand new project, verifying evidence grounding, quotation verbatim matching,
    unrelated request handling, human baseline confirmation, and workflow lifecycle.
    """
    # -------------------------------------------------------------
    # STEP 1: Create a brand new project
    # -------------------------------------------------------------
    proj_resp = client.post("/api/projects", json={
        "name": "Acme Web Services Portal",
        "client_name": "Acme Global",
        "currency": "USD",
        "default_hourly_rate": 150.0,
        "description": "Corporate web presence redesign for Acme Global"
    })
    assert proj_resp.status_code == 201
    project_data = proj_resp.json()
    proj_id = project_data["id"]
    assert project_data["name"] == "Acme Web Services Portal"
    assert project_data["default_hourly_rate"] == 150.0

    # -------------------------------------------------------------
    # STEP 2: Upload synthetic contract document
    # -------------------------------------------------------------
    file_bytes = SYNTHETIC_CONTRACT_TEXT.encode("utf-8")
    upload_resp = client.post(
        f"/api/projects/{proj_id}/contracts",
        files={"file": ("Acme_Services_Agreement.txt", io.BytesIO(file_bytes), "text/plain")}
    )
    assert upload_resp.status_code == 201
    contract_data = upload_resp.json()
    contract_id = contract_data["id"]
    assert contract_data["processing_status"] == "extracted"
    assert contract_data["baseline_review_status"] == "pending_review"  # Human confirmation required!
    assert contract_data["extracted_text"] == SYNTHETIC_CONTRACT_TEXT

    # -------------------------------------------------------------
    # STEP 3: Extract proposed baseline scope items
    # -------------------------------------------------------------
    extract_resp = client.post(f"/api/projects/{proj_id}/baseline/extract", json={
        "contract_id": contract_id
    })
    assert extract_resp.status_code == 200
    scope_items = extract_resp.json()
    assert len(scope_items) >= 4

    # Verify baseline requires human confirmation (all initial items are pending)
    for item in scope_items:
        assert item["review_status"] == "pending"

    # Find the payment exclusion item
    payment_exclusion = next(
        (i for i in scope_items if i["item_type"] == "exclusion" and "payment" in i["description"].lower()),
        None
    )
    assert payment_exclusion is not None, "Payment exclusion was not extracted from uploaded contract"
    
    # VERIFY EVIDENCE GROUNDING: Quoted text must exist verbatim in uploaded source!
    quoted_text = payment_exclusion["source_quote"]
    assert quoted_text is not None and len(quoted_text) > 10
    assert quoted_text in SYNTHETIC_CONTRACT_TEXT, f"Quotation '{quoted_text}' is not present in contract!"
    assert "3.1" in (payment_exclusion["source_clause_id"] or "")

    # -------------------------------------------------------------
    # STEP 4: Human Review & Baseline Confirmation
    # -------------------------------------------------------------
    confirm_resp = client.patch(f"/api/projects/{proj_id}/baseline", json={
        "confirm_all": True
    })
    assert confirm_resp.status_code == 200
    confirmed_items = confirm_resp.json()
    assert all(i["review_status"] == "confirmed" for i in confirmed_items)

    # -------------------------------------------------------------
    # STEP 5: Submit Client Requests
    # -------------------------------------------------------------
    # Request A: Stripe checkout request (should be classified as out of scope matching 3.1)
    req_a_resp = client.post(f"/api/projects/{proj_id}/requests", json={
        "message_text": "Hi team, can we integrate Stripe checkout and credit card processing on the website?",
        "sender": "Alice (Client PM)",
        "external_source": "slack"
    })
    assert req_a_resp.status_code == 201
    req_a = req_a_resp.json()

    # Request B: Unrelated conversational message (MUST NOT be classified as out of scope)
    req_b_resp = client.post(f"/api/projects/{proj_id}/requests", json={
        "message_text": "What is the weather today in San Francisco?",
        "sender": "Alice (Client PM)",
        "external_source": "slack"
    })
    assert req_b_resp.status_code == 201
    req_b = req_b_resp.json()

    # Request C: Ambiguous request with insufficient baseline evidence
    req_c_resp = client.post(f"/api/projects/{proj_id}/requests", json={
        "message_text": "Can you build an interactive VR metaverse experience for our launch?",
        "sender": "Alice (Client PM)",
        "external_source": "email"
    })
    assert req_c_resp.status_code == 201
    req_c = req_c_resp.json()

    # -------------------------------------------------------------
    # STEP 6: Run Evidence Analysis
    # -------------------------------------------------------------
    analyze_resp = client.post(f"/api/projects/{proj_id}/analyze", json={
        "request_ids": [req_a["id"], req_b["id"], req_c["id"]]
    })
    assert analyze_resp.status_code == 200
    findings = analyze_resp.json()
    assert len(findings) == 3

    finding_map = {f["request_id"]: f for f in findings}

    # Verify Finding A (Stripe checkout)
    finding_a = finding_map[req_a["id"]]
    assert finding_a["classification"] == "likely_out_of_scope"
    assert finding_a["scope_item_id"] == payment_exclusion["id"]
    assert finding_a["provider_source"] in ("gemini_live", "deterministic_fallback")
    assert finding_a["estimated_extra_hours"] is not None and finding_a["estimated_extra_hours"] > 0
    # Verifiable evidence quotation exists in extracted source:
    ev_a = finding_a["evidence_references"][0]
    assert ev_a["quote"] in SYNTHETIC_CONTRACT_TEXT
    assert "3.1" in ev_a["ref"]

    # Verify Finding B (Unrelated weather question)
    finding_b = finding_map[req_b["id"]]
    assert finding_b["classification"] == "ambiguous"
    assert finding_b["scope_item_id"] is None
    assert finding_b["estimated_extra_hours"] in (0.0, None)
    assert "unrelated" in finding_b["explanation"].lower() or "communication" in finding_b["explanation"].lower()

    # Verify Finding C (Ambiguous VR metaverse experience)
    finding_c = finding_map[req_c["id"]]
    assert finding_c["classification"] == "ambiguous"
    assert finding_c["scope_item_id"] is None
    assert finding_c["evidence_references"][0]["is_missing_or_incomplete"] is True

    # -------------------------------------------------------------
    # STEP 7: Developer Review Decision (Approval for workflow)
    # -------------------------------------------------------------
    review_resp = client.patch(f"/api/findings/{finding_a['id']}", json={
        "review_status": "approved",
        "reviewer_notes": "Scope change confirmed by developer. Excluded per Section 3.1.",
        "estimated_extra_hours": 10.0,
        "actor": "Lead Architect"
    })
    assert review_resp.status_code == 200
    reviewed_finding = review_resp.json()
    assert reviewed_finding["review_status"] == "approved"
    assert reviewed_finding["estimated_extra_hours"] == 10.0
    assert reviewed_finding["estimated_value"] == 1500.0  # 10 hrs * $150

    # -------------------------------------------------------------
    # STEP 8: Create and Link Work Item
    # -------------------------------------------------------------
    work_resp = client.post(f"/api/projects/{proj_id}/work", json={
        "source_type": "git_commit",
        "description": "feat(checkout): implement Stripe checkout integration and webhook handler",
        "actual_hours": 10.0,
        "request_id": req_a["id"],
        "approval_status": "pending_client_approval"
    })
    assert work_resp.status_code == 201
    work_data = work_resp.json()

    # Link work item to finding
    link_resp = client.patch(f"/api/findings/{finding_a['id']}", json={
        "linked_work_item_ids": [work_data["id"]]
    })
    assert link_resp.status_code == 200

    # -------------------------------------------------------------
    # STEP 9: Verify Financial Impact Summary
    # -------------------------------------------------------------
    impact_resp = client.get(f"/api/projects/{proj_id}/impact")
    assert impact_resp.status_code == 200
    impact_data = impact_resp.json()
    assert impact_data["potential_unapproved_hours"] >= 10.0
    assert impact_data["potential_unapproved_value"] >= 1500.0
    assert impact_data["estimated_revenue_at_risk"] >= 1500.0
    assert len(impact_data["breakdown"]) >= 1

    # -------------------------------------------------------------
    # STEP 10: Generate and Export Change Order PDF
    # -------------------------------------------------------------
    co_resp = client.post(f"/api/projects/{proj_id}/change-orders", json={
        "title": "Change Order #01 - Stripe Checkout Integration",
        "scope_summary": "Integration of Stripe checkout session and payment processing per client request.",
        "line_items": [
            {
                "title": "Stripe Gateway Integration",
                "description": "Checkout session creation, webhook listening, and receipt handling.",
                "hours": 10.0,
                "rate": 150.0,
                "line_total": 1500.0,
                "source_finding_id": finding_a["id"],
                "source_work_item_id": work_data["id"]
            }
        ],
        "notes": "Payment terms: Net 14 days upon delivery."
    })
    assert co_resp.status_code == 201
    co_data = co_resp.json()
    co_id = co_data["id"]
    assert co_data["status"] == "draft"
    assert co_data["total"] == 1500.0

    # Download PDF
    pdf_resp = client.get(f"/api/change-orders/{co_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-"), "Generated change order is not a valid PDF"
    assert len(pdf_resp.content) > 1000

    # -------------------------------------------------------------
    # STEP 11: Verify Persistence Across Database Reload
    # -------------------------------------------------------------
    db = SessionLocal()
    try:
        persisted_proj = db.query(Project).filter(Project.id == proj_id).first()
        assert persisted_proj is not None
        assert persisted_proj.name == "Acme Web Services Portal"

        persisted_contract = db.query(Contract).filter(Contract.id == contract_id).first()
        assert persisted_contract is not None
        assert persisted_contract.baseline_review_status == "confirmed"

        persisted_finding = db.query(Finding).filter(Finding.id == finding_a["id"]).first()
        assert persisted_finding is not None
        assert persisted_finding.review_status == "approved"
        assert persisted_finding.estimated_value == 1500.0

        persisted_co = db.query(ChangeOrder).filter(ChangeOrder.id == co_id).first()
        assert persisted_co is not None
        assert persisted_co.total == 1500.0
    finally:
        db.close()
