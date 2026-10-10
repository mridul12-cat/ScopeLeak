from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChangeOrderLineItem(BaseModel):
    title: str
    description: Optional[str] = None
    hours: float = Field(..., ge=0.0)
    rate: float = Field(..., ge=0.0)
    line_total: float = Field(..., ge=0.0)
    source_finding_id: Optional[str] = None
    source_work_item_id: Optional[str] = None
    is_estimated: bool = True

class ChangeOrderCreate(BaseModel):
    title: str = Field(..., min_length=1)
    finding_ids: Optional[List[str]] = None
    line_items: Optional[List[ChangeOrderLineItem]] = None
    tax_rate_percent: float = Field(default=0.0, ge=0.0)
    assumptions: Optional[str] = "Work commences upon receipt of initial deposit."
    exclusions: Optional[str] = "Any 3rd-party subscription or transaction fees."
    validity_days: int = Field(default=14, ge=1)
    payment_terms: str = "50% deposit, 50% upon completion"

class ChangeOrderUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None  # draft, ready_for_review, approved_by_freelancer, sent, accepted_by_client, declined
    line_items: Optional[List[ChangeOrderLineItem]] = None
    tax_rate_percent: Optional[float] = None
    assumptions: Optional[str] = None
    exclusions: Optional[str] = None
    validity_days: Optional[int] = None
    payment_terms: Optional[str] = None

class ChangeOrderResponse(BaseModel):
    id: str
    project_id: str
    version: int
    title: str
    status: str
    currency: str
    line_items: List[Dict[str, Any]]
    subtotal: float
    taxes: float
    total: float
    assumptions: Optional[str] = None
    exclusions: Optional[str] = None
    validity_days: Optional[int] = None
    payment_terms: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
