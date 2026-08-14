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


st.set_page_config(
    page_title="FlowPilot AI",
    layout="wide",
)


def get_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


def complete_login(api: FlowPilotClient) -> None:
    login_code = st.query_params.get("login_code")

    if not login_code:
        return

    try:
        access_token = api.exchange_login_code(
            login_code
        )

        st.session_state[
            AUTH_ACCESS_TOKEN_KEY
        ] = access_token

    except ApiError as error:
        st.error(error.message)

    finally:
        # Never leave the one-time credential in the URL.
        st.query_params.clear()


def render_sign_in(api: FlowPilotClient) -> None:
    st.title("FlowPilot AI")
    st.write(
        "Sign in to manage workflows, knowledge, "
        "executions and approvals."
    )

    try:
        authorization_url = api.google_login_url()

    except ApiError as error:
        st.error(error.message)
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
    render_sign_in(api)


with st.sidebar:
    st.caption("FlowPilot AI")

    try:
        gmail_authorization_url = (
            api.gmail_connect_url()
        )

        st.link_button(
            "Connect Gmail",
            gmail_authorization_url,
            use_container_width=True,
        )

    except ApiError as error:
        st.error(error.message)

    if st.button(
        "Logout",
        key="auth.logout",
        use_container_width=True,
    ):
        clear_session_state()
        st.rerun()


pages = [
    st.Page(
        "pages/home.py",
        title="Home",
        default=True,
    ),
    st.Page(
        "pages/workflows.py",
        title="Workflows",
    ),
    st.Page(
        "pages/knowledge.py",
        title="Knowledge",
    ),
    st.Page(
        "pages/executions.py",
        title="Executions",
    ),
    st.Page(
        "pages/approvals.py",
        title="Approvals",
    ),
]


try:
    st.navigation(pages).run()

except SessionExpired:
    clear_session_state()
    st.rerun()