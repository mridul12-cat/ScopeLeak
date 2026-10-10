import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class ChangeOrder(Base):
    __tablename__ = "change_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, ready_for_review, approved_by_freelancer, sent, accepted_by_client, declined
    currency = Column(String(10), default="INR", nullable=False)
    line_items_json = Column(Text, default="[]", nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    taxes = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    assumptions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    validity_days = Column(Integer, default=14, nullable=True)
    payment_terms = Column(String(255), default="50% upfront, 50% on completion", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="change_orders")

    @property
    def line_items(self):
        try:
            return json.loads(self.line_items_json or "[]")
        except Exception:
            return []

    @line_items.setter
    def line_items(self, value):
        self.line_items_json = json.dumps(value or [])
