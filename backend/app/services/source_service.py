"""Data source CRUD service."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import DataSource
from app.schemas.source import DataSourceCreate, DataSourceUpdate


async def get_sources(db: AsyncSession) -> list[DataSource]:
    result = await db.execute(select(DataSource).order_by(DataSource.name))
    return list(result.scalars().all())


async def get_source(db: AsyncSession, source_id: str) -> DataSource | None:
    try:
        uid = uuid.UUID(source_id)
    except (ValueError, AttributeError):
        return None
    result = await db.execute(
        select(DataSource).where(DataSource.id == uid)
    )
    return result.scalar_one_or_none()


async def create_source(
    db: AsyncSession,
    data: DataSourceCreate,
    owner_id: str,
) -> DataSource:
    source = DataSource(
        name=data.name,
        source_type=data.source_type,
        config=data.config,
        is_enabled=data.is_enabled,
        owner_id=uuid.UUID(owner_id),
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


async def update_source(
    db: AsyncSession,
    source_id: str,
    data: DataSourceUpdate,
) -> DataSource | None:
    source = await get_source(db, source_id)
    if source is None:
        return None
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(source, field, val)
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


async def delete_source(db: AsyncSession, source_id: str) -> bool:
    source = await get_source(db, source_id)
    if source is None:
        return False
    await db.delete(source)
    await db.flush()
    return True
