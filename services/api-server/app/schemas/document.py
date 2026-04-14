from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BoundingBoxItem(BaseModel):
    text: str
    x: float
    y: float
    width: float
    height: float


class BoundingBox(BaseModel):
    page_width: float
    page_height: float
    items: list[BoundingBoxItem]


class DocumentChunkCreate(BaseModel):
    chunk_index: int = Field(ge=0)
    text_content: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    section: str | None = Field(default=None, max_length=255)
    bbox: BoundingBox
    embedding: list[float] = Field(min_length=1)


class DocumentChunksCreateRequest(BaseModel):
    chunks: list[DocumentChunkCreate]


class DocumentChunksCreateResponse(BaseModel):
    stored: int


class DocumentUploadUrlRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_type: str = Field(min_length=1, max_length=100)
    file_size: int = Field(gt=0)
    table_id: UUID


class DocumentUploadUrlResponse(BaseModel):
    doc_id: UUID
    upload_url: str
    file_key: str


class DocumentConfirmResponse(BaseModel):
    doc_id: UUID
    parse_status: str


class DocumentUpdateRequest(BaseModel):
    parse_status: Literal["not_ready", "queued", "ready", "error"] | None = None
    page_count: int | None = Field(default=None, ge=1)
    error_message: str | None = None


class DocumentUpdateResponse(BaseModel):
    id: UUID
    parse_status: str
    page_count: int | None
    updated_at: datetime

    class Config:
        from_attributes = True
