import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import IdempotencyConflictError
from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent
from app.models.enums import ExecutionStatus


def _generate_input_hash(input_data: dict[str, Any]) -> str:
    normalized_input = json.dumps(
        input_data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        normalized_input.encode("utf-8")
    ).hexdigest()


def create_or_return_existing(
    db: Session,
    workflow_id: UUID,  # Change to int if your Workflow.id is an integer
    idempotency_key: str,
    initial_context: dict[str, Any],
) -> tuple[Execution, bool]:
    input_hash = _generate_input_hash(initial_context)

    existing_execution = db.scalar(
        select(Execution).where(
            Execution.workflow_id == workflow_id,
            Execution.idempotency_key == idempotency_key,
        )
    )

    if existing_execution:
        if existing_execution.input_hash != input_hash:
            raise IdempotencyConflictError(
                "Idempotency key was already used with a different payload"
            )

        return existing_execution, False

    execution = Execution(
        workflow_id=workflow_id,
        idempotency_key=idempotency_key,
        input_data=initial_context.copy(),
        input_hash=input_hash,
        status=ExecutionStatus.QUEUED,
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution, True


def get_execution_events(
    db: Session,
    execution_id: UUID,
) -> list[ExecutionEvent]:
    execution = db.get(
        Execution,
        execution_id,
    )

    if execution is None:
        raise ValueError("Execution not found")

    statement = (
        select(ExecutionEvent)
        .where(
            ExecutionEvent.execution_id == execution_id
        )
        .order_by(
            ExecutionEvent.sequence_number.asc(),
        )
    )

    events = db.scalars(statement).all()

    return list(events)

def get_execution_events_for_user(
    db: Session,
    execution_id: UUID,
    user_id: UUID,
) -> list[ExecutionEvent]:
    from app.models.project import Project
    from app.models.workflow import Workflow

    execution = db.scalar(
        select(Execution)
        .join(
            Workflow,
            Execution.workflow_id == Workflow.id,
        )
        .join(
            Project,
            Workflow.project_id == Project.id,
        )
        .where(
            Execution.id == execution_id,
            Project.user_id == user_id,
        )
    )

    if execution is None:
        raise ValueError(
            "Execution not found"
        )

    statement = (
        select(ExecutionEvent)
        .where(
            ExecutionEvent.execution_id
            == execution.id
        )
        .order_by(
            ExecutionEvent.sequence_number.asc(),
        )
    )

    events = db.scalars(statement).all()

    return list(events)
