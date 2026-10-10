from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EvidenceReferenceItem(BaseModel):
    type: str = "clause"  # clause, exclusion, revision_limit, message
    quote: Optional[str] = None
    ref: Optional[str] = None
    page: Optional[int] = None
    confidence: Optional[float] = None
    is_missing_or_incomplete: bool = False

class FindingBase(BaseModel):
    request_id: str
    scope_item_id: Optional[str] = None
    classification: str = Field(..., description="likely_in_scope, likely_out_of_scope, ambiguous")
    explanation: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence_references: List[EvidenceReferenceItem] = []
    linked_work_item_ids: List[str] = []
    estimated_extra_hours: Optional[float] = None
    estimated_value: Optional[float] = None
    review_status: str = Field(default="pending", description="pending, approved, dismissed, uncertain")
    reviewer_notes: Optional[str] = None

class FindingUpdate(BaseModel):
    review_status: Optional[str] = None  # approved, dismissed, uncertain, pending
    reviewer_notes: Optional[str] = None
    linked_work_item_ids: Optional[List[str]] = None
    estimated_extra_hours: Optional[float] = None
    estimated_value: Optional[float] = None
    actor: Optional[str] = "freelancer"

class ReviewDecisionResponse(BaseModel):
    id: str
    finding_id: str
    actor: str
    decision: str
    notes: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}

class FindingResponse(FindingBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    decisions: List[ReviewDecisionResponse] = []

    model_config = {"from_attributes": True}

class AnalyzeProjectRequest(BaseModel):
    request_ids: Optional[List[str]] = None
    force_reanalyze: bool = False
