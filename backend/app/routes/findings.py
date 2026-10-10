from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.client_request import ClientRequest
from backend.app.models.scope_item import ScopeItem
from backend.app.models.finding import Finding
from backend.app.models.review_decision import ReviewDecision
from backend.app.models.work_item import WorkItem
from backend.app.schemas.finding import (
    FindingResponse,
    FindingUpdate,
    AnalyzeProjectRequest,
)
from backend.app.services.ai_service import ai_engine
from backend.app.services.audit_service import log_audit_event
from backend.app.services.pricing_service import calculate_line_item

router = APIRouter(tags=["findings & analysis"])

@router.post("/api/projects/{project_id}/analyze", response_model=List[FindingResponse])
async def analyze_requests(
    project_id: str,
    req_body: AnalyzeProjectRequest = AnalyzeProjectRequest(),
    db: Session = Depends(get_db),
):
    """
    Compare client requests against reviewed scope baseline.
    Generates verifiable, evidence-grounded findings.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get scope items
    scope_items = db.query(ScopeItem).filter(ScopeItem.project_id == project_id).all()
    scope_items_dict = [
        {
            "id": s.id,
            "item_type": s.item_type,
            "description": s.description,
            "source_clause_id": s.source_clause_id,
            "source_quote": s.source_quote,
            "section_reference": s.section_reference,
            "page_number": s.page_number,
        }
        for s in scope_items
    ]

    # Get requests to analyze
    q = db.query(ClientRequest).filter(ClientRequest.project_id == project_id)
    if req_body.request_ids:
        q = q.filter(ClientRequest.id.in_(req_body.request_ids))
    requests_to_analyze = q.all()

    if not requests_to_analyze:
        raise HTTPException(status_code=400, detail="No client requests found to analyze.")

    # Get existing findings map
    existing_findings = db.query(Finding).filter(Finding.project_id == project_id).all()
    finding_by_req_id = {f.request_id: f for f in existing_findings}

    # Fetch work items for linking
    work_items = db.query(WorkItem).filter(WorkItem.project_id == project_id).all()

    results = []
    for cr in requests_to_analyze:
        if cr.id in finding_by_req_id and not req_body.force_reanalyze:
            results.append(finding_by_req_id[cr.id])
            continue

        # Run AI analysis
        analysis = await ai_engine.analyze_request(
            message_text=cr.message_text,
            scope_items=scope_items_dict,
            default_rate=float(project.default_hourly_rate or 2000.0),
        )

        # Match relevant work items by request_id or text
        matched_work_ids = []
        for wi in work_items:
            if wi.request_id == cr.id:
                matched_work_ids.append(wi.id)
            elif any(w in wi.description.lower() for w in cr.message_text.lower().split() if len(w) > 4):
                matched_work_ids.append(wi.id)

        # Evidence references list
        ev_refs = []
        has_grounded_evidence = bool(analysis.matched_scope_item_id or analysis.supporting_quote)
        is_genuine_ambiguity = (
            analysis.classification == "ambiguous"
            or not has_grounded_evidence
            or (
                bool(analysis.missing_evidence_notes)
                and any(kw in analysis.missing_evidence_notes.lower() for kw in ["lack", "missing", "ambigu", "unclear", "no matching", "clarif"])
                and analysis.classification not in ("likely_out_of_scope", "likely_in_scope")
            )
        )

        clause_ref = analysis.matched_clause_id or analysis.section_reference or (
            "Section Reference: " + analysis.section_reference if analysis.section_reference else "Confirmed Baseline Scope"
        )

        if analysis.supporting_quote or analysis.matched_clause_id or analysis.section_reference:
            ev_refs.append({
                "type": "clause",
                "quote": analysis.supporting_quote,
                "ref": clause_ref,
                "section": analysis.section_reference,
                "page": analysis.page_number,
                "confidence": analysis.confidence,
                "notes": analysis.missing_evidence_notes,
                "is_missing_or_incomplete": is_genuine_ambiguity,
            })
        elif analysis.missing_evidence_notes:
            ev_refs.append({
                "type": "missing_evidence",
                "ref": "Ambiguous Baseline",
                "notes": analysis.missing_evidence_notes,
                "is_missing_or_incomplete": True,
            })

        # Calculate estimated value deterministically
        est_hours = analysis.estimated_extra_hours
        est_val = None
        if est_hours is not None:
            est_val = calculate_line_item(est_hours, project.default_hourly_rate)

        # Check if finding already existed (for re-analyze)
        finding = finding_by_req_id.get(cr.id)
        if not finding:
            finding = Finding(
                project_id=project_id,
                request_id=cr.id,
                scope_item_id=analysis.matched_scope_item_id,
                classification=analysis.classification,
                explanation=analysis.explanation,
                confidence=analysis.confidence,
                estimated_extra_hours=est_hours,
                estimated_value=est_val,
                review_status="pending",
                provider_source=analysis.provider_source,
            )
            finding.evidence_references = ev_refs
            finding.linked_work_item_ids = list(set(matched_work_ids))
            db.add(finding)
        else:
            finding.scope_item_id = analysis.matched_scope_item_id
            finding.classification = analysis.classification
            finding.explanation = analysis.explanation
            finding.confidence = analysis.confidence
            finding.estimated_extra_hours = est_hours
            finding.estimated_value = est_val
            finding.provider_source = analysis.provider_source
            finding.evidence_references = ev_refs
            finding.linked_work_item_ids = list(set(matched_work_ids))

        results.append(finding)

    db.commit()
    for f in results:
        db.refresh(f)

    log_audit_event(
        db,
        project_id=project_id,
        actor="system",
        event_type="analysis_completed",
        entity_type="finding",
        entity_id=project_id,
        description=f"Scope evidence analysis executed for {len(results)} requests.",
    )
    return results

@router.get("/api/projects/{project_id}/findings", response_model=List[FindingResponse])
def list_findings(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    findings = db.query(Finding).filter(Finding.project_id == project_id).order_by(Finding.created_at.desc()).all()
    # Serialize relationships
    res = []
    for f in findings:
        item = FindingResponse(
            id=f.id,
            project_id=f.project_id,
            request_id=f.request_id,
            scope_item_id=f.scope_item_id,
            classification=f.classification,
            explanation=f.explanation,
            confidence=f.confidence,
            evidence_references=f.evidence_references,
            linked_work_item_ids=f.linked_work_item_ids,
            estimated_extra_hours=f.estimated_extra_hours,
            estimated_value=f.estimated_value,
            review_status=f.review_status,
            reviewer_notes=f.reviewer_notes,
            provider_source=getattr(f, "provider_source", "deterministic_fallback"),
            created_at=f.created_at,
            updated_at=f.updated_at,
            decisions=f.decisions,
        )
        res.append(item)
    return res

@router.get("/api/findings/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse(
        id=finding.id,
        project_id=finding.project_id,
        request_id=finding.request_id,
        scope_item_id=finding.scope_item_id,
        classification=finding.classification,
        explanation=finding.explanation,
        confidence=finding.confidence,
        evidence_references=finding.evidence_references,
        linked_work_item_ids=finding.linked_work_item_ids,
        estimated_extra_hours=finding.estimated_extra_hours,
        estimated_value=finding.estimated_value,
        review_status=finding.review_status,
        reviewer_notes=finding.reviewer_notes,
        provider_source=getattr(finding, "provider_source", "deterministic_fallback"),
        created_at=finding.created_at,
        updated_at=finding.updated_at,
        decisions=finding.decisions,
    )

@router.patch("/api/findings/{finding_id}", response_model=FindingResponse)
def update_finding_review(
    finding_id: str,
    update_in: FindingUpdate,
    db: Session = Depends(get_db),
):
    """
    Human review decision on a finding: approve, dismiss, mark uncertain, or reopen.
    Approving a finding means the user accepts the analysis for workflow purposes.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    before_state = {
        "status": finding.review_status,
        "notes": finding.reviewer_notes,
        "hours": finding.estimated_extra_hours,
    }

    actor = update_in.actor or "Lead Developer"

    if update_in.review_status is not None:
        finding.review_status = update_in.review_status
        # Log ReviewDecision
        decision = ReviewDecision(
            finding_id=finding.id,
            actor=actor,
            decision=update_in.review_status,
            notes=update_in.reviewer_notes,
        )
        db.add(decision)

    if update_in.reviewer_notes is not None:
        finding.reviewer_notes = update_in.reviewer_notes
    if update_in.linked_work_item_ids is not None:
        finding.linked_work_item_ids = update_in.linked_work_item_ids
    if update_in.estimated_extra_hours is not None:
        finding.estimated_extra_hours = update_in.estimated_extra_hours
        project = db.query(Project).filter(Project.id == finding.project_id).first()
        rate = project.default_hourly_rate if project else 2000.0
        finding.estimated_value = calculate_line_item(finding.estimated_extra_hours, rate)
    if update_in.estimated_value is not None:
        finding.estimated_value = update_in.estimated_value

    db.commit()
    db.refresh(finding)

    log_audit_event(
        db,
        project_id=finding.project_id,
        actor=actor,
        event_type="finding_reviewed",
        entity_type="finding",
        entity_id=finding.id,
        description=f"Finding review updated to '{finding.review_status}'. Notes: {finding.reviewer_notes or 'None'}",
        before_state=before_state,
        after_state={"status": finding.review_status, "notes": finding.reviewer_notes, "hours": finding.estimated_extra_hours},
    )

    return FindingResponse(
        id=finding.id,
        project_id=finding.project_id,
        request_id=finding.request_id,
        scope_item_id=finding.scope_item_id,
        classification=finding.classification,
        explanation=finding.explanation,
        confidence=finding.confidence,
        evidence_references=finding.evidence_references,
        linked_work_item_ids=finding.linked_work_item_ids,
        estimated_extra_hours=finding.estimated_extra_hours,
        estimated_value=finding.estimated_value,
        review_status=finding.review_status,
        reviewer_notes=finding.reviewer_notes,
        provider_source=getattr(finding, "provider_source", "deterministic_fallback"),
        created_at=finding.created_at,
        updated_at=finding.updated_at,
        decisions=finding.decisions,
    )
