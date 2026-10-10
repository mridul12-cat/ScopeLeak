from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.audit_event import AuditEvent

def log_audit_event(
    db: Session,
    project_id: str,
    actor: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    description: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Record an audit trail event distinguishing system and human decisions."""
    event = AuditEvent(
        project_id=project_id,
        actor=actor,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    if before_state is not None:
        event.before_state = before_state
    if after_state is not None:
        event.after_state = after_state

    db.add(event)
    db.commit()
    db.refresh(event)
    return event
