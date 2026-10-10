from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ClientRequestBase(BaseModel):
    message_text: str = Field(..., min_length=1)
    sender: Optional[str] = "Client"
    external_source: str = "manual"
    message_timestamp: Optional[datetime] = None

class ClientRequestCreate(ClientRequestBase):
    pass

class ClientRequestImportItem(BaseModel):
    message_text: str
    sender: Optional[str] = None
    external_source: Optional[str] = "csv_import"
    message_timestamp: Optional[str] = None

class ClientRequestImportRequest(BaseModel):
    messages: List[ClientRequestImportItem]

class ClientRequestResponse(ClientRequestBase):
    id: str
    project_id: str
    content_hash: str
    imported_at: datetime

    model_config = {"from_attributes": True}
