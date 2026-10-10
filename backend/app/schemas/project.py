from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    client_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    currency: str = Field(default="INR", max_length=10)
    default_hourly_rate: float = Field(default=2000.0, ge=0.0)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    default_hourly_rate: Optional[float] = None
    status: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
