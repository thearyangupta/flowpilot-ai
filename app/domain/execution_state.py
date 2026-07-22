from enum import Enum


class ExecutionStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


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


ALLOWED_TRANSITIONS: dict[
    ExecutionStatus,
    set[ExecutionStatus],
] = {
    ExecutionStatus.pending: {
        ExecutionStatus.running,
    },
    ExecutionStatus.running: {
        ExecutionStatus.completed,
        ExecutionStatus.failed,
    },
    ExecutionStatus.completed: set(),
    ExecutionStatus.failed: set(),
}


def ensure_transition(
    current: ExecutionStatus,
    target: ExecutionStatus,
) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(current, target)