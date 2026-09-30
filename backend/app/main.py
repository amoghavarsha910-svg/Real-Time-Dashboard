from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — registers all models with Base.metadata
from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.routers.alerts import router as alerts_router
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.data import router as data_router
from app.routers.metrics import router as metrics_router
from app.routers.notifications import router as notifications_router
from app.routers.profile import router as profile_router
from app.routers.reports import router as reports_router
from app.routers.simulator import router as simulator_router
from app.routers.sources import router as sources_router
from app.routers.users import router as users_router
from app.utils.logger import get_logger
from app.utils.seed import seed_database

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Real-Time Data Dashboard API…")
    await init_db()
    logger.info("Database initialised.")
    async with AsyncSessionLocal() as db:
        await seed_database(db)
    logger.info("Seed data applied.")
    yield
    # Shutdown — simulator will be stopped here in Phase 5
    logger.info("Shutting down Real-Time Data Dashboard API.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Real-Time Data Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(data_router, prefix="/api/data", tags=["Data"])
app.include_router(sources_router, prefix="/api/sources", tags=["Sources"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(simulator_router, prefix="/api/simulator", tags=["Simulator"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}
