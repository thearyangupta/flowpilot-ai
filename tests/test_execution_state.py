import pytest

from app.domain.execution_state import (
    InvalidTransition,
    ensure_transition,
)
from app.models.enums import ExecutionStatus


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.COMPLETED,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.FAILED,
        ),
    ],
)
def test_allowed_transitions(current, target):
    ensure_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.COMPLETED,
        ),
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.FAILED,
        ),
        (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.FAILED,
            ExecutionStatus.RUNNING,
        ),
    ],
)
def test_invalid_transitions(current, target):
    with pytest.raises(InvalidTransition):
        ensure_transition(current, target)