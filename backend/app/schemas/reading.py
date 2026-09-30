from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.metric import MetricDefinitionRead
from app.schemas.source import DataSourceRead


class ReadingCreate(BaseModel):
    metric_name: str  # look up metric_id from name
    value: float
    source_id: str | None = None  # if None, use first enabled simulator source
    timestamp: datetime | None = None  # if None, use UTC now
    status: str | None = None  # if None, auto-determine from alert thresholds


class ReadingRead(BaseModel):
    id: int
    metric_id: str
    source_id: str
    value: float
    status: str
    timestamp: datetime
    metric: MetricDefinitionRead | None = None
    source: DataSourceRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "ReadingRead":
        return cls(
            id=obj.id,  # type: ignore[attr-defined]
            metric_id=str(obj.metric_id),  # type: ignore[attr-defined]
            source_id=str(obj.source_id),  # type: ignore[attr-defined]
            value=obj.value,  # type: ignore[attr-defined]
            status=obj.status,  # type: ignore[attr-defined]
            timestamp=obj.timestamp,  # type: ignore[attr-defined]
            metric=MetricDefinitionRead.from_orm(obj.metric) if obj.metric else None,  # type: ignore[attr-defined]
            source=DataSourceRead.from_orm(obj.source) if obj.source else None,  # type: ignore[attr-defined]
        )


class ReadingPage(BaseModel):
    items: list[ReadingRead]
    total: int
    page: int
    page_size: int
    pages: int
