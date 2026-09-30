"""Alert rule management and evaluation service."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import AlertEvent, AlertRule
from app.models.reading import DataReading
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate

# ---------------------------------------------------------------------------
# Rule loading (always fresh per session to avoid DetachedInstanceError)
# ---------------------------------------------------------------------------

async def load_rules_cache(db: AsyncSession) -> list[AlertRule]:
    """Load all enabled alert rules from the current session."""
    result = await db.execute(
        select(AlertRule)
        .where(AlertRule.is_enabled == True)  # noqa: E712
    )
    return list(result.scalars().all())


def invalidate_cache() -> None:
    """No-op kept for API compatibility. Rules are loaded fresh each call."""


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

async def evaluate(
    db: AsyncSession,
    reading: DataReading,
    ws_manager=None,
) -> list[AlertEvent]:
    """
    For each enabled rule matching reading.metric_id:
    - If triggered AND no open event → create AlertEvent + Notification
    - If not triggered AND open event exists → resolve it
    Returns list of newly created AlertEvent objects.
    """
    rules = await load_rules_cache(db)
    reading_metric_id = str(reading.metric_id)
    new_events: list[AlertEvent] = []

    for rule in rules:
        if str(rule.metric_id) != reading_metric_id:
            continue

        triggered = _apply_operator(reading.value, rule.operator, rule.threshold)

        # Check for existing open event
        open_result = await db.execute(
            select(AlertEvent)
            .where(AlertEvent.rule_id == rule.id)
            .where(AlertEvent.resolved_at == None)  # noqa: E711
        )
        open_event = open_result.scalar_one_or_none()

        if triggered and open_event is None:
            # Create new alert event
            message = (
                f"{rule.name}: value {reading.value} {rule.operator} {rule.threshold}"
            )
            event = AlertEvent(
                rule_id=rule.id,
                triggered_value=reading.value,
                triggered_at=reading.timestamp or datetime.now(timezone.utc),
                message=message,
            )
            db.add(event)
            await db.flush()
            new_events.append(event)

            # Create notification for rule owner
            from app.services import notification_service  # noqa: PLC0415
            await notification_service.create_notification(
                db=db,
                user_id=str(rule.owner_id),
                title=f"Alert: {rule.name}",
                body=message,
                type_="alert",
                reference_id=str(event.id),
            )

        elif not triggered and open_event is not None:
            open_event.resolved_at = datetime.now(timezone.utc)
            db.add(open_event)

    # ws_manager broadcast wired in Phase 6
    return new_events


def _apply_operator(value: float, operator: str, threshold: float) -> bool:
    """Apply comparison operator."""
    ops = {
        "gt": lambda v, t: v > t,
        "lt": lambda v, t: v < t,
        "gte": lambda v, t: v >= t,
        "lte": lambda v, t: v <= t,
        "eq": lambda v, t: v == t,
        "neq": lambda v, t: v != t,
    }
    fn = ops.get(operator)
    return fn(value, threshold) if fn else False


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def get_alert_rules(
    db: AsyncSession,
    owner_id: str | None = None,
) -> list[AlertRule]:
    import uuid as _uuid  # noqa: PLC0415

    q = select(AlertRule).options(selectinload(AlertRule.metric))
    if owner_id:
        try:
            q = q.where(AlertRule.owner_id == _uuid.UUID(owner_id))
        except (ValueError, AttributeError):
            return []
    result = await db.execute(q.order_by(AlertRule.created_at.desc()))
    return list(result.scalars().all())


async def get_alert_rule(db: AsyncSession, rule_id: str) -> AlertRule | None:
    import uuid as _uuid  # noqa: PLC0415

    try:
        uid = _uuid.UUID(rule_id)
    except (ValueError, AttributeError):
        return None
    result = await db.execute(
        select(AlertRule)
        .where(AlertRule.id == uid)
        .options(selectinload(AlertRule.metric))
    )
    return result.scalar_one_or_none()


async def create_alert_rule(
    db: AsyncSession,
    data: AlertRuleCreate,
    owner_id: str,
) -> AlertRule:
    import uuid as _uuid  # noqa: PLC0415

    rule = AlertRule(
        name=data.name,
        metric_id=_uuid.UUID(data.metric_id),
        operator=data.operator,
        threshold=data.threshold,
        severity=data.severity,
        duration_seconds=data.duration_seconds,
        is_enabled=data.is_enabled,
        owner_id=_uuid.UUID(owner_id),
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    invalidate_cache()
    return rule


async def update_alert_rule(
    db: AsyncSession,
    rule_id: str,
    data: AlertRuleUpdate,
) -> AlertRule | None:
    rule = await get_alert_rule(db, rule_id)
    if rule is None:
        return None
    import uuid as _uuid  # noqa: PLC0415

    for field, val in data.model_dump(exclude_unset=True).items():
        if field == "metric_id" and val is not None:
            val = _uuid.UUID(val)
        setattr(rule, field, val)
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    invalidate_cache()
    return rule


async def delete_alert_rule(db: AsyncSession, rule_id: str) -> bool:
    rule = await get_alert_rule(db, rule_id)
    if rule is None:
        return False
    await db.delete(rule)
    await db.flush()
    invalidate_cache()
    return True


async def get_alert_events(
    db: AsyncSession,
    rule_id: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[AlertEvent], int]:
    """Return paginated alert events with optional filters."""
    import math  # noqa: PLC0415

    from sqlalchemy import func  # noqa: PLC0415

    q = select(AlertEvent).options(
        selectinload(AlertEvent.rule).selectinload(AlertRule.metric)
    )
    if rule_id:
        q = q.where(AlertEvent.rule_id == rule_id)
    if severity:
        q = q.join(AlertRule, AlertEvent.rule_id == AlertRule.id).where(
            AlertRule.severity == severity
        )

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    q = q.order_by(AlertEvent.triggered_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total
