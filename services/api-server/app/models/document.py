from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_key = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    page_count = Column(Integer, nullable=True)
    parse_status = Column(String(20), nullable=False, default="not_ready")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "parse_status IN ('not_ready', 'queued', 'ready', 'error')",
            name="check_document_parse_status"
        ),
    )
