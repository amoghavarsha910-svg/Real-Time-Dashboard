from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token
from app.config import settings
from app.models import (
    ActivityLog,
    DashboardConfig,
    PasswordResetToken,
    RefreshSession,
    User,
    UserPreference,
)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Token hashing
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """SHA-256 hex digest — used for refresh tokens and reset tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    return await db.get(User, uuid.UUID(user_id))


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# User creation
# ---------------------------------------------------------------------------

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: str = "user",
) -> User:
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # get the PK without committing

    # Create default dashboard config and preferences for the new user
    db.add(DashboardConfig(user_id=user.id))
    db.add(UserPreference(user_id=user.id))
    await db.flush()

    return user


# ---------------------------------------------------------------------------
# Refresh sessions
# ---------------------------------------------------------------------------

async def create_refresh_session(
    db: AsyncSession,
    user_id: str,
    user_agent: str,
    ip_address: str,
) -> tuple[str, RefreshSession]:
    """Create a refresh session.  Returns (plain_token, RefreshSession)."""
    plain_token, expires_at = create_refresh_token(user_id)
    session = RefreshSession(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        token_hash=hash_token(plain_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()
    return plain_token, session


async def validate_refresh_session(
    db: AsyncSession, plain_token: str
) -> RefreshSession | None:
    """Hash the token, look it up in the DB, check expiry."""
    token_hash = hash_token(plain_token)
    result = await db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    now = datetime.now(timezone.utc)
    expires = session.expires_at
    # expires_at may be stored as a naive datetime (SQLite); normalise
    if isinstance(expires, datetime) and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        return None
    return session


async def delete_refresh_session(db: AsyncSession, plain_token: str) -> bool:
    """Delete a refresh session by plain token.  Returns True if a row was deleted."""
    token_hash = hash_token(plain_token)
    result = await db.execute(
        delete(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )
    return result.rowcount > 0


async def delete_all_refresh_sessions(db: AsyncSession, user_id: str) -> None:
    """Delete all refresh sessions for a user (e.g. after password reset)."""
    await db.execute(
        delete(RefreshSession).where(RefreshSession.user_id == uuid.UUID(user_id))
    )


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

async def create_password_reset_token(db: AsyncSession, user_id: str) -> str:
    """Expire old unused tokens for the user, create a new one, return plain token."""
    # Expire (delete) any existing unused tokens for this user
    await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == uuid.UUID(user_id),
            PasswordResetToken.is_used.is_(False),
        )
    )
    plain_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
    )
    token = PasswordResetToken(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        token_hash=hash_token(plain_token),
        expires_at=expires_at,
        is_used=False,
    )
    db.add(token)
    await db.flush()
    return plain_token


async def validate_password_reset_token(
    db: AsyncSession, plain_token: str
) -> PasswordResetToken | None:
    """Validate hash, expiry, and used flag."""
    token_hash = hash_token(plain_token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used.is_(False),
        )
    )
    token = result.scalar_one_or_none()
    if token is None:
        return None
    now = datetime.now(timezone.utc)
    expires = token.expires_at
    if isinstance(expires, datetime) and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        return None
    return token


async def use_password_reset_token(
    db: AsyncSession, token: PasswordResetToken, new_password: str
) -> User:
    """Mark the token as used and update the user's password."""
    token.is_used = True
    db.add(token)

    user = await db.get(User, token.user_id)
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Activity logging
# ---------------------------------------------------------------------------

async def log_activity(
    db: AsyncSession,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> None:
    entry = ActivityLog(
        user_id=uuid.UUID(user_id) if user_id else None,
        action=action,
        resource_type=resource_type,
        resource_id=uuid.UUID(resource_id) if resource_id else None,
        ip_address=ip_address,
        metadata_=metadata,
    )
    db.add(entry)
    await db.flush()
