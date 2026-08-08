import base64
from typing import Any, Iterator
from html.parser import HTMLParser
import hashlib
from collections.abc import Iterable


class GmailNormalizationError(Exception):
    """Base exception for Gmail normalization failures."""


class GmailBase64DecodeError(GmailNormalizationError):
    """Raised when Gmail Base64URL content cannot be decoded."""


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()

        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


def decode_gmail_base64url(value: str) -> bytes:
    if not value:
        return b""

    try:
        padding = "=" * (-len(value) % 4)
        padded_value = value + padding

        return base64.urlsafe_b64decode(padded_value)

    except (ValueError, TypeError) as error:
        raise GmailBase64DecodeError(
            "Gmail Base64URL content could not be decoded."
        ) from error


def iter_gmail_mime_parts(
    part: dict[str, Any],
) -> Iterator[dict[str, Any]]:
    """
    Recursively yield every MIME part in a Gmail message.
    """

    yield part

    for child in part.get("parts", []):
        yield from iter_gmail_mime_parts(child)


def select_gmail_body_part(
    parts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Select the preferred Gmail body representation.

    text/plain is preferred.
    text/html is used as a fallback.
    """

    html_part: dict[str, Any] | None = None

    for part in parts:
        mime_type = part.get("mimeType", "").lower()

        if mime_type == "text/plain":
            return part

        if mime_type == "text/html" and html_part is None:
            html_part = part

    return html_part



def strip_html(value: str) -> str:
    if not value:
        return ""

    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()

    return parser.get_text()


def normalize_gmail_headers(
    headers: Iterable[dict[str, Any]],
) -> dict[str, str]:
    normalized: dict[str, str] = {}

    for header in headers:
        name = str(header.get("name", "")).strip().lower()
        value = str(header.get("value", "")).strip()

        if not name:
            continue

        if name in normalized:
            normalized[name] = (
                f"{normalized[name]}\n{value}"
            )
        else:
            normalized[name] = value

    return normalized


def compute_body_sha256(body_text: str) -> str:
    return hashlib.sha256(
        body_text.encode("utf-8")
    ).hexdigest()