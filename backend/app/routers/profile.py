"""Profile router — current user self-service."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.dashboard import UserPreference
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import hash_password, verify_password

router = APIRouter(redirect_slashes=False)


from pydantic import BaseModel  # noqa: E402


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PreferencesUpdate(BaseModel):
    theme: str | None = None
    notifications_enabled: bool | None = None
    default_export_format: str | None = None
    data_retention_days: int | None = None


@router.get("/", response_model=UserRead)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.from_orm_user(current_user)


@router.put("/", response_model=UserRead)
async def update_profile(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    if body.username is not None:
        current_user.username = body.username
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserRead.from_orm_user(current_user)


@router.put("/password", response_model=dict)
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
        )
    current_user.hashed_password = hash_password(body.new_password)
    db.add(current_user)
    await db.flush()
    return {"ok": True}


@router.put("/preferences", response_model=dict)
async def update_preferences(
    body: PreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        await db.flush()

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(prefs, field, val)
    db.add(prefs)
    await db.flush()
    return {"ok": True}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await db.delete(current_user)
    await db.flush()
