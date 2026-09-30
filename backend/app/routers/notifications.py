"""Notifications router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services import notification_service

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    is_read: bool | None = None,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    notifs = await notification_service.get_notifications(
        db, user_id=str(current_user.id), is_read=is_read, type_=type
    )
    return [NotificationRead.from_orm(n) for n in notifs]


@router.get("/count", response_model=dict)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    count = await notification_service.get_unread_count(db, user_id=str(current_user.id))
    return {"unread": count}


@router.put("/read-all", response_model=dict)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    count = await notification_service.mark_all_read(db, user_id=str(current_user.id))
    return {"updated": count}


@router.put("/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    ok = await notification_service.mark_read(db, notification_id, user_id=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"ok": True}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    ok = await notification_service.delete_notification(
        db, notification_id, user_id=str(current_user.id)
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
