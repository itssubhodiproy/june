from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TableCreate(BaseModel):
    workspace_id: UUID
    name: str | None = Field(default=None, min_length=1, max_length=255)


class TableUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TableResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TableListItem(TableResponse):
    document_count: int
    column_count: int


class TableDocumentItem(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    file_size: int
    page_count: int | None
    parse_status: str
    added_at: datetime


class TableColumnItem(BaseModel):
    id: UUID
    title: str
    prompt: str
    type: str
    order: int


class CellSourceReference(BaseModel):
    chunk_id: str
    page: int
    section: str
    quote: str


class TableCellItem(BaseModel):
    id: UUID
    document_id: UUID
    column_id: UUID
    status: str
    answer: str | None
    reasoning: str | None
    source_references: list[CellSourceReference]


class TableDetailResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    documents: list[TableDocumentItem]
    columns: list[TableColumnItem]
    cells: list[TableCellItem]

    class Config:
        from_attributes = True
