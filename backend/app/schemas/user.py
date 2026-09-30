from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    avatar_url: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_user(cls, user: object) -> "UserRead":
        """Convert a User ORM object, normalising the UUID id to str."""
        return cls(
            id=str(user.id),  # type: ignore[attr-defined]
            email=user.email,  # type: ignore[attr-defined]
            username=user.username,  # type: ignore[attr-defined]
            role=user.role,  # type: ignore[attr-defined]
            is_active=user.is_active,  # type: ignore[attr-defined]
            avatar_url=user.avatar_url,  # type: ignore[attr-defined]
            created_at=user.created_at,  # type: ignore[attr-defined]
        )


class UserUpdate(BaseModel):
    username: str | None = None
    avatar_url: str | None = None
