import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class WorkItem(Base):
    __tablename__ = "work_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id = Column(String(36), ForeignKey("client_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(50), default="manual", nullable=False)  # manual, csv_import, jira, timesheet
    external_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    work_status = Column(String(50), default="logged", nullable=False)  # planned, in_progress, completed, logged
    approval_status = Column(String(50), default="unapproved", nullable=False)  # unapproved, pending_review, approved, rejected
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="work_items")
    request = relationship("ClientRequest", back_populates="work_items")
