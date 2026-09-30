"""Notification service."""
from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    body: str | None,
    type_: str,
    reference_id: str | None = None,
) -> Notification:
    notif = Notification(
        user_id=uuid.UUID(user_id),
        title=title,
        body=body,
        type=type_,
        reference_id=uuid.UUID(reference_id) if reference_id else None,
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)
    return notif


async def get_notifications(
    db: AsyncSession,
    user_id: str,
    is_read: bool | None = None,
    type_: str | None = None,
) -> list[Notification]:
    q = select(Notification).where(Notification.user_id == uuid.UUID(user_id))
    if is_read is not None:
        q = q.where(Notification.is_read == is_read)
    if type_:
        q = q.where(Notification.type == type_)
    result = await db.execute(q.order_by(Notification.created_at.desc()))
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession,
    notification_id: str,
    user_id: str,
) -> bool:
    result = await db.execute(
        select(Notification)
        .where(Notification.id == uuid.UUID(notification_id))
        .where(Notification.user_id == uuid.UUID(user_id))
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        return False
    notif.is_read = True
    db.add(notif)
    await db.flush()
    return True


async def mark_all_read(db: AsyncSession, user_id: str) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == uuid.UUID(user_id))
        .where(Notification.is_read == False)  # noqa: E712
    )
    notifications = list(result.scalars().all())
    for n in notifications:
        n.is_read = True
        db.add(n)
    await db.flush()
    return len(notifications)


async def delete_notification(
    db: AsyncSession,
    notification_id: str,
    user_id: str,
) -> bool:
    result = await db.execute(
        select(Notification)
        .where(Notification.id == uuid.UUID(notification_id))
        .where(Notification.user_id == uuid.UUID(user_id))
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        return False
    await db.delete(notif)
    await db.flush()
    return True


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    from sqlalchemy import func  # noqa: PLC0415

    result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == uuid.UUID(user_id))
        .where(Notification.is_read == False)  # noqa: E712
    )
    return result.scalar_one() or 0
