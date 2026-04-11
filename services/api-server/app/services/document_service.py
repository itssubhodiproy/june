from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cell import Cell
from app.models.column import ColumnModel
from app.models.document import Document
from app.models.table import Table
from app.models.table_document import TableDocument
from app.models.user import User
from app.models.user_workspace import UserWorkspace
from app.services.storage_service import StorageService


class DocumentService:
    def __init__(self, db: AsyncSession, storage: StorageService):
        self.db = db
        self.storage = storage

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
    

    async def create_upload_url(
        self,
        *,
        user: User,
        table_id: UUID,
        file_name: str,
        file_type: str,
        file_size: int,
    ) -> dict:
        table = await self._get_accessible_table(user=user, table_id=table_id)

        document_id = uuid4()
        file_key = f"documents/{document_id}/{file_name}"

        row_order = await self.db.scalar(
            select(func.max(TableDocument.row_order)).where(TableDocument.table_id == table.id)
        )

        document = Document(
            id=document_id,
            workspace_id=table.workspace_id,
            file_name=file_name,
            file_type=file_type,
            file_key=file_key,
            file_size=file_size,
            parse_status="not_ready",
        )
        self.db.add(document)

        self.db.add(
            TableDocument(
                table_id=table.id,
                document_id=document_id,
                row_order=(row_order or 0) + 1,
            )
        )

        column_ids = (
            await self.db.scalars(
                select(ColumnModel.id).where(ColumnModel.table_id == table.id).order_by(ColumnModel.order.asc())
            )
        ).all()

        for column_id in column_ids:
            self.db.add(
                Cell(
                    table_id=table.id,
                    document_id=document_id,
                    column_id=column_id,
                    status="empty",
                )
            )

        upload_url = self.storage.create_presigned_upload_url(
            file_key=file_key,
            file_type=file_type,
        )

        await self.db.commit()

        return {
            "doc_id": document_id,
            "upload_url": upload_url,
            "file_key": file_key,
        }
