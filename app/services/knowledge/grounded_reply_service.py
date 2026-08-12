from dataclasses import dataclass
from enum import Enum

from app.ai.schemas import GroundedReply
from app.services.knowledge.citation_service import (
    InvalidCitationError,
    validate_citations,
)
from app.services.knowledge.context_service import (
    ContextSource,
)


class GroundedReplyStatus(str, Enum):
    GROUNDED = "grounded"
    NEEDS_KNOWLEDGE = "needs_knowledge"


@dataclass(frozen=True)
class GroundedReplyResult:
    status: GroundedReplyStatus
    reply: GroundedReply | None
    missing_information: tuple[str, ...]


def evaluate_grounded_reply(
    *,
    reply: GroundedReply,
    sources: list[ContextSource],
) -> GroundedReplyResult:
    """Convert structured AI output into a trusted application outcome."""

    if reply.unsupported:
        return GroundedReplyResult(
            status=GroundedReplyStatus.NEEDS_KNOWLEDGE,
            reply=None,
            missing_information=tuple(
                reply.missing_information
            ),
        )

    if not reply.citation_ids:
        return GroundedReplyResult(
            status=GroundedReplyStatus.NEEDS_KNOWLEDGE,
            reply=None,
            missing_information=(
                "No supporting knowledge citation was provided.",
            ),
        )

    try:
        validate_citations(
            citations=reply.citation_ids,
            sources=sources,
        )

    except InvalidCitationError:
        return GroundedReplyResult(
            status=GroundedReplyStatus.NEEDS_KNOWLEDGE,
            reply=None,
            missing_information=(
                "The generated reply referenced unavailable knowledge.",
            ),
        )

    return GroundedReplyResult(
        status=GroundedReplyStatus.GROUNDED,
        reply=reply,
        missing_information=(),
    )