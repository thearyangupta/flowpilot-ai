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
    (
        "Upload business documents that FlowPilot uses "
        "to generate grounded AI replies."
    )
)

st.info(
    (
        "Gmail reply automation requires at least one "
        "ready knowledge document. FlowPilot uses your "
        "knowledge base instead of inventing policies, "
        "prices, procedures, or other business facts."
    ),
    icon=":material/info:",
)

st.caption(
    (
        "Recommended demo flow: upload knowledge → "
        "create a workflow → connect Gmail → send a test "
        "email → review the generated draft in Approvals."
    )
)

api = page_api()



# Upload form


with st.form(
    "knowledge.upload",
    clear_on_submit=True,
):
    uploaded_file = st.file_uploader(
        "Knowledge document",
        type=["pdf", "txt", "md"],
        help=(
            "Upload policies, FAQs, support instructions, "
            "product information, or other facts FlowPilot "
            "may use when writing replies."
        ),
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
            "Uploaded file exceeds the 10MB limit."
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

            document_status = document["status"]

            if document_status == "ready":
                st.success(
                    (
                        "Knowledge is ready. FlowPilot can "
                        "now use this document when creating "
                        "grounded Gmail replies."
                    )
                )

            else:
                st.info(
                    (
                        f"Current status: {document_status}. "
                        "FlowPilot will use this document "
                        "after processing is complete."
                    )
                )



# Knowledge documents


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
    ready_documents = [
        document
        for document in documents
        if document.get("status") == "ready"
    ]

    if not documents:
        st.warning(
            (
                "No knowledge documents are available yet. "
                "Upload at least one document before testing "
                "AI Gmail reply generation."
            ),
            icon=":material/warning:",
        )

    else:
        for document in documents:
            name = document["name"]
            document_status = document["status"]

            st.write(
                f"**{name}** — `{document_status}`"
            )

        st.divider()

        if ready_documents:
            st.success(
                (
                    f"{len(ready_documents)} knowledge "
                    "document(s) ready for grounded AI "
                    "replies."
                ),
                icon=":material/check_circle:",
            )

            if st.button(
                "Continue to Workflows",
                type="primary",
                key="knowledge.continue",
            ):
                st.switch_page(
                    "pages/workflows.py"
                )

        else:
            st.info(
                (
                    "Your documents are still processing. "
                    "Wait until at least one document shows "
                    "`ready` before testing Gmail replies."
                )
            )