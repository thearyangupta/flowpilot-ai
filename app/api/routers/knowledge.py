from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentRead
from app.services.knowledge import document_service, upload_service
from app.services.knowledge.storage_service import storage

router = APIRouter()


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
        checksum = upload_service.sha256_bytes(content)

        existing_document = document_service.get_by_checksum(
            db=db,
            user_id=current_user.id,
            checksum=checksum,
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

        db.commit()

        return document

    except upload_service.UploadValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error