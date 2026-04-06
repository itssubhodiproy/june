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
