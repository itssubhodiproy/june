from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from uuid import uuid4

from app.models.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), nullable=False)
    total_cells = Column(Integer, nullable=False)
    completed_cells = Column(Integer, nullable=False, default=0)
    failed_cells = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="running")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="check_job_status"
        ),
    )