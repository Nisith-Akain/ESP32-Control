#pragma once
#include <Arduino.h>

// Starts NTP time sync (call once after WiFi first connects). Non-blocking.
void timeInit();

// True once the system clock holds a plausible real-world value (i.e. NTP
// sync has landed). Before that, isoTimestampNow() still returns a
// well-formed string, just anchored near the Unix epoch — acceptable for
// this reference build since telemetry/event timestamps are used for
// display/logging, not as a source of truth for ordering (that's `seq`).
bool timeIsSynced();

// Current time as an ISO8601 UTC string, e.g. "2026-09-13T12:00:00Z".
String isoTimestampNow();
