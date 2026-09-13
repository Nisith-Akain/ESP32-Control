
ESP32 Control Platform

A self-hosted, LAN-only control system for ESP32-based IoT devices — think "your own mini Home Assistant" scoped to ESP32 boards you build yourself, with a web dashboard, live telemetry, remote commands, simple automations, and an API for external agents/scripts.

What it does

- Register devices — an ESP32 announces itself and its capabilities (sensors it has, commands it accepts) on boot; no manual config needed on the server side.
- Live dashboard — see every device's status, last heartbeat, and sensor readings update in real time over WebSocket.
- Remote control — send commands (toggle a relay, move a slider, trigger a button) from the browser, with delivery/ack status shown live.
- Automations — simple threshold rules ("if temperature > 30°C, turn on the fan"), no visual programming, just dropdowns.
- Logs — per-device and cross-device log viewers backed by plain log files (no external logging stack needed).
- Agent API — a separate API-key-authenticated namespace so a script, bot, or LLM agent can read telemetry and issue commands alongside a human, with every action audited.
- OTA updates — push new firmware to a device over the air, with checksum verification.

How it's built

- Backend: Python (FastAPI + SQLAlchemy + SQLite), bridging REST/WebSocket to devices over MQTT.
- Frontend: React + TypeScript + Vite, plain CSS design tokens.
- Firmware: C++ for ESP32 (PlatformIO/Arduino), WiFi + MQTT + a pluggable per-board sensor/command config.
- Auth: single shared household password for the UI (session cookie), a separate device key for firmware, and per-agent API keys — no user accounts, designed for a single home/LAN, not multi-tenant use.

Status

Early / work in progress. Core device registry, auth, the frontend shell, and reference firmware are done and tested; live telemetry streaming, command dispatch, automations, and the full dashboard UI are still being built out. Not yet ready for production use — expect rough edges and missing features.


Prerequisites

- Python 3.11+
- Node.js 18+ (npm)
- (Optional, for firmware) An ESP32 dev board + USB cable + PlatformIO (pip install platformio)
- (Optional, for full functionality once BE-2 lands) An MQTT broker like Mosquitto — not required yet, since MQTT bridging isn't built.

1. Get the code

git clone https://github.com/Nisith-Akain/ESP32-Control.git
cd Claude-Team/projects/esp32-control

2. Run the backend

cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — set real values for:
#   UI_PASSWORD, SESSION_SECRET, DEVICE_SHARED_KEY
export $(cat .env | xargs)       # or otherwise load the env vars into your shell

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

The server refuses to start unless UI_PASSWORD, SESSION_SECRET, and DEVICE_SHARED_KEY are all set. It creates a SQLite DB and a data/nas/{logs,firmware,config} directory tree on first boot.

3. Run the frontend

In a second terminal:

cd frontend
npm install
BACKEND_ORIGIN=http://localhost:8000 npm run dev

Open http://localhost:5173, log in with the UI_PASSWORD you set above.

(No backend yet? npm run mock:server in one terminal + npm run dev in another lets you try the login flow against a fake backend, password test.)

4. Flash an ESP32 (optional — needs real hardware)

cd firmware
cp include/config.example.h include/config.h
# edit config.h: WiFi SSID/password, backend URL, and DEVICE_SHARED_KEY
# (must match the backend's DEVICE_SHARED_KEY exactly)

pio run                     # compile
pio run --target upload     # flash over USB
pio device monitor          # watch serial logs at 115200 baud

The reference build has one placeholder sensor (temp_c, read off an ADC pin) and one command (relay1, drives a GPIO pin) — enough to prove the pipeline works. Real sensors/commands go in firmware/src/board_config.cpp.

5. What you can actually do right now

- Log into the web UI with the shared password.
- Register a device by having firmware boot and call the backend (or curl the endpoint directly), which it does automatically.
- Query the backend directly, e.g.:
curl -X POST http://localhost:8000/api/devices/register \
  -H "X-Device-Key: <your DEVICE_SHARED_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32-abc123","capabilities":{"sensors":[...],"commands":[...]}}'
curl http://localhost:8000/api/devices -b cookies.txt   # after logging in via /api/auth/login
