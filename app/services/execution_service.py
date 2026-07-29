from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution import Execution
from app.models.execution_event import ExecutionEvent


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
            ExecutionEvent.created_at.asc(),
            ExecutionEvent.id.asc(),
        )
    )

    events = db.scalars(statement).all()

    return list(events)