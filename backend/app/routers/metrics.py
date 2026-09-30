"""Metrics router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user, require_role
from app.models.metric import MetricDefinition
from app.models.user import User
from app.schemas.metric import MetricDefinitionCreate, MetricDefinitionRead, MetricDefinitionUpdate

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=list[MetricDefinitionRead])
async def list_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MetricDefinitionRead]:
    result = await db.execute(select(MetricDefinition).order_by(MetricDefinition.name))
    metrics = list(result.scalars().all())
    return [MetricDefinitionRead.from_orm(m) for m in metrics]


@router.get("/{metric_id}", response_model=MetricDefinitionRead)
async def get_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricDefinitionRead:
    try:
        uid = uuid.UUID(metric_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == uid)
    )
    metric = result.scalar_one_or_none()
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return MetricDefinitionRead.from_orm(metric)


@router.post("/", response_model=MetricDefinitionRead, status_code=status.HTTP_201_CREATED)
async def create_metric(
    body: MetricDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> MetricDefinitionRead:
    metric = MetricDefinition(
        name=body.name,
        display_name=body.display_name,
        unit=body.unit,
        min_value=body.min_value,
        max_value=body.max_value,
        category=body.category,
        source_id=uuid.UUID(body.source_id) if body.source_id else None,
    )
    db.add(metric)
    await db.flush()
    await db.refresh(metric)
    return MetricDefinitionRead.from_orm(metric)


@router.put("/{metric_id}", response_model=MetricDefinitionRead)
async def update_metric(
    metric_id: str,
    body: MetricDefinitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> MetricDefinitionRead:
    try:
        uid = uuid.UUID(metric_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == uid)
    )
    metric = result.scalar_one_or_none()
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        if field == "source_id" and val is not None:
            try:
                val = uuid.UUID(val)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid source_id")
        setattr(metric, field, val)
    db.add(metric)
    await db.flush()
    await db.refresh(metric)
    return MetricDefinitionRead.from_orm(metric)


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    try:
        uid = uuid.UUID(metric_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.id == uid)
    )
    metric = result.scalar_one_or_none()
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    await db.delete(metric)
    await db.flush()
