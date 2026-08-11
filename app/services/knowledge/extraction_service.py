from io import BytesIO

from pypdf import PdfReader


class DocumentExtractionError(Exception):
    """Raised when document text extraction fails."""


def extract_text(content: bytes, content_type: str) -> str:
    if content_type in {"text/plain", "text/markdown"}:
        return content.decode("utf-8")

    if content_type == "application/pdf":
        return _extract_pdf_text(content)

    raise DocumentExtractionError(
        f"Unsupported content type for extraction: {content_type}"
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except Exception as exc:
        raise DocumentExtractionError(
            "Failed to extract text from PDF"
        ) from exc