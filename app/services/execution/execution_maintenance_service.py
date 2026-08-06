from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExecutionStatus
from app.models.execution import Execution


def find_stale_executions(
    db: Session,
    stale_after: timedelta,
) -> list[Execution]:
    cutoff = datetime.now(timezone.utc) - stale_after

    statement = (
        select(Execution)
        .where(
            Execution.status == ExecutionStatus.RUNNING,
            Execution.heartbeat_at.is_not(None),
            Execution.heartbeat_at < cutoff,
        )
        .order_by(Execution.heartbeat_at.asc())
    )

    executions = db.scalars(statement).all()

    return list(executions)