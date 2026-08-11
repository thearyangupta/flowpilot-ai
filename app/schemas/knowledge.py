from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    checksum: str
    storage_key: str
    status: str