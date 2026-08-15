from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ExecutionNotFoundError,
    ExecutionStillActiveError,
    RecoveryNotAllowedError,
)
from app.models.enums import ExecutionStatus
from app.models.execution import Execution
from app.models.project import Project
from app.models.workflow import Workflow


STALE_EXECUTION_THRESHOLD = timedelta(
    minutes=5
)


def _require_recoverable_state(
    execution: Execution,
    execution_id: UUID,
) -> Execution:
    if execution.status != ExecutionStatus.RUNNING:
        raise RecoveryNotAllowedError(
            f"Execution '{execution_id}' "
            "is not running."
        )

    stale_cutoff = (
        datetime.now(timezone.utc)
        - STALE_EXECUTION_THRESHOLD
    )

    if (
        execution.heartbeat_at is not None
        and execution.heartbeat_at > stale_cutoff
    ):
        raise ExecutionStillActiveError(
            execution_id
        )

    return execution


def require_recoverable_execution(
    db: Session,
    execution_id: UUID,
) -> Execution:
    execution = db.scalar(
        select(Execution)
        .where(
            Execution.id == execution_id
        )
        .with_for_update()
    )

    if execution is None:
        raise ExecutionNotFoundError(
            execution_id
        )

    return _require_recoverable_state(
        execution,
        execution_id,
    )


def require_recoverable_execution_for_user(
    db: Session,
    execution_id: UUID,
    user_id: UUID,
) -> Execution:
    execution = db.scalar(
        select(Execution)
        .join(
            Workflow,
            Execution.workflow_id
            == Workflow.id,
        )
        .join(
            Project,
            Workflow.project_id
            == Project.id,
        )
        .where(
            Execution.id == execution_id,
            Project.user_id == user_id,
        )
        .with_for_update(
            of=Execution
        )
    )

    if execution is None:
        raise ExecutionNotFoundError(
            execution_id
        )

    return _require_recoverable_state(
        execution,
        execution_id,
    )
