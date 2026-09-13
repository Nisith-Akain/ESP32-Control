#include "time_util.h"
#include <time.h>

namespace {
const char *kNtpServer1 = "pool.ntp.org";
const char *kNtpServer2 = "time.nist.gov";
constexpr time_t kPlausibleEpoch = 1577836800; // 2020-01-01T00:00:00Z
} // namespace

void timeInit() {
  // UTC, no DST offset — INTERFACES.md timestamps are all UTC ("Z" suffix).
  configTime(0, 0, kNtpServer1, kNtpServer2);
}

bool timeIsSynced() { return time(nullptr) > kPlausibleEpoch; }

String isoTimestampNow() {
  time_t now = time(nullptr);
  struct tm tmStruct;
  gmtime_r(&now, &tmStruct);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tmStruct);
  return String(buf);
}
