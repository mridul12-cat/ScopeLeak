from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.project import Project
from backend.app.models.work_item import WorkItem
from backend.app.models.finding import Finding
from backend.app.models.change_order import ChangeOrder

def calculate_line_item(hours: float, rate: float) -> float:
    """Calculate line item total: hours * rate, rounded to 2 decimal places."""
    if hours is None or hours < 0:
        hours = 0.0
    if rate is None or rate < 0:
        rate = 0.0
    return round(float(hours) * float(rate), 2)

def calculate_change_order_totals(
    line_items: List[Dict[str, Any]],
    tax_rate_percent: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate subtotal and total for a change order.
    subtotal = sum(hours * rate)
    taxes = subtotal * (tax_rate_percent / 100)
    total = subtotal + taxes
    """
    subtotal = 0.0
    for item in line_items:
        hours = float(item.get("hours", 0.0) or 0.0)
        rate = float(item.get("rate", 0.0) or 0.0)
        item_total = calculate_line_item(hours, rate)
        item["line_total"] = item_total
        subtotal += item_total

    subtotal = round(subtotal, 2)
    tax_rate = max(0.0, float(tax_rate_percent or 0.0))
    taxes = round(subtotal * (tax_rate / 100.0), 2)
    total = round(subtotal + taxes, 2)

    return {
        "subtotal": subtotal,
        "taxes": taxes,
        "total": total,
    }

def calculate_project_financial_impact(db: Session, project: Project) -> Dict[str, Any]:
    """
    Calculate transparent, deduplicated financial governance metrics for a project:
    
    INCLUSION & EXCLUSION RULES:
    1. Unapproved Work:
       - Any WorkItem where approval_status != 'approved' contributes to potential_unapproved_hours
         and potential_unapproved_value.
       - Any Finding flagged likely_out_of_scope or approved by developer that has estimated hours
         is included ONLY IF not already accounted for by a logged WorkItem (deduplicated by
         both linked_work_item_ids and request_id).
    2. Change Orders:
       - Draft: status in ('draft', 'ready_for_review')
       - Freelancer Approved (Sent): status in ('approved_by_freelancer', 'sent')
       - Client Accepted: status == 'accepted_by_client' (legally locked addendums)
    3. Revenue at Risk:
       - Defined deterministically as: max(0.0, potential_unapproved_value - accepted_by_client_value)
    4. Pending Findings:
       - Tracks unreviewed findings requiring developer attention before change-order drafting.
    5. Currency Isolation:
       - All rates and line totals are strictly computed in the project's native currency (e.g. INR or USD).
    """
    default_rate = float(project.default_hourly_rate or 0.0)
    currency = project.currency or "INR"

    # Fetch all work items for this project
    work_items = db.query(WorkItem).filter(WorkItem.project_id == project.id).all()
    # Fetch all findings
    findings = db.query(Finding).filter(Finding.project_id == project.id).all()
    finding_by_id = {f.id: f for f in findings}
    finding_by_request_id = {f.request_id: f for f in findings}

    potential_unapproved_hours = 0.0
    potential_unapproved_value = 0.0
    items_with_missing_rates = 0
    breakdown = []

    # Keep track of work items and requests counted to strictly prevent double-counting
    accounted_work_ids = set()
    accounted_request_ids = set()

    for item in work_items:
        accounted_work_ids.add(item.id)
        if item.request_id:
            accounted_request_ids.add(item.request_id)

        effective_rate = item.hourly_rate if item.hourly_rate is not None else default_rate
        if item.hourly_rate is None and default_rate == 0:
            items_with_missing_rates += 1

        # Use actual hours if logged, otherwise estimated hours
        if item.actual_hours is not None and item.actual_hours > 0:
            hours = float(item.actual_hours)
            hours_type = "logged"
        elif item.estimated_hours is not None and item.estimated_hours > 0:
            hours = float(item.estimated_hours)
            hours_type = "estimated"
        else:
            hours = 0.0
            hours_type = "unspecified"

        line_val = calculate_line_item(hours, effective_rate)

        # Linked finding classification if any
        finding_cls = None
        if item.request_id and item.request_id in finding_by_request_id:
            finding_cls = finding_by_request_id[item.request_id].classification

        # Check if unapproved work
        if item.approval_status != "approved":
            potential_unapproved_hours += hours
            potential_unapproved_value += line_val

        breakdown.append({
            "id": item.id,
            "description": item.description,
            "hours": hours,
            "hours_type": hours_type,
            "hourly_rate": effective_rate,
            "line_total": line_val,
            "approval_status": item.approval_status,
            "work_status": item.work_status,
            "linked_request_id": item.request_id,
            "finding_classification": finding_cls,
        })

    # Also include findings that have estimated extra hours but no work items attached yet
    for f in findings:
        if (f.classification == "likely_out_of_scope" or f.review_status == "approved") and f.estimated_extra_hours:
            linked_ids = set(f.linked_work_item_ids or [])
            # Deduplication: If already accounted for via work items or request_id, skip to prevent double counting
            if linked_ids.intersection(accounted_work_ids) or (f.request_id and f.request_id in accounted_request_ids):
                continue

            f_hours = float(f.estimated_extra_hours or 0.0)
            f_rate = default_rate
            f_val = calculate_line_item(f_hours, f_rate)
            # Only add if pending or approved
            if f.review_status in ("pending", "approved"):
                potential_unapproved_hours += f_hours
                potential_unapproved_value += f_val
                breakdown.append({
                    "id": f"finding-{f.id}",
                    "description": f"[Finding] {f.explanation[:80]}...",
                    "hours": f_hours,
                    "hours_type": "estimated",
                    "hourly_rate": f_rate,
                    "line_total": f_val,
                    "approval_status": "unapproved",
                    "work_status": "planned",
                    "linked_request_id": f.request_id,
                    "finding_classification": f.classification,
                })

    # Fetch Change Orders
    change_orders = db.query(ChangeOrder).filter(ChangeOrder.project_id == project.id).all()
    draft_co_value = 0.0
    approved_freelancer_value = 0.0
    accepted_client_value = 0.0

    for co in change_orders:
        if co.status in ("draft", "ready_for_review"):
            draft_co_value += float(co.total or 0.0)
        elif co.status in ("approved_by_freelancer", "sent"):
            approved_freelancer_value += float(co.total or 0.0)
        elif co.status == "accepted_by_client":
            accepted_client_value += float(co.total or 0.0)

    # Pending findings metrics
    pending_findings_count = 0
    pending_findings_hours = 0.0
    pending_findings_value = 0.0
    for f in findings:
        if f.review_status == "pending":
            pending_findings_count += 1
            if f.estimated_extra_hours and f.estimated_extra_hours > 0:
                h = float(f.estimated_extra_hours)
                pending_findings_hours += h
                pending_findings_value += calculate_line_item(h, default_rate)

    revenue_at_risk = round(max(0.0, potential_unapproved_value - accepted_client_value), 2)

    return {
        "project_id": project.id,
        "currency": currency,
        "potential_unapproved_hours": round(potential_unapproved_hours, 2),
        "potential_unapproved_value": round(potential_unapproved_value, 2),
        "draft_change_order_value": round(draft_co_value, 2),
        "approved_by_freelancer_value": round(approved_freelancer_value, 2),
        "accepted_by_client_value": round(accepted_client_value, 2),
        "estimated_revenue_at_risk": revenue_at_risk,
        "items_with_missing_rates_count": items_with_missing_rates,
        "pending_findings_count": pending_findings_count,
        "pending_findings_hours": round(pending_findings_hours, 2),
        "pending_findings_value": round(pending_findings_value, 2),
        "breakdown": breakdown,
    }
