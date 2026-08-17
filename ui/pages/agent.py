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
from ui.styles import render_html


AGENT_MESSAGES_KEY = "agent.messages"


QUICK_PROMPTS = (
    (
        "Projects",
        "View and understand your current projects.",
        "What projects do I currently have in FlowPilot?",
    ),
    (
        "Knowledge",
        "Search across your uploaded knowledge.",
        (
            "Search my knowledge base and tell me "
            "what you can help with."
        ),
    ),
    (
        "Order status",
        "Look up the latest status of an order.",
        "What is the status of order ORD-123456?",
    ),
)


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


def add_assistant_error(
    error: ApiError,
) -> None:
    st.session_state[
        AGENT_MESSAGES_KEY
    ].append(
        {
            "role": "assistant",
            "content": error.message,
            "is_error": True,
        }
    )


def submit_prompt(
    prompt: str,
    api: FlowPilotClient,
) -> None:
    st.session_state[
        AGENT_MESSAGES_KEY
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        response = api.chat_with_agent(
            prompt
        )

        st.session_state[
            AGENT_MESSAGES_KEY
        ].append(
            {
                "role": "assistant",
                "content": response,
            }
        )

    except ApiError as error:
        add_assistant_error(error)


def render_page_header() -> None:
    render_html(
        """
        <div class="fp-agent-hero">
            <div class="fp-agent-eyebrow">
                <span class="fp-agent-status"></span>
                FLOWPILOT AGENT
            </div>

            <h1>
                What can I help you get done?
            </h1>

            <p>
                Work with your projects, knowledge and
                connected tools from one place.
            </p>
        </div>
        """
    )


def render_quick_prompts(
    api: FlowPilotClient,
) -> None:
    render_html(
        """
        <div class="fp-section-heading">
            <div class="fp-section-kicker">
                START HERE
            </div>

            <h3>
                Try a quick action
            </h3>
        </div>
        """
    )

    columns = st.columns(
        len(QUICK_PROMPTS),
        gap="medium",
    )

    for column, (
        label,
        description,
        prompt,
    ) in zip(
        columns,
        QUICK_PROMPTS,
        strict=True,
    ):
        with column:
            with st.container(
                border=True,
            ):
                render_html(
                    f"""
                    <div class="fp-action-title">
                        {label}
                    </div>

                    <div class="fp-action-description">
                        {description}
                    </div>
                    """
                )

                if st.button(
                    f"Open {label}",
                    key=f"agent.quick.{label}",
                    icon=":material/arrow_forward:",
                    use_container_width=True,
                ):
                    submit_prompt(
                        prompt,
                        api,
                    )

                    st.rerun()


def render_conversation_header() -> None:
    header_left, header_right = (
        st.columns(
            [5, 1]
        )
    )

    with header_left:
        render_html(
            """
            <div class="fp-section-heading fp-chat-heading">
                <div class="fp-section-kicker">
                    CONVERSATION
                </div>

                <h3>
                    Working with FlowPilot
                </h3>
            </div>
            """
        )

    with header_right:
        if st.button(
            "Clear",
            key="agent.clear",
            icon=":material/delete_sweep:",
            use_container_width=True,
        ):
            st.session_state[
                AGENT_MESSAGES_KEY
            ] = []

            st.rerun()


def render_messages() -> None:
    for message in st.session_state[
        AGENT_MESSAGES_KEY
    ]:
        role = message["role"]

        avatar = (
            ":material/person:"
            if role == "user"
            else ":material/auto_awesome:"
        )

        with st.chat_message(
            role,
            avatar=avatar,
        ):
            if message.get(
                "is_error"
            ):
                st.error(
                    message["content"],
                    icon=":material/error:",
                )

            else:
                st.markdown(
                    message["content"]
                )


initialize_agent_messages()

api = get_api()

render_page_header()


if not st.session_state[
    AGENT_MESSAGES_KEY
]:
    render_html(
        """
        <div class="fp-agent-intro">
            Ask a question naturally or choose one of
            the actions below. FlowPilot will use the
            tools available to your workspace.
        </div>
        """
    )

    render_quick_prompts(
        api
    )

else:
    render_conversation_header()
    render_messages()


prompt = st.chat_input(
    "Ask FlowPilot anything..."
)


if prompt:
    st.session_state[
        AGENT_MESSAGES_KEY
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message(
        "user",
        avatar=":material/person:",
    ):
        st.markdown(prompt)

    with st.chat_message(
        "assistant",
        avatar=":material/auto_awesome:",
    ):
        try:
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
            st.error(
                error.message,
                icon=":material/error:",
            )

            add_assistant_error(
                error
            )