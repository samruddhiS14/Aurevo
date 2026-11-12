import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    FREELANCER = "FREELANCER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    role = Column(
        Enum(UserRole, name="user_role"),
        nullable=False,
    )

    country = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    client_profile = relationship(
        "ClientProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    freelancer_profile = relationship(
        "FreelancerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    company_name = Column(String(180), nullable=True)

    user = relationship("User", back_populates="client_profile")


class FreelancerProfile(Base):
    __tablename__ = "freelancer_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    professional_title = Column(String(180), nullable=False)
    skills = Column(String(1000), nullable=False)
    experience_years = Column(Integer, nullable=False)

    user = relationship("User", back_populates="freelancer_profile")