from __future__ import annotations

import streamlit as st

from ui.api import (
    ApiError,
    FlowPilotClient,
    SessionExpired,
    get_api_base_url,
    get_browser_api_base_url,
)
from ui.session import (
    AUTH_ACCESS_TOKEN_KEY,
    clear_session_state,
    initialize_session_state,
)
from ui.styles import (
    apply_global_styles,
    render_html,
)


st.set_page_config(
    page_title="FlowPilot AI",
    layout="wide",
)

apply_global_styles()


def get_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


def complete_login(
    api: FlowPilotClient,
) -> None:
    login_code = st.query_params.get(
        "login_code"
    )

    if not login_code:
        return

    try:
        access_token = (
            api.exchange_login_code(
                login_code
            )
        )

        st.session_state[
            AUTH_ACCESS_TOKEN_KEY
        ] = access_token

    except ApiError as error:
        st.error(
            error.message
        )

    finally:
        st.query_params.clear()


def render_public_home() -> None:
    st.title("FlowPilot AI")

    st.subheader(
        "AI-powered email workflow automation"
    )

    st.write(
        "FlowPilot helps users process incoming Gmail "
        "messages, use knowledge-grounded AI to prepare "
        "reply drafts, and review drafts through a "
        "human-in-the-loop approval workflow."
    )

    st.write(
        "FlowPilot connects to Gmail only after the user "
        "authorizes access through Google OAuth."
    )

    st.markdown("### How FlowPilot uses Gmail")

    st.write(
        "• Read incoming email content needed to understand "
        "and process messages."
    )

    st.write(
        "• Prepare reply drafts using the user's email "
        "context and FlowPilot knowledge."
    )

    st.write(
        "• Allow the user to review and approve guarded "
        "email actions."
    )

    st.divider()

    api = get_api()

    try:
        authorization_url = (
            api.google_login_url()
        )

    except ApiError as error:
        st.error(error.message)
        return

    st.link_button(
        "Continue with Google",
        authorization_url,
        type="primary",
    )

    st.write("")

    st.page_link(
        demo_page,
        label="Try Interactive Demo",
        icon=":material/play_circle:",
        use_container_width=True,
    )

    st.caption(
        "Explore a sample workflow without connecting Gmail."
    )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        st.page_link(
            privacy_page,
            label="Privacy Policy",
        )

    with col2:
        st.page_link(
            terms_page,
            label="Terms of Service",
        )


def render_privacy_policy() -> None:
    st.title("FlowPilot AI Privacy Policy")

    st.caption("Effective: August 22, 2026")

    st.markdown(
        """
FlowPilot AI is an AI-assisted email workflow application.
This Privacy Policy explains how FlowPilot handles information
when you connect your Google account and use the application.

### Information FlowPilot accesses

FlowPilot uses Google OAuth and may request the following Gmail
permissions:

- **Gmail read-only access** to read email messages and related
  information required to understand incoming messages and run
  email workflows.
- **Gmail compose access** to create and manage email drafts and
  perform user-authorized email actions.

FlowPilot accesses Google user data only after the user grants
permission through Google's OAuth consent process.

### How Google user data is used

Google user data is used only to provide FlowPilot's core
functionality, including:

- processing incoming emails;
- classifying messages;
- retrieving relevant user-provided knowledge;
- generating contextual reply drafts;
- presenting drafts and supporting evidence for review;
- performing email actions initiated or approved by the user.

FlowPilot does not use Google user data for advertising,
profiling for advertising, or selling user information.

### Application data

FlowPilot may retain application data necessary to operate and
demonstrate its workflows, such as workflow execution state,
generated draft records, approval records, connected-tool
configuration, and related operational metadata.

### Data sharing

FlowPilot does not sell Google user data. Information is shared
with service providers only when required to operate the
application and provide the requested functionality.

### User control

Users choose whether to authorize FlowPilot through Google
OAuth. Users can revoke FlowPilot's Google Account access at
any time from their Google Account security settings.

### Google API Services User Data Policy

FlowPilot's use and transfer of information received from Google
APIs will adhere to the Google API Services User Data Policy,
including the Limited Use requirements.

### Security and data protection

FlowPilot uses technical and organizational safeguards designed
to protect Google user data and authentication credentials against
unauthorized access, disclosure, alteration, or destruction.

FlowPilot uses HTTPS/TLS to protect data transmitted between users
and the application.

Google OAuth access and refresh tokens are encrypted before they
are stored by FlowPilot. Authentication credentials are not stored
as plaintext in the application database.

Access to Google user data is limited to the application
functionality required to provide the user-requested Gmail
features. FlowPilot requests only the Gmail permissions required
for its documented functionality and uses authentication and
authorization controls to restrict access to connected-account
data.

### Google user data retention and deletion

FlowPilot retains Google user data only for as long as reasonably
necessary to provide the user-requested functionality and operate
the associated workflow features.

FlowPilot may retain workflow execution records, generated reply
draft records, approval records, connected-tool configuration, and
related operational metadata when necessary to provide workflow
history, debugging, security, or other user-facing functionality.

When a user disconnects their Google account from FlowPilot,
FlowPilot attempts to revoke the Google authorization and deletes
the stored OAuth connection and its associated access and refresh
credentials from the application database.

Users may also request deletion of their FlowPilot account data
and Google user data stored by FlowPilot by contacting
aryangwork@gmail.com. FlowPilot will review and process deletion
requests in accordance with applicable legal and operational
requirements.

Google user data is not retained for advertising, sale, or other
unrelated purposes.

### Changes to this policy

This policy may be updated when FlowPilot's functionality or
data practices change. The current version will remain available
at this page.

### Contact

For privacy questions regarding FlowPilot AI, contact:

**aryangwork@gmail.com**
"""
    )

    st.divider()

    st.page_link(
        home_page,
        label="Back to FlowPilot",
    )


