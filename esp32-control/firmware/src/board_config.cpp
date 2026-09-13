#include "board_config.h"

// ---------------------------------------------------------------------------
// Capability table. To add a sensor or command for a new board: add a row
// here, and add the matching case in boardReadSensor()/boardExecuteCommand()
// below. That's it — registration JSON, telemetry payloads, and command
// dispatch all derive from this table generically.
// ---------------------------------------------------------------------------

const BoardSensor kBoardSensors[] = {
    {"temp_c", "Temperature", "C", SensorType::kFloat},
};
const size_t kBoardSensorCount = sizeof(kBoardSensors) / sizeof(kBoardSensors[0]);

const BoardCommand kBoardCommands[] = {
    {"relay1", "Relay 1", CommandType::kToggle, 0, 0},
};
const size_t kBoardCommandCount = sizeof(kBoardCommands) / sizeof(kBoardCommands[0]);

const char *sensorTypeToString(SensorType type) {
  switch (type) {
    case SensorType::kFloat:
      return "float";
    case SensorType::kInt:
      return "int";
    case SensorType::kBool:
      return "bool";
    case SensorType::kString:
      return "string";
  }
  return "float";
}

const char *commandTypeToString(CommandType type) {
  switch (type) {
    case CommandType::kToggle:
      return "toggle";
    case CommandType::kSlider:
      return "slider";
    case CommandType::kButton:
      return "button";
  }
  return "toggle";
}

void boardInit() {
  pinMode(board_pins::kRelay1, OUTPUT);
  digitalWrite(board_pins::kRelay1, LOW);
  pinMode(board_pins::kTempSensorAdc, INPUT);
}

bool boardReadSensor(const char *key, double &outValue) {
  if (strcmp(key, "temp_c") == 0) {
    // Placeholder sensor: this reference build has no real thermometer
    // wired up. It derives a plausible, stable-ish reading from the ADC
    // pin (e.g. a potentiometer, or a floating pin) purely so the
    // telemetry/graph pipeline has real numbers to move end to end.
    // Replace this branch with a real driver (DS18B20, DHT22, etc.) for an
    // actual deployment — boardInit()/boardReadSensor() are the only two
    // functions that would need to change.
    int raw = analogRead(board_pins::kTempSensorAdc); // 0..4095 on ESP32
    outValue = 15.0 + (raw / 4095.0) * 20.0;           // maps to ~15..35 C
    return true;
  }
  return false;
}

bool boardExecuteCommand(const char *key, JsonVariantConst value, String &detail) {
  if (strcmp(key, "relay1") == 0) {
    bool on = value.is<bool>() ? value.as<bool>() : (value.as<int>() != 0);
    digitalWrite(board_pins::kRelay1, on ? HIGH : LOW);
    detail = on ? "relay1 turned on" : "relay1 turned off";
    return true;
  }
  detail = "unknown command key";
  return false;
}
