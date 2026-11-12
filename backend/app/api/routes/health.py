from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def liveness_check() -> dict[str, str]:
    # Confirms the API process is responding; PostgreSQL is not required.
    return {"status": "ok", "service": "api"}


@router.get("/api/health")
def readiness_check() -> dict[str, str]:
    # Confirms both the API and PostgreSQL are available.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "api",
            "database": "connected",
            "message": "API is healthy and database is connected.",
        }
    except SQLAlchemyError as exc:
        # Do not leak connection strings or internal database errors to clients.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "service": "api",
                "database": "unavailable",
                "message": "The API is running, but PostgreSQL could not be reached. Check DATABASE_URL and PostgreSQL.",
            },
        ) from exc
