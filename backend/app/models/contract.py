import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    content_hash = Column(String(64), nullable=False)
    extracted_text = Column(Text, nullable=True)
    processing_status = Column(String(50), default="uploaded", nullable=False)  # uploaded, processing, extracted, failed
    baseline_review_status = Column(String(50), default="pending_review", nullable=False)  # pending_review, confirmed
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="contracts")
    scope_items = relationship("ScopeItem", back_populates="contract", cascade="all, delete-orphan")
