from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class TableDocument(Base):
    __tablename__ = "table_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    row_order = Column(Integer, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())