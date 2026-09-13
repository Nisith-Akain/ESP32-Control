#include "backend_client.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFi.h>

#include "board_config.h"
#include "config.h"

bool registerDevice(const String &deviceId, const String &ipAddress, MqttEndpoint &outEndpoint) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[register] skipped, no WiFi");
    return false;
  }

  // Build the request body from the board's capability table
  // (INTERFACES.md SS1) — never hand-written per board.
  StaticJsonDocument<768> body;
  body["device_id"] = deviceId;
  body["device_type"] = DEVICE_TYPE;
  body["firmware_version"] = FIRMWARE_VERSION;
  body["name"] = DEVICE_NAME;
  body["ip_address"] = ipAddress;

  JsonObject capabilities = body.createNestedObject("capabilities");
  JsonArray sensors = capabilities.createNestedArray("sensors");
  for (size_t i = 0; i < kBoardSensorCount; i++) {
    JsonObject s = sensors.createNestedObject();
    s["key"] = kBoardSensors[i].key;
    s["label"] = kBoardSensors[i].label;
    s["unit"] = kBoardSensors[i].unit;
    s["type"] = sensorTypeToString(kBoardSensors[i].type);
  }
  JsonArray commands = capabilities.createNestedArray("commands");
  for (size_t i = 0; i < kBoardCommandCount; i++) {
    JsonObject c = commands.createNestedObject();
    c["key"] = kBoardCommands[i].key;
    c["label"] = kBoardCommands[i].label;
    c["type"] = commandTypeToString(kBoardCommands[i].type);
    if (kBoardCommands[i].type == CommandType::kSlider) {
      c["min"] = kBoardCommands[i].minValue;
      c["max"] = kBoardCommands[i].maxValue;
    }
  }

  String payload;
  serializeJson(body, payload);

  String url = String("http://") + BACKEND_HOST + ":" + String(BACKEND_PORT) +
               "/api/devices/register";

  HTTPClient http;
  http.setTimeout(5000);
  if (!http.begin(url)) {
    Serial.println("[register] http.begin() failed");
    return false;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", DEVICE_SHARED_KEY);

  int status = http.POST(payload);
  if (status != 200) {
    Serial.printf("[register] failed, http status=%d\n", status);
    http.end();
    return false;
  }

  String responseBody = http.getString();
  http.end();

  StaticJsonDocument<512> resp;
  DeserializationError err = deserializeJson(resp, responseBody);
  if (err) {
    Serial.printf("[register] response parse error: %s\n", err.c_str());
    return false;
  }

  const char *host = resp["mqtt"]["host"] | static_cast<const char *>(nullptr);
  int port = resp["mqtt"]["port"] | 0;
  if (host == nullptr || port <= 0) {
    Serial.println("[register] response missing mqtt.host/port");
    return false;
  }

  outEndpoint.host = host;
  outEndpoint.port = static_cast<uint16_t>(port);
  Serial.printf("[register] ok, mqtt=%s:%u\n", outEndpoint.host.c_str(), outEndpoint.port);
  return true;
}
