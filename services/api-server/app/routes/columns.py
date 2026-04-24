from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.column import (
    ColumnCreateRequest,
    ColumnCreateResponse,
    ColumnUpdateRequest,
    ColumnUpdateResponse,
)
from app.services.column_service import ColumnService

router = APIRouter(prefix="/tables/{table_id}/columns", tags=["columns"])


@router.post(
    "/", response_model=ColumnCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_column(
    table_id: UUID,
    data: ColumnCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ColumnService(db)
    try:
        column = await service.create_column(
            user=current_user,
            table_id=table_id,
            title=data.title,
            prompt=data.prompt,
            type=data.type,
        )
        return column
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{col_id}", response_model=ColumnUpdateResponse)
async def update_column(
    table_id: UUID,
    col_id: UUID,
    data: ColumnUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ColumnService(db)
    try:
        column = await service.update_column(
            user=current_user,
            table_id=table_id,
            column_id=col_id,
            title=data.title,
            prompt=data.prompt,
            type=data.type,
        )
        return column
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{col_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    table_id: UUID,
    col_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ColumnService(db)
    try:
        await service.delete_column(
            user=current_user,
            table_id=table_id,
            column_id=col_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
