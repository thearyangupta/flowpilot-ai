from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.execution import Execution
from app.models.project import Project
from app.models.user import User
from app.models.workflow import Workflow
from app.models.enums import ExecutionStatus


def create_user(
    db: Session,
    email: str,
) -> User:
    user = User(
        email=email,
        display_name=email,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def auth_headers(
    user: User,
) -> dict[str, str]:
    token = create_access_token(
        user.id
    )

    return {
        "Authorization":
            f"Bearer {token}",
    }


def create_project(
    db: Session,
    user: User,
    name: str,
) -> Project:
    project = Project(
        user_id=user.id,
        name=name,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def create_workflow(
    db: Session,
    project: Project,
) -> Workflow:
    workflow = Workflow(
        project_id=project.id,
        name="Private Workflow",
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


def create_execution(
    db: Session,
    workflow: Workflow,
) -> Execution:
    execution = Execution(
        workflow_id=workflow.id,
        idempotency_key=(
            f"tenant-test-{uuid4()}"
        ),
        input_data={
            "test": True,
        },
        input_hash="tenant-test-hash",
        status=ExecutionStatus.QUEUED,
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


def test_project_listing_is_user_scoped(
    client: TestClient,
    db_session: Session,
) -> None:
    user_a = create_user(
        db_session,
        "tenant-a@example.com",
    )

    user_b = create_user(
        db_session,
        "tenant-b@example.com",
    )

    project_a = create_project(
        db_session,
        user_a,
        "Tenant A Project",
    )

    create_project(
        db_session,
        user_b,
        "Tenant B Project",
    )

    response = client.get(
        "/api/v1/projects",
        headers=auth_headers(user_a),
    )

    assert response.status_code == 200

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert str(project_a.id) in returned_ids
    assert len(returned_ids) == 1


def test_other_user_cannot_list_workflows(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        "workflow-owner@example.com",
    )

    attacker = create_user(
        db_session,
        "workflow-attacker@example.com",
    )

    project = create_project(
        db_session,
        owner,
        "Private Project",
    )

    create_workflow(
        db_session,
        project,
    )

    response = client.get(
        f"/api/v1/projects/"
        f"{project.id}/workflows",
        headers=auth_headers(attacker),
    )

    assert response.status_code == 404


def test_other_user_cannot_read_execution(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        "execution-owner@example.com",
    )

    attacker = create_user(
        db_session,
        "execution-attacker@example.com",
    )

    project = create_project(
        db_session,
        owner,
        "Execution Project",
    )

    workflow = create_workflow(
        db_session,
        project,
    )

    execution = create_execution(
        db_session,
        workflow,
    )

    response = client.get(
        f"/api/v1/executions/"
        f"{execution.id}",
        headers=auth_headers(attacker),
    )

    assert response.status_code == 404


def test_other_user_cannot_read_execution_events(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        "events-owner@example.com",
    )

    attacker = create_user(
        db_session,
        "events-attacker@example.com",
    )

    project = create_project(
        db_session,
        owner,
        "Events Project",
    )

    workflow = create_workflow(
        db_session,
        project,
    )

    execution = create_execution(
        db_session,
        workflow,
    )

    response = client.get(
        f"/api/v1/executions/"
        f"{execution.id}/events",
        headers=auth_headers(attacker),
    )

    assert response.status_code == 404


def test_other_user_cannot_resume_execution(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        "resume-owner@example.com",
    )

    attacker = create_user(
        db_session,
        "resume-attacker@example.com",
    )

    project = create_project(
        db_session,
        owner,
        "Resume Project",
    )

    workflow = create_workflow(
        db_session,
        project,
    )

    execution = create_execution(
        db_session,
        workflow,
    )

    execution.status = (
        ExecutionStatus.RUNNING
    )

    db_session.commit()

    response = client.post(
        f"/api/v1/executions/"
        f"{execution.id}/resume",
        headers=auth_headers(attacker),
    )

    assert response.status_code == 404


def test_project_routes_require_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/projects"
    )

    assert response.status_code == 401
