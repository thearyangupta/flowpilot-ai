from typing import Protocol


class TextCipher(Protocol):
    def encrypt(self, value: str | None) -> bytes | None:
        ...

    def decrypt(self, ciphertext: bytes | None) -> str | None:
        ...