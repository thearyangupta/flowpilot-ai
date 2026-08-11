import hashlib
from fastapi import UploadFile


ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


async def read_limited(
    upload: UploadFile,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> bytes:
    content = await upload.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise UploadValidationError(
            "Uploaded file exceeds the 10 MB limit."
        )

    return content


def validate_upload(upload: UploadFile) -> None:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError(
            f"Unsupported content type: {upload.content_type}"
        )


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
