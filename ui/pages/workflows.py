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
        "Create your first project below."
    )

    with st.form(
        "project.create",
        clear_on_submit=True,
    ):
        project_name = st.text_input(
            "Project name",
            max_chars=255,
            placeholder=(
                "Customer Support Automation"
            ),
        )

        create_project_submitted = (
            st.form_submit_button(
                "Create project",
                type="primary",
            )
        )

    if create_project_submitted:
        cleaned_name = project_name.strip()

        if not cleaned_name:
            st.error(
                "Project name is required."
            )

        else:
            try:
                api.create_project(
                    name=cleaned_name,
                )

            except ApiError as error:
                st.error(error.message)

            else:
                st.toast(
                    "Project created"
                )
                st.rerun()

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
        options=list(
            project_options.keys()
        ),
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
        options=list(
            TEMPLATES.keys()
        ),
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
                project_id=(
                    selected_project_id
                ),
                name=cleaned_name,
                description=(
                    description.strip()
                ),
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


    # Gmail automation binding


    st.divider()

    st.subheader(
        "Gmail automation"
    )

    st.caption(
        (
            "Connect Gmail to a workflow so new incoming "
            "emails can be processed automatically."
        )
    )


    # Knowledge readiness

    try:
        knowledge_documents = (
            api.list_knowledge_documents()
        )

    except ApiError as error:
        knowledge_documents = []

        st.warning(
            (
                "FlowPilot could not check knowledge "
                f"readiness: {error.message}"
            )
        )

    ready_knowledge_documents = [
        document
        for document in knowledge_documents
        if document.get("status") == "ready"
    ]

    if ready_knowledge_documents:
        st.success(
            (
                f"{len(ready_knowledge_documents)} knowledge "
                "document(s) ready. FlowPilot can generate "
                "grounded Gmail reply drafts."
            ),
            icon=":material/check_circle:",
        )

    else:
        st.warning(
            (
                "Knowledge required for AI replies. "
                "Upload at least one knowledge document "
                "before testing Gmail reply generation."
            ),
            icon=":material/warning:",
        )

        st.caption(
            (
                "You can connect Gmail now, but FlowPilot "
                "will not create a grounded reply draft "
                "until supporting knowledge is ready."
            )
        )

        if st.button(
            "Go to Knowledge",
            key="gmail.go_to_knowledge",
        ):
            st.switch_page(
                "pages/knowledge.py"
            )

    st.markdown(
        """
**Quick demo**

1. Upload a knowledge document
2. Connect Gmail to this workflow
3. Send a new email to the connected inbox
4. Open **Approvals** to review the generated reply
        """
    )

    workflow_connect_options = {
        workflow.get(
            "name",
            "Unnamed workflow",
        ): workflow.get(
            "id"
        )
        for workflow in workflows
        if workflow.get(
            "id"
        )
    }

    gmail_workflow_label = st.selectbox(
        "Workflow for incoming Gmail",
        options=list(
            workflow_connect_options.keys()
        ),
        key="gmail.workflow",
    )

    selected_gmail_workflow_id = (
        workflow_connect_options[
            gmail_workflow_label
        ]
    )

    if st.button(
        "Connect Gmail",
        type="primary",
        key="gmail.connect",
    ):
        try:
            authorization_url = (
                api.gmail_connect_url(
                    workflow_id=(
                        selected_gmail_workflow_id
                    ),
                )
            )

        except ApiError as error:
            st.error(
                error.message
            )

        else:
            st.session_state[
                "gmail.authorization_url"
            ] = authorization_url

    authorization_url = (
        st.session_state.get(
            "gmail.authorization_url"
        )
    )

    if authorization_url:
        st.success(
            (
                "Gmail authorization is ready. "
                "Continue with Google to connect "
                "this workflow."
            )
        )

        st.link_button(
            "Continue with Google",
            authorization_url,
            type="primary",
        )