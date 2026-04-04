from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceListItem, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace_service = WorkspaceService(db)
    workspace = await workspace_service.create_workspace(user=current_user, name=data.name)
    return workspace


@router.get("", response_model=list[WorkspaceListItem])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace_service = WorkspaceService(db)
    memberships = await workspace_service.list_workspaces(user=current_user)
    return [
        WorkspaceListItem(
            id=workspace.id,
            name=workspace.name,
            is_personal=workspace.is_personal,
            created_at=workspace.created_at,
            role=membership.role,
            joined_at=membership.joined_at,
        )
        for workspace, membership in memberships
    ]


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace_service = WorkspaceService(db)
    try:
        await workspace_service.delete_workspace(
            user=current_user,
            workspace_id=workspace_id,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
