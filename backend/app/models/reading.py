import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from .metric import MetricDefinition
    from .source import DataSource


class DataReading(Base):
    __tablename__ = "data_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    metric_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("metric_definitions.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("normal", "warning", "critical", name="reading_status"),
        nullable=False,
        default="normal",
    )
    timestamp: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    metric: Mapped["MetricDefinition"] = relationship(back_populates="readings")
    source: Mapped["DataSource"] = relationship(back_populates="readings")

    __table_args__ = (
        Index("idx_readings_metric_timestamp", "metric_id", "timestamp"),
        Index("idx_readings_source_timestamp", "source_id", "timestamp"),
        Index("idx_readings_timestamp", "timestamp"),
    )
