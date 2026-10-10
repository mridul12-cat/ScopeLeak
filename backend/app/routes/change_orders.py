from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.change_order import ChangeOrder
from backend.app.models.finding import Finding
from backend.app.models.work_item import WorkItem
from backend.app.schemas.change_order import (
    ChangeOrderCreate,
    ChangeOrderUpdate,
    ChangeOrderResponse,
)
from backend.app.services.pricing_service import calculate_change_order_totals, calculate_line_item
from backend.app.services.pdf_export_service import generate_change_order_pdf
from backend.app.services.audit_service import log_audit_event

router = APIRouter(tags=["change orders"])

@router.post("/api/projects/{project_id}/change-orders", response_model=ChangeOrderResponse, status_code=status.HTTP_201_CREATED)
def create_change_order(
    project_id: str,
    co_in: ChangeOrderCreate,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine next version number
    latest_co = db.query(ChangeOrder).filter(
        ChangeOrder.project_id == project_id
    ).order_by(ChangeOrder.version.desc()).first()
    version = (latest_co.version + 1) if latest_co else 1

    line_items = []
    # If explicit line items provided
    if co_in.line_items:
        for it in co_in.line_items:
            line_items.append(it.model_dump())

    # If selected findings provided
    if co_in.finding_ids:
        findings = db.query(Finding).filter(
            Finding.id.in_(co_in.finding_ids),
            Finding.project_id == project_id,
        ).all()
        for f in findings:
            hours = f.estimated_extra_hours or 0.0
            rate = project.default_hourly_rate or 2000.0
            line_items.append({
                "title": f"Scope Change: {f.explanation[:60]}...",
                "description": f.explanation,
                "hours": hours,
                "rate": rate,
                "line_total": calculate_line_item(hours, rate),
                "source_finding_id": f.id,
                "is_estimated": True,
            })

    # Calculate deterministic totals
    totals = calculate_change_order_totals(line_items, co_in.tax_rate_percent)

    co = ChangeOrder(
        project_id=project_id,
        version=version,
        title=co_in.title,
        status="draft",
        currency=project.currency or "INR",
        subtotal=totals["subtotal"],
        taxes=totals["taxes"],
        total=totals["total"],
        assumptions=co_in.assumptions,
        exclusions=co_in.exclusions,
        validity_days=co_in.validity_days,
        payment_terms=co_in.payment_terms,
    )
    co.line_items = line_items
    db.add(co)
    db.commit()
    db.refresh(co)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="change_order_created",
        entity_type="change_order",
        entity_id=co.id,
        description=f"Created Change Order '{co.title}' (v{co.version}) for {co.currency} {co.total:,.2f}",
        after_state={"title": co.title, "total": co.total, "status": co.status},
    )

    return ChangeOrderResponse(
        id=co.id,
        project_id=co.project_id,
        version=co.version,
        title=co.title,
        status=co.status,
        currency=co.currency,
        line_items=co.line_items,
        subtotal=co.subtotal,
        taxes=co.taxes,
        total=co.total,
        assumptions=co.assumptions,
        exclusions=co.exclusions,
        validity_days=co.validity_days,
        payment_terms=co.payment_terms,
        created_at=co.created_at,
        updated_at=co.updated_at,
    )

