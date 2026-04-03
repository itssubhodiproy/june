from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class TemplateColumn(Base):
    __tablename__ = "template_columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "type IN ('free_response', 'yes_no', 'date', 'currency', 'verbatim')",
            name="check_template_column_type"
        ),
    )