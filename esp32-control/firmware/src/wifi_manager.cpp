#include "wifi_manager.h"
#include <WiFi.h>

void WifiManager::begin(const char *ssid, const char *password) {
  ssid_ = ssid;
  password_ = password;
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false); // we drive reconnect ourselves, with backoff
  attemptConnect();
}

void WifiManager::attemptConnect() {
  Serial.printf("[wifi] connecting to \"%s\"...\n", ssid_);
  WiFi.begin(ssid_, password_);
  lastAttemptMs_ = millis();
}

bool WifiManager::isConnected() const { return WiFi.status() == WL_CONNECTED; }

void WifiManager::loop() {
  if (isConnected()) {
    if (!everConnected_) {
      Serial.printf("[wifi] connected, ip=%s\n", WiFi.localIP().toString().c_str());
      everConnected_ = true;
    }
    backoffMs_ = 1000; // reset backoff once the link is back up
    return;
  }

  everConnected_ = false;
  unsigned long now = millis();
  if (now - lastAttemptMs_ >= backoffMs_) {
    attemptConnect();
    backoffMs_ = min(backoffMs_ * 2, kMaxBackoffMs);
  }
}
