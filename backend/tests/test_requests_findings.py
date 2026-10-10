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


def test_clause_reference_falls_back_to_section_without_inventing_id():
    """Verify that when a scope item lacks a formal clause ID, it truthfully references the section without inventing an ID."""
    scope_items = [
        {
            "id": "uuid-section-3-exclusion",
            "item_type": "exclusion",
            "description": "Customer accounts and order history: No user authentication, customer dashboard, account management, or order-history feature is included.",
            "source_clause_id": None,  # No numbered clause ID in contract
            "source_quote": "No user authentication, customer dashboard, account management, or order-history feature is included.",
            "section_reference": "Section 3: Explicit Exclusions",
            "page_number": 1,
        }
    ]

    res = DeterministicScopeEngine.analyze_request("Can we also add a customer order-history page?", scope_items)
    assert res.classification == "likely_out_of_scope"
    # Preserves actual confirmed database UUID
    assert res.matched_scope_item_id == "uuid-section-3-exclusion"
    # Human-readable reference uses section without inventing a fake clause ID
    assert res.matched_clause_id == "Section 3: Explicit Exclusions"
    assert res.section_reference == "Section 3: Explicit Exclusions"
    assert res.estimated_extra_hours == 5.0
    # No spurious missing evidence notes on a clear exclusion match
    assert res.missing_evidence_notes is None


def test_ambiguity_warning_distinction_and_financial_calibration(db_session):
    """
    Verify that:
    1. A clear, confirmed exclusion finding does NOT flag is_missing_or_incomplete = True.
    2. A genuinely ambiguous request DOES flag is_missing_or_incomplete = True with explanatory notes.
    3. Financial calibration accurately calculates USD 5/hr * 5 hours = USD 25.
    """
    from backend.app.services.pricing_service import calculate_line_item

    # 1. Financial calibration check
    rate = 5.0
    hours = 5.0
    val = calculate_line_item(hours, rate)
    assert val == 25.0

    # 2. Scope item with section-only reference
    project = Project(name="Custom Rate Project", client_name="Client X", currency="USD", default_hourly_rate=5.0)
    db_session.add(project)
    db_session.commit()

    scope_item = ScopeItem(
        project_id=project.id,
        item_type="exclusion",
        description="Customer accounts and order history: No user authentication, customer dashboard, account management, or order-history feature is included.",
        normalized_description="Customer accounts & order history excluded",
        source_clause_id=None,
        source_quote="No user authentication, customer dashboard, account management, or order-history feature is included.",
        section_reference="Section 3: Explicit Exclusions",
        page_number=1,
        review_status="confirmed"
    )
    db_session.add(scope_item)
    db_session.commit()

    scope_items_dict = [
        {
            "id": scope_item.id,
            "item_type": scope_item.item_type,
            "description": scope_item.description,
            "source_clause_id": scope_item.source_clause_id,
            "source_quote": scope_item.source_quote,
            "section_reference": scope_item.section_reference,
            "page_number": scope_item.page_number,
        }
    ]

    # Test Clear Out-of-Scope Analysis
    res_clear = DeterministicScopeEngine.analyze_request("Can we add customer order-history?", scope_items_dict)
    assert res_clear.classification == "likely_out_of_scope"
    assert res_clear.matched_scope_item_id == scope_item.id
    assert res_clear.matched_clause_id == "Section 3: Explicit Exclusions"

    # Simulate evidence reference creation logic as in findings.py
    has_grounded_evidence = bool(res_clear.matched_scope_item_id or res_clear.supporting_quote)
    is_genuine_ambiguity_clear = (
        res_clear.classification == "ambiguous"
        or not has_grounded_evidence
        or (
            bool(res_clear.missing_evidence_notes)
            and any(kw in res_clear.missing_evidence_notes.lower() for kw in ["lack", "missing", "ambigu", "unclear", "no matching", "clarif"])
            and res_clear.classification not in ("likely_out_of_scope", "likely_in_scope")
        )
    )
    # Clear confirmed exclusion must NOT have contradictory ambiguity warning!
    assert is_genuine_ambiguity_clear is False

    # Test Genuinely Ambiguous Analysis
    res_amb = DeterministicScopeEngine.analyze_request("Can you build an interactive VR metaverse game?", scope_items_dict)
    assert res_amb.classification == "ambiguous"
    assert res_amb.matched_scope_item_id is None

    has_grounded_evidence_amb = bool(res_amb.matched_scope_item_id or res_amb.supporting_quote)
    is_genuine_ambiguity_amb = (
        res_amb.classification == "ambiguous"
        or not has_grounded_evidence_amb
        or (
            bool(res_amb.missing_evidence_notes)
            and any(kw in res_amb.missing_evidence_notes.lower() for kw in ["lack", "missing", "ambigu", "unclear", "no matching", "clarif"])
            and res_amb.classification not in ("likely_out_of_scope", "likely_in_scope")
        )
    )
    # Genuinely ambiguous request MUST have ambiguity warning with explanatory notes!
    assert is_genuine_ambiguity_amb is True
    assert res_amb.missing_evidence_notes is not None
    assert "lacks explicit language" in res_amb.missing_evidence_notes or "clarification" in res_amb.missing_evidence_notes
