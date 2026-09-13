#pragma once
#include <Arduino.h>

// Manages the WiFi station connection with basic exponential backoff on
// disconnect (EC-1 acceptance criteria: "basic reconnect/backoff on WiFi or
// MQTT drop", not required to be sophisticated for v1).
//
// begin() kicks off the first connection attempt; loop() must be called on
// every main-loop iteration afterward and transparently retries with
// backoff (starting at 1s, doubling, capped at 30s) whenever WiFi.status()
// isn't WL_CONNECTED. Backoff resets to 1s once a connection succeeds.
class WifiManager {
 public:
  void begin(const char *ssid, const char *password);
  void loop();
  bool isConnected() const;

 private:
  const char *ssid_ = nullptr;
  const char *password_ = nullptr;
  bool everConnected_ = false;
  unsigned long lastAttemptMs_ = 0;
  unsigned long backoffMs_ = 1000;
  static constexpr unsigned long kMaxBackoffMs = 30000;

  void attemptConnect();
};
