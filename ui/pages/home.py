import streamlit as st


st.title("FlowPilot AI")

st.caption(
    "AI-powered workflow automation with "
    "projects, knowledge, approvals and agents."
)

st.markdown(
    """
### Build, automate and reason with your work

FlowPilot combines structured workflows with
an AI agent that can work across your projects,
knowledge base and connected tools.
"""
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
#### ✦ Agent

Ask FlowPilot to reason across your projects,
knowledge and connected tools.
"""
    )

with col2:
    st.markdown(
        """
#### ⚙️ Workflows

Create and run structured automation with
tracked execution history.
"""
    )

with col3:
    st.markdown(
        """
#### 📚 Knowledge

Upload documents and retrieve relevant context
for grounded AI responses.
"""
    )

st.divider()

col4, col5 = st.columns(2)

with col4:
    st.markdown(
        """
#### ✅ Human approvals

Review AI-generated actions before they are
executed when human oversight is required.
"""
    )

with col5:
    st.markdown(
        """
#### 🔌 Connected tools

Use Gmail and MCP-backed tools from the same
FlowPilot workspace.
"""
    )

st.info(
    "Start with the Agent page for the primary "
    "FlowPilot AI experience."
)