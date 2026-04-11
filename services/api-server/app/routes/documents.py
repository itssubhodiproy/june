from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_storage_service
from app.models.user import User
from app.schemas.document import DocumentUploadUrlRequest, DocumentUploadUrlResponse
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload-url", response_model=DocumentUploadUrlResponse, status_code=status.HTTP_201_CREATED)
async def create_document_upload_url(
    data: DocumentUploadUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    document_service = DocumentService(db, storage)
    try:
        return await document_service.create_upload_url(
            user=current_user,
            table_id=data.table_id,
            file_name=data.file_name,
            file_type=data.file_type,
            file_size=data.file_size,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
