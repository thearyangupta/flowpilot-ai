import pytest

from app.domain.execution_state import (
    ExecutionStatus,
    InvalidTransition,
    ensure_transition,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.pending,
            ExecutionStatus.running,
        ),
        (
            ExecutionStatus.running,
            ExecutionStatus.completed,
        ),
        (
            ExecutionStatus.running,
            ExecutionStatus.failed,
        ),
    ],
)
def test_allowed_transitions(current, target):
    ensure_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.pending,
            ExecutionStatus.completed,
        ),
        (
            ExecutionStatus.pending,
            ExecutionStatus.failed,
        ),
        (
            ExecutionStatus.completed,
            ExecutionStatus.running,
        ),
        (
            ExecutionStatus.failed,
            ExecutionStatus.running,
        ),
    ],
)
def test_invalid_transitions(current, target):
    with pytest.raises(InvalidTransition):
        ensure_transition(current, target)