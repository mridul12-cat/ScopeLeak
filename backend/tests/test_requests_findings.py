import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.project import Project
from backend.app.models.client_request import ClientRequest
from backend.app.models.scope_item import ScopeItem
from backend.app.models.finding import Finding
from backend.app.models.review_decision import ReviewDecision
from backend.app.services.ai_service import DeterministicScopeEngine
from backend.app.utils.hashing import compute_text_hash

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_request_deduplication(db_session):
    project = Project(name="P", client_name="C")
    db_session.add(project)
    db_session.commit()

    text = "Can you add Stripe checkout?"
    hash1 = compute_text_hash(text)
    hash2 = compute_text_hash("  Can you add Stripe checkout?  ")
    assert hash1 == hash2

    req1 = ClientRequest(project_id=project.id, message_text=text, content_hash=hash1)
    db_session.add(req1)
    db_session.commit()

    # Query by hash
    existing = db_session.query(ClientRequest).filter(
        ClientRequest.project_id == project.id,
        ClientRequest.content_hash == hash2
    ).first()
    assert existing is not None
    assert existing.id == req1.id

def test_finding_classification_and_evidence():
    scope_items = [
        {
            "id": "scope-1",
            "item_type": "exclusion",
            "description": "Payment integration excluded",
            "source_clause_id": "Exclusion 4.1",
            "source_quote": "Payment gateway integration is strictly out of scope.",
            "section_reference": "Section 4",
            "page_number": 1,
        },
        {
            "id": "scope-2",
            "item_type": "deliverable",
            "description": "Responsive layout across mobile screens",
            "source_clause_id": "Clause 2.2",
            "source_quote": "All templates shall be responsive.",
            "section_reference": "Section 2",
            "page_number": 1,
        }
    ]

    # Out of scope test
    res_stripe = DeterministicScopeEngine.analyze_request("Can you add Stripe checkout?", scope_items)
    assert res_stripe.classification == "likely_out_of_scope"
    assert res_stripe.matched_scope_item_id == "scope-1"
    assert res_stripe.matched_clause_id == "Exclusion 4.1"
    assert res_stripe.estimated_extra_hours == 8.0

    # In scope test
    res_nav = DeterministicScopeEngine.analyze_request("Please fix the mobile navigation layout", scope_items)
    assert res_nav.classification == "likely_in_scope"
    assert res_nav.matched_scope_item_id == "scope-2"
    assert res_nav.matched_clause_id == "Clause 2.2"

    # Ambiguous test
    res_amb = DeterministicScopeEngine.analyze_request("Make the button blue", scope_items)
    assert res_amb.classification == "ambiguous"

def test_review_decision_history(db_session):
    project = Project(name="P", client_name="C")
    db_session.add(project)
    db_session.commit()

    req = ClientRequest(project_id=project.id, message_text="Test", content_hash="hash1")
    db_session.add(req)
    db_session.commit()

    finding = Finding(
        project_id=project.id,
        request_id=req.id,
        classification="likely_out_of_scope",
        explanation="Payment excluded",
        review_status="pending"
    )
    db_session.add(finding)
    db_session.commit()

    # User approves
    finding.review_status = "approved"
    finding.reviewer_notes = "Verified with client"
    decision = ReviewDecision(
        finding_id=finding.id,
        actor="Lead Developer",
        decision="approved",
        notes="Verified with client"
    )
    db_session.add(decision)
    db_session.commit()

    decisions = db_session.query(ReviewDecision).filter(ReviewDecision.finding_id == finding.id).all()
    assert len(decisions) == 1
    assert decisions[0].decision == "approved"
    assert decisions[0].actor == "Lead Developer"
