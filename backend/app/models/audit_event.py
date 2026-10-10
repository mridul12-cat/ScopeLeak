import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    actor = Column(String(100), default="user", nullable=False)  # system, user, gemini_ai
    event_type = Column(String(100), nullable=False)  # baseline_created, request_imported, finding_created, finding_reviewed, etc.
    entity_type = Column(String(50), nullable=False)  # project, contract, scope_item, client_request, finding, work_item, change_order
    entity_id = Column(String(36), nullable=False)
    description = Column(Text, nullable=True)
    before_state_json = Column(Text, nullable=True)
    after_state_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    project = relationship("Project", back_populates="audit_events")

    @property
    def before_state(self):
        try:
            return json.loads(self.before_state_json) if self.before_state_json else None
        except Exception:
            return None

    @before_state.setter
    def before_state(self, value):
        self.before_state_json = json.dumps(value) if value is not None else None

    @property
    def after_state(self):
        try:
            return json.loads(self.after_state_json) if self.after_state_json else None
        except Exception:
            return None

    @after_state.setter
    def after_state(self, value):
        self.after_state_json = json.dumps(value) if value is not None else None
