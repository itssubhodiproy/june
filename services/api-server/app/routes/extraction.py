from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_current_user, get_db, get_redis_client, require_internal_service
from app.models.user import User
from app.schemas.extraction import (
    BulkCellUpdateRequest,
    BulkCellUpdateResponse,
    CellRerunResponse,
    ExtractionManifestResponse,
    ExtractionRunResponse,
)
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/tables/{table_id}", tags=["extraction"])


@router.post("/run", response_model=ExtractionRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_extraction(
    table_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    service = ExtractionService(db, redis)
    try:
        return await service.run_table_extraction(user=current_user, table_id=table_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/cells/{cell_id}/rerun", response_model=CellRerunResponse, status_code=status.HTTP_202_ACCEPTED)
async def rerun_cell(
    table_id: UUID,
    cell_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
):
    service = ExtractionService(db, redis)
    try:
        return await service.rerun_cell(user=current_user, table_id=table_id, cell_id=cell_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/extraction-manifest", response_model=ExtractionManifestResponse)
async def get_extraction_manifest(
    table_id: UUID,
    cell_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_service),
):
    service = ExtractionService(db)
    return await service.get_extraction_manifest(table_id=table_id, cell_id=cell_id)


@router.post("/cells/bulk-update", response_model=BulkCellUpdateResponse)
async def bulk_update_cells(
    table_id: UUID,
    data: BulkCellUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_internal_service),
):
    service = ExtractionService(db)
    updated = await service.bulk_update_cells(table_id=table_id, results=data.results)
    return {"updated": updated}
