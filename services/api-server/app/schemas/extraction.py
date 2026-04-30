from app.schemas.cell import CellStatusType
from app.schemas.column import ColumnType
from pydantic import BaseModel
from uuid import UUID
from typing import Any


class ExtractionRunResponse(BaseModel):
    table_id: UUID
    total_cells: int
    status: CellStatusType


class ExtractionManifestCell(BaseModel):
    cell_id: UUID
    document_id: UUID
    column_id: UUID
    column_title: str
    column_prompt: str
    column_type: ColumnType


class ExtractionManifestResponse(BaseModel):
    table_id: UUID
    cells: list[ExtractionManifestCell]


class BulkCellUpdateItem(BaseModel):
    cell_id: UUID
    status: CellStatusType
    answer: str | None = None
    reasoning: str | None = None
    source_references: list[dict[str, Any]] | None = None
    error_message: str | None = None


class BulkCellUpdateRequest(BaseModel):
    results: list[BulkCellUpdateItem]


class BulkCellUpdateResponse(BaseModel):
    updated: int


class CellRerunResponse(BaseModel):
    cell_id: UUID
    status: CellStatusType
