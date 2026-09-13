"""Test setup.

Required env vars must be set *before* `app.config` (and anything that
imports it) is imported for the first time, since `Settings` are validated
at module-import time. We set them here, at conftest module scope, which
pytest imports before collecting/importing any test module.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = Path(tempfile.mkdtemp(prefix="esp32-backend-test-"))

os.environ["UI_PASSWORD"] = "test-password"
os.environ["SESSION_SECRET"] = "test-session-secret"
os.environ["DEVICE_SHARED_KEY"] = "test-device-key"
os.environ["DB_URL"] = f"sqlite:///{(_TMP_DIR / 'test.db').as_posix()}"
os.environ["NAS_ROOT"] = str(_TMP_DIR / "nas")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """A fresh TestClient (fresh cookie jar) per test, sharing the one
    on-disk test database/app for the whole test session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def device_key_headers() -> dict:
    return {"X-Device-Key": settings.device_shared_key}


@pytest.fixture()
def authed_client(client):
    resp = client.post("/api/auth/login", json={"password": settings.ui_password})
    assert resp.status_code == 200
    yield client
