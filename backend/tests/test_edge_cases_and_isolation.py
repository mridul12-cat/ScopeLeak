import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_invalid_contract_upload():
    """Verify that unsupported file types are rejected safely with HTTP 400."""
    proj = client.post("/api/projects", json={
        "name": "Validation Test Project",
        "client_name": "Test Client",
        "currency": "USD",
        "default_hourly_rate": 100.0
    }).json()
    proj_id = proj["id"]

    # Attempt to upload an executable
    bad_file = b"BINARY_EXECUTABLE_CONTENT"
    resp = client.post(
        f"/api/projects/{proj_id}/contracts",
        files={"file": ("malicious_payload.exe", io.BytesIO(bad_file), "application/octet-stream")}
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]

def test_repeated_demo_seeding_is_idempotent():
    """Verify that calling demo seed repeatedly NEVER creates duplicate projects or records."""
    # Seed without force multiple times
    res1 = client.post("/api/projects/demo/seed?force=false")
    assert res1.status_code == 200
    demo1 = res1.json()

    res2 = client.post("/api/projects/demo/seed?force=false")
    assert res2.status_code == 200
    demo2 = res2.json()
    assert demo1["id"] == demo2["id"]

    # Seed with force_reset multiple times
    res3 = client.post("/api/projects/demo/seed?force=true")
    assert res3.status_code == 200
    demo3 = res3.json()

    res4 = client.post("/api/projects/demo/seed?force=true")
    assert res4.status_code == 200
    demo4 = res4.json()

    # Query all projects in database
    projects_res = client.get("/api/projects")
    assert projects_res.status_code == 200
    all_projects = projects_res.json()
    northstar_count = sum(1 for p in all_projects if p["name"] == "Northstar Website Redesign")
    assert northstar_count == 1, f"Expected exactly 1 Northstar project, found {northstar_count}"

def test_cross_project_isolation():
    """Verify that projects, scope items, findings, and financial calculations are 100% isolated."""
    # Create Project A (USD @ $100/hr)
    proj_a = client.post("/api/projects", json={
        "name": "Project Alpha Isolation",
        "client_name": "Alpha Corp",
        "currency": "USD",
        "default_hourly_rate": 100.0
    }).json()
    id_a = proj_a["id"]

    # Create Project B (INR @ ₹2,500/hr)
    proj_b = client.post("/api/projects", json={
        "name": "Project Beta Isolation",
        "client_name": "Beta Corp",
        "currency": "INR",
        "default_hourly_rate": 2500.0
    }).json()
    id_b = proj_b["id"]

    # Add scope item to Alpha only
    scope_a = client.post(f"/api/projects/{id_a}/scope", json={
        "item_type": "deliverable",
        "description": "Alpha Deliverable 1",
        "review_status": "confirmed"
    }).json()

    # Add client request to Beta only
    req_b = client.post(f"/api/projects/{id_b}/requests", json={
        "message_text": "Beta specific feature request",
        "sender": "Beta Client"
    }).json()

    # Check Project A requests
    requests_a = client.get(f"/api/projects/{id_a}/requests").json()
    assert len(requests_a) == 0

    # Check Project B scope
    scope_b = client.get(f"/api/projects/{id_b}/baseline").json()
    assert len(scope_b) == 0

    # Check Project A impact
    impact_a = client.get(f"/api/projects/{id_a}/impact").json()
    assert impact_a["currency"] == "USD"
    assert impact_a["potential_unapproved_value"] == 0.0

    # Check Project B impact
    impact_b = client.get(f"/api/projects/{id_b}/impact").json()
    assert impact_b["currency"] == "INR"
