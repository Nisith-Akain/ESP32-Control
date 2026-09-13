#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

#include "backend_client.h"
#include "board_config.h"
#include "config.h"
#include "device_identity.h"
#include "mqtt_client.h"
#include "time_util.h"
#include "wifi_manager.h"

// ---------------------------------------------------------------------------
// EC-1 reference firmware: WiFi + MQTT + telemetry + command handling.
// See TEAM/INTERFACES.md for the wire contracts and README.md in this
// directory for build/config instructions.
//
// Globals are kept as file-scope statics (standard for a small Arduino
// sketch) rather than wrapped in a singleton class: there is exactly one
// WiFi link, one MQTT connection, and one device identity per board.
// ---------------------------------------------------------------------------

static String g_deviceId;
static WifiManager g_wifi;
static DeviceMqtt g_mqtt;

static unsigned long g_lastTelemetryMs = 0;
static uint32_t g_telemetrySeq = 0;
static bool g_sessionReady = false; // true once register+MQTT connect has run for this WiFi session

static void publishCommandResult(const String &commandId, const char *status,
                                  const String &detail) {
  StaticJsonDocument<256> doc;
  doc["type"] = "command_result";
  doc["command_id"] = commandId;
  doc["status"] = status;
  doc["detail"] = detail;
  String out;
  serializeJson(doc, out);
  g_mqtt.publishEvent(out);
}

// Parses an incoming devices/{id}/commands payload (INTERFACES.md SS4/SS5),
// executes it via board_config, and reports the outcome as a command_result
// event referencing the same command_id.
static void onCommand(const String &payload) {
  StaticJsonDocument<384> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("[cmd] malformed payload: %s\n", err.c_str());
    return; // no command_id to reference, nothing useful to report back
  }

  String commandId = doc["command_id"] | "";
  const char *command = doc["command"] | "";
  if (commandId.isEmpty() || strlen(command) == 0) {
    Serial.println("[cmd] missing command_id/command, ignoring");
    return;
  }

  String detail;
  bool ok = boardExecuteCommand(command, doc["value"], detail);
  Serial.printf("[cmd] %s -> %s (%s)\n", command, ok ? "ok" : "failed", detail.c_str());
  publishCommandResult(commandId, ok ? "ok" : "failed", detail);
}

// Builds and publishes one telemetry message from every sensor in the
// board's capability table (INTERFACES.md SS4).
static void publishTelemetry() {
  StaticJsonDocument<384> doc;
  doc["ts"] = isoTimestampNow();
  doc["seq"] = g_telemetrySeq++;
  JsonObject data = doc.createNestedObject("data");
  for (size_t i = 0; i < kBoardSensorCount; i++) {
    double value = 0;
    if (boardReadSensor(kBoardSensors[i].key, value)) {
      data[kBoardSensors[i].key] = value;
    }
  }
  String out;
  serializeJson(doc, out);
  g_mqtt.publishTelemetry(out);
}

// Runs the register handshake (INTERFACES.md SS1/SS12.2); on success uses
// the broker address it returns, on failure falls back to the compiled-in
// default, then (re)connects MQTT. Safe to call again after a WiFi
// reconnect — register is an idempotent upsert.
static void doRegisterAndConnectMqtt() {
  MqttEndpoint endpoint;
  bool ok = registerDevice(g_deviceId, WiFi.localIP().toString(), endpoint);
  if (!ok) {
    Serial.println("[register] using compiled-in default MQTT broker");
    endpoint.host = MQTT_DEFAULT_HOST;
    endpoint.port = MQTT_DEFAULT_PORT;
  }
  g_mqtt.setCommandHandler(&onCommand);
  g_mqtt.begin(g_deviceId, endpoint.host, endpoint.port);
  g_sessionReady = true;
}

void setup() {
  Serial.begin(115200);
  delay(200);

  g_deviceId = getDeviceId();
  Serial.printf("[boot] device_id=%s fw=%s\n", g_deviceId.c_str(), FIRMWARE_VERSION);

  boardInit();
  g_wifi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void loop() {
  g_wifi.loop();

  if (!g_wifi.isConnected()) {
    g_sessionReady = false; // force a fresh register+MQTT setup after reconnect
    return;
  }

  if (!g_sessionReady) {
    timeInit();
    doRegisterAndConnectMqtt();
  }

  g_mqtt.loop();

  unsigned long now = millis();
  if (g_mqtt.isConnected() && now - g_lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
    g_lastTelemetryMs = now;
    publishTelemetry();
  }
}
