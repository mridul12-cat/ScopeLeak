from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ContractResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    content_hash: str
    extracted_text: Optional[str] = None
    processing_status: str
    baseline_review_status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}

class ContractExtractRequest(BaseModel):
    contract_id: Optional[str] = None
    force_reextract: bool = False
