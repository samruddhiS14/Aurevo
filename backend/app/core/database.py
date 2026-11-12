from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    # SQLAlchemy ORM models will inherit from this base in later phases.
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    # FastAPI dependency: provide a session and always close it.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
