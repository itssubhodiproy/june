from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ColumnType = Literal["free_response", "yes_no", "date", "currency", "verbatim"]
CellStatus = Literal["completed", "error"]
TaskType = Literal["run_all", "run_rerun"]


class ExtractionTask(BaseModel):
    table_id: str
    type: TaskType
    cell_id: str | None = None
    retry_count: int = Field(default=0, ge=0)


class ExtractionManifestCell(BaseModel):
    cell_id: str
    document_id: str
    column_id: str
    column_title: str
    column_prompt: str
    column_type: ColumnType


class ExtractionManifest(BaseModel):
    table_id: str
    cells: list[ExtractionManifestCell]


class RetrievedChunk(BaseModel):
    id: str
    chunk_index: int = Field(ge=0)
    text_content: str
    page_number: int = Field(ge=1)
    section: str | None = None
    similarity_score: float | None = None


class ChunkSearchResponse(BaseModel):
    chunks: list[RetrievedChunk]


class RAGContextResult(BaseModel):
    chunks: list[RetrievedChunk]
    context: str


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    page: int = Field(ge=1)
    section: str
    quote: str


class ParsedLLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    reasoning: str
    source_references: list[SourceReference]


class CellUpdatePayload(BaseModel):
    cell_id: str
    status: CellStatus
    answer: str | None = None
    reasoning: str | None = None
    source_references: list[SourceReference] = Field(default_factory=list)
    error_message: str | None = None


class BulkUpdateResponse(BaseModel):
    updated: int = Field(ge=0)


class CellCompletedEvent(BaseModel):
    type: Literal["cell_completed"]
    cell_id: str
    table_id: str
    document_id: str
    column_id: str
    answer: str
    reasoning: str
    source_references: list[SourceReference]


class CellErrorEvent(BaseModel):
    type: Literal["cell_error"]
    cell_id: str
    table_id: str
    document_id: str
    column_id: str
    error: str


class RunCompletedEvent(BaseModel):
    type: Literal["run_completed"]
    table_id: str
    total: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
