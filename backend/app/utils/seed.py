"""Idempotent seed script for development data."""
from __future__ import annotations

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertRule
from app.models.dashboard import DashboardConfig, UserPreference
from app.models.metric import MetricDefinition
from app.models.source import DataSource
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def seed_database(db: AsyncSession) -> None:
    """Seed initial data for development. Safe to call multiple times."""

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    users_data = [
        {
            "email": "admin@rtdd.dev",
            "username": "admin",
            "role": "admin",
            "password": "Admin@1234",
        },
        {
            "email": "user@rtdd.dev",
            "username": "user",
            "role": "user",
            "password": "User@1234",
        },
        {
            "email": "viewer@rtdd.dev",
            "username": "viewer",
            "role": "viewer",
            "password": "Viewer@1234",
        },
    ]

    created_users: dict[str, User] = {}
    for ud in users_data:
        result = await db.execute(select(User).where(User.email == ud["email"]))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=ud["email"],
                username=ud["username"],
                role=ud["role"],
                hashed_password=_hash(ud["password"]),
            )
            db.add(user)
            await db.flush()
            logger.info("Seeded user: %s", ud["email"])
        created_users[ud["username"]] = user

    admin_user = created_users["admin"]

    # ------------------------------------------------------------------
    # Data Sources
    # ------------------------------------------------------------------
    sources_data = [
        {
            "name": "Main Simulator",
            "source_type": "simulator",
            "is_enabled": True,
            "config": {"interval_seconds": 2.0},
        },
        {
            "name": "Secondary Sensor",
            "source_type": "sensor",
            "is_enabled": False,
            "config": {},
        },
    ]

    created_sources: dict[str, DataSource] = {}
    for sd in sources_data:
        result = await db.execute(
            select(DataSource).where(DataSource.name == sd["name"])
        )
        source = result.scalar_one_or_none()
        if source is None:
            source = DataSource(
                name=sd["name"],
                source_type=sd["source_type"],
                is_enabled=sd["is_enabled"],
                config=sd["config"],
                owner_id=admin_user.id,
            )
            db.add(source)
            await db.flush()
            logger.info("Seeded data source: %s", sd["name"])
        created_sources[sd["name"]] = source

    main_source = created_sources["Main Simulator"]

    # ------------------------------------------------------------------
    # Metric Definitions
    # ------------------------------------------------------------------
    metrics_data = [
        {"name": "temperature",     "display_name": "Temperature",     "unit": "°C",  "min_value": 0.0,   "max_value": 100.0,  "category": "environmental"},
        {"name": "humidity",        "display_name": "Humidity",        "unit": "%",   "min_value": 0.0,   "max_value": 100.0,  "category": "environmental"},
        {"name": "pressure",        "display_name": "Pressure",        "unit": "hPa", "min_value": 900.0, "max_value": 1100.0, "category": "environmental"},
        {"name": "heart_rate",      "display_name": "Heart Rate",      "unit": "BPM", "min_value": 40.0,  "max_value": 200.0,  "category": "biometric"},
        {"name": "speed",           "display_name": "Speed",           "unit": "km/h","min_value": 0.0,   "max_value": 200.0,  "category": "motion"},
        {"name": "voltage",         "display_name": "Voltage",         "unit": "V",   "min_value": 0.0,   "max_value": 240.0,  "category": "electrical"},
        {"name": "current",         "display_name": "Current",         "unit": "A",   "min_value": 0.0,   "max_value": 30.0,   "category": "electrical"},
        {"name": "cpu_usage",       "display_name": "CPU Usage",       "unit": "%",   "min_value": 0.0,   "max_value": 100.0,  "category": "system"},
        {"name": "network_latency", "display_name": "Network Latency", "unit": "ms",  "min_value": 0.0,   "max_value": 500.0,  "category": "network"},
    ]

    created_metrics: dict[str, MetricDefinition] = {}
    for md in metrics_data:
        result = await db.execute(
            select(MetricDefinition).where(MetricDefinition.name == md["name"])
        )
        metric = result.scalar_one_or_none()
        if metric is None:
            metric = MetricDefinition(
                name=md["name"],
                display_name=md["display_name"],
                unit=md["unit"],
                min_value=md["min_value"],
                max_value=md["max_value"],
                category=md["category"],
                source_id=main_source.id,
            )
            db.add(metric)
            await db.flush()
            logger.info("Seeded metric: %s", md["name"])
        created_metrics[md["name"]] = metric

    # ------------------------------------------------------------------
    # Alert Rules
    # ------------------------------------------------------------------
    alert_rules_data = [
        {
            "name": "High Temperature",
            "metric": "temperature",
            "operator": "gt",
            "threshold": 35.0,
            "severity": "warning",
            "duration_seconds": 0,
        },
        {
            "name": "Critical Temperature",
            "metric": "temperature",
            "operator": "gt",
            "threshold": 45.0,
            "severity": "critical",
            "duration_seconds": 0,
        },
        {
            "name": "Low Heart Rate",
            "metric": "heart_rate",
            "operator": "lt",
            "threshold": 55.0,
            "severity": "warning",
            "duration_seconds": 0,
        },
        {
            "name": "High CPU Usage",
            "metric": "cpu_usage",
            "operator": "gt",
            "threshold": 90.0,
            "severity": "critical",
            "duration_seconds": 0,
        },
    ]

    for ard in alert_rules_data:
        result = await db.execute(
            select(AlertRule).where(AlertRule.name == ard["name"])
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            rule = AlertRule(
                name=ard["name"],
                metric_id=created_metrics[ard["metric"]].id,
                operator=ard["operator"],
                threshold=ard["threshold"],
                severity=ard["severity"],
                duration_seconds=ard["duration_seconds"],
                owner_id=admin_user.id,
            )
            db.add(rule)
            logger.info("Seeded alert rule: %s", ard["name"])

    await db.flush()

    # ------------------------------------------------------------------
    # DashboardConfig and UserPreference for each user
    # ------------------------------------------------------------------
    for user in created_users.values():
        result = await db.execute(
            select(DashboardConfig).where(DashboardConfig.user_id == user.id)
        )
        if result.scalar_one_or_none() is None:
            db.add(DashboardConfig(user_id=user.id))
            logger.info("Seeded dashboard config for: %s", user.username)

        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        if result.scalar_one_or_none() is None:
            db.add(UserPreference(user_id=user.id))
            logger.info("Seeded user preferences for: %s", user.username)

    await db.commit()
    logger.info("Seed complete.")
