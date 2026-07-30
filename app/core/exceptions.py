from typing import Any
from uuid import UUID


class FlowPilotError(Exception):
    """Base class for FlowPilot domain errors."""


class ProjectNotFoundError(FlowPilotError):
    def __init__(self, project_id: Any) -> None:
        self.project_id = project_id
        super().__init__(
            f"Project with ID '{project_id}' was not found."
        )


class EmptyWorkflowError(FlowPilotError):
    def __init__(self) -> None:
        super().__init__(
            "A workflow must contain at least one step."
        )


class InvalidStepOrder(FlowPilotError):
    def __init__(self, positions: list[int]) -> None:
        self.positions = positions
        super().__init__(
            "Workflow step positions must be unique, contiguous, "
            f"and start from 1. Received: {positions}."
        )


class UnsupportedStepType(FlowPilotError):
    def __init__(self, step_types: list[str]) -> None:
        self.step_types = step_types
        super().__init__(
            f"Unsupported workflow step types: {step_types}."
        )


class RetryableStepError(Exception):
    """Raised when a workflow step fails temporarily and may be retried."""


class IdempotencyConflictError(Exception):
    """Raised when an idempotency key is reused with a different payload."""



class ExecutionNotFoundError(Exception):
    def __init__(self, execution_id: UUID) -> None:
        super().__init__(
            f"Execution '{execution_id}' was not found."
        )


class ExecutionStillActiveError(Exception):
    def __init__(self, execution_id: UUID) -> None:
        super().__init__(
            f"Execution '{execution_id}' is still active."
        )


class RecoveryNotAllowedError(Exception):
    pass