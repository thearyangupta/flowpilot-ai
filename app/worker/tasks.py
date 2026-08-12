from uuid import UUID
from app.models.enums import ExecutionStatus
from app.db.session import SessionLocal
from app.models.execution import Execution
from app.services.execution.execution_event_service import create_execution_event
from app.services.workflow_runner import run,resume
from app.worker.celery_app import celery_app
from app.core.exceptions import RetryableExecutionError
from sqlalchemy import select

from app.ai.providers.gemini_embeddings import GeminiEmbedder
from app.core.config import get_settings
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.knowledge.batching import batched
from app.services.knowledge.document_service import (
    mark_failed,
    mark_ready,
)
from app.services.knowledge.embedding_errors import (
    PermanentEmbeddingError,
    RetryableEmbeddingError,
)
from app.services.knowledge.embedding_validation import (
    validate_embeddings,
)
from app.services.knowledge.embedding_version import (
    embedding_key,
)
import random


@celery_app.task(
    bind=True,
    name="flowpilot.run_execution",
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_execution_task(
    self,
    execution_id: str,
) -> None:
    db = SessionLocal()

    try:
        execution_uuid = UUID(execution_id)

        execution = db.get(
            Execution,
            execution_uuid,
        )

        if execution is None:
            return

        create_execution_event(
            db=db,
            execution_id=execution.id,
            event_type="execution.worker_started",
            details={
                "celery_task_id": self.request.id,
            },
            actor="celery_worker",
        )

        db.commit()

        if execution.status == ExecutionStatus.QUEUED:
            run(
                db=db,
                execution=execution,
                initial_context=dict(execution.input_data or {}),
            )
        else:
            resume(
                db=db,
                execution=execution,
            )

    except RetryableExecutionError as exc:

        db.rollback()

        retry_count = self.request.retries
        countdown = (2 ** retry_count) + random.uniform(0, 1)
        
        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=5,
            )
    
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="flowpilot.knowledge.embed_document",
    acks_late=True,
    reject_on_worker_lost=True,
)
def embed_document_task(
    self,
    document_id: str,
) -> None:
    db = SessionLocal()

    try:
        document_uuid = UUID(document_id)

        document = db.get(
            KnowledgeDocument,
            document_uuid,
        )

        if document is None:
            return

        settings = get_settings()
        embedder = GeminiEmbedder(settings)

        chunks = list(
            db.scalars(
                select(KnowledgeChunk)
                .where(
                    KnowledgeChunk.document_id
                    == document.id
                )
                .order_by(KnowledgeChunk.ordinal)
            )
        )

        pending_chunks = []

        for chunk in chunks:
            expected_key = embedding_key(
                chunk,
                embedder,
            )

            if (
                chunk.embedding is not None
                and chunk.embedding_key
                == expected_key
            ):
                continue

            pending_chunks.append(chunk)

        for batch in batched(
            pending_chunks,
            size=64,
        ):
            texts = [
                chunk.content
                for chunk in batch
            ]

            vectors = embedder.embed(texts)

            validate_embeddings(
                texts=texts,
                vectors=vectors,
                dimensions=embedder.dimensions,
            )

            for chunk, vector in zip(
                batch,
                vectors,
                strict=True,
            ):
                chunk.embedding = vector
                chunk.embedding_model = (
                    embedder.model_name
                )
                chunk.embedding_key = embedding_key(
                    chunk,
                    embedder,
                )

            db.commit()

        remaining = db.scalar(
            select(KnowledgeChunk.id)
            .where(
                KnowledgeChunk.document_id
                == document.id,
                KnowledgeChunk.embedding.is_(None),
            )
            .limit(1)
        )

        if remaining is not None:
            raise PermanentEmbeddingError(
                "Document still contains "
                "unembedded chunks."
            )

        mark_ready(
            db=db,
            document=document,
        )

        db.commit()

    except RetryableEmbeddingError as exc:
        db.rollback()

        retry_count = self.request.retries
        countdown = (
            2 ** retry_count
        ) + random.uniform(0, 1)

        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=5,
        )

    except PermanentEmbeddingError:
        db.rollback()

        document = db.get(
            KnowledgeDocument,
            UUID(document_id),
        )

        if document is not None:
            mark_failed(
                db=db,
                document=document,
            )
            db.commit()

        raise

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()