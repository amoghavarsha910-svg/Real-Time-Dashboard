"""Data ingestion and history router."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.reading import ReadingCreate, ReadingPage, ReadingRead
from app.services import data_service

router = APIRouter(redirect_slashes=False)


@router.post("/ingest", response_model=ReadingRead, status_code=status.HTTP_201_CREATED)
async def ingest_reading(
    body: ReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingRead:
    """Ingest a single data reading."""
    try:
        reading = await data_service.ingest_reading(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ReadingRead.from_orm(reading)


@router.get("", response_model=list[ReadingRead])
async def get_latest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReadingRead]:
    """Get the latest reading per metric."""
    readings = await data_service.get_latest_readings(db)
    return [ReadingRead.from_orm(r) for r in readings]


@router.get("/history", response_model=ReadingPage)
async def get_history(
    metric_id: Annotated[list[str] | None, Query()] = None,
    source_id: Annotated[list[str] | None, Query()] = None,
    start: datetime | None = None,
    end: datetime | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "timestamp",
    sort_dir: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingPage:
    """Paginated, filtered reading history."""
    return await data_service.get_readings_history(
        db,
        metric_ids=metric_id,
        source_ids=source_id,
        start_time=start,
        end_time=end,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
