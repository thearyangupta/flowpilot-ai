import hashlib

from fastapi import UploadFile

from app.core.public_errors import (
    UPLOAD_TOO_LARGE,
    UPLOAD_TYPE_UNSUPPORTED,
)


ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class UploadValidationError(ValueError):
    """Expected, public-safe upload validation failure."""

    def __init__(
        self,
        public_message: str,
    ) -> None:
        self.public_message = public_message
        super().__init__(public_message)


async def read_limited(
    upload: UploadFile,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> bytes:
    content = await upload.read(
        max_bytes + 1
    )

    if len(content) > max_bytes:
        raise UploadValidationError(
            UPLOAD_TOO_LARGE
        )

    return content


def validate_upload(
    upload: UploadFile,
) -> None:
    if (
        upload.content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise UploadValidationError(
            UPLOAD_TYPE_UNSUPPORTED
        )


def sha256_bytes(
    content: bytes,
) -> str:
    return hashlib.sha256(
        content
    ).hexdigest()
