from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuditEventResponse(BaseModel):
    id: str
    project_id: str
    actor: str
    event_type: str
    entity_type: str
    entity_id: str
    description: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
