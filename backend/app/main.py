from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.protected import router as protected_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.projects import router as projects_router
from app.api.routes.agreement import router as agreement_router
from app.api.routes.ai import router as ai_router
from app.api.routes.workspace import router as workspace_router
from app.api.routes.disputes import router as disputes_router
from app.api.routes.account import router as account_router
from app.api.routes.admin import router as admin_router

from app.core.config import settings

# Import models so SQLAlchemy registers them with the shared Base.
from app.models import User, ClientProfile, FreelancerProfile
from app.api.routes.milestones import router as milestones_router

from app.api.routes.payments import router as payments_router
from app.api.routes.paypal_webhooks import router as paypal_webhooks_router
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Aurevo project collaboration, agreement, AI assistance, and PayPal payment API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Health endpoint remains at /health (as defined by its router).
app.include_router(health_router)

# All application API routes use the configured /api/v1 prefix.
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(protected_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(projects_router, prefix=settings.api_v1_prefix)
app.include_router(agreement_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router)
app.include_router(workspace_router)
app.include_router(disputes_router)
app.include_router(account_router)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(payments_router, prefix="/api")
app.include_router(paypal_webhooks_router, prefix="/api")
app.include_router(milestones_router, prefix="/api")
@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    return {"message": "Aurevo API is running."}