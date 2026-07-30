from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

from app.models.project import Project
from app.models.workflow import Workflow
from app.models.workflow_step import WorkflowStep


settings = get_settings()

test_engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def workflow(db_session: Session) -> Workflow:
    project = Project(
        name="Test Project",
    )

    db_session.add(project)
    db_session.flush()

    workflow = Workflow(
        project_id=project.id,
        name="Test Workflow",
    )

    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)


    step1 = WorkflowStep(
    workflow_id=workflow.id,
    position=1,
    step_type="step1",
    config={"output_key": "step1"},
)

    step2 = WorkflowStep(
    workflow_id=workflow.id,
    position=2,
    step_type="step2",
    config={"output_key": "step2"},
)

    db_session.add_all([step1, step2])
    db_session.commit()
    db_session.refresh(workflow)

    return workflow

    