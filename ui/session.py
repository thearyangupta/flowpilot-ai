from __future__ import annotations

import os

import streamlit as st


AUTH_ACCESS_TOKEN_KEY = "auth.access_token"

AUTH_COOKIE_NAME = os.getenv(
    "FLOWPILOT_AUTH_COOKIE_NAME",
    "flowpilot_session",
)

SELECTED_EXECUTION_KEY = (
    "ui.selected_execution"
)


def get_browser_access_token() -> str | None:
    token = st.context.cookies.get(
        AUTH_COOKIE_NAME
    )

    if (
        isinstance(token, str)
        and token.strip()
    ):
        return token

    return None


def initialize_session_state() -> None:
    """
    Initialize temporary Streamlit state.

    Authentication is restored from the
    HttpOnly browser cookie when a new
    Streamlit session starts.
    """

    if (
        AUTH_ACCESS_TOKEN_KEY
        not in st.session_state
    ):
        st.session_state[
            AUTH_ACCESS_TOKEN_KEY
        ] = get_browser_access_token()

    st.session_state.setdefault(
        SELECTED_EXECUTION_KEY,
        None,
    )


def clear_session_state() -> None:
    """
    Clear temporary user-specific UI state.

    The persistent auth cookie itself is
    cleared by the FastAPI logout endpoint.
    """

    st.session_state[
        AUTH_ACCESS_TOKEN_KEY
    ] = None

    st.session_state[
        SELECTED_EXECUTION_KEY
    ] = None