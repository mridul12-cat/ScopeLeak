from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.schemas.impact import FinancialImpactResponse
from backend.app.services.pricing_service import calculate_project_financial_impact

router = APIRouter(prefix="/api/projects/{project_id}/impact", tags=["financial impact"])

@router.get("", response_model=FinancialImpactResponse)
def get_financial_impact(project_id: str, db: Session = Depends(get_db)):
    """
    Returns transparent, deterministic financial calculations for the project.
    Distinguishes potential unapproved estimates from approved change orders.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    impact = calculate_project_financial_impact(db, project)
    return impact
