from pathlib import Path
from uuid import UUID


class StorageService:
    def __init__(self, root: str = "storage"):
        self.root = Path(root)

    def put_private(
        self,
        user_id: UUID,
        checksum: str,
        content: bytes,
    ) -> str:
        storage_key = f"knowledge/{user_id}/{checksum}"

        path = self.root / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

        return storage_key

    def read(self, storage_key: str) -> bytes:
        path = self.root / storage_key
        return path.read_bytes()


storage = StorageService()