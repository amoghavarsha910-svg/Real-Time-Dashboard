"""Data ingestion and query service."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import AlertEvent
from app.models.metric import MetricDefinition
from app.models.reading import DataReading
from app.models.source import DataSource
from app.schemas.dashboard import DashboardSummary
from app.schemas.reading import ReadingCreate, ReadingPage, ReadingRead


async def ingest_reading(
    db: AsyncSession,
    reading_data: ReadingCreate,
    ws_manager=None,
) -> DataReading:
    """
    Core ingestion function. Called by simulator and external sources.
    1. Look up metric by name
    2. Resolve source_id (use first enabled simulator if not provided)
    3. Determine status from alert thresholds if not supplied
    4. Persist DataReading
    5. Update DataSource.last_seen_at
    6. Evaluate alert rules
    7. Broadcast via ws_manager if provided (wired in Phase 6)
    """
    # 1. Resolve metric
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.name == reading_data.metric_name)
    )
    metric = result.scalar_one_or_none()
    if metric is None:
        raise ValueError(f"Unknown metric: {reading_data.metric_name!r}")

    # 2. Resolve source
    if reading_data.source_id:
        source_result = await db.execute(
            select(DataSource).where(DataSource.id == reading_data.source_id)
        )
        source = source_result.scalar_one_or_none()
        if source is None:
            raise ValueError(f"Unknown source_id: {reading_data.source_id!r}")
    else:
        source_result = await db.execute(
            select(DataSource)
            .where(DataSource.is_enabled == True)  # noqa: E712
            .where(DataSource.source_type == "simulator")
            .limit(1)
        )
        source = source_result.scalar_one_or_none()
        if source is None:
            # Fall back to any enabled source
            source_result = await db.execute(
                select(DataSource).where(DataSource.is_enabled == True).limit(1)  # noqa: E712
            )
            source = source_result.scalar_one_or_none()
        if source is None:
            raise ValueError("No enabled data source found")

    # 3. Determine status
    status = reading_data.status
    if status is None:
        status = await _determine_status(db, metric.id, reading_data.value)

    # 4. Persist reading
    ts = reading_data.timestamp or datetime.now(timezone.utc)
    reading = DataReading(
        metric_id=metric.id,
        source_id=source.id,
        value=reading_data.value,
        status=status,
        timestamp=ts,
    )
    db.add(reading)

    # 5. Update source last_seen_at
    source.last_seen_at = ts
    db.add(source)

    await db.flush()
    # Re-fetch reading with relationships to avoid DetachedInstanceError
    from sqlalchemy.orm import selectinload as _sil  # noqa: PLC0415
    _result = await db.execute(
        select(DataReading)
        .where(DataReading.id == reading.id)
        .options(_sil(DataReading.metric), _sil(DataReading.source))
    )
    reading = _result.scalar_one()

    # 6. Evaluate alert rules (import here to avoid circular)
    from app.services import alert_service  # noqa: PLC0415
    await alert_service.evaluate(db, reading, ws_manager=ws_manager)

    # 7. ws_manager broadcast wired in Phase 6
    if ws_manager is not None:
        pass  # placeholder

    return reading


async def _determine_status(db: AsyncSession, metric_id, value: float) -> str:
    """Auto-determine reading status from enabled alert rules for this metric."""
    from app.services import alert_service  # noqa: PLC0415

    rules = await alert_service.load_rules_cache(db)
    metric_id_str = str(metric_id)
    status = "normal"
    for rule in rules:
        if str(rule.metric_id) != metric_id_str:
            continue
        if alert_service._apply_operator(value, rule.operator, rule.threshold):
            if rule.severity == "critical":
                return "critical"
            status = "warning"
    return status


async def get_latest_readings(db: AsyncSession, limit: int = 50) -> list[DataReading]:
    """Get most recent reading per metric using a subquery."""
    # Subquery: max id per metric_id
    subq = (
        select(func.max(DataReading.id).label("max_id"))
        .group_by(DataReading.metric_id)
        .scalar_subquery()
    )
    result = await db.execute(
        select(DataReading)
        .where(DataReading.id.in_(subq))
        .options(selectinload(DataReading.metric), selectinload(DataReading.source))
        .order_by(DataReading.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_readings_history(
    db: AsyncSession,
    metric_ids: list[str] | None = None,
    source_ids: list[str] | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "timestamp",
    sort_dir: str = "desc",
) -> ReadingPage:
    """Paginated, filtered, sortable history query."""
    query = (
        select(DataReading)
        .options(selectinload(DataReading.metric), selectinload(DataReading.source))
    )

    if metric_ids:
        query = query.where(DataReading.metric_id.in_(metric_ids))
    if source_ids:
        query = query.where(DataReading.source_id.in_(source_ids))
    if start_time:
        query = query.where(DataReading.timestamp >= start_time)
    if end_time:
        query = query.where(DataReading.timestamp <= end_time)
    if status:
        query = query.where(DataReading.status == status)

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Sort
    sort_col = getattr(DataReading, sort_by, DataReading.timestamp)
    if sort_dir == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return ReadingPage(
        items=[ReadingRead.from_orm(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 1,
    )


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummary:
    """Compute dashboard summary statistics."""
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_5min = now - timedelta(minutes=5)
    last_60s = now - timedelta(seconds=60)

    # total_readings_24h
    r = await db.execute(
        select(func.count(DataReading.id)).where(DataReading.timestamp >= last_24h)
    )
    total_readings_24h = r.scalar_one() or 0

    # active_sources (enabled + seen in last 5 min)
    r = await db.execute(
        select(func.count(DataSource.id))
        .where(DataSource.is_enabled == True)  # noqa: E712
        .where(DataSource.last_seen_at >= last_5min)
    )
    active_sources = r.scalar_one() or 0

    # active_alerts (unresolved alert events)
    r = await db.execute(
        select(func.count(AlertEvent.id)).where(AlertEvent.resolved_at == None)  # noqa: E711
    )
    active_alerts = r.scalar_one() or 0

    # data_rate
    r = await db.execute(
        select(func.count(DataReading.id)).where(DataReading.timestamp >= last_60s)
    )
    rate_count = r.scalar_one() or 0
    data_rate = round(rate_count / 60.0, 4)

    # system_status
    from app.models.alert import AlertRule  # noqa: PLC0415
    r = await db.execute(
        select(AlertEvent)
        .join(AlertRule, AlertEvent.rule_id == AlertRule.id)
        .where(AlertEvent.resolved_at == None)  # noqa: E711
        .options(selectinload(AlertEvent.rule))
    )
    open_events = list(r.scalars().all())
    system_status = "normal"
    for ev in open_events:
        if ev.rule and ev.rule.severity == "critical":
            system_status = "critical"
            break
        if ev.rule and ev.rule.severity == "warning":
            system_status = "warning"

    # avg_values per metric (last 5 min)
    r = await db.execute(
        select(MetricDefinition.name, func.avg(DataReading.value))
        .join(DataReading, DataReading.metric_id == MetricDefinition.id)
        .where(DataReading.timestamp >= last_5min)
        .group_by(MetricDefinition.name)
    )
    avg_values: dict[str, float] = {}
    for row in r.all():
        avg_values[row[0]] = round(float(row[1]), 4)

    # latest reading per metric
    latest = await get_latest_reading_per_metric(db)

    return DashboardSummary(
        total_readings_24h=total_readings_24h,
        active_sources=active_sources,
        active_alerts=active_alerts,
        data_rate=data_rate,
        system_status=system_status,
        avg_values=avg_values,
        latest_readings=[ReadingRead.from_orm(r) for r in latest],
    )


async def get_latest_reading_per_metric(db: AsyncSession) -> list[DataReading]:
    """One reading per metric, most recent."""
    subq = (
        select(func.max(DataReading.id).label("max_id"))
        .group_by(DataReading.metric_id)
        .scalar_subquery()
    )
    result = await db.execute(
        select(DataReading)
        .where(DataReading.id.in_(subq))
        .options(selectinload(DataReading.metric), selectinload(DataReading.source))
        .order_by(DataReading.timestamp.desc())
    )
    return list(result.scalars().all())
