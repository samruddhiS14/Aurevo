from fastapi import APIRouter, Depends

from app.api.routes.auth import require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/protected", tags=["Protected routes"])


@router.get("/client")
def client_only(
    user: User = Depends(require_role(UserRole.CLIENT)),
):
    return {"message": "Client access granted"}


@router.get("/freelancer")
def freelancer_only(
    user: User = Depends(require_role(UserRole.FREELANCER)),
):
    return {"message": "Freelancer access granted"}