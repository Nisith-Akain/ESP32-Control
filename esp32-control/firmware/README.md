# ESP32 core firmware (EC-1)

WiFi + MQTT + telemetry + command-handling reference firmware for the ESP32
Control Platform. Implements the device side of the contracts in
`TEAM/INTERFACES.md` (Sections 0, 1, 4, 12.2).

## Toolchain

[PlatformIO](https://platformio.org/) + Arduino framework, target board
`esp32dev` (generic ESP32 dev module, 4MB flash). PlatformIO pulls the
Espressif32 platform, Xtensa toolchain, and the two libraries below
automatically — no manual Arduino IDE / ESP-IDF setup needed.

Libraries (declared in `platformio.ini`):
- `knolleary/PubSubClient` (^2.8) — MQTT client. Chosen over `arduino-mqtt` or
  a raw ESP-IDF MQTT client for maturity/ubiquity and because it exposes the
  `willTopic/willQos/willRetain/willMessage` overload of `connect()` needed
  for the LWT requirement, without extra abstraction.
- `bblanchon/ArduinoJson` (^6.21.5) — JSON building/parsing for the register
  request/response, telemetry, command, and event payloads.

## Build

```
pip install platformio        # one-time, if you don't already have pio
cd projects/esp32-control/firmware
cp include/config.example.h include/config.h   # then edit config.h with real values
pio run                        # compile
pio run --target upload        # flash to a connected ESP32 (after config.h is filled in)
pio device monitor             # serial log at 115200 baud
```

`include/config.h` is git-ignored — it holds your real WiFi SSID/password
and the `DEVICE_SHARED_KEY` that must match the backend's `DEVICE_SHARED_KEY`
env var (INTERFACES.md SS9/SS12.2). Only `include/config.example.h` (placeholder
values) is committed.

This was validated with a real compile: `pio run` was run in this sandbox
(with network access to fetch the Espressif32 platform/toolchain and the two
libraries above) against a placeholder `config.h` copied from the example,
and it built successfully end-to-end, producing `firmware.bin` — see
`.pio/build/esp32dev/firmware.elf` size report. No real ESP32 hardware, MQTT
broker, or backend was available to test against beyond that; see
"How this was validated" in `TEAM/TASKS.md` under EC-1 for the full picture.

## Project layout

```
platformio.ini              project/build config, library deps
include/
  config.example.h          template for WiFi/backend/device-key config (copy -> config.h)
  board_config.h            capability table declaration (see below)
  device_identity.h         device_id generation (MAC-derived)
  wifi_manager.h            WiFi connect + reconnect/backoff
  backend_client.h          POST /api/devices/register
  mqtt_client.h             MQTT connect w/ LWT, publish/subscribe helpers
  time_util.h               NTP-backed ISO8601 timestamps
src/
  board_config.cpp          *** the one file a new board edits ***
  device_identity.cpp
  wifi_manager.cpp
  backend_client.cpp
  mqtt_client.cpp
  time_util.cpp
  main.cpp                  setup()/loop(): wires everything together
```

## Adding a new board's sensors/commands

Everything specific to a physical build's capabilities lives in
`src/board_config.cpp` (declared in `include/board_config.h`):

- `kBoardSensors[]` / `kBoardCommands[]` — the capability table sent verbatim
  (mapped to INTERFACES.md SS1's wire shape) on `register`, and iterated to
  build each telemetry payload.
- `boardInit()` — one-time pin/peripheral setup.
- `boardReadSensor(key, ...)` — real sensor read, keyed by the same string
  used in the table.
- `boardExecuteCommand(key, value, ...)` — real GPIO/peripheral action, keyed
  by the same string used in the table.

No other file needs to change to add/remove a sensor or command.

## Reference capability set (this build)

Since no specific hardware was specified for EC-1, this reference build
declares exactly one sensor and one command, per the ticket's suggestion:

- Sensor `temp_c` (float, °C) — **placeholder**: reads the ADC pin
  `board_pins::kTempSensorAdc` (GPIO34) and maps it to a plausible ~15-35°C
  range. There's no real thermometer wired up in this reference build; this
  exists purely so telemetry/graphing has real numbers moving end-to-end.
  Swap in a real driver (DS18B20, DHT22, etc.) by editing only
  `boardReadSensor()`.
- Command `relay1` (toggle) — drives GPIO26 HIGH/LOW. Wire an actual relay
  module (or just an LED for bench testing) to that pin.

## Protocol behavior (per INTERFACES.md)

- `device_id` = `"esp32-" + lowercase hex MAC` (no separators), derived from
  the factory WiFi-station MAC via `esp_read_mac()` — stable across reboots,
  available before WiFi connects.
- On boot, once WiFi is up: calls `POST /api/devices/register` with header
  `X-Device-Key: <DEVICE_SHARED_KEY>` and the capability table above. Reruns
  this handshake after every WiFi reconnect (not just cold boot) since it's
  an idempotent upsert and keeps `ip_address`/broker address fresh — cheap
  and more robust than gating it to "boot only."
- On register success, uses the response's `mqtt.host`/`mqtt.port`; on any
  failure (no network, non-200, malformed body), falls back to the
  compiled-in `MQTT_DEFAULT_HOST`/`MQTT_DEFAULT_PORT`.
- MQTT connects with LWT on `devices/{id}/status` -> `{"status":"offline"}`
  (retained, QoS 1); publishes `{"status":"online"}` (retained) immediately
  after a successful connect.
- Telemetry published to `devices/{id}/telemetry` every
  `TELEMETRY_INTERVAL_MS` (default 10000, compile-time only) as
  `{"ts": "...", "seq": N, "data": {...}}`.
- Subscribes to `devices/{id}/commands`; on a message, executes the command
  via `board_config` and publishes `{"type":"command_result", "command_id":
  "...", "status": "ok"|"failed", "detail": "..."}` to `devices/{id}/events`.
- WiFi and MQTT each retry with exponential backoff (1s, doubling, capped at
  30s) whenever disconnected; backoff resets to 1s after a successful
  (re)connect. This is intentionally simple per the ticket's "doesn't need to
  be sophisticated for v1."

## Known limitations / assumptions (for QA and future EC-2 work)

- Timestamps use NTP (`pool.ntp.org` / `time.nist.gov`) once WiFi is up;
  before sync completes, `isoTimestampNow()` still returns a well-formed
  string anchored near the Unix epoch. Only affects display/logging — event
  ordering uses `seq`, not `ts`.
- MQTT is unauthenticated (no username/password), matching INTERFACES.md
  SS0/SS12.2's note that the broker is treated as LAN-trusted infrastructure
  in this wave.
- `MQTT_MAX_PACKET_SIZE` is raised to 512 bytes via a PlatformIO build flag
  (PubSubClient's default is tighter than comfortable once a JSON payload
  picks up a few more fields — e.g. a longer `detail` string).
- No OTA handling here — that's EC-2, which will add another `boardExecuteCommand`-adjacent
  path for `command: "ota_update"` per INTERFACES.md SS8, layered on top of
  this file's MQTT/command scaffolding without needing to change it.
