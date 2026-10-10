from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.work_item import WorkItem
from backend.app.models.client_request import ClientRequest
from backend.app.schemas.work_item import (
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemResponse,
    WorkItemImportRequest,
)
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/api/projects/{project_id}/work", tags=["work tracking"])

@router.post("", response_model=WorkItemResponse, status_code=status.HTTP_201_CREATED)
def create_work_item(
    project_id: str,
    work_in: WorkItemCreate,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If hourly rate not provided, default to project hourly rate
    rate = work_in.hourly_rate if work_in.hourly_rate is not None else project.default_hourly_rate

    # If request_id provided, verify it belongs to the same project
    if work_in.request_id:
        req = db.query(ClientRequest).filter(
            ClientRequest.id == work_in.request_id,
            ClientRequest.project_id == project_id,
        ).first()
        if not req:
            raise HTTPException(status_code=400, detail="Linked request does not belong to this project")

    wi = WorkItem(
        project_id=project_id,
        description=work_in.description,
        source_type=work_in.source_type or "manual",
        external_id=work_in.external_id,
        estimated_hours=work_in.estimated_hours,
        actual_hours=work_in.actual_hours,
        hourly_rate=rate,
        work_status=work_in.work_status or "logged",
        approval_status=work_in.approval_status or "unapproved",
        source_reference=work_in.source_reference,
        request_id=work_in.request_id,
    )
    db.add(wi)
    db.commit()
    db.refresh(wi)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="work_item_created",
        entity_type="work_item",
        entity_id=wi.id,
        description=f"Created work item: '{wi.description[:60]}'",
    )
    return wi

@router.post("/import", response_model=List[WorkItemResponse])
def import_work_items(
    project_id: str,
    import_data: WorkItemImportRequest,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    created = []
    for item in import_data.items:
        if not item.description.strip():
            continue
        rate = item.hourly_rate if item.hourly_rate is not None else project.default_hourly_rate
        wi = WorkItem(
            project_id=project_id,
            description=item.description.strip(),
            source_type=item.source_type or "csv_import",
            external_id=item.external_id,
            estimated_hours=item.estimated_hours,
            actual_hours=item.actual_hours,
            hourly_rate=rate,
            work_status=item.work_status or "logged",
            approval_status=item.approval_status or "unapproved",
            source_reference=item.source_reference,
            request_id=item.request_id,
        )
        db.add(wi)
        created.append(wi)

    db.commit()
    for w in created:
        db.refresh(w)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="work_items_imported",
        entity_type="work_item",
        entity_id=project_id,
        description=f"Imported {len(created)} work items / timesheet records.",
    )
    return created

@router.get("", response_model=List[WorkItemResponse])
def list_work_items(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(WorkItem).filter(
        WorkItem.project_id == project_id
    ).order_by(WorkItem.created_at.desc()).all()

@router.patch("/{work_item_id}", response_model=WorkItemResponse)
def update_work_item(
    project_id: str,
    work_item_id: str,
    work_in: WorkItemUpdate,
    db: Session = Depends(get_db),
):
    wi = db.query(WorkItem).filter(
        WorkItem.id == work_item_id,
        WorkItem.project_id == project_id,
    ).first()
    if not wi:
        raise HTTPException(status_code=404, detail="Work item not found")

    before = {"approval": wi.approval_status, "hours": wi.actual_hours or wi.estimated_hours}

    if work_in.description is not None:
        wi.description = work_in.description
    if work_in.estimated_hours is not None:
        wi.estimated_hours = work_in.estimated_hours
    if work_in.actual_hours is not None:
        wi.actual_hours = work_in.actual_hours
    if work_in.hourly_rate is not None:
        wi.hourly_rate = work_in.hourly_rate
    if work_in.work_status is not None:
        wi.work_status = work_in.work_status
    if work_in.approval_status is not None:
        wi.approval_status = work_in.approval_status
    if work_in.request_id is not None:
        # Cross-project reference prevention
        if work_in.request_id:
            req = db.query(ClientRequest).filter(
                ClientRequest.id == work_in.request_id,
                ClientRequest.project_id == project_id
            ).first()
            if not req:
                raise HTTPException(status_code=400, detail="Cannot link to request from another project")
        wi.request_id = work_in.request_id

    db.commit()
    db.refresh(wi)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="work_item_updated",
        entity_type="work_item",
        entity_id=wi.id,
        description=f"Updated work item {wi.id[:8]}",
        before_state=before,
        after_state={"approval": wi.approval_status, "hours": wi.actual_hours or wi.estimated_hours},
    )
    return wi

@router.delete("/{work_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(project_id: str, work_item_id: str, db: Session = Depends(get_db)):
    wi = db.query(WorkItem).filter(
        WorkItem.id == work_item_id,
        WorkItem.project_id == project_id,
    ).first()
    if not wi:
        raise HTTPException(status_code=404, detail="Work item not found")
    db.delete(wi)
    db.commit()
    return None
