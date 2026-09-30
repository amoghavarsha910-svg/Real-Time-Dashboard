from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DataSourceCreate(BaseModel):
    name: str
    source_type: str = "simulator"
    config: dict = {}
    is_enabled: bool = True


class DataSourceUpdate(BaseModel):
    name: str | None = None
    source_type: str | None = None
    config: dict | None = None
    is_enabled: bool | None = None


class DataSourceRead(BaseModel):
    id: str
    name: str
    source_type: str
    is_enabled: bool
    last_seen_at: datetime | None
    config: dict | None
    owner_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "DataSourceRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            name=obj.name,  # type: ignore[attr-defined]
            source_type=obj.source_type,  # type: ignore[attr-defined]
            is_enabled=obj.is_enabled,  # type: ignore[attr-defined]
            last_seen_at=obj.last_seen_at,  # type: ignore[attr-defined]
            config=obj.config,  # type: ignore[attr-defined]
            owner_id=str(obj.owner_id) if obj.owner_id else None,  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
        )
