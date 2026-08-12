from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.knowledge.chunking_service import ChunkData,build_chunk_version


def get_by_checksum(
    db: Session,
    user_id: UUID,
    checksum: str,
) -> KnowledgeDocument | None:
    statement = select(KnowledgeDocument).where(
        KnowledgeDocument.user_id == user_id,
        KnowledgeDocument.checksum == checksum,
    )

    return db.scalar(statement)


def create_document(
    db: Session,
    user_id: UUID,
    name: str,
    checksum: str,
    storage_key: str,
) -> KnowledgeDocument:
    document_id = uuid4()

    document = KnowledgeDocument(
        id=document_id,
        user_id=user_id,
        name=name,
        checksum=checksum,
        storage_key=storage_key,
    )

    db.add(document)
    db.flush()

    return document


def save_extracted_text(
    db: Session,
    document: KnowledgeDocument,
    text: str,
) -> KnowledgeDocument:
    document.extracted_text = text
    db.flush()

    return document


def mark_processing(
    db: Session,
    document: KnowledgeDocument,
) -> KnowledgeDocument:
    document.status = "processing"
    db.flush()
    return document


def mark_ready(
    db: Session,
    document: KnowledgeDocument,
) -> KnowledgeDocument:
    document.status = "ready"
    db.flush()
    return document


def mark_failed(
    db: Session,
    document: KnowledgeDocument,
) -> KnowledgeDocument:
    document.status = "failed"
    db.flush()
    return document


def create_chunks(
    db: Session,
    document: KnowledgeDocument,
    chunks: list[ChunkData],
    embedding_model: str,
) -> list[KnowledgeChunk]:
    knowledge_chunks = [
        KnowledgeChunk(
            document_id=document.id,
            user_id=document.user_id,
            ordinal=chunk.ordinal,
            token_start=chunk.token_start,
            token_end=chunk.token_end,
            content=chunk.content,
            token_count=chunk.token_count,
            chunk_version=build_chunk_version(
                embedding_model=embedding_model,
                content=chunk.content,
            ),
        )
        for chunk in chunks
    ]

    db.add_all(knowledge_chunks)
    db.flush()

    return knowledge_chunks