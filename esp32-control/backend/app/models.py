"""SQLAlchemy models. See TEAM/INTERFACES.md Section 10 for the schema this
mirrors.

Note: the `devices` table below has one column beyond the strict list in
INTERFACES.md Section 10 (`latest_telemetry_json`). Section 10 documents it
as "informational for consumers of the REST shapes", and `GET /api/devices`
/ `GET /api/devices/{id}` (Section 2) are specified to return a "latest
snapshot of each sensor" -- there's nowhere else in the documented schema to
persist that. BE-1 doesn't populate it (no telemetry pipeline exists yet --
that's BE-2), but the column exists now so BE-2 doesn't need a migration to
add it. Flagged in TASKS.md notes as a resolved ambiguity.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    device_type: Mapped[str] = mapped_column(String, nullable=False)
    firmware_version: Mapped[str | None] = mapped_column(String, nullable=True)
    capabilities_json: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="offline")
    last_heartbeat: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # See module docstring -- reserved for BE-2, unused/empty in BE-1.
    latest_telemetry_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
