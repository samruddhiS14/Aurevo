from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="open", index=True)
    ai_report = Column(JSON, nullable=True)
    resolution_summary = Column(Text, nullable=True)
    resolution_outcome = Column(String(30), nullable=True)
    resolution_proposed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    client_accepted = Column(Boolean, nullable=False, default=False)
    freelancer_accepted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    milestone = relationship("Milestone")
    raiser = relationship("User", foreign_keys=[raised_by])
    resolution_proposer = relationship("User", foreign_keys=[resolution_proposed_by])

class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"
    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(Text, nullable=True)
    mime_type = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    dispute = relationship("Dispute")
    submitter = relationship("User")
