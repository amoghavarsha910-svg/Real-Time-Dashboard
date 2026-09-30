from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: str
    user_id: str
    title: str
    body: str | None
    type: str
    is_read: bool
    reference_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "NotificationRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            user_id=str(obj.user_id),  # type: ignore[attr-defined]
            title=obj.title,  # type: ignore[attr-defined]
            body=obj.body,  # type: ignore[attr-defined]
            type=obj.type,  # type: ignore[attr-defined]
            is_read=obj.is_read,  # type: ignore[attr-defined]
            reference_id=str(obj.reference_id) if obj.reference_id else None,  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
        )
