import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class ClientRequest(Base):
    __tablename__ = "client_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    external_source = Column(String(50), default="manual", nullable=False)  # manual, email, slack, csv_import
    sender = Column(String(255), nullable=True)
    message_text = Column(Text, nullable=False)
    message_timestamp = Column(DateTime, nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="requests")
    findings = relationship("Finding", back_populates="request", cascade="all, delete-orphan")
    work_items = relationship("WorkItem", back_populates="request")
