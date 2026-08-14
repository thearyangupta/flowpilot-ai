import streamlit as st

from ui.api import (
    ApiError,
    FlowPilotClient,
    get_api_base_url,
)
from ui.session import AUTH_ACCESS_TOKEN_KEY


TEMPLATES = {
    "Customer email reply": "customer_reply_v1",
    "Triage only": "email_triage_v1",
}


def page_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


st.title("Workflows")

api = page_api()

# Projects


try:
    projects = api.get_projects()

except ApiError as error:
    st.error(error.message)
    st.stop()


if not projects:
    st.info(
        "No projects exist yet. "
        "Create a project before adding workflows."
    )
    st.stop()


project_options = {
    project["name"]: project["id"]
    for project in projects
}

# Create workflow

with st.form(
    "workflow.create",
    clear_on_submit=True,
):
    project_label = st.selectbox(
        "Project",
        options=list(project_options.keys()),
        key="workflow.project",
    )

    name = st.text_input(
        "Workflow name",
        max_chars=120,
        key="workflow.name",
    )

    description = st.text_area(
        "Description",
        max_chars=500,
        key="workflow.description",
    )

    template_label = st.selectbox(
        "Starting template",
        options=list(TEMPLATES.keys()),
        key="workflow.template",
    )

    submitted = st.form_submit_button(
        "Create workflow",
        type="primary",
    )


selected_project_id = project_options[
    project_label
]


if submitted:
    cleaned_name = name.strip()

    if not cleaned_name:
        st.error(
            "Workflow name is required."
        )

    else:
        try:
            api.create_workflow(
                project_id=selected_project_id,
                name=cleaned_name,
                description=description.strip(),
                template=TEMPLATES[
                    template_label
                ],
            )

        except ApiError as error:
            st.error(error.message)

        else:
            st.toast(
                "Workflow created"
            )
            st.rerun()

# Existing workflows

st.subheader(
    "Existing workflows"
)

try:
    workflows = api.list_workflows(
        project_id=selected_project_id,
    )

except ApiError as error:
    st.error(error.message)
    st.stop()


if not workflows:
    st.info(
        "No workflows exist for this project yet."
    )

else:
    rows = [
        {
            "Name": workflow.get(
                "name",
                "",
            ),
            "Created": workflow.get(
                "created_at",
                "",
            ),
            "Workflow ID": workflow.get(
                "id",
                "",
            ),
        }
        for workflow in workflows
    ]

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )