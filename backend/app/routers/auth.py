from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services import auth_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 days in seconds


def _set_refresh_cookie(response: Response, plain_token: str) -> None:
    """Attach the httpOnly refresh token cookie to the response."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value=plain_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT != "development",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/")


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Check for duplicate email
    if await auth_service.get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check for duplicate username
    if await auth_service.get_user_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    user = await auth_service.create_user(
        db, username=body.username, email=body.email, password=body.password
    )

    plain_token, _ = await auth_service.create_refresh_session(
        db,
        user_id=str(user.id),
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else None,
    )

    await auth_service.log_activity(
        db,
        user_id=str(user.id),
        action="user_registered",
        ip_address=request.client.host if request.client else None,
    )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    _set_refresh_cookie(response, plain_token)

    return TokenResponse(
        access_token=access_token,
        user=UserRead.from_orm_user(user),
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await auth_service.get_user_by_email(db, body.email)
    # Return 401 even if email not found (don't leak existence)
    if not user or not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    plain_token, _ = await auth_service.create_refresh_session(
        db,
        user_id=str(user.id),
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else None,
    )

    await auth_service.log_activity(
        db,
        user_id=str(user.id),
        action="user_login",
        ip_address=request.client.host if request.client else None,
    )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    _set_refresh_cookie(response, plain_token)

    return TokenResponse(
        access_token=access_token,
        user=UserRead.from_orm_user(user),
    )


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    plain_token: str | None = request.cookies.get(_COOKIE_NAME)
    if not plain_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    session = await auth_service.validate_refresh_session(db, plain_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotate: delete old session, create new one
    await auth_service.delete_refresh_session(db, plain_token)
    new_plain_token, _ = await auth_service.create_refresh_session(
        db,
        user_id=str(user.id),
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else None,
    )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    _set_refresh_cookie(response, new_plain_token)

    return RefreshResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    plain_token: str | None = request.cookies.get(_COOKIE_NAME)
    if plain_token:
        await auth_service.delete_refresh_session(db, plain_token)
    _clear_refresh_cookie(response)
    return {"message": "logged out"}


# ---------------------------------------------------------------------------
# POST /forgot-password
# ---------------------------------------------------------------------------

@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await auth_service.get_user_by_email(db, body.email)
    if user:
        plain_token = await auth_service.create_password_reset_token(db, str(user.id))
        reset_link = (
            f"{settings.FRONTEND_URL}/auth/reset-password?token={plain_token}"
        )
        logger.info("[PASSWORD RESET] Token for %s: %s", body.email, reset_link)

    # Always return the same message regardless of whether the email exists
    return {"message": "If that email exists, a reset link has been sent"}


# ---------------------------------------------------------------------------
# POST /reset-password
# ---------------------------------------------------------------------------

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    token = await auth_service.validate_password_reset_token(db, body.token)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await auth_service.use_password_reset_token(db, token, body.new_password)
    # Force logout everywhere
    await auth_service.delete_all_refresh_sessions(db, str(user.id))

    return {"message": "Password reset successful"}


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.from_orm_user(current_user)
