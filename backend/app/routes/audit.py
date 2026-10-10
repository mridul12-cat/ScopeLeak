from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.audit_event import AuditEvent
from backend.app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/api/projects/{project_id}/audit", tags=["audit trail"])

@router.get("", response_model=List[AuditEventResponse])
def get_audit_trail(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    events = db.query(AuditEvent).filter(
        AuditEvent.project_id == project_id
    ).order_by(AuditEvent.timestamp.desc()).all()

    return [
        AuditEventResponse(
            id=ev.id,
            project_id=ev.project_id,
            actor=ev.actor,
            event_type=ev.event_type,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            description=ev.description,
            before_state=ev.before_state,
            after_state=ev.after_state,
            timestamp=ev.timestamp,
        )
        for ev in events
    ]
