from fastapi import (
    APIRouter,
    Depends,
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

    final_message = result["messages"][-1]

    return AgentChatResponse(
        message=str(final_message.content),
    )