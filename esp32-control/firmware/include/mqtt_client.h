#pragma once
#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiClient.h>

// Owns the MQTT connection for one device per INTERFACES.md SS4:
// - Connects with a Last Will configured on devices/{id}/status ->
//   {"status":"offline"} (retained), so an ungraceful disconnect still
//   flips the device to offline broker-side.
// - Publishes {"status":"online"} (retained) right after a successful
//   connect.
// - Subscribes to devices/{id}/commands and forwards raw payloads to the
//   registered CommandHandler.
// - Exposes publish helpers for devices/{id}/telemetry and
//   devices/{id}/events.
//
// Reconnects with basic exponential backoff (1s..30s) if the WiFi link is
// up but the broker connection drops (EC-1 acceptance criteria).
class DeviceMqtt {
 public:
  using CommandHandler = void (*)(const String &payload);

  void begin(const String &deviceId, const String &host, uint16_t port);
  void setCommandHandler(CommandHandler handler) { handler_ = handler; }

  // Call every loop() iteration once WiFi is connected.
  void loop();

  bool isConnected();

  void publishTelemetry(const String &jsonPayload);
  void publishEvent(const String &jsonPayload);

  const String &deviceId() const { return deviceId_; }

 private:
  WiFiClient netClient_;
  PubSubClient mqtt_{netClient_};
  String deviceId_;
  String host_;
  uint16_t port_ = 0;

  String statusTopic_;
  String commandsTopic_;
  String eventsTopic_;
  String telemetryTopic_;

  CommandHandler handler_ = nullptr;

  unsigned long lastAttemptMs_ = 0;
  unsigned long backoffMs_ = 1000;
  static constexpr unsigned long kMaxBackoffMs = 30000;

  void attemptConnect();
  void handleMessage(char *topic, uint8_t *payload, unsigned int length);

  static DeviceMqtt *instance_;
  static void staticCallback(char *topic, uint8_t *payload, unsigned int length);
};
