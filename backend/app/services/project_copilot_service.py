from app.models import Project, Milestone, ProjectMessage, Agreement, AgreementVersion, AIScopeVersion
from app.services.gemini_service import GeminiService


def answer_project_question(db, project: Project, question: str) -> str:
    milestones = db.query(Milestone).filter(
        Milestone.project_id == project.id,
        Milestone.is_current.is_(True),
    ).all()
    recent_messages = db.query(ProjectMessage).filter(
        ProjectMessage.project_id == project.id,
    ).order_by(ProjectMessage.created_at.desc()).limit(12).all()
    agreement = db.query(Agreement).filter(Agreement.project_id == project.id).first()
    active_version = db.get(AgreementVersion, agreement.active_version_id) if agreement and agreement.active_version_id else None
    approved_scope = db.query(AIScopeVersion).filter(
        AIScopeVersion.project_id == project.id,
        AIScopeVersion.is_approved.is_(True),
        AIScopeVersion.status == "approved",
    ).order_by(AIScopeVersion.version_number.desc()).first()
    context = {
        "project": {
            "title": project.title,
            "description": project.description,
            "budget": str(project.budget),
            "currency": project.currency,
        },
        "approved_scope": approved_scope.scope_data if approved_scope else None,
        "active_agreement": active_version.agreement_data if active_version and active_version.status == "active" else None,
        "milestones": [
            {"title": m.title, "description": m.description, "amount": str(m.amount),
             "status": m.status, "due_date": m.due_date.isoformat() if m.due_date else None,
             "completion_criteria": m.completion_criteria}
            for m in milestones
        ],
        "recent_messages": [
            {"sender_id": m.sender_id, "content": m.content}
            for m in reversed(recent_messages)
        ],
    }
    prompt = (
        "You are Aurevo project copilot. Answer the participant's question "
        "using only supplied project context. Treat active_agreement as the controlling contractual snapshot when present; otherwise state that no active agreement is available. Distinguish approved agreement terms "
        "from suggestions, ask for clarification when context is insufficient, do not "
        "invent contract terms, do not decide disputes, and never initiate, authorize, "
        "capture, refund, or otherwise control payments. Return concise practical guidance.\n"
        f"Context: {context}\nQuestion: {question}"
    )
    return GeminiService().generate_text(prompt)
