from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.services import project_service

router = APIRouter()


@router.get("/db-check", tags=["system"])
def database_check(
    db: Session = Depends(get_db),#depends - This endpoint needs something before it can run.Before running this endpoint, call get_db() and use the yielded value as db
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }

@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    return project_service.create(db, payload)