from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ColumnType = Literal["free_response", "yes_no", "date", "currency", "verbatim"]


class ColumnCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    prompt: str = Field(min_length=1)
    type: ColumnType


class ColumnCreateResponse(BaseModel):
    id: UUID
    table_id: UUID
    title: str
    prompt: str
    type: str
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ColumnUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    prompt: str | None = Field(default=None, min_length=1)
    type: ColumnType | None = None


class ColumnUpdateResponse(BaseModel):
    id: UUID
    title: str
    prompt: str
    type: str
    order: int
    updated_at: datetime

    class Config:
        from_attributes = True
