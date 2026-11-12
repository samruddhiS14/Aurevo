from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, UserRole, Project, AIScopeVersion, Milestone, ProjectMessage, AISubmissionReview
from app.schemas.ai_scope import ScopeGenerationRequest, ScopeEditRequest, CopilotRequest, SubmissionComparisonRequest, SubmissionComparisonResult
from app.services.scope_generator_service import generate_project_scope
from app.services.gemini_service import GeminiService
from app.services.gemini_errors import GeminiUnavailableError, GeminiInvalidResponseError
from app.services.scope_validation import reconcile_scope_data
from app.services.project_copilot_service import answer_project_question

router = APIRouter(prefix="/api/v1/ai", tags=["AI Copilot"])

def _project_access(db, project_id, user):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found.")
    if user.id not in (project.client_id, project.freelancer_id):
        raise HTTPException(403, "You are not a participant in this project.")
    return project

@router.post("/projects/{project_id}/scope")
def generate_scope(project_id: int, payload: ScopeGenerationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = _project_access(db, project_id, user)
    if user.role != UserRole.CLIENT or project.client_id != user.id:
        raise HTTPException(403, "Only the project client can generate a scope draft.")
    try:
        return generate_project_scope(db, project, user.id, payload.additional_instructions)
    except GeminiUnavailableError as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "30"})
    except GeminiInvalidResponseError as exc:
        raise HTTPException(502, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))

@router.get("/projects/{project_id}/scope")
def list_scope_versions(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _project_access(db, project_id, user)
    rows = db.query(AIScopeVersion).filter(AIScopeVersion.project_id == project_id).order_by(AIScopeVersion.version_number.desc()).all()
    return [{"id": r.id, "project_id": r.project_id, "version_number": r.version_number, "scope_data": r.scope_data, "status": r.status, "is_approved": r.is_approved, "created_at": r.created_at} for r in rows]

@router.put("/scope/{scope_id}")
def edit_scope(scope_id: int, payload: ScopeEditRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scope = db.get(AIScopeVersion, scope_id)
    if not scope:
        raise HTTPException(404, "Scope version not found.")
    project = _project_access(db, scope.project_id, user)
    if user.role != UserRole.CLIENT or project.client_id != user.id:
        raise HTTPException(403, "Only the project client can edit the scope.")
    if scope.is_approved:
        raise HTTPException(409, "Approved scope versions are immutable. Generate a new version to change scope.")
    try:
        reconciled = reconcile_scope_data(payload.scope_data, project.budget)
    except (ValueError, GeminiInvalidResponseError) as exc:
        raise HTTPException(422, str(exc))
    scope.scope_data = reconciled.model_dump(mode="json")
    db.commit(); db.refresh(scope)
    return {"id": scope.id, "version_number": scope.version_number, "scope_data": scope.scope_data, "status": scope.status}

@router.post("/scope/{scope_id}/approve")
def approve_scope(scope_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scope = db.get(AIScopeVersion, scope_id)
    if not scope:
        raise HTTPException(404, "Scope version not found.")
    project = _project_access(db, scope.project_id, user)
    if user.role != UserRole.CLIENT or project.client_id != user.id:
        raise HTTPException(403, "Only the project client can approve the scope.")
    if scope.is_approved:
        return {"id": scope.id, "status": scope.status, "is_approved": True, "idempotent": True}
    scope.is_approved = True
    scope.status = "approved"
    scope.approved_by = user.id
    scope.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": scope.id, "status": scope.status, "is_approved": True, "approved_at": scope.approved_at}

@router.post("/projects/{project_id}/copilot")
def project_copilot(project_id: int, payload: CopilotRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = _project_access(db, project_id, user)
    try:
        answer = answer_project_question(db, project, payload.question)
    except GeminiUnavailableError as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "30"})
    except GeminiInvalidResponseError as exc:
        raise HTTPException(502, str(exc))
    return {"answer": answer, "advisory_only": True, "payment_actions_taken": False}

@router.post("/milestones/{milestone_id}/submission-review")
def review_submission(milestone_id: int, payload: SubmissionComparisonRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        raise HTTPException(404, "Milestone not found.")
    project = _project_access(db, milestone.project_id, user)
    if milestone.status not in ("submitted", "under_review"):
        raise HTTPException(409, "Only submitted work can be compared with the agreed criteria.")
    scope = db.query(AIScopeVersion).filter(AIScopeVersion.project_id == project.id, AIScopeVersion.is_approved.is_(True), AIScopeVersion.status == "approved").order_by(AIScopeVersion.version_number.desc()).first()
    if not scope:
        raise HTTPException(409, "An approved AI scope is required before submission comparison.")
    prompt = "Compare the freelancer's submission with the milestone requirements. Return JSON keys requirements_fulfilled, potentially_missing_requirements, possible_scope_deviations, clarification_questions, overall_assessment (appears_aligned, partially_aligned, needs_clarification), disclaimer. Do not approve, reject, request revisions, or trigger payments. This is advisory only.\nMilestone: " + str({"title": milestone.title, "description": milestone.description, "deliverables": milestone.deliverables, "criteria": milestone.completion_criteria}) + "\nSubmission: " + payload.submission_description
    try:
        result = GeminiService().generate_json(prompt)
    except GeminiUnavailableError as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "30"})
    except GeminiInvalidResponseError as exc:
        raise HTTPException(502, str(exc))
    try:
        result = SubmissionComparisonResult.model_validate(result).model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(502, "AI returned an invalid submission review. Please retry.") from exc
    result["advisory_only"] = True
    result["decision_made"] = False
    db.add(AISubmissionReview(project_id=project.id, milestone_id=milestone.id, scope_version_id=scope.id, submitted_by=user.id, submission_description=payload.submission_description, review_result=result))
    db.commit()
    return result
