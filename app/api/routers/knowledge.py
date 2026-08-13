from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentRead
from app.services.knowledge import (
    document_service,
    upload_service,
)
from app.services.knowledge.chunking_service import token_chunks
from app.services.knowledge.extraction_service import (
    DocumentExtractionError,
    extract_text,
)
from app.services.knowledge.storage_service import storage
from app.services.knowledge.tokenizer import WhitespaceTokenizer
from app.worker.tasks import embed_document_task


router = APIRouter()


@router.get(
    "/knowledge/documents",
    response_model=list[KnowledgeDocumentRead],
)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KnowledgeDocumentRead]:
    return document_service.list_for_user(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/knowledge/documents/{document_id}",
    response_model=KnowledgeDocumentRead,
)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentRead:
    document = document_service.get_for_user(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found.",
        )

    return document


@router.post(
    "/knowledge/documents",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentRead:
    try:
        upload_service.validate_upload(file)

        content = await upload_service.read_limited(file)

        checksum = upload_service.sha256_bytes(
            content
        )

        existing_document = (
            document_service.get_by_checksum(
                db=db,
                user_id=current_user.id,
                checksum=checksum,
            )
        )

        if existing_document is not None:
            return existing_document

        storage_key = storage.put_private(
            user_id=current_user.id,
            checksum=checksum,
            content=content,
        )

        document = document_service.create_document(
            db=db,
            user_id=current_user.id,
            name=file.filename or "unnamed",
            checksum=checksum,
            storage_key=storage_key,
        )

        extracted_text = extract_text(
            content,
            file.content_type or "",
        )

        document_service.save_extracted_text(
            db=db,
            document=document,
            text=extracted_text,
        )

        chunks = token_chunks(
            extracted_text,
            tokenizer=WhitespaceTokenizer(),
        )

        document_service.create_chunks(
            db=db,
            document=document,
            chunks=chunks,
        )

        document_service.mark_processing(
            db=db,
            document=document,
        )

        db.commit()
        db.refresh(document)

        embed_document_task.delay(
            str(document.id)
        )

        return document

    except upload_service.UploadValidationError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DocumentExtractionError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document text extraction failed.",
        ) from error