#pragma once
#include <Arduino.h>

struct MqttEndpoint {
  String host;
  uint16_t port = 0;
};

// Performs the device registration handshake per INTERFACES.md SS1/SS12.2:
// POST http://BACKEND_HOST:BACKEND_PORT/api/devices/register with header
// `X-Device-Key: DEVICE_SHARED_KEY` and a body built from board_config's
// capability tables (device_id/device_type/firmware_version/name/
// ip_address/capabilities.sensors[]/capabilities.commands[]).
//
// On a 200 response with a well-formed body, fills outEndpoint from the
// response's "mqtt.host"/"mqtt.port" and returns true. On any failure (no
// WiFi, connection error, non-200 status, malformed JSON, missing
// mqtt.host/port) returns false and leaves outEndpoint untouched — the
// caller falls back to the compiled-in MQTT_DEFAULT_HOST/MQTT_DEFAULT_PORT
// per INTERFACES.md SS1.
bool registerDevice(const String &deviceId, const String &ipAddress, MqttEndpoint &outEndpoint);
