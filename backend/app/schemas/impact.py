from typing import List, Optional
from pydantic import BaseModel

class WorkItemBreakdown(BaseModel):
    id: str
    description: str
    hours: float
    hours_type: str  # estimated, logged
    hourly_rate: float
    line_total: float
    approval_status: str
    work_status: str
    linked_request_id: Optional[str] = None
    finding_classification: Optional[str] = None

class FinancialImpactResponse(BaseModel):
    project_id: str
    currency: str
    potential_unapproved_hours: float
    potential_unapproved_value: float
    draft_change_order_value: float
    approved_by_freelancer_value: float
    accepted_by_client_value: float
    estimated_revenue_at_risk: float
    items_with_missing_rates_count: int
    breakdown: List[WorkItemBreakdown]
