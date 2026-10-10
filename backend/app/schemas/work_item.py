from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class WorkItemBase(BaseModel):
    description: str = Field(..., min_length=1)
    source_type: str = "manual"
    external_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    work_status: str = "logged"
    approval_status: str = "unapproved"
    source_reference: Optional[str] = None
    request_id: Optional[str] = None

class WorkItemCreate(WorkItemBase):
    pass

class WorkItemUpdate(BaseModel):
    description: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    work_status: Optional[str] = None
    approval_status: Optional[str] = None
    request_id: Optional[str] = None

class WorkItemImportItem(BaseModel):
    description: str
    source_type: Optional[str] = "csv_import"
    external_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    work_status: Optional[str] = "logged"
    approval_status: Optional[str] = "unapproved"
    source_reference: Optional[str] = None
    request_id: Optional[str] = None

class WorkItemImportRequest(BaseModel):
    items: List[WorkItemImportItem]

class WorkItemResponse(WorkItemBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
