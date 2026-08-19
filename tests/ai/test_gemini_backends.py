from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.ai.agent.model import build_agent_model
from app.ai.providers.gemini_client import (
    build_gemini_client,
)


def make_settings(**overrides):
    values = {
        "gemini_backend": "api_key",
        "gemini_api_key": "fake-test-key",
        "gemini_model": "gemini-3.5-flash",
        "google_cloud_project": "flowpilot-ai-504508",
        "google_cloud_location": "global",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_gemini_client_uses_api_key_backend():
    with patch(
        "app.ai.providers.gemini_client.genai.Client"
    ) as client:
        build_gemini_client(
            make_settings()
        )

    client.assert_called_once_with(
        api_key="fake-test-key",
    )


def test_gemini_client_uses_vertex_backend():
    with patch(
        "app.ai.providers.gemini_client.genai.Client"
    ) as client:
        build_gemini_client(
            make_settings(
                gemini_backend="vertex"
            )
        )

    client.assert_called_once_with(
        vertexai=True,
        project="flowpilot-ai-504508",
        location="global",
    )


def test_gemini_client_requires_vertex_project():
    with pytest.raises(
        ValueError,
        match="GOOGLE_CLOUD_PROJECT is required",
    ):
        build_gemini_client(
            make_settings(
                gemini_backend="vertex",
                google_cloud_project="",
            )
        )


def test_gemini_client_rejects_unknown_backend():
    with pytest.raises(
        ValueError,
        match="Unsupported GEMINI_BACKEND",
    ):
        build_gemini_client(
            make_settings(
                gemini_backend="invalid"
            )
        )


def test_agent_model_uses_api_key_backend():
    with patch(
        "app.ai.agent.model.ChatGoogleGenerativeAI"
    ) as model:
        build_agent_model(
            make_settings()
        )

    model.assert_called_once_with(
        model="gemini-3.5-flash",
        google_api_key="fake-test-key",
        temperature=0,
    )


def test_agent_model_uses_vertex_backend():
    with patch(
        "app.ai.agent.model.ChatGoogleGenerativeAI"
    ) as model:
        build_agent_model(
            make_settings(
                gemini_backend="vertex"
            )
        )

    model.assert_called_once_with(
        model="gemini-3.5-flash",
        vertexai=True,
        project="flowpilot-ai-504508",
        location="global",
        temperature=0,
    )


def test_agent_model_requires_vertex_project():
    with pytest.raises(
        ValueError,
        match="GOOGLE_CLOUD_PROJECT is required",
    ):
        build_agent_model(
            make_settings(
                gemini_backend="vertex",
                google_cloud_project="",
            )
        )


def test_agent_model_rejects_unknown_backend():
    with pytest.raises(
        ValueError,
        match="Unsupported GEMINI_BACKEND",
    ):
        build_agent_model(
            make_settings(
                gemini_backend="invalid"
            )
        )
