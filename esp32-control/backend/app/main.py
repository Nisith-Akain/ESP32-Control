"""FastAPI application entrypoint.

Run locally (from `projects/esp32-control/backend/`, with UI_PASSWORD /
SESSION_SECRET / DEVICE_SHARED_KEY set in the environment):

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import UnauthenticatedError
from .config import settings
from .db import init_db
from .routers import auth as auth_router
from .routers import devices as devices_router


def _ensure_nas_layout(nas_root: str) -> None:
    """Create the NAS_ROOT directory layout from INTERFACES.md Section 9."""
    root = Path(nas_root)
    for sub in ("logs", "firmware", "config"):
        (root / sub).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _ensure_nas_layout(settings.nas_root)
    yield


app = FastAPI(title="ESP32 Control Backend", lifespan=lifespan)


@app.exception_handler(UnauthenticatedError)
async def handle_unauthenticated(request: Request, exc: UnauthenticatedError) -> JSONResponse:
    # exc.detail is already the exact body INTERFACES.md Section 12.1
    # specifies ({"error": "unauthenticated"}) -- return it as-is instead of
    # FastAPI's default nesting under a "detail" key.
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


app.include_router(auth_router.router)
app.include_router(devices_router.router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok"}
