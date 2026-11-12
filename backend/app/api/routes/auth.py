import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.config import settings
from app.models.user import (
    User,
    UserRole,
    ClientProfile,
    FreelancerProfile,
)
from app.schemas.auth import (
    ClientRegister,
    FreelancerRegister,
    LoginRequest,
    UserResponse,
    AuthResponse,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = int(payload["sub"])
        token_role = payload["role"]
        token_version = int(payload.get("ver", 0))

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise unauthorized

    # A role change invalidates a token carrying the previous role.
    if user.role.value != token_role or user.token_version != token_version:
        raise unauthorized

    return user


def require_role(required_role: UserRole):
    def role_dependency(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return user

    return role_dependency


def ensure_passwords_match(password: str, confirmation: str):
    if password != confirmation:
        raise HTTPException(
            status_code=422,
            detail="Passwords do not match",
        )


def ensure_terms_accepted(accepted: bool):
    if not accepted:
        raise HTTPException(
            status_code=422,
            detail="You must accept the terms and conditions",
        )


def ensure_unique_email(db: Session, email: str):
    existing = db.query(User).filter(
        User.email == email.lower()
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )


def build_auth_response(user: User):
    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        token_version=user.token_version,
    )

    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/client/register", response_model=AuthResponse)
def register_client(data: ClientRegister, db: Session = Depends(get_db)):
    ensure_passwords_match(data.password, data.confirm_password)
    ensure_terms_accepted(data.terms_accepted)
    ensure_unique_email(db, str(data.email).lower())

    user = User(
        full_name=data.full_name.strip(),
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        role=UserRole.CLIENT,
        country=data.country.strip(),
    )

    user.client_profile = ClientProfile(
        company_name=(data.company_name or "").strip() or None
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    return build_auth_response(user)


@router.post("/freelancer/register", response_model=AuthResponse)
def register_freelancer(
    data: FreelancerRegister,
    db: Session = Depends(get_db),
):
    ensure_passwords_match(data.password, data.confirm_password)
    ensure_terms_accepted(data.terms_accepted)
    ensure_unique_email(db, str(data.email).lower())

    clean_skills = [
        skill.strip()
        for skill in data.skills
        if skill.strip()
    ]

    if not clean_skills:
        raise HTTPException(
            status_code=422,
            detail="Please provide at least one valid skill",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        role=UserRole.FREELANCER,
        country=data.country.strip(),
    )

    user.freelancer_profile = FreelancerProfile(
        professional_title=data.professional_title.strip(),
        skills=", ".join(clean_skills),
        experience_years=data.experience_years,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    return build_auth_response(user)


def login_for_role(
    data: LoginRequest,
    expected_role: UserRole,
    db: Session,
):
    user = db.query(User).filter(
        User.email == str(data.email).lower()
    ).first()

    # Keep the error generic to avoid revealing whether an email exists.
    if (
        not user
        or not verify_password(data.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if user.role != expected_role:
        raise HTTPException(
            status_code=403,
            detail="This account belongs to the other portal",
        )

    return build_auth_response(user)


@router.post("/client/login", response_model=AuthResponse)
def client_login(data: LoginRequest, db: Session = Depends(get_db)):
    return login_for_role(data, UserRole.CLIENT, db)


@router.post("/freelancer/login", response_model=AuthResponse)
def freelancer_login(data: LoginRequest, db: Session = Depends(get_db)):
    return login_for_role(data, UserRole.FREELANCER, db)


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)

@router.post("/admin/login", response_model=AuthResponse)
def admin_login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate an administrator provisioned through the backend CLI."""
    return login_for_role(data, UserRole.ADMIN, db)
