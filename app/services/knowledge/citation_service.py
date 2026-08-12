from collections.abc import Sequence

from app.services.knowledge.context_service import ContextSource


class InvalidCitationError(ValueError):
    """Raised when generated citations reference unavailable sources."""


def validate_citations(
    *,
    citations: Sequence[str],
    sources: Sequence[ContextSource],
) -> None:
    allowed_labels = {
        source.label
        for source in sources
    }

    invalid_labels = {
        citation
        for citation in citations
        if citation not in allowed_labels
    }

    if invalid_labels:
        invalid = ", ".join(
            sorted(invalid_labels)
        )

        raise InvalidCitationError(
            f"Invalid knowledge citations: {invalid}"
        )