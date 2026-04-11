from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.cell import Cell
from app.models.column import ColumnModel
from app.models.document import Document
from app.models.table import Table
from app.models.table_document import TableDocument
from app.models.user import User
from app.models.user_workspace import UserWorkspace
from app.services.storage_service import StorageService
from app.utils.redis_tasks import enqueue_document_parsing


class DocumentService:
    def __init__(self, db: AsyncSession, storage: StorageService, redis: Redis | None = None):
        self.db = db
        self.storage = storage
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

    async def _get_accessible_document(self, *, user: User, document_id: UUID) -> tuple[Document, UUID]:
        result = await self.db.execute(
            select(Document, Table.id)
            .join(TableDocument, TableDocument.document_id == Document.id)
            .join(Table, Table.id == TableDocument.table_id)
            .join(UserWorkspace, UserWorkspace.workspace_id == Table.workspace_id)
            .where(
                Document.id == document_id,
                Document.deleted_at.is_(None),
                Table.deleted_at.is_(None),
                UserWorkspace.user_id == user.id,
            )
            .order_by(TableDocument.added_at.asc())
        )
        row = result.first()
        if not row:
            raise LookupError("Document not found")
        document, table_id = row
        return document, table_id
    

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

    async def confirm_upload(
        self,
        *,
        user: User,
        document_id: UUID,
    ) -> dict:
        document, table_id = await self._get_accessible_document(user=user, document_id=document_id)

        if document.parse_status != "not_ready":
            raise ValueError("Document upload has already been confirmed")

        if not self.storage.object_exists(file_key=document.file_key):
            raise ValueError("Uploaded file not found")

        if self.redis is None:
            raise RuntimeError("Redis client not configured")

        document.parse_status = "queued"
        await self.db.commit()

        await enqueue_document_parsing(
            self.redis,
            document_id=document.id,
            file_key=document.file_key,
            table_id=table_id,
        )

        return {
            "doc_id": document.id,
            "parse_status": document.parse_status,
        }
