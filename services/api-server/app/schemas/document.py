from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadUrlRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_type: str = Field(min_length=1, max_length=100)
    file_size: int = Field(gt=0)
    table_id: UUID


class DocumentUploadUrlResponse(BaseModel):
    doc_id: UUID
    upload_url: str
    file_key: str
