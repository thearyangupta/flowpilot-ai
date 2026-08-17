from uuid import UUID

from langchain.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.providers.gemini_embeddings import (
    GeminiEmbedder,
)
from app.core.config import Settings
from app.services import project_service
from app.services.knowledge.retrieval_service import (
    hybrid_search,
)


class SearchKnowledgeArgs(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=500,
    )


def build_flowpilot_tools(
    *,
    db: Session,
    user_id: UUID,
    settings: Settings,
):
    @tool("list_projects")
    def list_projects() -> list[dict]:
        """List the current user's FlowPilot projects."""

        projects = project_service.get_all(
            db=db,
            user_id=user_id,
        )

        return [
            {
                "id": str(project.id),
                "name": project.name,
            }
            for project in projects
        ]

    @tool(
        "search_knowledge",
        args_schema=SearchKnowledgeArgs,
    )
    def search_knowledge(
        query: str,
    ) -> list[dict]:
        """Search the current user's FlowPilot knowledge base.

        Use this when answering questions that may
        depend on documents uploaded to FlowPilot.
        """

        embedder = GeminiEmbedder(
            settings,
        )

        hits = hybrid_search(
            db=db,
            user_id=user_id,
            query=query,
            embedder=embedder,
            limit=5,
        )

        return [
            {
                "chunk_id": str(
                    hit.chunk.id
                ),
                "content": (
                    hit.chunk.content
                ),
                "score": (
                    hit.fused_score
                ),
            }
            for hit in hits
        ]

    return [
        list_projects,
        search_knowledge,
    ]