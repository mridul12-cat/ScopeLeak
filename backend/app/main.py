import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import *  # ensure all models are registered
from backend.app.routes import (
    projects_router,
    contracts_router,
    requests_router,
    findings_router,
    work_router,
    impact_router,
    change_orders_router,
    audit_router,
)
from backend.app.services.seed_service import seed_demo_project
from backend.app.services.ai_service import ai_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    # Proactively seed Northstar demo project so out-of-the-box experience works instantly
    db = SessionLocal()
    try:
        seed_demo_project(db, force_reset=False)
    finally:
        db.close()
    yield

app = FastAPI(
    title="ScopeLeak API",
    description="AI Scope-Change Evidence Engine for Software Freelancers & Agencies",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(projects_router)
app.include_router(contracts_router)
app.include_router(requests_router)
app.include_router(findings_router)
app.include_router(work_router)
app.include_router(impact_router)
app.include_router(change_orders_router)
app.include_router(audit_router)

@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint displaying system and AI provider configuration status."""
    return {
        "status": "healthy",
        "service": "ScopeLeak API",
        "version": "1.0.0",
        "gemini_configured": ai_engine.provider.is_configured(),
        "gemini_model": settings.GEMINI_MODEL,
        "environment": settings.ENVIRONMENT,
    }

# Single-service deployment: Serve built frontend if dist exists
dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.isdir(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
