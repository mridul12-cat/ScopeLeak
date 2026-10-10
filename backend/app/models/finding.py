import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id = Column(String(36), ForeignKey("client_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    scope_item_id = Column(String(36), ForeignKey("scope_items.id", ondelete="SET NULL"), nullable=True, index=True)
    classification = Column(String(50), nullable=False)  # likely_in_scope, likely_out_of_scope, ambiguous
    explanation = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8, nullable=False)
    evidence_references_json = Column(Text, default="[]", nullable=False)
    linked_work_item_ids_json = Column(Text, default="[]", nullable=False)
    estimated_extra_hours = Column(Float, nullable=True)
    estimated_value = Column(Float, nullable=True)
    review_status = Column(String(50), default="pending", nullable=False)  # pending, approved, dismissed, uncertain
    reviewer_notes = Column(Text, nullable=True)
    provider_source = Column(String(50), default="deterministic_fallback", nullable=False)  # gemini_live or deterministic_fallback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="findings")
    request = relationship("ClientRequest", back_populates="findings")
    scope_item = relationship("ScopeItem", back_populates="findings")
    decisions = relationship("ReviewDecision", back_populates="finding", cascade="all, delete-orphan")

    @property
    def evidence_references(self):
        try:
            return json.loads(self.evidence_references_json or "[]")
        except Exception:
            return []

    @evidence_references.setter
    def evidence_references(self, value):
        self.evidence_references_json = json.dumps(value or [])

    @property
    def linked_work_item_ids(self):
        try:
            return json.loads(self.linked_work_item_ids_json or "[]")
        except Exception:
            return []

    @linked_work_item_ids.setter
    def linked_work_item_ids(self, value):
        self.linked_work_item_ids_json = json.dumps(value or [])
