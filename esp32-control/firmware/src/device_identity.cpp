#include "device_identity.h"
#include <esp_mac.h>

String getDeviceId() {
  uint8_t mac[6] = {0};
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char hex[13];
  snprintf(hex, sizeof(hex), "%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4],
           mac[5]);
  return String("esp32-") + hex;
}
