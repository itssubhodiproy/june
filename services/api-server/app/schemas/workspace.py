from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    is_personal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListItem(WorkspaceResponse):
    role: str
    joined_at: datetime
