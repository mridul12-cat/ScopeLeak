import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.contract import Contract
from backend.app.models.scope_item import ScopeItem
from backend.app.schemas.contract import ContractResponse, ContractExtractRequest
from backend.app.schemas.scope_item import (
    ScopeItemResponse,
    ScopeItemCreate,
    ScopeItemUpdate,
    BaselineBatchUpdate,
)
from backend.app.services.contract_extractor import extract_text_from_file
from backend.app.services.ai_service import ai_engine
from backend.app.services.audit_service import log_audit_event
from backend.app.utils.hashing import compute_file_hash, compute_text_hash
from backend.app.config import settings

router = APIRouter(prefix="/api/projects/{project_id}", tags=["contracts & baseline"])

@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type
    allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".md"}
    filename = file.filename or "contract.txt"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Please upload a PDF, DOCX, or text file."
        )

    # Read bytes and compute hash
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size exceeds 15MB limit")

    content_hash = compute_file_hash(contents)

    # Check for duplicate contract upload in this project
    existing = db.query(Contract).filter(
        Contract.project_id == project_id,
        Contract.content_hash == content_hash
    ).first()
    if existing:
        return existing

    # Save to upload dir
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{filename}"
    saved_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    with open(saved_path, "wb") as f:
        f.write(contents)

    # Extract text immediately
    try:
        extracted = extract_text_from_file(saved_path, filename)
        extracted_text = extracted.get("full_text", "")
        processing_status = "extracted"
    except Exception as e:
        extracted_text = ""
        processing_status = "failed"

    contract = Contract(
        project_id=project_id,
        filename=filename,
        file_path=saved_path,
        content_hash=content_hash,
        extracted_text=extracted_text,
        processing_status=processing_status,
        baseline_review_status="pending_review",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="contract_uploaded",
        entity_type="contract",
        entity_id=contract.id,
        description=f"Uploaded contract '{filename}' ({len(contents)} bytes). Processing status: {processing_status}.",
    )
    return contract

@router.get("/contracts", response_model=List[ContractResponse])
def list_contracts(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Contract).filter(Contract.project_id == project_id).order_by(Contract.uploaded_at.desc()).all()

@router.post("/baseline/extract", response_model=List[ScopeItemResponse])
async def extract_baseline(
    project_id: str,
    req: ContractExtractRequest = ContractExtractRequest(),
    db: Session = Depends(get_db),
):
    """
    Extract proposed deliverables, exclusions, revisions, and milestones with clause references.
    AI interprets the evidence; user must explicitly confirm baseline before authoritative comparison.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    contract = None
    if req.contract_id:
        contract = db.query(Contract).filter(Contract.id == req.contract_id, Contract.project_id == project_id).first()
    if not contract:
        contract = db.query(Contract).filter(Contract.project_id == project_id).order_by(Contract.uploaded_at.desc()).first()

    if not contract or not contract.extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No contract with extracted text found. Please upload a contract first."
        )

    # Perform structured extraction
    result = await ai_engine.extract_contract_scope(contract.extracted_text, contract.filename)

    # If force_reextract, remove previous unconfirmed items
    if req.force_reextract:
        db.query(ScopeItem).filter(
            ScopeItem.project_id == project_id,
            ScopeItem.contract_id == contract.id,
            ScopeItem.review_status == "pending"
        ).delete()
        db.commit()

    created_items = []
    for item in result.items:
        scope_item = ScopeItem(
            project_id=project_id,
            contract_id=contract.id,
            item_type=item.item_type,
            description=item.description,
            normalized_description=item.normalized_description,
            source_clause_id=item.source_clause_id,
            source_quote=item.source_quote,
            page_number=item.page_number,
            section_reference=item.section_reference,
            review_status="pending",  # Crucial: Unconfirmed until human review
        )
        db.add(scope_item)
        created_items.append(scope_item)

    db.commit()
    for ci in created_items:
        db.refresh(ci)

    log_audit_event(
        db,
        project_id=project_id,
        actor="system",
        event_type="baseline_extracted",
        entity_type="contract",
        entity_id=contract.id,
        description=f"Extracted {len(created_items)} baseline scope items. Pending human review.",
    )
    return created_items

@router.get("/baseline", response_model=List[ScopeItemResponse])
def get_baseline(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(ScopeItem).filter(ScopeItem.project_id == project_id).order_by(ScopeItem.created_at.asc()).all()

@router.patch("/baseline", response_model=List[ScopeItemResponse])
def update_baseline(
    project_id: str,
    update_data: BaselineBatchUpdate,
    db: Session = Depends(get_db),
):
    """Confirm or update multiple baseline items in batch."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items = db.query(ScopeItem).filter(ScopeItem.project_id == project_id).all()
    if update_data.confirm_all:
        for it in items:
            it.review_status = "confirmed"
        # Also mark contracts as confirmed
        contracts = db.query(Contract).filter(Contract.project_id == project_id).all()
        for c in contracts:
            c.baseline_review_status = "confirmed"
        db.commit()
        log_audit_event(
            db,
            project_id=project_id,
            actor="user",
            event_type="baseline_confirmed",
            entity_type="project",
            entity_id=project_id,
            description="Freelancer reviewed and confirmed entire contract baseline scope.",
        )

    return db.query(ScopeItem).filter(ScopeItem.project_id == project_id).all()

