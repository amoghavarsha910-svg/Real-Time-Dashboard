import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from .user import User


class DashboardConfig(Base):
    __tablename__ = "dashboard_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    layout: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    default_time_range: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1h"
    )
    default_chart_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="line"
    )
    refresh_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="dashboard_config")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    theme: Mapped[str] = mapped_column(
        Enum("light", "dark", "system", name="user_theme"),
        nullable=False,
        default="system",
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    default_export_format: Mapped[str] = mapped_column(
        Enum("csv", "json", "pdf", name="export_format"),
        nullable=False,
        default="csv",
    )
    data_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="preferences")
