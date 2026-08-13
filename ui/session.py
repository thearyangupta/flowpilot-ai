from __future__ import annotations

import streamlit as st


AUTH_ACCESS_TOKEN_KEY = "auth.access_token"
SELECTED_EXECUTION_KEY = "ui.selected_execution"


def initialize_session_state() -> None:
    """Initialize FlowPilot's short-lived Streamlit session state."""

    st.session_state.setdefault(
        AUTH_ACCESS_TOKEN_KEY,
        None,
    )

    st.session_state.setdefault(
        SELECTED_EXECUTION_KEY,
        None,
    )


def clear_session_state() -> None:
    """Clear user-specific temporary UI state."""

    st.session_state[AUTH_ACCESS_TOKEN_KEY] = None
    st.session_state[SELECTED_EXECUTION_KEY] = None