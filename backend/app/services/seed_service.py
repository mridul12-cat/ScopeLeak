from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.models.contract import Contract
from backend.app.models.scope_item import ScopeItem
from backend.app.models.client_request import ClientRequest
from backend.app.models.work_item import WorkItem
from backend.app.models.finding import Finding
from backend.app.models.review_decision import ReviewDecision
from backend.app.models.change_order import ChangeOrder
from backend.app.models.audit_event import AuditEvent
from backend.app.utils.hashing import compute_text_hash

DEMO_PROJECT_NAME = "Northstar Website Redesign"
DEMO_CLIENT_NAME = "Northstar Studio"

def seed_demo_project(db: Session, force_reset: bool = False) -> Project:
    """
    Seed the Northstar Website Redesign demo project with contracts, baseline scope items,
    incoming client messages, work logs, AI evidence findings, and audit history.
    """
    existing_projects = db.query(Project).filter(
        (Project.name == DEMO_PROJECT_NAME) | (Project.client_name == DEMO_CLIENT_NAME)
    ).all()

    if existing_projects:
        if not force_reset:
            return existing_projects[0]
        # Delete all existing demo copies to recreate cleanly
        for p in existing_projects:
            db.delete(p)
        db.commit()

    now = datetime.utcnow()

    # 1. Project
    project = Project(
        name=DEMO_PROJECT_NAME,
        client_name=DEMO_CLIENT_NAME,
        description="Complete redesign and development of Northstar Studio's corporate marketing presence.",
        currency="INR",
        default_hourly_rate=2000.0,
        status="active",
        created_at=now - timedelta(days=14),
        updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. Contract
    contract_text = """MASTER SERVICES AGREEMENT - NORTHSTAR STUDIO REDESIGN
Date: September 1, 2026
Parties: Northstar Studio ("Client") and Lead Developer ("Contractor")

1. OBJECTIVE & GENERAL TERMS
Contractor shall develop and deploy a refreshed corporate presence according to the deliverables specified below.

2. DELIVERABLES
2.1 Marketing Website: Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact.
2.2 Responsive Design: All website templates shall be responsive and verified on current mobile and desktop screen sizes.
2.3 Contact Inquiries: Basic contact form capturing visitor inquiries with direct email notification routing.

3. REVISIONS & LIMITS
3.1 Milestones: Milestone 1 (Design Approval) and Milestone 2 (Staging Deployment).
3.2 Revision Rounds: Contract includes up to two (2) rounds of design revisions. Additional rounds will be billed at standard hourly rates.

4. EXCLUSIONS
4.1 E-Commerce & Payments: Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope.
4.2 Dynamic User Portals: Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.

5. COMMERCIAL TERMS
5.1 Rate: Any additional approved work outside agreed deliverables shall be billed at the agreed hourly rate of ₹2,000.
5.2 Payment: 50% initial deposit, 50% on final delivery within 14 calendar days."""

    contract = Contract(
        project_id=project.id,
        filename="Northstar_Redesign_Agreement_v1.pdf",
        content_hash=compute_text_hash(contract_text),
        extracted_text=contract_text,
        processing_status="extracted",
        baseline_review_status="confirmed",
        uploaded_at=now - timedelta(days=12),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # 3. Scope Items (Reviewed baseline)
    scope_items_data = [
        {
            "item_type": "deliverable",
            "description": "Five-page marketing website (Home, About, Services, Case Studies, Contact).",
            "normalized_description": "Five-page marketing website",
            "source_clause_id": "Clause 2.1",
            "source_quote": "Delivery of a five-page marketing website comprising Home, About, Services, Case Studies, and Contact.",
            "section_reference": "Section 2 - Deliverables",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "deliverable",
            "description": "Responsive layout supporting current mobile and desktop screen viewports.",
            "normalized_description": "Responsive design across devices",
            "source_clause_id": "Clause 2.2",
            "source_quote": "All website templates shall be responsive and verified on current mobile and desktop screen sizes.",
            "section_reference": "Section 2 - Deliverables",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "deliverable",
            "description": "Basic contact form with automated email notification routing.",
            "normalized_description": "Basic contact form",
            "source_clause_id": "Clause 2.3",
            "source_quote": "Basic contact form capturing visitor inquiries with direct email notification routing.",
            "section_reference": "Section 2 - Deliverables",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "revision_limit",
            "description": "Two (2) rounds of revisions included for design and layout.",
            "normalized_description": "Two rounds of revisions",
            "source_clause_id": "Clause 3.2",
            "source_quote": "Contract includes up to two (2) rounds of design revisions. Additional rounds will be billed at standard hourly rates.",
            "section_reference": "Section 3 - Terms & Deliverables",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "exclusion",
            "description": "Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope.",
            "normalized_description": "Payment integration explicitly excluded",
            "source_clause_id": "Exclusion 4.1",
            "source_quote": "Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope.",
            "section_reference": "Section 4 - Exclusions",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "exclusion",
            "description": "Customer accounts, authentication, order history, and backend portal functionality are not included.",
            "normalized_description": "Customer accounts & order history excluded",
            "source_clause_id": "Exclusion 4.2",
            "source_quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
            "section_reference": "Section 4 - Exclusions",
            "page_number": 1,
            "review_status": "confirmed",
        },
        {
            "item_type": "commercial_term",
            "description": "Agreed hourly rate of ₹2,000 for approved out-of-scope work.",
            "normalized_description": "Hourly rate ₹2,000",
            "source_clause_id": "Clause 5.1",
            "source_quote": "Any additional approved work outside agreed deliverables shall be billed at the agreed hourly rate of ₹2,000.",
            "section_reference": "Section 5 - Commercial Terms",
            "page_number": 1,
            "review_status": "confirmed",
        },
    ]

    scope_items = []
    for sid in scope_items_data:
        si = ScopeItem(
            project_id=project.id,
            contract_id=contract.id,
            **sid,
            created_at=now - timedelta(days=12),
        )
        db.add(si)
        scope_items.append(si)
    db.commit()
    for si in scope_items:
        db.refresh(si)

    scope_by_clause = {si.source_clause_id: si for si in scope_items}

    # 4. Client Requests
    requests_data = [
        {
            "message_text": "Can you add Stripe checkout before launch?",
            "sender": "Aarav Mehta (Product Lead)",
            "external_source": "slack",
            "message_timestamp": now - timedelta(days=5, hours=3),
        },
        {
            "message_text": "Can we also add a customer order-history page?",
            "sender": "Priya Sharma (Operations)",
            "external_source": "email",
            "message_timestamp": now - timedelta(days=4, hours=6),
        },
        {
            "message_text": "Please fix the mobile navigation; it currently overlaps the page title.",
            "sender": "Aarav Mehta (Product Lead)",
            "external_source": "slack",
            "message_timestamp": now - timedelta(days=3, hours=1),
        },
        {
            "message_text": "Can you make the existing contact form button blue?",
            "sender": "Sneha Roy (Design QA)",
            "external_source": "slack",
            "message_timestamp": now - timedelta(days=2, hours=4),
        },
    ]

    client_requests = []
    for rd in requests_data:
        cr = ClientRequest(
            project_id=project.id,
            message_text=rd["message_text"],
            sender=rd["sender"],
            external_source=rd["external_source"],
            message_timestamp=rd["message_timestamp"],
            content_hash=compute_text_hash(rd["message_text"]),
            imported_at=now - timedelta(days=2),
        )
        db.add(cr)
        client_requests.append(cr)
    db.commit()
    for cr in client_requests:
        db.refresh(cr)

    # 5. Work Items
    # Stripe checkout: 8 estimated hours, unapproved
    # Order-history: 5 estimated hours, unapproved
    # Mobile nav fix: 1.5 actual hours, logged
    # Button color: 0.5 actual hours, logged
    work_items_data = [
        {
            "request_id": client_requests[0].id,
            "description": "Stripe checkout API integration, webhook handler, and payment status UI",
            "source_type": "timesheet",
            "external_id": "TASK-101",
            "estimated_hours": 8.0,
            "actual_hours": None,
            "hourly_rate": 2000.0,
            "work_status": "planned",
            "approval_status": "unapproved",
            "source_reference": "Estimate provided for Stripe setup",
        },
        {
            "request_id": client_requests[1].id,
            "description": "Customer order-history view, authentication checks, and database query service",
            "source_type": "timesheet",
            "external_id": "TASK-102",
            "estimated_hours": 5.0,
            "actual_hours": None,
            "hourly_rate": 2000.0,
            "work_status": "planned",
            "approval_status": "unapproved",
            "source_reference": "Estimate provided for order history view",
        },
        {
            "request_id": client_requests[2].id,
            "description": "Fix mobile navigation viewport z-index overlap on iOS and Android Chrome",
            "source_type": "timesheet",
            "external_id": "TASK-103",
            "estimated_hours": 1.5,
            "actual_hours": 1.5,
            "hourly_rate": 2000.0,
            "work_status": "completed",
            "approval_status": "approved",
            "source_reference": "Git commit 7f83a21: Fix responsive nav header layout",
        },
        {
            "request_id": client_requests[3].id,
            "description": "Adjust contact form submit button background color to primary brand blue",
            "source_type": "timesheet",
            "external_id": "TASK-104",
            "estimated_hours": 0.5,
            "actual_hours": 0.5,
            "hourly_rate": 2000.0,
            "work_status": "completed",
            "approval_status": "approved",  # In-scope design revision round
            "source_reference": "CSS style adjustment on contact form button",
        },
    ]

    work_items = []
    for wd in work_items_data:
        wi = WorkItem(
            project_id=project.id,
            **wd,
            created_at=now - timedelta(days=2),
        )
        db.add(wi)
        work_items.append(wi)
    db.commit()
    for wi in work_items:
        db.refresh(wi)

    # 6. Findings (Evidence-grounded)
    findings_data = [
        # 1. Stripe Checkout
        {
            "request": client_requests[0],
            "scope_item": scope_by_clause.get("Exclusion 4.1"),
            "classification": "likely_out_of_scope",
            "explanation": "Client requested Stripe payment integration. Exclusion 4.1 explicitly states that payment gateways and checkout workflows are strictly out of scope.",
            "confidence": 0.95,
            "evidence_references": [
                {
                    "type": "exclusion",
                    "quote": "Payment gateway integration, merchant onboarding, and checkout workflows are strictly out of scope.",
                    "ref": "Exclusion 4.1",
                    "page": 1,
                    "confidence": 0.95,
                }
            ],
            "linked_work_item_ids": [work_items[0].id],
            "estimated_extra_hours": 8.0,
            "estimated_value": 16000.0,
            "review_status": "approved",  # Freelancer verified this scope change
            "reviewer_notes": "Confirmed out of scope. Client requested quote before beginning work.",
        },
        # 2. Order History
        {
            "request": client_requests[1],
            "scope_item": scope_by_clause.get("Exclusion 4.2"),
            "classification": "likely_out_of_scope",
            "explanation": "Customer order history requires authentication and dynamic database models. Exclusion 4.2 specifically excludes customer accounts and order history functionality.",
            "confidence": 0.92,
            "evidence_references": [
                {
                    "type": "exclusion",
                    "quote": "Customer accounts, authentication, order history, and backend portal functionality are not included in the defined deliverables.",
                    "ref": "Exclusion 4.2",
                    "page": 1,
                    "confidence": 0.92,
                }
            ],
            "linked_work_item_ids": [work_items[1].id],
            "estimated_extra_hours": 5.0,
            "estimated_value": 10000.0,
            "review_status": "pending",  # Pending freelancer review
            "reviewer_notes": "Needs client confirmation on whether this should be rolled into a phase 2 sprint.",
        },
        # 3. Mobile Nav
        {
            "request": client_requests[2],
            "scope_item": scope_by_clause.get("Clause 2.2"),
            "classification": "likely_in_scope",
            "explanation": "Fixing mobile navigation layout overlapping the title is covered under the agreed deliverable for responsive layout across devices (Clause 2.2).",
            "confidence": 0.88,
            "evidence_references": [
                {
                    "type": "clause",
                    "quote": "All website templates shall be responsive and verified on current mobile and desktop screen sizes.",
                    "ref": "Clause 2.2",
                    "page": 1,
                    "confidence": 0.88,
                }
            ],
            "linked_work_item_ids": [work_items[2].id],
            "estimated_extra_hours": 0.0,
            "estimated_value": 0.0,
            "review_status": "approved",
            "reviewer_notes": "Completed as part of standard responsive QA obligations.",
        },
        # 4. Button Color
        {
            "request": client_requests[3],
            "scope_item": scope_by_clause.get("Clause 3.2"),
            "classification": "ambiguous",
            "explanation": "Adjusting the submit button color is covered if within the two agreed revision rounds. If revision limits have been reached, additional styling adjustments are billable at ₹2,000/hour.",
            "confidence": 0.65,
            "evidence_references": [
                {
                    "type": "revision_limit",
                    "quote": "Contract includes up to two (2) rounds of design revisions. Additional rounds will be billed at standard hourly rates.",
                    "ref": "Clause 3.2",
                    "page": 1,
                    "confidence": 0.65,
                    "is_missing_or_incomplete": True,
                }
            ],
            "linked_work_item_ids": [work_items[3].id],
            "estimated_extra_hours": 0.5,
            "estimated_value": 1000.0,
            "review_status": "uncertain",
            "reviewer_notes": "Checking design sign-off logs to verify whether this is round 2 or round 3.",
        },
    ]

    findings = []
    for fd in findings_data:
        f = Finding(
            project_id=project.id,
            request_id=fd["request"].id,
            scope_item_id=fd["scope_item"].id if fd["scope_item"] else None,
            classification=fd["classification"],
            explanation=fd["explanation"],
            confidence=fd["confidence"],
            estimated_extra_hours=fd["estimated_extra_hours"],
            estimated_value=fd["estimated_value"],
            review_status=fd["review_status"],
            reviewer_notes=fd["reviewer_notes"],
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
        f.evidence_references = fd["evidence_references"]
        f.linked_work_item_ids = fd["linked_work_item_ids"]
        db.add(f)
        findings.append(f)
    db.commit()
    for f in findings:
        db.refresh(f)

    # 7. Review Decisions
    for idx, f in enumerate(findings):
        rd = ReviewDecision(
            finding_id=f.id,
            actor="Lead Developer",
            decision=f.review_status,
            notes=f.reviewer_notes,
            timestamp=now - timedelta(hours=12 - idx),
        )
        db.add(rd)
    db.commit()

    # 8. Sample Change Order Draft for Stripe Checkout (Demonstrating draft vs accepted)
    co = ChangeOrder(
        project_id=project.id,
        version=1,
        title="Change Order #1: Stripe Checkout Integration",
        status="ready_for_review",
        currency="INR",
        subtotal=16000.0,
        taxes=0.0,
        total=16000.0,
        assumptions="Requires client to provide verified Stripe production and sandbox API keys.",
        exclusions="Stripe transaction percentage fees and dispute handling are managed directly with Stripe.",
        validity_days=14,
        payment_terms="50% deposit prior to webhook setup, 50% upon deployment to production.",
        created_at=now - timedelta(days=1),
    )
    co.line_items = [
        {
            "title": "Stripe Checkout & Webhook Integration",
            "description": "Integration of Stripe checkout session, webhook handler, and payment success page.",
            "hours": 8.0,
            "rate": 2000.0,
            "line_total": 16000.0,
            "source_finding_id": findings[0].id,
            "source_work_item_id": work_items[0].id,
            "is_estimated": True,
        }
    ]
    db.add(co)
    db.commit()
    db.refresh(co)

    # 9. Audit Events
    audit_trail = [
        ("system", "baseline_created", "contract", contract.id, "Initial contract text extracted and 7 baseline items loaded."),
        ("Lead Developer", "baseline_confirmed", "contract", contract.id, "Freelancer reviewed and confirmed contract baseline."),
        ("system", "request_imported", "client_request", client_requests[0].id, "Imported client request: 'Can you add Stripe checkout before launch?'"),
        ("system", "finding_analyzed", "finding", findings[0].id, "AI categorized request as likely_out_of_scope with Exclusion 4.1 evidence."),
        ("Lead Developer", "finding_reviewed", "finding", findings[0].id, "Freelancer marked finding as approved out-of-scope work."),
        ("Lead Developer", "change_order_created", "change_order", co.id, "Drafted Change Order #1 for ₹16,000 based on finding #1."),
    ]

    for actor, etype, ent_type, ent_id, desc in audit_trail:
        db.add(AuditEvent(
            project_id=project.id,
            actor=actor,
            event_type=etype,
            entity_type=ent_type,
            entity_id=ent_id,
            description=desc,
            timestamp=now - timedelta(hours=6),
        ))
    db.commit()

    return project
