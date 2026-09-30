"""Pytest configuration and shared fixtures for the backend test suite."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Integer, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateTable

import app.models  # noqa: F401 — ensures all models are registered with Base.metadata
from app.database import Base, get_db
from app.main import app
from app.utils.seed import seed_database

_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _patch_bigint_for_sqlite(target, connection, **kw):
    """
    SQLite does not autoincrement BIGINT primary keys.
    Before creating tables, swap any BigInteger PK columns to Integer
    so that SQLite treats them as INTEGER PRIMARY KEY (i.e., rowid alias).
    """
    from sqlalchemy import BigInteger  # noqa: PLC0415

    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            if col.primary_key and isinstance(col.type, BigInteger):
                col.type = Integer()


async def _build_engine_and_factory():
    """Create a fresh in-memory SQLite engine with BigInteger→Integer patch."""
    engine = create_async_engine(_TEST_DATABASE_URL, future=True)

    event.listen(Base.metadata, "before_create", _patch_bigint_for_sqlite)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    event.remove(Base.metadata, "before_create", _patch_bigint_for_sqlite)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return engine, session_factory


@pytest.fixture
async def async_client():
    """
    Yield an AsyncClient wired to the FastAPI app using a fresh in-memory SQLite
    database.  Tables are created before each test and dropped afterwards so
    every test starts with a completely clean state.
    """
    engine, session_factory = await _build_engine_and_factory()

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def seeded_client():
    """
    Like async_client but also runs seed_database so seed users, sources,
    metrics and alert rules are present in the test DB.
    """
    engine, session_factory = await _build_engine_and_factory()

    # Seed data
    async with session_factory() as db:
        await seed_database(db)

    async def _override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def auth_headers(seeded_client: AsyncClient) -> dict:
    """Returns Authorization headers for the seeded admin user."""
    resp = await seeded_client.post(
        "/api/auth/login",
        json={"email": "admin@rtdd.dev", "password": "Admin@1234"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
