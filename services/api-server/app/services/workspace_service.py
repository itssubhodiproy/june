from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_workspace import UserWorkspace
from app.models.workspace import Workspace


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _create_workspace(
        self,
        *,
        user: User,
        name: str,
        is_personal: bool = False,
    ) -> Workspace:
        workspace = Workspace(name=name, is_personal=is_personal)
        self.db.add(workspace)
        await self.db.flush()

        membership = UserWorkspace(
            user_id=user.id,
            workspace_id=workspace.id,
            role="owner",
        )
        self.db.add(membership)
        await self.db.flush()
        return workspace

    async def create_workspace(
        self,
        *,
        user: User,
        name: str,
        is_personal: bool = False,
    ) -> Workspace:
        workspace = await self._create_workspace(
            user=user,
            name=name,
            is_personal=is_personal,
        )
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def list_workspaces(self, *, user: User) -> list[tuple[Workspace, UserWorkspace]]:
        result = await self.db.execute(
            select(Workspace, UserWorkspace)
            .join(UserWorkspace, UserWorkspace.workspace_id == Workspace.id)
            .where(UserWorkspace.user_id == user.id)
            .order_by(Workspace.created_at.asc())
        )
        return list(result.all())

    async def delete_workspace(self, *, user: User, workspace_id: UUID) -> None:
        result = await self.db.execute(
            select(Workspace, UserWorkspace)
            .join(UserWorkspace, UserWorkspace.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                UserWorkspace.user_id == user.id,
            )
        )
        row = result.first()
        if not row:
            raise LookupError("Workspace not found")

        workspace, membership = row
        if membership.role != "owner":
            raise PermissionError("Only workspace owners can delete workspaces")
        if workspace.is_personal:
            raise RuntimeError("Personal workspaces cannot be deleted")

        await self.db.delete(workspace)
        await self.db.commit()
