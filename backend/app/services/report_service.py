"""Report generation service (on-the-fly, no DB persistence)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertEvent, AlertRule
from app.models.metric import MetricDefinition
from app.models.reading import DataReading
from app.models.source import DataSource


async def generate_report(
    db: AsyncSession,
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    metric_ids: list[str] | None = None,
) -> dict:
    """
    Generate a report on-the-fly from existing data.
    Returns a dict with period, kpis, alert_summary, source_status, readings_count.
    """

    # Base reading query
    reading_q = select(DataReading).where(
        DataReading.timestamp >= start_date,
        DataReading.timestamp <= end_date,
    )
    if metric_ids:
        reading_q = reading_q.where(DataReading.metric_id.in_(metric_ids))

    # Total readings count
    count_result = await db.execute(
        select(func.count()).select_from(reading_q.subquery())
    )
    readings_count = count_result.scalar_one() or 0

    # KPIs per metric
    kpi_q = (
        select(
            MetricDefinition.name,
            func.avg(DataReading.value).label("avg"),
            func.min(DataReading.value).label("min"),
            func.max(DataReading.value).label("max"),
            func.count(DataReading.id).label("count"),
        )
        .join(DataReading, DataReading.metric_id == MetricDefinition.id)
        .where(DataReading.timestamp >= start_date)
        .where(DataReading.timestamp <= end_date)
        .group_by(MetricDefinition.name)
    )
    if metric_ids:
        kpi_q = kpi_q.where(DataReading.metric_id.in_(metric_ids))

    kpi_result = await db.execute(kpi_q)
    kpis: dict[str, dict] = {}
    for row in kpi_result.all():
        kpis[row[0]] = {
            "avg": round(float(row[1]), 4) if row[1] is not None else None,
            "min": round(float(row[2]), 4) if row[2] is not None else None,
            "max": round(float(row[3]), 4) if row[3] is not None else None,
            "count": row[4],
        }

    # Alert summary
    alert_q = (
        select(AlertRule.severity, func.count(AlertEvent.id).label("cnt"))
        .join(AlertEvent, AlertEvent.rule_id == AlertRule.id)
        .where(AlertEvent.triggered_at >= start_date)
        .where(AlertEvent.triggered_at <= end_date)
        .group_by(AlertRule.severity)
    )
    alert_result = await db.execute(alert_q)
    by_severity: dict[str, int] = {}
    total_events = 0
    for row in alert_result.all():
        by_severity[row[0]] = row[1]
        total_events += row[1]

    # Source status
    sources_result = await db.execute(
        select(DataSource).order_by(DataSource.name)
    )
    sources = list(sources_result.scalars().all())
    source_status = [
        {
            "id": str(s.id),
            "name": s.name,
            "is_enabled": s.is_enabled,
            "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
        }
        for s in sources
    ]

    return {
        "id": str(uuid.uuid4()),
        "type": report_type,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "kpis": kpis,
        "alert_summary": {
            "total_events": total_events,
            "by_severity": by_severity,
        },
        "source_status": source_status,
        "readings_count": readings_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
