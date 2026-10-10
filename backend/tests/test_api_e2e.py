import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "gemini_configured" in data

def test_full_project_workflow():
    # 1. Create project
    proj_res = client.post("/api/projects", json={
        "name": "E2E Test Project",
        "client_name": "Acme Corp",
        "currency": "USD",
        "default_hourly_rate": 100.0,
    })
    assert proj_res.status_code == 201
    project = proj_res.json()
    proj_id = project["id"]

    # 2. Add manual scope item
    scope_res = client.post(f"/api/projects/{proj_id}/scope", json={
        "item_type": "exclusion",
        "description": "Native mobile iOS/Android app is excluded",
        "normalized_description": "Mobile app excluded",
        "source_clause_id": "Clause 4.1",
        "source_quote": "Native iOS and Android apps are excluded from deliverables.",
        "review_status": "confirmed",
    })
    assert scope_res.status_code == 201

    # 3. Add client request
    req_res = client.post(f"/api/projects/{proj_id}/requests", json={
        "message_text": "Can you also build an iOS native mobile app?",
        "sender": "John Doe",
    })
    assert req_res.status_code == 201
    req_data = req_res.json()

    # 4. Run Analysis
    analyze_res = client.post(f"/api/projects/{proj_id}/analyze", json={
        "request_ids": [req_data["id"]],
    })
    assert analyze_res.status_code == 200
    findings = analyze_res.json()
    assert len(findings) >= 1
    finding_id = findings[0]["id"]

    # 5. Review Finding
    patch_finding = client.patch(f"/api/findings/{finding_id}", json={
        "review_status": "approved",
        "reviewer_notes": "Client acknowledged mobile app is out of scope.",
        "estimated_extra_hours": 40.0,
    })
    assert patch_finding.status_code == 200
    assert patch_finding.json()["review_status"] == "approved"

    # 6. Check Financial Impact
    impact_res = client.get(f"/api/projects/{proj_id}/impact")
    assert impact_res.status_code == 200
    impact = impact_res.json()
    assert impact["potential_unapproved_hours"] == 40.0
    assert impact["potential_unapproved_value"] == 4000.0  # 40 * 100

    # 7. Create Change Order
    co_res = client.post(f"/api/projects/{proj_id}/change-orders", json={
        "title": "Change Order: Native iOS Application",
        "finding_ids": [finding_id],
        "tax_rate_percent": 10.0,
    })
    assert co_res.status_code == 201
    co = co_res.json()
    assert co["subtotal"] == 4000.0
    assert co["taxes"] == 400.0
    assert co["total"] == 4400.0
    co_id = co["id"]

    # 8. Export PDF
    pdf_res = client.get(f"/api/change-orders/{co_id}/export")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 500

    # 9. Verify Audit Trail
    audit_res = client.get(f"/api/projects/{proj_id}/audit")
    assert audit_res.status_code == 200
    trail = audit_res.json()
    assert len(trail) >= 3
    event_types = [t["event_type"] for t in trail]
    assert "project_created" in event_types
    assert "change_order_created" in event_types

def test_seed_demo_endpoint():
    res = client.post("/api/projects/demo/seed?force=true")
    assert res.status_code == 200
    demo = res.json()
    assert demo["name"] == "Northstar Website Redesign"
    assert demo["client_name"] == "Northstar Studio"
    assert demo["currency"] == "INR"
    assert demo["default_hourly_rate"] == 2000.0

    # Check that findings exist
    findings_res = client.get(f"/api/projects/{demo['id']}/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) == 4

    # Check that impact matches synthetic specifications
    # (Stripe 16,000 + Order history 10,000 = 26,000 total unapproved exposure)
    impact_res = client.get(f"/api/projects/{demo['id']}/impact")
    assert impact_res.status_code == 200
    impact = impact_res.json()
    assert impact["potential_unapproved_value"] == 26000.0
    assert impact["potential_unapproved_hours"] == 13.0
