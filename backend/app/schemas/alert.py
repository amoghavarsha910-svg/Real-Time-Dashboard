from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.metric import MetricDefinitionRead


class AlertRuleCreate(BaseModel):
    name: str
    metric_id: str
    operator: str  # "gt", "lt", "gte", "lte", "eq", "neq"
    threshold: float
    severity: str = "warning"  # "info", "warning", "critical"
    duration_seconds: int = 0
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    metric_id: str | None = None
    operator: str | None = None
    threshold: float | None = None
    severity: str | None = None
    duration_seconds: int | None = None
    is_enabled: bool | None = None


class AlertRuleRead(BaseModel):
    id: str
    name: str
    metric_id: str
    operator: str
    threshold: float
    severity: str
    duration_seconds: int
    is_enabled: bool
    owner_id: str
    created_at: datetime
    metric: MetricDefinitionRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "AlertRuleRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            name=obj.name,  # type: ignore[attr-defined]
            metric_id=str(obj.metric_id),  # type: ignore[attr-defined]
            operator=obj.operator,  # type: ignore[attr-defined]
            threshold=obj.threshold,  # type: ignore[attr-defined]
            severity=obj.severity,  # type: ignore[attr-defined]
            duration_seconds=obj.duration_seconds,  # type: ignore[attr-defined]
            is_enabled=obj.is_enabled,  # type: ignore[attr-defined]
            owner_id=str(obj.owner_id),  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
            metric=MetricDefinitionRead.from_orm(obj.metric) if obj.metric else None,  # type: ignore[attr-defined]
        )


class AlertEventRead(BaseModel):
    id: str
    rule_id: str
    triggered_value: float
    triggered_at: datetime
    resolved_at: datetime | None
    message: str | None
    rule: AlertRuleRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: object) -> "AlertEventRead":
        return cls(
            id=str(obj.id),  # type: ignore[attr-defined]
            rule_id=str(obj.rule_id),  # type: ignore[attr-defined]
            triggered_value=obj.triggered_value,  # type: ignore[attr-defined]
            triggered_at=obj.triggered_at,  # type: ignore[attr-defined]
            resolved_at=obj.resolved_at,  # type: ignore[attr-defined]
            message=obj.message,  # type: ignore[attr-defined]
            rule=AlertRuleRead.from_orm(obj.rule) if obj.rule else None,  # type: ignore[attr-defined]
        )
