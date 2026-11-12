from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, UserRole, ClientProfile, FreelancerProfile, Notification, Project, Milestone, ProjectReview
from app.services.auth_service import verify_password, hash_password

router = APIRouter(prefix="/api/v1", tags=["Account"])

class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    company_name: str | None = Field(default=None, max_length=180)
    professional_title: str | None = Field(default=None, max_length=180)
    skills: str | None = Field(default=None, max_length=1000)
    experience_years: int | None = Field(default=None, ge=0, le=60)

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=3000)

@router.get("/account/profile")
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = user.client_profile if user.role == UserRole.CLIENT else user.freelancer_profile
    ratings = db.query(func.avg(ProjectReview.rating), func.count(ProjectReview.id)).filter(ProjectReview.reviewee_id == user.id).first()
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role.value, "country": user.country,
        "profile": ({"company_name": profile.company_name} if user.role == UserRole.CLIENT and profile else
                    {"professional_title": profile.professional_title, "skills": profile.skills, "experience_years": profile.experience_years} if profile else {}),
        "average_rating": float(ratings[0]) if ratings and ratings[0] is not None else None,
        "review_count": int(ratings[1] or 0) if ratings else 0}

@router.patch("/account/profile")
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = payload.model_dump(exclude_unset=True)
    for field in ("full_name", "country"):
        if field in data:
            setattr(user, field, data[field].strip())
    if user.role == UserRole.CLIENT:
        if any(k in data for k in ("professional_title", "skills", "experience_years")):
            raise HTTPException(422, "Freelancer-only profile fields cannot be changed on a client account.")
        if not user.client_profile:
            user.client_profile = ClientProfile()
        if "company_name" in data:
            user.client_profile.company_name = data["company_name"].strip() or None
    else:
        if "company_name" in data:
            raise HTTPException(422, "Client-only profile fields cannot be changed on a freelancer account.")
        if not user.freelancer_profile:
            user.freelancer_profile = FreelancerProfile(professional_title="Freelancer", skills="", experience_years=0)
        if "professional_title" in data:
            user.freelancer_profile.professional_title = data["professional_title"].strip()
        if "skills" in data:
            user.freelancer_profile.skills = data["skills"].strip()
        if "experience_years" in data:
            user.freelancer_profile.experience_years = data["experience_years"]
    db.commit(); db.refresh(user)
    return get_profile(db, user)

@router.post("/account/password")
def change_password(payload: PasswordUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    if payload.current_password == payload.new_password:
        raise HTTPException(422, "Choose a new password different from the current password.")
    user.password_hash = hash_password(payload.new_password)
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    return {"updated": True, "message": "Password updated. All existing sessions have been invalidated; sign in again."}

@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in rows]

@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if not notification:
        raise HTTPException(404, "Notification not found.")
    notification.is_read = True
    db.commit()
    return {"id": notification.id, "is_read": True}

@router.post("/notifications/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"updated": count}

@router.post("/projects/{project_id}/reviews")
def create_review(project_id: int, payload: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project or user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(404, "Completed project not found for this account.")
    if not project.freelancer_id:
        raise HTTPException(409, "A freelancer must be assigned before reviewing the project.")
    milestones = db.query(Milestone).filter(Milestone.project_id == project_id, Milestone.is_current.is_(True)).all()
    if not milestones or any(m.status != "paid" for m in milestones):
        raise HTTPException(409, "Reviews are available only after every current project milestone is paid and completed.")
    reviewee_id = project.freelancer_id if user.id == project.client_id else project.client_id
    existing = db.query(ProjectReview).filter(ProjectReview.project_id == project_id, ProjectReview.reviewer_id == user.id).first()
    if existing:
        raise HTTPException(409, "You have already reviewed this project.")
    review = ProjectReview(project_id=project_id, reviewer_id=user.id, reviewee_id=reviewee_id, rating=payload.rating, comment=payload.comment)
    db.add(review)
    db.add(Notification(user_id=reviewee_id, title="You received a project review", message=f"A participant left a {payload.rating}-star review for '{project.title}'."))
    db.commit(); db.refresh(review)
    return {"id": review.id, "project_id": review.project_id, "reviewer_id": review.reviewer_id, "reviewee_id": review.reviewee_id, "rating": review.rating, "comment": review.comment, "created_at": review.created_at}

@router.get("/account/reviews")
def get_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ProjectReview).filter(ProjectReview.reviewee_id == user.id).order_by(ProjectReview.created_at.desc()).all()
    return [{"id": r.id, "project_id": r.project_id, "reviewer_id": r.reviewer_id, "rating": r.rating, "comment": r.comment, "created_at": r.created_at} for r in rows]
