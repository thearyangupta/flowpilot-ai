from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from langchain_google_genai.chat_models import (
    ChatGoogleGenerativeAIError,
)
from sqlalchemy.orm import Session

from app.ai.agent.agent import (
    build_flowpilot_agent,
)
from app.ai.agent.model import (
    build_agent_model,
)
from app.api.dependencies import (
    get_current_user,
)
from app.core.config import (
    Settings,
    get_settings,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
)


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


def extract_agent_text(
    content: object,
) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for item in content:
            if not isinstance(item, dict):
                continue

            if item.get("type") != "text":
                continue

            text = item.get("text")

            if isinstance(text, str):
                text_parts.append(text)

        if text_parts:
            return "\n".join(text_parts)

    return str(content)


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def chat_with_agent(
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
    settings: Settings = Depends(
        get_settings
    ),
) -> AgentChatResponse:
    model = build_agent_model(
        settings,
    )

    agent = build_flowpilot_agent(
        model=model,
        db=db,
        user_id=current_user.id,
        settings=settings,
    )

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": payload.message,
                    }
                ]
            }
        )

    except ChatGoogleGenerativeAIError as error:
        error_message = str(error)

        if (
            "RESOURCE_EXHAUSTED"
            in error_message
            or "429" in error_message
        ):
            raise HTTPException(
                status_code=503,
                detail=(
                    "The AI model has reached its "
                    "current usage limit. "
                    "Please try again later."
                ),
            ) from error

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI model is temporarily "
                "unavailable."
            ),
        ) from error

    final_message = result[
        "messages"
    ][-1]

    return AgentChatResponse(
        message=extract_agent_text(
            final_message.content
        ),
    )