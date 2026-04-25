from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cell import Cell
from app.models.column import ColumnModel
from app.models.document import Document
from app.models.table import Table
from app.models.table_document import TableDocument
from app.models.user import User
from app.models.user_workspace import UserWorkspace


class ColumnService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def _get_column(self, *, table_id: UUID, column_id: UUID) -> ColumnModel:
        column = await self.db.scalar(
            select(ColumnModel).where(
                ColumnModel.id == column_id,
                ColumnModel.table_id == table_id,
            )
        )
        if not column:
            raise LookupError("Column not found")
        return column

    async def create_column(
        self,
        *,
        user: User,
        table_id: UUID,
        title: str,
        prompt: str,
        type: str,
    ) -> ColumnModel:
        table = await self._get_accessible_table(user=user, table_id=table_id)

        max_order = await self.db.scalar(
            select(func.max(ColumnModel.order)).where(ColumnModel.table_id == table.id)
        )

        column = ColumnModel(
            table_id=table.id,
            title=title,
            prompt=prompt,
            type=type,
            order=(max_order or 0) + 1,
        )
        self.db.add(column)
        await self.db.flush()

        # Batch-insert empty cells for every document in the table
        document_ids = (
            await self.db.scalars(
                select(TableDocument.document_id)
                .join(Document, Document.id == TableDocument.document_id)
                .where(
                    TableDocument.table_id == table.id,
                    Document.deleted_at.is_(None),
                )
            )
        ).all()

        if document_ids:
            await self.db.execute(
                insert(Cell),
                [
                    {
                        "table_id": table.id,
                        "document_id": doc_id,
                        "column_id": column.id,
                        "status": "empty",
                    }
                    for doc_id in document_ids
                ],
            )

        await self.db.commit()
        await self.db.refresh(column)
        return column

    async def update_column(
        self,
        *,
        user: User,
        table_id: UUID,
        column_id: UUID,
        title: str | None = None,
        prompt: str | None = None,
        type: str | None = None,
    ) -> ColumnModel:
        await self._get_accessible_table(user=user, table_id=table_id)
        column = await self._get_column(table_id=table_id, column_id=column_id)

        prompt_changed = prompt is not None and prompt != column.prompt
        type_changed = type is not None and type != column.type

        if title is not None:
            column.title = title
        if prompt is not None:
            column.prompt = prompt
        if type is not None:
            column.type = type

        # If prompt or type changed, mark completed cells as stale
        if prompt_changed or type_changed:
            await self.db.execute(
                update(Cell)
                .where(
                    Cell.column_id == column_id,
                    Cell.status == "completed",
                )
                .values(status="stale")
            )

        await self.db.commit()
        await self.db.refresh(column)
        return column

    async def delete_column(
        self,
        *,
        user: User,
        table_id: UUID,
        column_id: UUID,
    ) -> None:
        await self._get_accessible_table(user=user, table_id=table_id)
        column = await self._get_column(table_id=table_id, column_id=column_id)

        await self.db.execute(
            delete(Cell).where(Cell.column_id == column.id)
        )
        await self.db.delete(column)
        await self.db.commit()
