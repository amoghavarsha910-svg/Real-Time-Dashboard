"""
SQLAlchemy models package.

Importing this package registers all models with Base.metadata,
which is required before Alembic autogenerate and before init_db().
"""

from .activity import ActivityLog
from .alert import AlertEvent, AlertRule
from .dashboard import DashboardConfig, UserPreference
from .metric import MetricDefinition
from .notification import Notification
from .reading import DataReading
from .session import PasswordResetToken, RefreshSession
from .source import DataSource
from .user import User

__all__ = [
    "User",
    "RefreshSession",
    "PasswordResetToken",
    "DataSource",
    "MetricDefinition",
    "DataReading",
    "AlertRule",
    "AlertEvent",
    "Notification",
    "DashboardConfig",
    "UserPreference",
    "ActivityLog",
]
