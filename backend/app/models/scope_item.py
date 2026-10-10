import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class ScopeItem(Base):
    __tablename__ = "scope_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True)
    item_type = Column(String(50), nullable=False)  # deliverable, exclusion, revision_limit, milestone, commercial_term, ambiguous
    description = Column(Text, nullable=False)
    normalized_description = Column(Text, nullable=False)
    source_clause_id = Column(String(100), nullable=True)
    source_quote = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    section_reference = Column(String(255), nullable=True)
    review_status = Column(String(50), default="pending", nullable=False)  # pending, confirmed, modified, rejected
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="scope_items")
    contract = relationship("Contract", back_populates="scope_items")
    findings = relationship("Finding", back_populates="scope_item")