@router.post("/scope", response_model=ScopeItemResponse, status_code=status.HTTP_201_CREATED)
def add_scope_item(project_id: str, item_in: ScopeItemCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scope_item = ScopeItem(
        project_id=project_id,
        contract_id=item_in.contract_id,
        item_type=item_in.item_type,
        description=item_in.description,
        normalized_description=item_in.normalized_description or item_in.description[:50],
        source_clause_id=item_in.source_clause_id,
        source_quote=item_in.source_quote,
        page_number=item_in.page_number,
        section_reference=item_in.section_reference,
        review_status=item_in.review_status,
    )
    db.add(scope_item)
    db.commit()
    db.refresh(scope_item)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="scope_item_created",
        entity_type="scope_item",
        entity_id=scope_item.id,
        description=f"Added manual scope item: {scope_item.description[:60]}",
    )
    return scope_item

@router.patch("/scope/{scope_item_id}", response_model=ScopeItemResponse)
def update_scope_item(
    project_id: str,
    scope_item_id: str,
    item_in: ScopeItemUpdate,
    db: Session = Depends(get_db),
):
    scope_item = db.query(ScopeItem).filter(
        ScopeItem.id == scope_item_id,
        ScopeItem.project_id == project_id
    ).first()
    if not scope_item:
        raise HTTPException(status_code=404, detail="Scope item not found")

    before = {"description": scope_item.description, "status": scope_item.review_status}

    if item_in.item_type is not None:
        scope_item.item_type = item_in.item_type
    if item_in.description is not None:
        scope_item.description = item_in.description
    if item_in.normalized_description is not None:
        scope_item.normalized_description = item_in.normalized_description
    if item_in.source_clause_id is not None:
        scope_item.source_clause_id = item_in.source_clause_id
    if item_in.source_quote is not None:
        scope_item.source_quote = item_in.source_quote
    if item_in.page_number is not None:
        scope_item.page_number = item_in.page_number
    if item_in.section_reference is not None:
        scope_item.section_reference = item_in.section_reference
    if item_in.review_status is not None:
        scope_item.review_status = item_in.review_status

    db.commit()
    db.refresh(scope_item)

    log_audit_event(
        db,
        project_id=project_id,
        actor="user",
        event_type="scope_item_updated",
        entity_type="scope_item",
        entity_id=scope_item.id,
        description=f"Updated scope item {scope_item.id[:8]}",
        before_state=before,
        after_state={"description": scope_item.description, "status": scope_item.review_status},
    )
    return scope_item

@router.delete("/scope/{scope_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scope_item(project_id: str, scope_item_id: str, db: Session = Depends(get_db)):
    scope_item = db.query(ScopeItem).filter(
        ScopeItem.id == scope_item_id,
        ScopeItem.project_id == project_id
    ).first()
    if not scope_item:
        raise HTTPException(status_code=404, detail="Scope item not found")
    db.delete(scope_item)
    db.commit()
    return None
