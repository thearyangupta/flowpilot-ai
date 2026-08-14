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


def page_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


st.title("Approvals")

st.write(
    "Review AI-generated drafts and their "
    "supporting evidence before allowing "
    "a guarded action."
)

api = page_api()


try:
    drafts = api.list_pending_reply_drafts()

except SessionExpired:
    clear_session_state()
    st.rerun()

except ApiError as error:
    st.error(error.message)
    st.stop()


if not drafts:
    st.info(
        "No drafts are waiting for approval."
    )
    st.stop()


st.subheader("Pending approvals")


draft_rows = [
    {
        "Draft ID": draft["id"],
        "Status": draft["status"],
        "Subject": (
            draft.get(
                "draft_message",
                {},
            ).get(
                "subject",
                "",
            )
        ),
    }
    for draft in drafts
]


st.dataframe(
    draft_rows,
    use_container_width=True,
    hide_index=True,
)


draft_ids = [
    draft["id"]
    for draft in drafts
]


selected_draft_id = st.selectbox(
    "Draft to review",
    options=draft_ids,
)


selected_draft = next(
    draft
    for draft in drafts
    if draft["id"] == selected_draft_id
)


source_message = selected_draft.get(
    "source_message",
    {},
)

draft_message = selected_draft.get(
    "draft_message",
    {},
)


st.divider()

st.subheader("Source request")


st.write(
    "**From:**",
    source_message.get(
        "sender",
        source_message.get(
            "from",
            "",
        ),
    ),
)


st.write(
    "**Subject:**",
    source_message.get(
        "subject",
        "",
    ),
)


st.text_area(
    "Customer message",
    value=source_message.get(
        "body_text",
        source_message.get(
            "body",
            "",
        ),
    ),
    height=180,
    disabled=True,
)


st.divider()

st.subheader("AI-generated draft")


st.write(
    "**Recipient:**",
    draft_message.get(
        "recipient",
        "",
    ),
)


st.write(
    "**Subject:**",
    draft_message.get(
        "subject",
        "",
    ),
)


st.text_area(
    "Draft reply",
    value=draft_message.get(
        "body",
        "",
    ),
    height=220,
    disabled=True,
)


citation_ids = draft_message.get(
    "citation_ids",
    [],
)


st.subheader("Grounding evidence")


if citation_ids:
    st.write(
        "Knowledge sources used by this draft:"
    )

    for citation_id in citation_ids:
        st.code(
            str(citation_id),
            language=None,
        )

else:
    st.warning(
        "This draft has no grounding citations."
    )


st.divider()

st.subheader("Decision")


acknowledged = st.checkbox(
    (
        "I reviewed the source request, "
        "AI draft and grounding evidence."
    ),
    key=(
        "approval.acknowledged."
        f"{selected_draft_id}"
    ),
)


rejection_reason = st.text_area(
    "Rejection reason",
    placeholder=(
        "Required only when rejecting "
        "this draft."
    ),
    key=(
        "approval.rejection_reason."
        f"{selected_draft_id}"
    ),
)


approve_col, reject_col = st.columns(2)


with approve_col:
    approve_clicked = st.button(
        "Approve draft",
        type="primary",
        use_container_width=True,
        disabled=not acknowledged,
    )


with reject_col:
    reject_clicked = st.button(
        "Reject draft",
        use_container_width=True,
        disabled=(
            not rejection_reason.strip()
        ),
    )


if approve_clicked:
    try:
        api.approve_reply_draft(
            draft_id=selected_draft_id,
        )

    except SessionExpired:
        clear_session_state()
        st.rerun()

    except ApiError as error:
        st.error(error.message)

    else:
        st.success(
            "Draft approved."
        )

        st.rerun()


if reject_clicked:
    try:
        api.reject_reply_draft(
            draft_id=selected_draft_id,
            reason=rejection_reason.strip(),
        )

    except SessionExpired:
        clear_session_state()
        st.rerun()

    except ApiError as error:
        st.error(error.message)

    else:
        st.success(
            "Draft rejected."
        )

        st.rerun()