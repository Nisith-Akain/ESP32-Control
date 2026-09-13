#include "mqtt_client.h"

DeviceMqtt *DeviceMqtt::instance_ = nullptr;

void DeviceMqtt::begin(const String &deviceId, const String &host, uint16_t port) {
  deviceId_ = deviceId;
  host_ = host;
  port_ = port;

  statusTopic_ = "devices/" + deviceId_ + "/status";
  commandsTopic_ = "devices/" + deviceId_ + "/commands";
  eventsTopic_ = "devices/" + deviceId_ + "/events";
  telemetryTopic_ = "devices/" + deviceId_ + "/telemetry";

  instance_ = this;
  mqtt_.setServer(host_.c_str(), port_);
  mqtt_.setCallback(&DeviceMqtt::staticCallback);

  attemptConnect();
}

void DeviceMqtt::attemptConnect() {
  Serial.printf("[mqtt] connecting to %s:%u...\n", host_.c_str(), port_);
  lastAttemptMs_ = millis();

  static const char *kOfflinePayload = "{\"status\":\"offline\"}";
  bool ok = mqtt_.connect(deviceId_.c_str(),
                           /*user*/ nullptr, /*pass*/ nullptr,
                           statusTopic_.c_str(), /*willQos*/ 1, /*willRetain*/ true,
                           kOfflinePayload, /*cleanSession*/ true);
  if (!ok) {
    Serial.printf("[mqtt] connect failed, state=%d\n", mqtt_.state());
    return;
  }

  Serial.println("[mqtt] connected");
  mqtt_.publish(statusTopic_.c_str(), "{\"status\":\"online\"}", /*retained*/ true);
  mqtt_.subscribe(commandsTopic_.c_str(), 1);
  backoffMs_ = 1000;
}

bool DeviceMqtt::isConnected() { return mqtt_.connected(); }

void DeviceMqtt::loop() {
  if (mqtt_.connected()) {
    mqtt_.loop();
    return;
  }

  unsigned long now = millis();
  if (now - lastAttemptMs_ >= backoffMs_) {
    attemptConnect();
    backoffMs_ = min(backoffMs_ * 2, kMaxBackoffMs);
  }
}

void DeviceMqtt::publishTelemetry(const String &jsonPayload) {
  if (!mqtt_.connected()) return;
  mqtt_.publish(telemetryTopic_.c_str(), jsonPayload.c_str(), /*retained*/ false);
}

void DeviceMqtt::publishEvent(const String &jsonPayload) {
  if (!mqtt_.connected()) return;
  mqtt_.publish(eventsTopic_.c_str(), jsonPayload.c_str(), /*retained*/ false);
}

void DeviceMqtt::handleMessage(char *topic, uint8_t *payload, unsigned int length) {
  if (String(topic) != commandsTopic_) return;
  String body;
  body.reserve(length);
  for (unsigned int i = 0; i < length; i++) body += static_cast<char>(payload[i]);
  if (handler_) handler_(body);
}

void DeviceMqtt::staticCallback(char *topic, uint8_t *payload, unsigned int length) {
  if (instance_) instance_->handleMessage(topic, payload, length);
}
