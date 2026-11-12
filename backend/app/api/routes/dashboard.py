
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.routes.auth import require_role

from app.services.dashboard_service import (
    get_client_dashboard,
    get_freelancer_dashboard,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/client")
def client_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT)),
):
    return get_client_dashboard(db, current_user.id)


@router.get("/freelancer")
def freelancer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.FREELANCER)),
):
    return get_freelancer_dashboard(db, current_user.id)
