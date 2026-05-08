from uuid import UUID
from sqlalchemy import bindparam, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.cell import Cell
from app.models.column import ColumnModel
from app.models.document import Document
from app.models.table import Table
from app.models.user import User
from app.models.user_workspace import UserWorkspace
from app.schemas.extraction import BulkCellUpdateItem
from app.utils.redis_tasks import enqueue_extraction_run


class ExtractionService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis

    async def _get_accessible_table(self, *, user: User, table_id: UUID) -> Table:
        table = await self.db.scalar(
            select(Table)
            .join(UserWorkspace, UserWorkspace.workspace_id == Table.workspace_id)
            .where(
                Table.id == table_id,
                Table.deleted_at.is_(None),
                UserWorkspace.user_id == user.id,
            )
        )
        if not table:
            raise LookupError("Table not found")
        return table

    async def run_table_extraction(self, *, user: User, table_id: UUID) -> dict:
        table = await self._get_accessible_table(user=user, table_id=table_id)

        result = await self.db.execute(
            select(Cell)
            .join(Document, Document.id == Cell.document_id)
            .where(
                Cell.table_id == table.id,
                Cell.status.in_(["empty", "stale"]),
                Document.parse_status == "ready",
            )
        )
        cells = result.scalars().all()
        
        cell_ids = [cell.id for cell in cells]
        total_cells = len(cell_ids)

        if total_cells > 0:
            if not self.redis:
                raise RuntimeError("Redis client not configured")

            await self.db.execute(
                update(Cell)
                .where(Cell.id.in_(cell_ids))
                .values(status="extracting")
            )
            await enqueue_extraction_run(self.redis, table_id=table.id)
            await self.db.commit()

        return {
            "table_id": table.id,
            "total_cells": total_cells,
            "status": "extracting" if total_cells > 0 else "completed",
        }

    async def get_extraction_manifest(self, *, table_id: UUID, cell_id: UUID | None = None) -> dict:
        query = (
            select(Cell, ColumnModel)
            .join(ColumnModel, ColumnModel.id == Cell.column_id)
            .where(
                Cell.table_id == table_id,
                Cell.status == "extracting",
            )
        )
        
        if cell_id:
            query = query.where(Cell.id == cell_id)
            
        result = await self.db.execute(query)
        
        cells_data = []
        for cell, column in result.all():
            cells_data.append({
                "cell_id": cell.id,
                "document_id": cell.document_id,
                "column_id": column.id,
                "column_title": column.title,
                "column_prompt": column.prompt,
                "column_type": column.type,
            })
            
        return {
            "table_id": table_id,
            "cells": cells_data,
        }

    async def bulk_update_cells(self, *, table_id: UUID, results: list[BulkCellUpdateItem]) -> int:
        if not results:
            return 0

        mappings = [
            {
                "cell_id": item.cell_id,
                "status": item.status,
                "answer": item.answer,
                "reasoning": item.reasoning,
                "source_references": item.source_references,
                "error_message": item.error_message,
            }
            for item in results
        ]

        stmt = (
            update(Cell.__table__)
            .where(Cell.id == bindparam("cell_id"), Cell.table_id == table_id)
            .values(
                status=bindparam("status"),
                answer=bindparam("answer"),
                reasoning=bindparam("reasoning"),
                source_references=bindparam("source_references"),
                error_message=bindparam("error_message"),
            )
        )
        await self.db.execute(stmt, mappings)
        await self.db.commit()
        return len(results)

    async def rerun_cell(self, *, user: User, table_id: UUID, cell_id: UUID) -> dict:
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        table = await self._get_accessible_table(user=user, table_id=table_id)
        
        cell = await self.db.scalar(
            select(Cell)
            .where(Cell.id == cell_id, Cell.table_id == table.id)
        )
        if not cell:
            raise LookupError("Cell not found")
        # Enqueue before commit to prevent stuck 'extracting' status on queue failure
        cell.status = "extracting"
        await enqueue_extraction_run(self.redis, table_id=table.id, type="rerun_cell", cell_id=cell.id)
        await self.db.commit()
            
        return {
            "cell_id": cell.id,
            "status": "extracting"
        }
