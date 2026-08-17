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
        # Never leave the one-time credential
        # in the browser URL.
        st.query_params.clear()


def render_sign_in(
    api: FlowPilotClient,
) -> None:
    st.title(
        "FlowPilot AI"
    )

    st.caption(
        "AI-powered workflow automation with "
        "agents, knowledge and connected tools."
    )

    st.write(
        "Sign in to access your FlowPilot workspace."
    )

    try:
        authorization_url = (
            api.google_login_url()
        )

    except ApiError as error:
        st.error(
            error.message
        )

        st.stop()

    st.link_button(
        "Continue with Google",
        authorization_url,
        type="primary",
    )

    st.stop()


initialize_session_state()

api = get_api()

complete_login(api)


if not st.session_state.get(
    AUTH_ACCESS_TOKEN_KEY
):
    render_sign_in(
        api
    )


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

    try:
        gmail_authorization_url = (
            api.gmail_connect_url()
        )

        st.link_button(
            "Gmail",
            gmail_authorization_url,
            icon=":material/mail:",
            use_container_width=True,
        )

    except ApiError as error:
        st.caption(
            f"Gmail unavailable: "
            f"{error.message}"
        )

    st.divider()

    if st.button(
        "Logout",
        key="auth.logout",
        icon=":material/logout:",
        use_container_width=True,
    ):
        clear_session_state()

        st.rerun()


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
]


try:
    st.navigation(
        pages
    ).run()

except SessionExpired:
    clear_session_state()

    st.rerun()