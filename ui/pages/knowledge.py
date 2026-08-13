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

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def page_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


st.title("Knowledge")

st.write(
    "Upload documents that FlowPilot can use as "
    "grounding knowledge."
)

api = page_api()


# ---------------------------------------------------------
# Upload form
# ---------------------------------------------------------

with st.form(
    "knowledge.upload",
    clear_on_submit=True,
):
    uploaded_file = st.file_uploader(
        "Knowledge document",
        type=["pdf", "txt", "md"],
    )

    submitted = st.form_submit_button(
        "Upload document",
        type="primary",
    )


if submitted:
    if uploaded_file is None:
        st.warning(
            "Choose a document before uploading."
        )

    elif uploaded_file.size > MAX_UPLOAD_BYTES:
        st.error(
            "Uploaded file exceeds the 10MB limit"
        )

    else:
        try:
            document = api.upload_knowledge_document(
                filename=uploaded_file.name,
                content=uploaded_file.getvalue(),
                content_type=(
                    uploaded_file.type
                    or "application/octet-stream"
                ),
            )

        except SessionExpired:
            clear_session_state()
            st.rerun()

        except ApiError as error:
            st.error(error.message)

        else:
            st.success(
                f"Uploaded {document['name']}."
            )

            st.write(
                "Status:",
                document["status"],
            )


# ---------------------------------------------------------
# Knowledge documents
# ---------------------------------------------------------

st.divider()

st.subheader("Your knowledge documents")

try:
    documents = api.list_knowledge_documents()


except SessionExpired:
    clear_session_state()
    st.rerun()

except ApiError as error:
    st.error(error.message)

else:
    if not documents:
        st.info(
            "No knowledge documents uploaded yet."
        )

    else:
        for document in documents:
            name = document["name"]
            document_status = document["status"]

            st.write(
                f"**{name}** — `{document_status}`"
            )