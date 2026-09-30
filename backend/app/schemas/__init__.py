"""Schemas package — exports all Pydantic request/response models."""

from app.schemas.alert import AlertEventRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.dashboard import DashboardConfigRead, DashboardConfigUpdate, DashboardSummary
from app.schemas.metric import MetricDefinitionCreate, MetricDefinitionRead, MetricDefinitionUpdate
from app.schemas.notification import NotificationRead
from app.schemas.reading import ReadingCreate, ReadingPage, ReadingRead
from app.schemas.report import ReportCreate, ReportRead
from app.schemas.source import DataSourceCreate, DataSourceRead, DataSourceUpdate
from app.schemas.user import UserRead, UserUpdate

__all__ = [
    # auth
    "RegisterRequest",
    "LoginRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    "TokenResponse",
    "RefreshResponse",
    # user
    "UserRead",
    "UserUpdate",
    # source
    "DataSourceCreate",
    "DataSourceUpdate",
    "DataSourceRead",
    # metric
    "MetricDefinitionCreate",
    "MetricDefinitionUpdate",
    "MetricDefinitionRead",
    # reading
    "ReadingCreate",
    "ReadingRead",
    "ReadingPage",
    # alert
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRuleRead",
    "AlertEventRead",
    # notification
    "NotificationRead",
    # dashboard
    "DashboardSummary",
    "DashboardConfigRead",
    "DashboardConfigUpdate",
    # report
    "ReportCreate",
    "ReportRead",
]
