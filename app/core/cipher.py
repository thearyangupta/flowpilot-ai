from collections.abc import Sequence
from typing import Protocol

from cryptography.fernet import (
    Fernet,
    InvalidToken,
    MultiFernet,
)


class TextCipher(Protocol):
    def encrypt(self, value: str | None) -> bytes | None:
        ...

    def decrypt(self, ciphertext: bytes | None) -> str | None:
        ...


class TokenCipher:
    def __init__(self, keys: Sequence[bytes]):
        if not keys:
            raise ValueError(
                "At least one encryption key is required."
            )

        fernets = [
            Fernet(key)
            for key in keys
        ]

        self._fernet = MultiFernet(fernets)

    def encrypt(
        self,
        value: str | None,
    ) -> bytes | None:
        if value is None:
            return None

        return self._fernet.encrypt(
            value.encode("utf-8")
        )

    def decrypt(
        self,
        ciphertext: bytes | None,
    ) -> str | None:
        if ciphertext is None:
            return None

        try:
            plaintext = self._fernet.decrypt(
                ciphertext
            )
        except InvalidToken as error:
            raise ValueError(
                "Invalid encrypted token."
            ) from error

        return plaintext.decode("utf-8")

    def rotate(
        self,
        ciphertext: bytes,
    ) -> bytes:
        try:
            return self._fernet.rotate(ciphertext)
        except InvalidToken as error:
            raise ValueError(
                "Invalid encrypted token."
            ) from error