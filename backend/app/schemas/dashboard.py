from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.reading import ReadingRead


class DashboardSummary(BaseModel):
    total_readings_24h: int
    active_sources: int
    active_alerts: int
    data_rate: float  # readings per second (last 60 seconds)
    system_status: str  # "normal", "warning", "critical"
    avg_values: dict[str, float]  # {metric_name: avg_value}
    latest_readings: list[ReadingRead]  # last reading per metric


class DashboardConfigRead(BaseModel):
    id: str
    user_id: str
    default_time_range: str
    default_chart_type: str
    refresh_interval: int
    layout: dict | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "DashboardConfigRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            user_id=str(obj.user_id),  # type: ignore[attr-defined]
            default_time_range=obj.default_time_range,  # type: ignore[attr-defined]
            default_chart_type=obj.default_chart_type,  # type: ignore[attr-defined]
            refresh_interval=obj.refresh_interval,  # type: ignore[attr-defined]
            layout=obj.layout,  # type: ignore[attr-defined]
        )


class DashboardConfigUpdate(BaseModel):
    default_time_range: str | None = None
    default_chart_type: str | None = None
    refresh_interval: int | None = None
    layout: dict | None = None
