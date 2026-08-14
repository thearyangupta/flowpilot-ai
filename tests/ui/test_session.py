from __future__ import annotations

from unittest.mock import patch

from ui.session import (
    AUTH_ACCESS_TOKEN_KEY,
    SELECTED_EXECUTION_KEY,
    clear_session_state,
    initialize_session_state,
)


def test_initialize_session_state() -> None:
    fake_state: dict[str, object] = {}

    with patch(
        "ui.session.st.session_state",
        fake_state,
    ):
        initialize_session_state()

    assert (
        fake_state[AUTH_ACCESS_TOKEN_KEY]
        is None
    )

    assert (
        fake_state[SELECTED_EXECUTION_KEY]
        is None
    )


def test_initialize_preserves_existing_state() -> None:
    fake_state: dict[str, object] = {
        AUTH_ACCESS_TOKEN_KEY: "token-123",
        SELECTED_EXECUTION_KEY: "execution-123",
    }

    with patch(
        "ui.session.st.session_state",
        fake_state,
    ):
        initialize_session_state()

    assert (
        fake_state[AUTH_ACCESS_TOKEN_KEY]
        == "token-123"
    )

    assert (
        fake_state[SELECTED_EXECUTION_KEY]
        == "execution-123"
    )


def test_clear_session_state() -> None:
    fake_state: dict[str, object] = {
        AUTH_ACCESS_TOKEN_KEY: "secret-token",
        SELECTED_EXECUTION_KEY: "execution-123",
    }

    with patch(
        "ui.session.st.session_state",
        fake_state,
    ):
        clear_session_state()

    assert (
        fake_state[AUTH_ACCESS_TOKEN_KEY]
        is None
    )

    assert (
        fake_state[SELECTED_EXECUTION_KEY]
        is None
    )
