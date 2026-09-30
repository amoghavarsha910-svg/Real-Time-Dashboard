"""Users management router (admin only)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.database import AsyncSession, get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(redirect_slashes=False)


class UserRoleUpdate:
    def __init__(self, role: str | None = None, is_active: bool | None = None):
        self.role = role
        self.is_active = is_active


from pydantic import BaseModel  # noqa: E402


class UserAdminUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> list[UserRead]:
    result = await db.execute(select(User).order_by(User.created_at))
    users = list(result.scalars().all())
    return [UserRead.from_orm_user(u) for u in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> UserRead:
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.from_orm_user(user)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    body: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> UserRead:
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserRead.from_orm_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.flush()
