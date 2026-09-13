"""Pydantic request/response models. Shapes mirror TEAM/INTERFACES.md
Sections 1 and 2 exactly."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

SensorType = Literal["float", "int", "bool", "string"]
CommandType = Literal["toggle", "slider", "button"]


class SensorCapability(BaseModel):
    key: str
    label: str
    unit: Optional[str] = None
    type: SensorType


class CommandCapability(BaseModel):
    key: str
    label: str
    type: CommandType
    min: Optional[float] = None
    max: Optional[float] = None

    @model_validator(mode="after")
    def _validate_slider_bounds(self) -> "CommandCapability":
        if self.type == "slider":
            if self.min is None or self.max is None:
                raise ValueError("commands[].type == 'slider' requires both 'min' and 'max'")
            if self.min >= self.max:
                raise ValueError("commands[].min must be less than commands[].max")
        return self


class Capabilities(BaseModel):
    sensors: list[SensorCapability] = Field(default_factory=list)
    commands: list[CommandCapability] = Field(default_factory=list)


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str
    firmware_version: Optional[str] = None
    name: Optional[str] = None
    ip_address: Optional[str] = None
    capabilities: Capabilities


class MqttInfo(BaseModel):
    host: str
    port: int
    telemetry_topic: str
    commands_topic: str
    status_topic: str
    events_topic: str


class DeviceRegisterResponse(BaseModel):
    device_id: str
    status: Literal["registered"] = "registered"
    mqtt: MqttInfo
    server_time: dt.datetime


class DeviceSummary(BaseModel):
    """Shape returned by `GET /api/devices` per INTERFACES.md Section 2."""

    device_id: str
    name: str
    status: str
    last_heartbeat: Optional[dt.datetime] = None
    latest_telemetry: dict[str, Any] = Field(default_factory=dict)


class DeviceDetail(DeviceSummary):
    """Shape returned by `GET /api/devices/{device_id}` -- includes
    `capabilities`, per INTERFACES.md Section 2."""

    device_type: str
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    capabilities: Capabilities
    created_at: dt.datetime
    updated_at: dt.datetime


class DevicePatchRequest(BaseModel):
    """Only `name` is UI-editable per INTERFACES.md Section 2."""

    name: str = Field(min_length=1)
