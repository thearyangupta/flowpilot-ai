from __future__ import annotations

import streamlit as st

from ui.api import (
    ApiError,
    FlowPilotClient,
    SessionExpired,
    get_api_base_url,
)
from ui.session import (
    AUTH_ACCESS_TOKEN_KEY,
    clear_session_state,
)


EXECUTION_STATUSES = [
    "All",
    "pending",
    "queued",
    "running",
    "succeeded",
    "failed",
]

ACTIVE_EXECUTION_STATUSES = {
    "pending",
    "queued",
    "running",
}


def page_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


def load_execution_detail(
    api: FlowPilotClient,
    execution_id: str,
) -> dict:
    try:
        return api.get_execution_detail(
            execution_id=execution_id,
        )

    except SessionExpired:
        clear_session_state()
        st.rerun()

    except ApiError as error:
        st.error(error.message)
        st.stop()


def render_execution_detail(
    execution_detail: dict,
) -> None:
    st.write(
        "Status:",
        execution_detail["status"],
    )

    st.write(
        "Created:",
        execution_detail["created_at"],
    )

    st.write(
        "Updated:",
        execution_detail["updated_at"],
    )

    st.subheader("Steps")

    step_runs = sorted(
        execution_detail["step_runs"],
        key=lambda step: (
            step["workflow_step"]["position"]
        ),
    )

    if not step_runs:
        st.info(
            "This execution has no recorded steps."
        )
        return

    trace_rows = []

    for step in step_runs:
        workflow_step = step["workflow_step"]

        failure_reason = (
            step.get("error_message")
            or ""
        )

        trace_rows.append(
            {
                "Step": workflow_step["position"],
                "Type": workflow_step["step_type"],
                "Status": step["status"],
                "Started": step["started_at"],
                "Finished": step["finished_at"],
                "Duration (s)": (
                    step["duration_seconds"]
                ),
                "Attempts": step["attempt_count"],
                "Failure reason": failure_reason,
            }
        )

    st.dataframe(
        trace_rows,
        use_container_width=True,
        hide_index=True,
    )


@st.fragment(run_every="3s")
def active_execution_fragment(
    api: FlowPilotClient,
    execution_id: str,
) -> None:
    execution_detail = load_execution_detail(
        api,
        execution_id,
    )

    render_execution_detail(
        execution_detail
    )

    if (
        execution_detail["status"]
        not in ACTIVE_EXECUTION_STATUSES
    ):
        st.rerun()


st.title("Executions")

st.write(
    "Inspect workflow executions and their "
    "current backend status."
)

api = page_api()

# Project selection

try:
    projects = api.get_projects()

except SessionExpired:
    clear_session_state()
    st.rerun()

except ApiError as error:
    st.error(error.message)
    st.stop()


if not projects:
    st.info(
        "Create a project before viewing executions."
    )
    st.stop()


project_names = {
    project["name"]: project["id"]
    for project in projects
}

selected_project_name = st.selectbox(
    "Project",
    options=list(project_names),
)

project_id = project_names[
    selected_project_name
]

# Workflow selection

try:
    workflows = api.list_workflows(
        project_id=project_id,
    )

except SessionExpired:
    clear_session_state()
    st.rerun()

except ApiError as error:
    st.error(error.message)
    st.stop()


if not workflows:
    st.info(
        "No workflows found for this project."
    )
    st.stop()


workflow_names = {
    workflow["name"]: workflow["id"]
    for workflow in workflows
}

selected_workflow_name = st.selectbox(
    "Workflow",
    options=list(workflow_names),
)

workflow_id = workflow_names[
    selected_workflow_name
]

# Status filter

selected_status = st.selectbox(
    "Status",
    options=EXECUTION_STATUSES,
)

execution_status = (
    None
    if selected_status == "All"
    else selected_status
)

# Execution list

try:
    executions = api.list_executions(
        project_id=project_id,
        workflow_id=workflow_id,
        execution_status=execution_status,
    )

except SessionExpired:
    clear_session_state()
    st.rerun()

except ApiError as error:
    st.error(error.message)
    st.stop()


if not executions:
    st.info(
        "No executions match the selected filters."
    )
    st.stop()


table_rows = [
    {
        "Execution": execution["id"],
        "Status": execution["status"],
        "Created": execution["created_at"],
        "Updated": execution["updated_at"],
    }
    for execution in executions
]

st.dataframe(
    table_rows,
    use_container_width=True,
    hide_index=True,
)

# Execution detail

st.divider()

st.subheader("Execution detail")

execution_ids = [
    execution["id"]
    for execution in executions
]

selected_execution_id = st.selectbox(
    "Execution",
    options=execution_ids,
)


initial_detail = load_execution_detail(
    api,
    selected_execution_id,
)

initial_status = initial_detail["status"]

# Bounded refresh

if initial_status in ACTIVE_EXECUTION_STATUSES:
    st.caption(
        "Execution is active. "
        "Refreshing status every 3 seconds."
    )

    active_execution_fragment(
        api,
        selected_execution_id,
    )

else:
    render_execution_detail(
        initial_detail
    )