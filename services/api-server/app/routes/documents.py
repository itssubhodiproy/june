from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from redis.asyncio import Redis

from uuid import UUID

from app.dependencies import get_current_user, get_db, get_redis_client, get_storage_service
from app.models.user import User
from app.schemas.document import (
    DocumentChunksCreateRequest,
    DocumentChunksCreateResponse,
    DocumentConfirmResponse,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
    DocumentUploadUrlRequest,
    DocumentUploadUrlResponse,
)
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


@router.post("/{doc_id}/confirm", response_model=DocumentConfirmResponse)
async def confirm_document_upload(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
    redis: Redis = Depends(get_redis_client),
):
    document_service = DocumentService(db, storage, redis)
    try:
        return await document_service.confirm_upload(
            user=current_user,
            document_id=doc_id,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{doc_id}/chunks", response_model=DocumentChunksCreateResponse, status_code=status.HTTP_201_CREATED)
async def store_document_chunks(
    doc_id: UUID,
    data: DocumentChunksCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    document_service = DocumentService(db, storage)
    try:
        return await document_service.store_chunks(
            user=current_user,
            document_id=doc_id,
            chunks=[chunk.model_dump() for chunk in data.chunks],
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{doc_id}", response_model=DocumentUpdateResponse)
async def update_document(
    doc_id: UUID,
    data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    document_service = DocumentService(db, storage)
    try:
        return await document_service.update_document(
            user=current_user,
            document_id=doc_id,
            parse_status=data.parse_status,
            page_count=data.page_count,
            error_message=data.error_message,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
