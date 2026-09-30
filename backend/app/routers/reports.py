"""Reports router."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate
from app.services import report_service

router = APIRouter(redirect_slashes=False)


@router.post("/generate", response_model=dict, status_code=status.HTTP_200_OK)
async def generate_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Generate a report on-the-fly."""
    now = datetime.now(timezone.utc)

    # Resolve date range from type if not explicitly provided
    if body.start_date is None or body.end_date is None:
        match body.type:
            case "daily":
                start = now - timedelta(days=1)
                end = now
            case "weekly":
                start = now - timedelta(weeks=1)
                end = now
            case "monthly":
                start = now - timedelta(days=30)
                end = now
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date and end_date required for custom reports",
                )
    else:
        start = body.start_date
        end = body.end_date

    return await report_service.generate_report(
        db,
        report_type=body.type,
        start_date=start,
        end_date=end,
        metric_ids=body.metric_ids,
    )


@router.get("/{report_type}", response_model=dict)
async def get_report(
    report_type: str,
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Generate a report for a given type and optional date range."""
    now = datetime.now(timezone.utc)
    if start is None or end is None:
        match report_type:
            case "daily":
                start = now - timedelta(days=1)
                end = now
            case "weekly":
                start = now - timedelta(weeks=1)
                end = now
            case "monthly":
                start = now - timedelta(days=30)
                end = now
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start and end query params required for this report type",
                )
    return await report_service.generate_report(
        db,
        report_type=report_type,
        start_date=start,
        end_date=end,
    )
