from __future__ import annotations

import streamlit as st

from ui.styles import apply_global_styles, render_html


st.set_page_config(
    page_title="FlowPilot Demo",
    layout="wide",
)

apply_global_styles()


SAMPLE_EMAIL = {
    "sender": "Sarah Mitchell <sarah.mitchell@example.com>",
    "subject": "Order #ORD-123456 — Delivery Delay",
    "body": """
Hi FlowPilot,

My order was supposed to arrive yesterday, but the tracking
page has not updated since Monday.

Could you check what happened and let me know when I can
expect the delivery?

Thanks,
Sarah
""".strip(),
}


SAMPLE_KNOWLEDGE = {
    "title": "Shipping & Returns Policy",
    "content": """
Standard deliveries normally arrive within 3–5 business days.
If a shipment has not received a tracking update for more than
48 hours, the customer should be informed that the shipment
may be delayed in transit and the latest tracking information
should be reviewed before providing a delivery estimate.
""".strip(),
}


DEMO_DRAFT = """
Hi Sarah,

Thanks for reaching out. I checked the available shipment
information for order #ORD-123456.

It appears that the shipment has been delayed in transit and
the tracking information has not updated recently. We are
reviewing the latest available tracking information and will
provide an updated delivery estimate as soon as it becomes
available.

Thanks for your patience,
FlowPilot
""".strip()


if "demo_stage" not in st.session_state:
    st.session_state.demo_stage = "start"


if "demo_approved" not in st.session_state:
    st.session_state.demo_approved = False


def reset_demo() -> None:
    st.session_state.demo_stage = "start"
    st.session_state.demo_approved = False


render_html(
    """
    <div class="fp-agent-hero">
        <div class="fp-agent-eyebrow">
            <span class="fp-agent-status"></span>
            INTERACTIVE DEMO
        </div>

        <h1>
            See FlowPilot in action
        </h1>

        <p>
            Explore a realistic email workflow using sample data.
            No Google account or Gmail access is required.
        </p>
    </div>
    """
)

st.info(
    "Demo mode uses sample email and knowledge data. "
    "It does not connect to your Gmail account."
)

st.divider()

st.markdown("### 1. Incoming email")

with st.container(border=True):
    st.markdown(
        f"**From:** {SAMPLE_EMAIL['sender']}"
    )

    st.markdown(
        f"**Subject:** {SAMPLE_EMAIL['subject']}"
    )

    st.divider()

    st.markdown(
        SAMPLE_EMAIL["body"]
    )


if st.session_state.demo_stage == "start":

    st.write("")

    if st.button(
        "Analyze Email",
        type="primary",
        icon=":material/auto_awesome:",
        use_container_width=True,
    ):
        st.session_state.demo_stage = "analyzed"
        st.rerun()


if st.session_state.demo_stage in {
    "analyzed",
    "drafted",
    "approved",
}:

    st.divider()

    st.markdown("### 2. FlowPilot analysis")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Intent detected**")
            st.markdown("Delivery delay")

    with col2:
        with st.container(border=True):
            st.markdown("**Workflow**")
            st.markdown("Customer support reply")

    st.write("")

    with st.container(border=True):
        st.markdown("**Relevant knowledge retrieved**")
        st.markdown(
            f"**{SAMPLE_KNOWLEDGE['title']}**"
        )
        st.caption(
            "Retrieved context used to ground the response"
        )
        st.markdown(
            SAMPLE_KNOWLEDGE["content"]
        )

    st.divider()

    st.markdown("### 3. AI-generated reply")

    with st.container(border=True):
        st.markdown(
            DEMO_DRAFT
        )

    st.caption(
        "AI-generated content is presented for human review "
        "before an action is approved."
    )

    if st.session_state.demo_stage == "analyzed":

        st.write("")

        if st.button(
            "Generate Reply Draft",
            type="primary",
            icon=":material/draft:",
            use_container_width=True,
        ):
            st.session_state.demo_stage = "drafted"
            st.rerun()


if st.session_state.demo_stage in {
    "drafted",
    "approved",
}:

    st.divider()

    st.markdown("### 4. Human approval")

    if st.session_state.demo_stage == "drafted":

        st.warning(
            "This action requires human approval."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Approve Draft",
                type="primary",
                icon=":material/check_circle:",
                use_container_width=True,
            ):
                st.session_state.demo_stage = "approved"
                st.session_state.demo_approved = True
                st.rerun()

        with col2:
            if st.button(
                "Reject Draft",
                icon=":material/cancel:",
                use_container_width=True,
            ):
                st.session_state.demo_stage = "start"
                st.session_state.demo_approved = False
                st.rerun()


if st.session_state.demo_stage == "approved":

    st.divider()

    st.markdown("### 5. Workflow completed")

    st.success(
        "Draft approved successfully."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Intent",
            "Delivery delay",
        )

    with col2:
        st.metric(
            "Knowledge",
            "Retrieved",
        )

    with col3:
        st.metric(
            "Approval",
            "Approved",
        )

    with st.container(border=True):
        st.markdown("**Execution result**")

        st.markdown(
            """
            ✓ Email analyzed

            ✓ Relevant knowledge retrieved

            ✓ Reply draft generated

            ✓ Human approval recorded

            ✓ Guarded action completed
            """
        )

    st.caption(
        "This interactive demo uses sample data. "
        "The production FlowPilot workflow can connect to Gmail "
        "after the user authorizes Google OAuth."
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "Restart Demo",
        icon=":material/replay:",
        use_container_width=True,
    ):
        reset_demo()
        st.rerun()

with col2:
    st.link_button(
        "Back to FlowPilot",
        "/",
        icon=":material/home:",
        use_container_width=True,
    )
