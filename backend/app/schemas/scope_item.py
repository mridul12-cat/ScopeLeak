from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ScopeItemBase(BaseModel):
    item_type: str = Field(..., description="deliverable, exclusion, revision_limit, milestone, commercial_term, ambiguous")
    description: str
    normalized_description: Optional[str] = None
    source_clause_id: Optional[str] = None
    source_quote: Optional[str] = None
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    review_status: str = Field(default="pending", description="pending, confirmed, modified, rejected")

class ScopeItemCreate(ScopeItemBase):
    contract_id: Optional[str] = None

class ScopeItemUpdate(BaseModel):
    item_type: Optional[str] = None
    description: Optional[str] = None
    normalized_description: Optional[str] = None
    source_clause_id: Optional[str] = None
    source_quote: Optional[str] = None
    page_number: Optional[int] = None
    section_reference: Optional[str] = None
    review_status: Optional[str] = None

class ScopeItemResponse(ScopeItemBase):
    id: str
    project_id: str
    contract_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class BaselineBatchUpdate(BaseModel):
    items: List[ScopeItemCreate] = []
    confirm_all: bool = False
