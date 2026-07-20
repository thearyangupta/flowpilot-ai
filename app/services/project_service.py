from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


def create(db: Session, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())

    db.add(project)
    db.commit()
    db.refresh(project)

    return project