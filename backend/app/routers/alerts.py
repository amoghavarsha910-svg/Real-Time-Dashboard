"""Alerts router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import AsyncSession, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.alert import AlertEventRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate
from app.services import alert_service

router = APIRouter(redirect_slashes=False)


@router.get("/rules", response_model=list[AlertRuleRead])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlertRuleRead]:
    # Admins see all rules, others see only their own
    owner_id = None if current_user.role == "admin" else str(current_user.id)
    rules = await alert_service.get_alert_rules(db, owner_id=owner_id)
    return [AlertRuleRead.from_orm(r) for r in rules]


@router.post("/rules", response_model=AlertRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertRuleRead:
    rule = await alert_service.create_alert_rule(db, body, owner_id=str(current_user.id))
    return AlertRuleRead.from_orm(rule)


@router.get("/rules/{rule_id}", response_model=AlertRuleRead)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertRuleRead:
    rule = await alert_service.get_alert_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return AlertRuleRead.from_orm(rule)


@router.put("/rules/{rule_id}", response_model=AlertRuleRead)
async def update_rule(
    rule_id: str,
    body: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertRuleRead:
    rule = await alert_service.get_alert_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    if current_user.role != "admin" and str(rule.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    updated = await alert_service.update_alert_rule(db, rule_id, body)
    return AlertRuleRead.from_orm(updated)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    rule = await alert_service.get_alert_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    if current_user.role != "admin" and str(rule.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    await alert_service.delete_alert_rule(db, rule_id)


@router.get("/events", response_model=dict)
async def list_events(
    rule_id: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    events, total = await alert_service.get_alert_events(
        db, rule_id=rule_id, severity=severity, page=page, page_size=page_size
    )
    import math  # noqa: PLC0415
    return {
        "items": [AlertEventRead.from_orm(e) for e in events],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 1,
    }
