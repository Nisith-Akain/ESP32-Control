"""Session-cookie auth for the browser UI, per TEAM/INTERFACES.md Section
12.1, plus the device shared-key check for Section 12.2.

Session store is an in-memory dict (token -> expiry), which is explicitly
called out as acceptable for v1 in INTERFACES.md ("a single-process backend
and a restart just forces re-login"). Expiry is a 7-day sliding window: every
successful validation pushes the expiry forward.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from fastapi import Header, HTTPException, Request, Response

from .config import settings

SESSION_COOKIE_NAME = "session_token"
SESSION_TTL = dt.timedelta(days=7)


class UnauthenticatedError(HTTPException):
    """401 raised by `require_session`. Carries the exact body shape
    INTERFACES.md Section 12.1 specifies: `{"error": "unauthenticated"}`.
    See the exception handler registered in `app.main` that unwraps
    `.detail` directly into the response body (FastAPI's default handler
    would otherwise nest it as `{"detail": {...}}`)."""

    def __init__(self) -> None:
        super().__init__(status_code=401, detail={"error": "unauthenticated"})


@dataclass
class _Session:
    expires_at: dt.datetime


# token -> session record. Module-level singleton for the process lifetime.
_sessions: dict[str, _Session] = {}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def create_session() -> str:
    """Mint a new opaque session token and record it as valid."""
    raw = secrets.token_bytes(32)
    token = hmac.new(settings.session_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    _sessions[token] = _Session(expires_at=_now() + SESSION_TTL)
    return token


def invalidate_session(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def is_valid_session(token: str | None) -> bool:
    """Check validity and, if valid, slide the expiry forward."""
    if not token:
        return False
    session = _sessions.get(token)
    if session is None:
        return False
    if session.expires_at < _now():
        _sessions.pop(token, None)
        return False
    session.expires_at = _now() + SESSION_TTL
    return True


def require_session(request: Request) -> str:
    """FastAPI dependency enforcing the session cookie. Add
    `dependencies=[Depends(require_session)]` to any `/api/*` route that
    isn't one of the documented exemptions (INTERFACES.md Section 12.1)."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not is_valid_session(token):
        raise UnauthenticatedError()
    return token


def require_device_key(x_device_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency enforcing the device shared-key header
    (INTERFACES.md Section 12.2), for the two device-facing routes
    (`POST /api/devices/register`, `GET /api/firmware/{id}/download`)."""
    if not x_device_key or not hmac.compare_digest(x_device_key, settings.device_shared_key):
        raise HTTPException(status_code=401, detail="invalid or missing X-Device-Key")


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
