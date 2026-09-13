"""`/api/devices*` endpoints per TEAM/INTERFACES.md Sections 1 and 2."""

from __future__ import annotations

import datetime as dt
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_device_key, require_session
from ..config import settings
from ..db import get_db
from ..models import Device
from ..schemas import (
    Capabilities,
    DeviceDetail,
    DevicePatchRequest,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DeviceSummary,
    MqttInfo,
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _device_to_summary(device: Device) -> DeviceSummary:
    return DeviceSummary(
        device_id=device.device_id,
        name=device.name,
        status=device.status,
        last_heartbeat=device.last_heartbeat,
        latest_telemetry=json.loads(device.latest_telemetry_json),
    )


def _device_to_detail(device: Device) -> DeviceDetail:
    return DeviceDetail(
        device_id=device.device_id,
        name=device.name,
        status=device.status,
        last_heartbeat=device.last_heartbeat,
        latest_telemetry=json.loads(device.latest_telemetry_json),
        device_type=device.device_type,
        firmware_version=device.firmware_version,
        ip_address=device.ip_address,
        capabilities=Capabilities.model_validate(json.loads(device.capabilities_json)),
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


def _get_device_or_404(db: Session, device_id: str) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="device not found")
    return device


# NOTE: `/register` must be declared before `/{device_id}` routes below --
# FastAPI matches routes in registration order, and a `/{device_id}` route
# declared first would swallow requests to `/register` as device_id
# ="register".
@router.post(
    "/register",
    response_model=DeviceRegisterResponse,
    dependencies=[Depends(require_device_key)],
)
def register_device(payload: DeviceRegisterRequest, db: Session = Depends(get_db)) -> DeviceRegisterResponse:
    now = dt.datetime.now(dt.timezone.utc)
    capabilities_json = payload.capabilities.model_dump_json()
    name = payload.name or payload.device_id

    device = db.get(Device, payload.device_id)
    if device is None:
        device = Device(
            device_id=payload.device_id,
            name=name,
            device_type=payload.device_type,
            firmware_version=payload.firmware_version,
            capabilities_json=capabilities_json,
            ip_address=payload.ip_address,
            status="offline",
            last_heartbeat=None,
            latest_telemetry_json="{}",
            created_at=now,
            updated_at=now,
        )
        db.add(device)
    else:
        device.name = name
        device.device_type = payload.device_type
        device.firmware_version = payload.firmware_version
        device.capabilities_json = capabilities_json
        device.ip_address = payload.ip_address
        device.updated_at = now

    db.commit()

    return DeviceRegisterResponse(
        device_id=payload.device_id,
        mqtt=MqttInfo(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            telemetry_topic=f"devices/{payload.device_id}/telemetry",
            commands_topic=f"devices/{payload.device_id}/commands",
            status_topic=f"devices/{payload.device_id}/status",
            events_topic=f"devices/{payload.device_id}/events",
        ),
        server_time=now,
    )


@router.get("", response_model=list[DeviceSummary], dependencies=[Depends(require_session)])
def list_devices(db: Session = Depends(get_db)) -> list[DeviceSummary]:
    devices = db.query(Device).order_by(Device.device_id).all()
    return [_device_to_summary(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceDetail, dependencies=[Depends(require_session)])
def get_device(device_id: str, db: Session = Depends(get_db)) -> DeviceDetail:
    device = _get_device_or_404(db, device_id)
    return _device_to_detail(device)


@router.patch("/{device_id}", response_model=DeviceDetail, dependencies=[Depends(require_session)])
def patch_device(
    device_id: str, payload: DevicePatchRequest, db: Session = Depends(get_db)
) -> DeviceDetail:
    device = _get_device_or_404(db, device_id)
    device.name = payload.name
    device.updated_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return _device_to_detail(device)


@router.delete("/{device_id}", dependencies=[Depends(require_session)])
def delete_device(device_id: str, db: Session = Depends(get_db)) -> dict:
    device = _get_device_or_404(db, device_id)
    db.delete(device)
    db.commit()
    return {"status": "deleted", "device_id": device_id}
