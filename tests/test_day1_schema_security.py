import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginCodeExchangeCreate
from app.schemas.execution import ExecutionCreate
from app.schemas.project import ProjectCreate
from app.schemas.reply_draft import (
    ReplyDraftDecisionCreate,
    ReplyDraftEditCreate,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowTemplateCreate,
)


def test_project_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            name="Safe Project",
            admin=True,
        )


def test_login_code_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        LoginCodeExchangeCreate(
            login_code="valid-code",
            user_id="unexpected",
        )


def test_reply_draft_decision_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        ReplyDraftDecisionCreate(
            expected_revision=1,
            bypass_approval=True,
        )


def test_execution_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        ExecutionCreate(
            input_data={},
            idempotency_key="safe-key",
            admin=True,
        )


def test_idempotency_key_cannot_exceed_database_limit() -> None:
    with pytest.raises(ValidationError):
        ExecutionCreate(
            input_data={},
            idempotency_key="x" * 256,
        )


def test_execution_input_has_size_limit() -> None:
    with pytest.raises(ValidationError):
        ExecutionCreate(
            input_data={
                "payload": "x" * (256 * 1024),
            },
            idempotency_key="large-input-test",
        )


def test_reply_draft_content_has_size_limit() -> None:
    with pytest.raises(ValidationError):
        ReplyDraftEditCreate(
            expected_revision=1,
            content={
                "body": "x" * (256 * 1024),
            },
        )


def test_workflow_rejects_more_than_100_steps() -> None:
    steps = [
        {
            "position": index + 1,
            "step_type": "set_value",
            "config": {
                "key": f"key_{index}",
                "value": "value",
            },
        }
        for index in range(101)
    ]

    with pytest.raises(ValidationError):
        WorkflowCreate(
            name="Too Many Steps",
            steps=steps,
        )


def test_workflow_step_position_cannot_exceed_100() -> None:
    with pytest.raises(ValidationError):
        WorkflowCreate(
            name="Bad Position",
            steps=[
                {
                    "position": 101,
                    "step_type": "set_value",
                    "config": {
                        "key": "message",
                        "value": "hello",
                    },
                }
            ],
        )


def test_workflow_config_key_is_bounded() -> None:
    with pytest.raises(ValidationError):
        WorkflowCreate(
            name="Huge Config Key",
            steps=[
                {
                    "position": 1,
                    "step_type": "set_value",
                    "config": {
                        "key": "x" * 256,
                        "value": "hello",
                    },
                }
            ],
        )


def test_nested_workflow_config_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WorkflowCreate(
            name="Unexpected Config",
            steps=[
                {
                    "position": 1,
                    "step_type": "uppercase",
                    "config": {
                        "key": "message",
                        "admin": True,
                    },
                }
            ],
        )


def test_workflow_template_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WorkflowTemplateCreate(
            name="Email Triage",
            template="email_triage_v1",
            hidden_option=True,
        )
