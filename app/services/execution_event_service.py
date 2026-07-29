from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.execution_event import ExecutionEvent


def create_execution_event(
    db: Session,
    execution_id: UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
) -> ExecutionEvent:
    event = ExecutionEvent(
        execution_id=execution_id,
        event_type=event_type,
        details=details or {},
        actor=actor,
        correlation_id=correlation_id,
    )

    db.add(event)

    return event