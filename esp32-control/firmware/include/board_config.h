#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>

// ---------------------------------------------------------------------------
// Board capability table.
//
// This is THE single place a future physical build edits: the sensors[]/
// commands[] tables below (defined in board_config.cpp) declare exactly what
// INTERFACES.md SS1's `capabilities.sensors[]`/`capabilities.commands[]`
// contain, and boardReadSensor()/boardExecuteCommand() (also in
// board_config.cpp) are the only two functions that touch real hardware
// (GPIO/ADC/peripheral drivers). Nothing in wifi_manager, mqtt_client,
// backend_client, or main.cpp needs to change to add a new board — they all
// iterate these tables generically.
//
// Reference build shipped here: one simulated temperature sensor
// ("temp_c") + one relay toggle command ("relay1"), per EC-1's acceptance
// criteria ("pick a simple example capability set").
// ---------------------------------------------------------------------------

enum class SensorType { kFloat, kInt, kBool, kString };
enum class CommandType { kToggle, kSlider, kButton };

struct BoardSensor {
  const char *key;
  const char *label;
  const char *unit;
  SensorType type;
};

struct BoardCommand {
  const char *key;
  const char *label;
  CommandType type;
  long minValue; // only meaningful for kSlider
  long maxValue; // only meaningful for kSlider
};

// Pin map for this reference build.
namespace board_pins {
constexpr uint8_t kRelay1 = 26;
constexpr uint8_t kTempSensorAdc = 34; // ADC1_CH6 on most ESP32 devkits
} // namespace board_pins

extern const BoardSensor kBoardSensors[];
extern const size_t kBoardSensorCount;
extern const BoardCommand kBoardCommands[];
extern const size_t kBoardCommandCount;

// Maps the enums above to the exact wire strings INTERFACES.md SS1 expects
// (`float|int|bool|string`, `toggle|slider|button`).
const char *sensorTypeToString(SensorType type);
const char *commandTypeToString(CommandType type);

// One-time hardware init (pinMode etc.) for everything declared above. Call
// once from setup().
void boardInit();

// Reads the current value of a declared sensor by key. Returns true and
// fills outValue on success (numeric/bool sensors report as double; this
// reference build has no string sensor to exercise that path).
bool boardReadSensor(const char *key, double &outValue);

// Executes a declared command against hardware. `value` is the "value"
// field parsed out of the incoming devices/{id}/commands payload
// (INTERFACES.md SS4/SS5). Returns true/false (execution result) and fills
// `detail` with a short human-readable status used as the command_result
// event's "detail" field.
bool boardExecuteCommand(const char *key, JsonVariantConst value, String &detail);
