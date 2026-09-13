#pragma once

// -----------------------------------------------------------------------
// Copy this file to `config.h` (same directory) and fill in real values.
// `config.h` is git-ignored — this example file is the only one committed,
// so no real WiFi password or device shared key ever lands in the repo.
// -----------------------------------------------------------------------

// ---- WiFi station credentials ----
#define WIFI_SSID       "your-wifi-ssid"
#define WIFI_PASSWORD   "your-wifi-password"

// ---- Backend REST (device registration handshake, INTERFACES.md Section 1/12.2) ----
// Plain HTTP, no TLS in v1 (LAN-trusted per INTERFACES.md Section 0/12).
#define BACKEND_HOST        "192.168.1.10"
#define BACKEND_PORT        8000
// Must exactly match the backend's DEVICE_SHARED_KEY env var (INTERFACES.md Section 9/12.2).
#define DEVICE_SHARED_KEY   "change-me-shared-secret"

// ---- MQTT fallback ----
// Used only if the register call fails (network down, backend unreachable,
// malformed response); otherwise the broker address the backend returns in
// its response's mqtt.host/mqtt.port is authoritative (INTERFACES.md Section 1).
#define MQTT_DEFAULT_HOST   "192.168.1.10"
#define MQTT_DEFAULT_PORT   1883

// ---- Device metadata sent on register (INTERFACES.md Section 1) ----
#define DEVICE_TYPE         "esp32"
#define DEVICE_NAME         "ESP32 Reference Board"
#define FIRMWARE_VERSION    "1.0.0"

// ---- Telemetry ----
// Compile-time only per EC-1's acceptance criteria (not user-adjustable at
// runtime in v1).
#define TELEMETRY_INTERVAL_MS  10000UL