@router.get("/api/projects/{project_id}/change-orders", response_model=List[ChangeOrderResponse])
def list_change_orders(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cos = db.query(ChangeOrder).filter(
        ChangeOrder.project_id == project_id
    ).order_by(ChangeOrder.version.desc()).all()

    return [
        ChangeOrderResponse(
            id=co.id,
            project_id=co.project_id,
            version=co.version,
            title=co.title,
            status=co.status,
            currency=co.currency,
            line_items=co.line_items,
            subtotal=co.subtotal,
            taxes=co.taxes,
            total=co.total,
            assumptions=co.assumptions,
            exclusions=co.exclusions,
            validity_days=co.validity_days,
            payment_terms=co.payment_terms,
            created_at=co.created_at,
            updated_at=co.updated_at,
        )
        for co in cos
    ]

@router.get("/api/change-orders/{change_order_id}", response_model=ChangeOrderResponse)
def get_change_order(change_order_id: str, db: Session = Depends(get_db)):
    co = db.query(ChangeOrder).filter(ChangeOrder.id == change_order_id).first()
    if not co:
        raise HTTPException(status_code=404, detail="Change order not found")

    return ChangeOrderResponse(
        id=co.id,
        project_id=co.project_id,
        version=co.version,
        title=co.title,
        status=co.status,
        currency=co.currency,
        line_items=co.line_items,
        subtotal=co.subtotal,
        taxes=co.taxes,
        total=co.total,
        assumptions=co.assumptions,
        exclusions=co.exclusions,
        validity_days=co.validity_days,
        payment_terms=co.payment_terms,
        created_at=co.created_at,
        updated_at=co.updated_at,
    )

@router.patch("/api/change-orders/{change_order_id}", response_model=ChangeOrderResponse)
def update_change_order(
    change_order_id: str,
    update_in: ChangeOrderUpdate,
    db: Session = Depends(get_db),
):
    co = db.query(ChangeOrder).filter(ChangeOrder.id == change_order_id).first()
    if not co:
        raise HTTPException(status_code=404, detail="Change order not found")

    before = {"status": co.status, "total": co.total}

    if update_in.title is not None:
        co.title = update_in.title
    if update_in.status is not None:
        # Validate status progression
        valid_statuses = {"draft", "ready_for_review", "approved_by_freelancer", "sent", "accepted_by_client", "declined"}
        if update_in.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status '{update_in.status}'")
        co.status = update_in.status

    if update_in.line_items is not None:
        raw_items = [it.model_dump() for it in update_in.line_items]
        tax_pct = update_in.tax_rate_percent if update_in.tax_rate_percent is not None else 0.0
        totals = calculate_change_order_totals(raw_items, tax_pct)
        co.line_items = raw_items
        co.subtotal = totals["subtotal"]
        co.taxes = totals["taxes"]
        co.total = totals["total"]

    if update_in.assumptions is not None:
        co.assumptions = update_in.assumptions
    if update_in.exclusions is not None:
        co.exclusions = update_in.exclusions
    if update_in.validity_days is not None:
        co.validity_days = update_in.validity_days
    if update_in.payment_terms is not None:
        co.payment_terms = update_in.payment_terms

    db.commit()
    db.refresh(co)

    log_audit_event(
        db,
        project_id=co.project_id,
        actor="user",
        event_type="change_order_updated",
        entity_type="change_order",
        entity_id=co.id,
        description=f"Updated Change Order v{co.version}. Status: {co.status}. Total: {co.currency} {co.total:,.2f}",
        before_state=before,
        after_state={"status": co.status, "total": co.total},
    )

    return ChangeOrderResponse(
        id=co.id,
        project_id=co.project_id,
        version=co.version,
        title=co.title,
        status=co.status,
        currency=co.currency,
        line_items=co.line_items,
        subtotal=co.subtotal,
        taxes=co.taxes,
        total=co.total,
        assumptions=co.assumptions,
        exclusions=co.exclusions,
        validity_days=co.validity_days,
        payment_terms=co.payment_terms,
        created_at=co.created_at,
        updated_at=co.updated_at,
    )

@router.get("/api/change-orders/{change_order_id}/export")
@router.get("/api/change-orders/{change_order_id}/pdf")
def export_change_order_pdf(change_order_id: str, db: Session = Depends(get_db)):
    """Export change order document as a beautifully formatted PDF."""
    co = db.query(ChangeOrder).filter(ChangeOrder.id == change_order_id).first()
    if not co:
        raise HTTPException(status_code=404, detail="Change order not found")

    project = db.query(Project).filter(Project.id == co.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found")

    pdf_bytes = generate_change_order_pdf(co, project)
    filename = f"ChangeOrder_v{co.version}_{project.name.replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
