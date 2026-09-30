from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricDefinitionRead(BaseModel):
    id: str
    name: str
    display_name: str
    unit: str | None
    min_value: float | None
    max_value: float | None
    category: str | None
    source_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "MetricDefinitionRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            name=obj.name,  # type: ignore[attr-defined]
            display_name=obj.display_name,  # type: ignore[attr-defined]
            unit=obj.unit,  # type: ignore[attr-defined]
            min_value=obj.min_value,  # type: ignore[attr-defined]
            max_value=obj.max_value,  # type: ignore[attr-defined]
            category=obj.category,  # type: ignore[attr-defined]
            source_id=str(obj.source_id) if obj.source_id else None,  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
        )


class MetricDefinitionCreate(BaseModel):
    name: str
    display_name: str
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    category: str | None = None
    source_id: str | None = None


class MetricDefinitionUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    category: str | None = None
    source_id: str | None = None
