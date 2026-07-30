import pytest

from app.core.exceptions import IdempotencyConflictError

from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.services.execution_service import (
    create_or_return_existing,
)


def test_duplicate_request_returns_existing_execution(
    db_session: Session,
    workflow: Workflow,
):
    initial_context = {
        "email_subject": "Refund request",
        "customer_id": "customer-123",
    }

    first_execution, first_created = create_or_return_existing(
        db=db_session,
        workflow_id=workflow.id,
        idempotency_key="duplicate-request-001",
        initial_context=initial_context,
    )

    second_execution, second_created = create_or_return_existing(
        db=db_session,
        workflow_id=workflow.id,
        idempotency_key="duplicate-request-001",
        initial_context=initial_context,
    )

    assert first_created is True
    assert second_created is False
    assert first_execution.id == second_execution.id
    

def test_same_idempotency_key_with_different_payload_raises_conflict(
    db_session: Session,
    workflow: Workflow,
):
    create_or_return_existing(
        db=db_session,
        workflow_id=workflow.id,
        idempotency_key="conflicting-request-001",
        initial_context={
            "email_subject": "Refund request",
            "customer_id": "customer-123",
        },
    )

    with pytest.raises(
        IdempotencyConflictError,
        match="Idempotency key was already used with a different payload",
    ):
        create_or_return_existing(
            db=db_session,
            workflow_id=workflow.id,
            idempotency_key="conflicting-request-001",
            initial_context={
                "email_subject": "Cancel subscription",
                "customer_id": "customer-123",
            },
        )