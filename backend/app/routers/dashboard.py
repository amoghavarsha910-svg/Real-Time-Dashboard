"""Dashboard router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.dashboard import DashboardConfig
from app.models.user import User
from app.schemas.dashboard import DashboardConfigRead, DashboardConfigUpdate, DashboardSummary
from app.services import data_service

router = APIRouter(redirect_slashes=False)


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    return await data_service.get_dashboard_summary(db)


@router.get("/config", response_model=DashboardConfigRead)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardConfigRead:
    result = await db.execute(
        select(DashboardConfig).where(DashboardConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard config not found")
    return DashboardConfigRead.from_orm(config)


@router.put("/config", response_model=DashboardConfigRead)
async def update_config(
    body: DashboardConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardConfigRead:
    result = await db.execute(
        select(DashboardConfig).where(DashboardConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    if config is None:
        # Create default config
        config = DashboardConfig(user_id=current_user.id)
        db.add(config)
        await db.flush()

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(config, field, val)
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return DashboardConfigRead.from_orm(config)
