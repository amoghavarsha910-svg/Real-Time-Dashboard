"""Data sources router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.source import DataSourceCreate, DataSourceRead, DataSourceUpdate
from app.services import source_service

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=list[DataSourceRead])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DataSourceRead]:
    sources = await source_service.get_sources(db)
    return [DataSourceRead.from_orm(s) for s in sources]


@router.post("", response_model=DataSourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSourceRead:
    source = await source_service.create_source(db, body, owner_id=str(current_user.id))
    return DataSourceRead.from_orm(source)


@router.get("/{source_id}", response_model=DataSourceRead)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSourceRead:
    source = await source_service.get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return DataSourceRead.from_orm(source)


@router.put("/{source_id}", response_model=DataSourceRead)
async def update_source(
    source_id: str,
    body: DataSourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataSourceRead:
    source = await source_service.get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    # Only admin or owner can update
    if current_user.role != "admin" and str(source.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    updated = await source_service.update_source(db, source_id, body)
    return DataSourceRead.from_orm(updated)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    source = await source_service.get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if current_user.role != "admin" and str(source.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    await source_service.delete_source(db, source_id)
