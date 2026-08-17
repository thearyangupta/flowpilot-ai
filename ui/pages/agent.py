from __future__ import annotations

import streamlit as st

from ui.api import (
    ApiError,
    FlowPilotClient,
    get_api_base_url,
)
from ui.session import (
    AUTH_ACCESS_TOKEN_KEY,
)


AGENT_MESSAGES_KEY = "agent.messages"


def get_api() -> FlowPilotClient:
    return FlowPilotClient(
        get_api_base_url(),
        token_getter=lambda: st.session_state.get(
            AUTH_ACCESS_TOKEN_KEY
        ),
    )


def initialize_agent_messages() -> None:
    if AGENT_MESSAGES_KEY not in st.session_state:
        st.session_state[
            AGENT_MESSAGES_KEY
        ] = []


st.title("FlowPilot Agent")

st.caption(
    "Ask FlowPilot to work with your projects, "
    "knowledge and connected tools."
)

initialize_agent_messages()

api = get_api()

if st.button(
    "Clear conversation",
    key="agent.clear",
):
    st.session_state[
        AGENT_MESSAGES_KEY
    ] = []
    st.rerun()

for message in st.session_state[
    AGENT_MESSAGES_KEY
]:
    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )


prompt = st.chat_input(
    "Ask FlowPilot..."
)

if prompt:
    user_message = {
        "role": "user",
        "content": prompt,
    }

    st.session_state[
        AGENT_MESSAGES_KEY
    ].append(
        user_message
    )

    with st.chat_message(
        "user"
    ):
        st.markdown(prompt)

    try:
        with st.chat_message(
            "assistant"
        ):
            with st.spinner(
                "FlowPilot is working..."
            ):
                response = (
                    api.chat_with_agent(
                        prompt
                    )
                )

            st.markdown(response)

        st.session_state[
            AGENT_MESSAGES_KEY
        ].append(
            {
                "role": "assistant",
                "content": response,
            }
        )

    except ApiError as error:
        st.error(error.message)