"""Environment-driven configuration.

Per TEAM/INTERFACES.md Section 9, the backend must refuse to start if
UI_PASSWORD, SESSION_SECRET, or DEVICE_SHARED_KEY are unset. We enforce that
by validating at *import* time: ``settings`` below is built the moment this
module is first imported (which happens as soon as ``app.main`` -- or
anything that depends on it -- is imported), so a misconfigured process
fails immediately instead of starting up and failing requests later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


_REQUIRED_VARS = ("UI_PASSWORD", "SESSION_SECRET", "DEVICE_SHARED_KEY")


@dataclass(frozen=True)
class Settings:
    ui_password: str
    session_secret: str
    device_shared_key: str
    db_url: str
    nas_root: str
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None


def load_settings() -> Settings:
    missing = [name for name in _REQUIRED_VARS if not os.environ.get(name)]
    if missing:
        raise ConfigError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. The backend refuses to start without "
            "UI_PASSWORD, SESSION_SECRET, and DEVICE_SHARED_KEY set -- see "
            "TEAM/INTERFACES.md Section 9 and Section 12."
        )

    return Settings(
        ui_password=os.environ["UI_PASSWORD"],
        session_secret=os.environ["SESSION_SECRET"],
        device_shared_key=os.environ["DEVICE_SHARED_KEY"],
        db_url=os.environ.get("DB_URL", "sqlite:///./data/app.db"),
        nas_root=os.environ.get("NAS_ROOT", "./data/nas"),
        mqtt_host=os.environ.get("MQTT_HOST", "localhost"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        mqtt_username=os.environ.get("MQTT_USERNAME") or None,
        mqtt_password=os.environ.get("MQTT_PASSWORD") or None,
    )


settings = load_settings()