def render_terms_of_service() -> None:
    st.title("FlowPilot AI Terms of Service")

    st.caption("Effective: August 20, 2026")

    st.markdown(
        """
By accessing or using FlowPilot AI, you agree to these Terms of
Service.

### Purpose of FlowPilot

FlowPilot is an AI-assisted workflow application that can connect
to Gmail, process email content, retrieve relevant knowledge,
generate reply drafts, and support human review and approval
before guarded actions are performed.

### Google account access

Some FlowPilot features require authorization through Google
OAuth. You are responsible for granting only the permissions you
are comfortable providing and for maintaining control of your
Google account.

You may revoke FlowPilot's Google Account access at any time
through your Google Account settings.

### AI-generated content

FlowPilot may generate draft responses or other AI-assisted
content. AI-generated output may contain mistakes or incomplete
information.

Users are responsible for reviewing generated content before
approving, sending, or otherwise relying on it.

### Acceptable use

You agree not to use FlowPilot to:

- violate applicable laws or regulations;
- access another person's account or information without
  authorization;
- send abusive, fraudulent, deceptive, or unlawful content;
- interfere with the security or operation of the service.

### Availability

FlowPilot may be changed, suspended, or discontinued at any
time. Continuous or error-free availability is not guaranteed.

### Limitation of responsibility

FlowPilot is provided for demonstration and productivity
purposes. Users remain responsible for decisions, communications,
and actions taken using the application.

### Privacy

Use of FlowPilot is also governed by the FlowPilot AI Privacy
Policy.

### Changes to these terms

These terms may be updated as FlowPilot evolves. The current
version will remain available on this page.

### Contact

For questions regarding these terms, contact:

**aryangwork@gmail.com**
"""
    )

    st.divider()

    st.page_link(
        privacy_page,
        label="Privacy Policy",
    )

    st.page_link(
        home_page,
        label="Back to FlowPilot",
    )


initialize_session_state()

api = get_api()

complete_login(api)


home_page = st.Page(
    render_public_home,
    title="FlowPilot AI",
    url_path="home",
    icon=":material/home:",
)

privacy_page = st.Page(
    render_privacy_policy,
    title="Privacy Policy",
    url_path="privacy",
    icon=":material/privacy_tip:",
)

terms_page = st.Page(
    render_terms_of_service,
    title="Terms of Service",
    url_path="terms",
    icon=":material/gavel:",
)

demo_page = st.Page(
    "pages/demo.py",
    title="Interactive Demo",
    url_path="demo",
    icon=":material/play_circle:",
)


if not st.session_state.get(
    AUTH_ACCESS_TOKEN_KEY
):
    public_pages = [
        home_page,
        demo_page,
        privacy_page,
        terms_page,
    ]

    st.navigation(
        public_pages,
        position="hidden",
    ).run()

    st.stop()


with st.sidebar:
    render_html(
        """
        <div class="fp-brand">
            <div class="fp-brand-row">
                <div class="fp-brand-mark">
                    ✦
                </div>

                <div class="fp-brand-name">
                    FlowPilot
                </div>
            </div>

            <div class="fp-brand-copy">
                AI workspace
            </div>
        </div>
        """
    )

    st.divider()

    render_html(
        """
        <div class="fp-sidebar-label">
            CONNECTED
        </div>
        """
    )

    if st.button(
        "Gmail",
        icon=":material/mail:",
        use_container_width=True,
        key="sidebar.gmail",
    ):
        st.switch_page(
            "pages/workflows.py"
        )

    st.divider()

    logout_url = (
        f"{get_browser_api_base_url()}"
        "/api/v1/auth/logout"
    )

    st.link_button(
        "Logout",
        logout_url,
        icon=":material/logout:",
        use_container_width=True,
    )


pages = [
    st.Page(
        "pages/agent.py",
        title="Agent",
        icon=":material/auto_awesome:",
        default=True,
    ),
    st.Page(
        "pages/home.py",
        title="Home",
        icon=":material/home:",
    ),
    st.Page(
        "pages/workflows.py",
        title="Workflows",
        icon=":material/account_tree:",
    ),
    st.Page(
        "pages/knowledge.py",
        title="Knowledge",
        icon=":material/library_books:",
    ),
    st.Page(
        "pages/executions.py",
        title="Executions",
        icon=":material/play_circle:",
    ),
    st.Page(
        "pages/approvals.py",
        title="Approvals",
        icon=":material/approval:",
    ),
    privacy_page,
    terms_page,
]


try:
    st.navigation(
        pages
    ).run()

except SessionExpired:
    clear_session_state()

    st.rerun()
