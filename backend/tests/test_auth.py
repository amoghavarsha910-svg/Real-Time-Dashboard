"""Tests for the /api/auth endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
}

_VALID_USER2 = {
    "username": "otheruser",
    "email": "other@example.com",
    "password": "password123",
}


async def _register(client: AsyncClient, payload: dict | None = None) -> dict:
    payload = payload or _VALID_USER
    resp = await client.post("/api/auth/register", json=payload)
    return resp


async def _login(client: AsyncClient, payload: dict | None = None) -> dict:
    payload = payload or {"email": _VALID_USER["email"], "password": _VALID_USER["password"]}
    resp = await client.post("/api/auth/login", json=payload)
    return resp


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def test_register_success(async_client: AsyncClient):
    resp = await _register(async_client)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == _VALID_USER["email"]
    assert data["user"]["username"] == _VALID_USER["username"]
    assert "refresh_token" in async_client.cookies


async def test_register_duplicate_email(async_client: AsyncClient):
    await _register(async_client)
    # Same email, different username
    resp = await async_client.post(
        "/api/auth/register",
        json={**_VALID_USER, "username": "differentname"},
    )
    assert resp.status_code == 409
    assert "Email" in resp.json()["detail"]


async def test_register_duplicate_username(async_client: AsyncClient):
    await _register(async_client)
    # Different email, same username
    resp = await async_client.post(
        "/api/auth/register",
        json={**_VALID_USER, "email": "another@example.com"},
    )
    assert resp.status_code == 409


async def test_register_invalid_username(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/auth/register",
        json={**_VALID_USER2, "username": "ab"},  # too short
    )
    assert resp.status_code == 422


async def test_register_weak_password(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/auth/register",
        json={**_VALID_USER2, "password": "short"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success(async_client: AsyncClient):
    await _register(async_client)
    resp = await _login(async_client)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == _VALID_USER["email"]
    # Cookie should be present
    assert "refresh_token" in async_client.cookies


async def test_login_wrong_password(async_client: AsyncClient):
    await _register(async_client)
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": _VALID_USER["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

async def test_refresh_token(async_client: AsyncClient):
    await _register(async_client)
    await _login(async_client)

    resp = await async_client.post("/api/auth/refresh")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    # Cookie should be rotated (still present)
    assert "refresh_token" in async_client.cookies


async def test_refresh_without_cookie(async_client: AsyncClient):
    # Ensure no cookie is present
    async_client.cookies.clear()
    resp = await async_client.post("/api/auth/refresh")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

async def test_logout(async_client: AsyncClient):
    await _register(async_client)
    await _login(async_client)

    resp = await async_client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "logged out"


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

async def test_get_me(async_client: AsyncClient):
    reg = await _register(async_client)
    token = reg.json()["access_token"]

    resp = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == _VALID_USER["email"]
    assert data["username"] == _VALID_USER["username"]


async def test_protected_without_token(async_client: AsyncClient):
    resp = await async_client.get("/api/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Forgot / Reset password
# ---------------------------------------------------------------------------

async def test_forgot_password_always_200(async_client: AsyncClient):
    # Non-existent email — must still return 200
    resp = await async_client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"]


async def test_reset_password_invalid_token(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/auth/reset-password",
        json={"token": "invalidtoken", "new_password": "newpassword123"},
    )
    assert resp.status_code == 400
