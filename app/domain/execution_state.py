from enum import Enum
from app.models.enums import ExecutionStatus


class InvalidTransition(Exception):
    def __init__(
        self,
        current: ExecutionStatus,
        target: ExecutionStatus,
    ) -> None:
        self.current = current
        self.target = target

        message = (
            f"Cannot transition execution "
            f"from '{current.value}' to '{target.value}'"
        )

        super().__init__(message)


ALLOWED_TRANSITIONS = {
    ExecutionStatus.PENDING: {
        ExecutionStatus.RUNNING,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.COMPLETED: set(),
    ExecutionStatus.FAILED: set(),
}


def ensure_transition(
    current: ExecutionStatus,
    target: ExecutionStatus,
) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(current, target)