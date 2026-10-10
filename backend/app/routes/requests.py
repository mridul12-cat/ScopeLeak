from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.client_request import ClientRequest
from backend.app.schemas.client_request import (
    ClientRequestCreate,
    ClientRequestResponse,
    ClientRequestImportRequest,
)
from backend.app.utils.hashing import compute_text_hash
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/api/projects/{project_id}/requests", tags=["client requests"])

@router.post("", response_model=ClientRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    project_id: str,
    req_in: ClientRequestCreate,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content_hash = compute_text_hash(req_in.message_text)
    # Check for duplicate
    existing = db.query(ClientRequest).filter(
        ClientRequest.project_id == project_id,
        ClientRequest.content_hash == content_hash,
    ).first()
    if existing:
        return existing

    req = ClientRequest(
        project_id=project_id,
        message_text=req_in.message_text,
        sender=req_in.sender or "Client",
        external_source=req_in.external_source or "manual",
        message_timestamp=req_in.message_timestamp or datetime.utcnow(),
        content_hash=content_hash,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="request_created",
        entity_type="client_request",
        entity_id=req.id,
        description=f"Logged client request from '{req.sender}': {req.message_text[:80]}",
    )
    return req

@router.post("/import", response_model=List[ClientRequestResponse])
def import_requests(
    project_id: str,
    import_data: ClientRequestImportRequest,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    created = []
    for item in import_data.messages:
        if not item.message_text.strip():
            continue
        content_hash = compute_text_hash(item.message_text)
        # Avoid duplicate counting
        existing = db.query(ClientRequest).filter(
            ClientRequest.project_id == project_id,
            ClientRequest.content_hash == content_hash,
        ).first()
        if existing:
            created.append(existing)
            continue

        ts = datetime.utcnow()
        if item.message_timestamp:
            try:
                ts = datetime.fromisoformat(item.message_timestamp)
            except Exception:
                pass

        req = ClientRequest(
            project_id=project_id,
            message_text=item.message_text.strip(),
            sender=item.sender or "Client",
            external_source=item.external_source or "csv_import",
            message_timestamp=ts,
            content_hash=content_hash,
        )
        db.add(req)
        created.append(req)

    db.commit()
    for r in created:
        db.refresh(r)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="requests_imported",
        entity_type="client_request",
        entity_id=project_id,
        description=f"Imported {len(created)} client requests.",
    )
    return created

@router.get("", response_model=List[ClientRequestResponse])
def list_requests(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(ClientRequest).filter(
        ClientRequest.project_id == project_id
    ).order_by(ClientRequest.imported_at.desc()).all()

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(project_id: str, request_id: str, db: Session = Depends(get_db)):
    req = db.query(ClientRequest).filter(
        ClientRequest.id == request_id,
        ClientRequest.project_id == project_id,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    db.delete(req)
    db.commit()
    return None
