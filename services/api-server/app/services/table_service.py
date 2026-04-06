from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.column import ColumnModel
from app.models.table import Table
from app.models.table_document import TableDocument
from app.models.user import User
from app.models.user_workspace import UserWorkspace


class TableService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _ensure_workspace_member(self, *, user: User, workspace_id: UUID) -> None:
        membership = await self.db.scalar(
            select(UserWorkspace).where(
                UserWorkspace.user_id == user.id,
                UserWorkspace.workspace_id == workspace_id,
            )
        )
        if not membership:
            raise PermissionError("You do not have access to this workspace")

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

    async def create_table(
        self,
        *,
        user: User,
        workspace_id: UUID,
        name: str | None,
    ) -> Table:
        await self._ensure_workspace_member(user=user, workspace_id=workspace_id)

        if not name:
            count = await self.db.scalar(
                select(func.count(Table.id)).where(
                    Table.workspace_id == workspace_id,
                    Table.deleted_at.is_(None),
                )
            )
            name = f"Review Table #{(count or 0) + 1}"

        table = Table(workspace_id=workspace_id, name=name)
        self.db.add(table)
        await self.db.commit()
        await self.db.refresh(table)
        return table

    async def list_tables(self, *, user: User, workspace_id: UUID) -> list[dict]:
        await self._ensure_workspace_member(user=user, workspace_id=workspace_id)

        document_count = (
            select(func.count(TableDocument.id))
            .where(TableDocument.table_id == Table.id)
            .correlate(Table)
            .scalar_subquery()
        )
        column_count = (
            select(func.count(ColumnModel.id))
            .where(ColumnModel.table_id == Table.id)
            .correlate(Table)
            .scalar_subquery()
        )

        result = await self.db.execute(
            select(Table, document_count.label("document_count"), column_count.label("column_count"))
            .where(
                Table.workspace_id == workspace_id,
                Table.deleted_at.is_(None),
            )
            .order_by(Table.created_at.asc())
        )

        return [
            {
                "id": table.id,
                "workspace_id": table.workspace_id,
                "name": table.name,
                "created_at": table.created_at,
                "updated_at": table.updated_at,
                "document_count": document_count,
                "column_count": column_count,
            }
            for table, document_count, column_count in result.all()
        ]

    async def update_table(self, *, user: User, table_id: UUID, name: str) -> Table:
        table = await self._get_accessible_table(user=user, table_id=table_id)
        table.name = name
        await self.db.commit()
        await self.db.refresh(table)
        return table

    async def delete_table(self, *, user: User, table_id: UUID) -> None:
        table = await self._get_accessible_table(user=user, table_id=table_id)
        table.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
