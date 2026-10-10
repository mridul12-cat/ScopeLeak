from backend.app.routes.projects import router as projects_router
from backend.app.routes.contracts import router as contracts_router
from backend.app.routes.requests import router as requests_router
from backend.app.routes.findings import router as findings_router
from backend.app.routes.work import router as work_router
from backend.app.routes.impact import router as impact_router
from backend.app.routes.change_orders import router as change_orders_router
from backend.app.routes.audit import router as audit_router

__all__ = [
    "projects_router",
    "contracts_router",
    "requests_router",
    "findings_router",
    "work_router",
    "impact_router",
    "change_orders_router",
    "audit_router",
]
