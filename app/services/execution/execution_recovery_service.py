from datetime import datetime, timedelta, timezone
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


STALE_EXECUTION_THRESHOLD = timedelta(minutes=5)


def require_recoverable_execution(
    db: Session,
    execution_id: UUID,
) -> Execution:
    execution = db.scalar(
        select(Execution)
        .where(Execution.id == execution_id)
        .with_for_update()
    )

    if execution is None:
        raise ExecutionNotFoundError(execution_id)

    if execution.status != ExecutionStatus.RUNNING:
        raise RecoveryNotAllowedError(
            f"Execution '{execution_id}' is not running."
        )

    stale_cutoff = (
        datetime.now(timezone.utc)
        - STALE_EXECUTION_THRESHOLD
    )

    if (
        execution.heartbeat_at is not None
        and execution.heartbeat_at > stale_cutoff
    ):
        raise ExecutionStillActiveError(execution_id)

    return execution