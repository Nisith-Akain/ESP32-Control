from __future__ import annotations

import uuid


def _sample_payload(device_id: str) -> dict:
    return {
        "device_id": device_id,
        "device_type": "esp32",
        "firmware_version": "1.0.0",
        "name": "Test Device",
        "ip_address": "192.168.1.42",
        "capabilities": {
            "sensors": [
                {"key": "temp_c", "label": "Temperature", "unit": "C", "type": "float"},
                {"key": "humidity", "label": "Humidity", "unit": "%", "type": "float"},
            ],
            "commands": [
                {"key": "relay1", "label": "Relay 1", "type": "toggle"},
                {
                    "key": "led_brightness",
                    "label": "LED Brightness",
                    "type": "slider",
                    "min": 0,
                    "max": 255,
                },
                {"key": "reboot", "label": "Reboot", "type": "button"},
            ],
        },
    }


def _new_device_id() -> str:
    return f"esp32-{uuid.uuid4().hex[:12]}"


# --- device-key enforcement on register ------------------------------------


def test_register_missing_device_key_rejected(client):
    payload = _sample_payload(_new_device_id())
    resp = client.post("/api/devices/register", json=payload)
    assert resp.status_code == 401


def test_register_wrong_device_key_rejected(client):
    payload = _sample_payload(_new_device_id())
    resp = client.post(
        "/api/devices/register", json=payload, headers={"X-Device-Key": "wrong-key"}
    )
    assert resp.status_code == 401


# --- register: idempotent upsert --------------------------------------------


def test_register_then_reregister_is_idempotent_upsert(client, device_key_headers):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)

    first = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert first.status_code == 200
    body = first.json()
    assert body["device_id"] == device_id
    assert body["status"] == "registered"
    assert body["mqtt"]["telemetry_topic"] == f"devices/{device_id}/telemetry"
    assert body["mqtt"]["commands_topic"] == f"devices/{device_id}/commands"
    assert body["mqtt"]["status_topic"] == f"devices/{device_id}/status"
    assert body["mqtt"]["events_topic"] == f"devices/{device_id}/events"
    assert "server_time" in body

    # Re-register with a changed firmware_version -- should update in place,
    # not create a second row / error.
    payload["firmware_version"] = "1.1.0"
    second = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert second.status_code == 200
    assert second.json()["device_id"] == device_id


def test_register_defaults_name_to_device_id_when_omitted(client, device_key_headers, authed_client):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)
    payload.pop("name")

    resp = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert resp.status_code == 200

    detail = authed_client.get(f"/api/devices/{device_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == device_id


# --- register: capability validation ----------------------------------------


def test_register_invalid_sensor_type_rejected(client, device_key_headers):
    payload = _sample_payload(_new_device_id())
    payload["capabilities"]["sensors"][0]["type"] = "not-a-real-type"

    resp = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert resp.status_code == 422


def test_register_invalid_command_type_rejected(client, device_key_headers):
    payload = _sample_payload(_new_device_id())
    payload["capabilities"]["commands"][0]["type"] = "not-a-real-type"

    resp = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert resp.status_code == 422


def test_register_slider_missing_bounds_rejected(client, device_key_headers):
    payload = _sample_payload(_new_device_id())
    payload["capabilities"]["commands"][1] = {
        "key": "led_brightness",
        "label": "LED Brightness",
        "type": "slider",
    }

    resp = client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert resp.status_code == 422


# --- auth enforcement on the rest of the devices API -------------------------


def test_list_devices_requires_session(client):
    resp = client.get("/api/devices")
    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthenticated"}


def test_device_key_does_not_grant_session_routes(client, device_key_headers):
    # X-Device-Key is a different scheme (Section 12.2) -- it must not work
    # as a substitute for the session cookie on session-gated routes.
    resp = client.get("/api/devices", headers=device_key_headers)
    assert resp.status_code == 401


def test_list_devices_authenticated(authed_client, device_key_headers):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)
    reg = authed_client.post("/api/devices/register", json=payload, headers=device_key_headers)
    assert reg.status_code == 200

    resp = authed_client.get("/api/devices")
    assert resp.status_code == 200
    ids = [d["device_id"] for d in resp.json()]
    assert device_id in ids


# --- get / patch / delete ----------------------------------------------------


def test_get_device_detail(authed_client, device_key_headers):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)
    authed_client.post("/api/devices/register", json=payload, headers=device_key_headers)

    resp = authed_client.get(f"/api/devices/{device_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["device_type"] == "esp32"
    assert body["capabilities"]["sensors"][0]["key"] == "temp_c"
    assert body["capabilities"]["commands"][1]["min"] == 0
    assert body["capabilities"]["commands"][1]["max"] == 255


def test_get_device_not_found_returns_404(authed_client):
    resp = authed_client.get("/api/devices/does-not-exist")
    assert resp.status_code == 404


def test_patch_device_name(authed_client, device_key_headers):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)
    authed_client.post("/api/devices/register", json=payload, headers=device_key_headers)

    resp = authed_client.patch(f"/api/devices/{device_id}", json={"name": "Renamed Device"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Device"

    confirm = authed_client.get(f"/api/devices/{device_id}")
    assert confirm.json()["name"] == "Renamed Device"


def test_patch_device_not_found_returns_404(authed_client):
    resp = authed_client.patch("/api/devices/does-not-exist", json={"name": "x"})
    assert resp.status_code == 404


def test_delete_device(authed_client, device_key_headers):
    device_id = _new_device_id()
    payload = _sample_payload(device_id)
    authed_client.post("/api/devices/register", json=payload, headers=device_key_headers)

    resp = authed_client.delete(f"/api/devices/{device_id}")
    assert resp.status_code == 200

    confirm = authed_client.get(f"/api/devices/{device_id}")
    assert confirm.status_code == 404


def test_delete_device_not_found_returns_404(authed_client):
    resp = authed_client.delete("/api/devices/does-not-exist")
    assert resp.status_code == 404
