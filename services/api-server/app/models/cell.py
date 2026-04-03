from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class Cell(Base):
    __tablename__ = "cells"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    column_id = Column(UUID(as_uuid=True), ForeignKey("columns.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="empty")
    answer = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    source_references = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('empty', 'extracting', 'completed', 'stale', 'error')",
            name="check_cell_status"
        ),
    )