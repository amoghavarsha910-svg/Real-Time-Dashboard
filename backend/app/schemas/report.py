from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    type: str  # "daily", "weekly", "monthly", "custom"
    start_date: datetime | None = None
    end_date: datetime | None = None
    metric_ids: list[str] | None = None  # None = all metrics


class ReportRead(BaseModel):
    id: str
    type: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    summary: dict | None  # aggregated data
