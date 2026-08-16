from langchain_google_genai import (
    ChatGoogleGenerativeAI,
)

from app.core.config import Settings


def build_agent_model(
    settings: Settings,
) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )