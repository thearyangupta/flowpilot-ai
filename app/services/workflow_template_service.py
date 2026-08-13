from __future__ import annotations

from dataclasses import dataclass

from app.schemas.workflow import WorkflowCreate


class UnsupportedWorkflowTemplateError(ValueError):
    """Raised when a requested workflow template is unknown."""


@dataclass(frozen=True, slots=True)
class WorkflowTemplate:
    template_id: str
    label: str


CUSTOMER_REPLY_V1 = WorkflowTemplate(
    template_id="customer_reply_v1",
    label="Customer email reply",
)

EMAIL_TRIAGE_V1 = WorkflowTemplate(
    template_id="email_triage_v1",
    label="Triage only",
)


SUPPORTED_WORKFLOW_TEMPLATES = {
    CUSTOMER_REPLY_V1.template_id: CUSTOMER_REPLY_V1,
    EMAIL_TRIAGE_V1.template_id: EMAIL_TRIAGE_V1,
}


def build_workflow_from_template(
    *,
    name: str,
    template_id: str,
) -> WorkflowCreate:
    if template_id not in SUPPORTED_WORKFLOW_TEMPLATES:
        raise UnsupportedWorkflowTemplateError(
            f"Unsupported workflow template: {template_id}"
        )

    if template_id == EMAIL_TRIAGE_V1.template_id:
        return WorkflowCreate.model_validate(
            {
                "name": name,
                "steps": [
                    {
                        "position": 1,
                        "step_type": "classify_email",
                        "config": {
                            "input_key": "body_text",
                            "output_key": "decision",
                        },
                    }
                ],
            }
        )

    if template_id == CUSTOMER_REPLY_V1.template_id:
        return WorkflowCreate.model_validate(
            {
                "name": name,
                "steps": [
                    {
                        "position": 1,
                        "step_type": "classify_email",
                        "config": {
                            "input_key": "body_text",
                            "output_key": "decision",
                        },
                    },
                    {
                        "position": 2,
                        "step_type": "require_key",
                        "config": {
                            "key": "decision",
                        },
                    },
                ],
            }
        )

    # Defensive guard in case the registry and builder diverge.
    raise UnsupportedWorkflowTemplateError(
        f"Unsupported workflow template: {template_id}"
    )