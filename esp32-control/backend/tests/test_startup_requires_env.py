"""Verifies the backend refuses to start without UI_PASSWORD / SESSION_SECRET
/ DEVICE_SHARED_KEY (INTERFACES.md Section 9 / TASKS.md BE-1 acceptance
criteria).

Run as a subprocess rather than in-process: `app.config` validates env vars
at *import* time, and by the time this test module runs, `conftest.py` has
already imported `app.main` successfully in this process with valid env
vars set (required for every other test in this suite) -- there's no way to
re-trigger "missing var" behavior in the same interpreter without unloading
already-imported modules, which is fragile. A subprocess gives a clean
environment/import state.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


_MANAGED_VARS = ("UI_PASSWORD", "SESSION_SECRET", "DEVICE_SHARED_KEY", "DB_URL", "NAS_ROOT")


def _run_import_with_env(env_overrides: dict) -> subprocess.CompletedProcess:
    # Start from a full copy of the current environment (Windows Python
    # needs e.g. SYSTEMROOT/TEMP to even start up) minus the vars this test
    # cares about, then apply the overrides under test.
    env = {k: v for k, v in os.environ.items() if k not in _MANAGED_VARS}
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_refuses_to_start_with_no_env_vars_set():
    result = _run_import_with_env({})
    assert result.returncode != 0
    assert "UI_PASSWORD" in result.stderr
    assert "SESSION_SECRET" in result.stderr
    assert "DEVICE_SHARED_KEY" in result.stderr


def test_refuses_to_start_missing_one_var():
    result = _run_import_with_env(
        {"UI_PASSWORD": "x", "SESSION_SECRET": "y"}  # DEVICE_SHARED_KEY missing
    )
    assert result.returncode != 0
    assert "Missing required environment variable(s): DEVICE_SHARED_KEY" in result.stderr


def test_starts_with_all_vars_set(tmp_path):
    result = _run_import_with_env(
        {
            "UI_PASSWORD": "x",
            "SESSION_SECRET": "y",
            "DEVICE_SHARED_KEY": "z",
            "DB_URL": f"sqlite:///{(tmp_path / 'ok.db').as_posix()}",
            "NAS_ROOT": str(tmp_path / "nas"),
        }
    )
    assert result.returncode == 0, result.stderr
