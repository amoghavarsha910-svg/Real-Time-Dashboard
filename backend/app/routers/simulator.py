"""Simulator control router (Phase 4 placeholders; real logic in Phase 5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(redirect_slashes=False)

# Simulator state shared in Phase 5 — for now just return placeholder data
_sim_running = False
_sim_interval = 2.0


@router.get("/status", response_model=dict)
async def simulator_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "running": _sim_running,
        "interval_seconds": _sim_interval,
        "message": "Simulator control will be wired in Phase 5",
    }


@router.post("/start", response_model=dict)
async def start_simulator(
    current_user: User = Depends(get_current_user),
) -> dict:
    global _sim_running
    _sim_running = True
    return {"running": True, "message": "Simulator start scheduled (Phase 5)"}


@router.post("/stop", response_model=dict)
async def stop_simulator(
    current_user: User = Depends(get_current_user),
) -> dict:
    global _sim_running
    _sim_running = False
    return {"running": False, "message": "Simulator stop scheduled (Phase 5)"}


@router.put("/config", response_model=dict)
async def configure_simulator(
    interval_seconds: float = 2.0,
    current_user: User = Depends(get_current_user),
) -> dict:
    global _sim_interval
    _sim_interval = interval_seconds
    return {"interval_seconds": _sim_interval}
