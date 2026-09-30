import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from .metric import MetricDefinition
    from .user import User


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("metric_definitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operator: Mapped[str] = mapped_column(
        Enum("gt", "lt", "gte", "lte", "eq", "neq", name="alert_operator"),
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum("info", "warning", "critical", name="alert_severity"),
        nullable=False,
        default="warning",
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    metric: Mapped["MetricDefinition"] = relationship(back_populates="alert_rules")
    owner: Mapped["User"] = relationship(back_populates="alert_rules")
    events: Mapped[list["AlertEvent"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    triggered_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    rule: Mapped["AlertRule"] = relationship(back_populates="events")
