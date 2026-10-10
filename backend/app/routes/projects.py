from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.services.audit_service import log_audit_event
from backend.app.services.seed_service import seed_demo_project

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=project_in.name,
        client_name=project_in.client_name,
        description=project_in.description,
        currency=project_in.currency or "INR",
        default_hourly_rate=project_in.default_hourly_rate,
        status="active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_audit_event(
        db,
        project_id=project.id,
        actor="user",
        event_type="project_created",
        entity_type="project",
        entity_id=project.id,
        description=f"Created project '{project.name}' for client '{project.client_name}'",
        after_state={"name": project.name, "client": project.client_name, "rate": project.default_hourly_rate},
    )
    return project

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project_in: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    before_state = {"name": project.name, "rate": project.default_hourly_rate, "status": project.status}

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.client_name is not None:
        project.client_name = project_in.client_name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.currency is not None:
        project.currency = project_in.currency
    if project_in.default_hourly_rate is not None:
        project.default_hourly_rate = project_in.default_hourly_rate
    if project_in.status is not None:
        project.status = project_in.status

    db.commit()
    db.refresh(project)

    log_audit_event(
        db,
        project_id=project.id,
        actor="user",
        event_type="project_updated",
        entity_type="project",
        entity_id=project.id,
        description=f"Updated project settings for '{project.name}'",
        before_state=before_state,
        after_state={"name": project.name, "rate": project.default_hourly_rate, "status": project.status},
    )
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None

@router.post("/demo/seed", response_model=ProjectResponse)
def seed_demo(force: bool = False, db: Session = Depends(get_db)):
    """Seed or reseed the Northstar Website Redesign demo project."""
    project = seed_demo_project(db, force_reset=force)
    return project
