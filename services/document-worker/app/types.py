from typing import Literal

from pydantic import BaseModel, Field


class DocumentParsingTask(BaseModel):
    task_id: str
    document_id: str
    file_key: str
    table_id: str
    retry_count: int = Field(ge=0, default=0)


class ParsedTextItem(BaseModel):
    text: str
    x: float
    y: float
    width: float
    height: float


class ParsedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str
    page_width: float
    page_height: float
    text_items: list[ParsedTextItem]


class ParsedDocument(BaseModel):
    pages: list[ParsedPage]


class BoundingBox(BaseModel):
    page_width: float
    page_height: float
    items: list[ParsedTextItem]


class ChunkDraft(BaseModel):
    chunk_index: int = Field(ge=0)
    text_content: str
    page_number: int = Field(ge=1)
    section: str | None = None
    bbox: BoundingBox


class ChunkPayload(BaseModel):
    chunk_index: int = Field(ge=0)
    text_content: str
    page_number: int = Field(ge=1)
    section: str | None = None
    bbox: BoundingBox
    embedding: list[float] = Field(min_length=1)


class DocumentProcessingEvent(BaseModel):
    type: Literal["doc_processing"]
    document_id: str
    table_id: str


class DocumentReadyEvent(BaseModel):
    type: Literal["doc_ready"]
    document_id: str
    table_id: str
    page_count: int = Field(ge=1)


class DocumentErrorEvent(BaseModel):
    type: Literal["doc_error"]
    document_id: str
    table_id: str
