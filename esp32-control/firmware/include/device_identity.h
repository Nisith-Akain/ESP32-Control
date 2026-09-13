#pragma once
#include <Arduino.h>

// Returns the stable device_id per INTERFACES.md SS1: "esp32-" + lowercase
// hex MAC, no separators, e.g. "esp32-aabbccddeeff". Derived from the
// factory-programmed WiFi-station MAC via efuse, so it's stable across
// reboots and available before WiFi actually connects.
String getDeviceId();
