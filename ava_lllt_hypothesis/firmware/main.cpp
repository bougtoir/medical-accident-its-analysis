/**
 * AVA-PBM Glove Firmware v1.0
 * 
 * Platform: ESP32-S3 (PlatformIO / Arduino framework)
 * 
 * Controls 32x 660nm LEDs via 2x TLC5940 PWM drivers,
 * reads skin temperature via MLX90614, and communicates
 * with companion app via BLE.
 * 
 * License: MIT
 */

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Wire.h>

// ─── Pin Definitions ───────────────────────────
#define TLC_SIN_PIN     11   // TLC5940 serial data in
#define TLC_SCLK_PIN    12   // TLC5940 serial clock
#define TLC_XLAT_PIN    13   // TLC5940 latch
#define TLC_BLANK_PIN   14   // TLC5940 blank (PWM cycle reset)
#define TLC_GSCLK_PIN   15   // TLC5940 grayscale clock

#define I2C_SDA_PIN     8    // I2C SDA (MLX90614, MAX30102)
#define I2C_SCL_PIN     9    // I2C SCL

#define LED_STATUS_PIN  2    // Onboard status LED
#define BATTERY_ADC_PIN 4    // Battery voltage divider

// ─── MLX90614 I2C Address ──────────────────────
#define MLX90614_ADDR   0x5A
#define MLX90614_TOBJ1  0x07  // Object temperature register

// ─── Configuration ─────────────────────────────
struct DeviceConfig {
    uint16_t led_intensity;     // 0-4095 (TLC5940 12-bit PWM)
    uint16_t duty_on_ms;        // LED ON duration (ms)
    uint16_t duty_off_ms;       // LED OFF duration (ms)
    uint16_t session_duration_s; // Total session length (s)
    float    temp_limit_c;      // Safety cutoff temperature (°C)
    bool     session_active;
};

DeviceConfig config = {
    .led_intensity = 2048,      // 50% of max (~20 mW/cm²)
    .duty_on_ms = 10000,        // 10 seconds ON
    .duty_off_ms = 5000,        // 5 seconds OFF
    .session_duration_s = 1200, // 20 minutes
    .temp_limit_c = 42.0f,      // Safety limit
    .session_active = false
};

// ─── State ─────────────────────────────────────
float skin_temp_c = 0.0f;
float battery_voltage = 0.0f;
uint32_t session_start_ms = 0;
uint32_t session_elapsed_s = 0;
bool leds_on = false;
uint32_t last_toggle_ms = 0;

// ─── BLE ───────────────────────────────────────
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHAR_CONTROL_UUID   "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHAR_TELEMETRY_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a9"

BLEServer* pServer = nullptr;
BLECharacteristic* pControlChar = nullptr;
BLECharacteristic* pTelemetryChar = nullptr;
bool ble_connected = false;

// ─── TLC5940 Functions ─────────────────────────

void tlc5940_init() {
    pinMode(TLC_SIN_PIN, OUTPUT);
    pinMode(TLC_SCLK_PIN, OUTPUT);
    pinMode(TLC_XLAT_PIN, OUTPUT);
    pinMode(TLC_BLANK_PIN, OUTPUT);
    pinMode(TLC_GSCLK_PIN, OUTPUT);

    digitalWrite(TLC_BLANK_PIN, HIGH);  // All LEDs off
    digitalWrite(TLC_XLAT_PIN, LOW);
}

void tlc5940_set_all(uint16_t value) {
    // Shift in 12-bit grayscale data for 32 channels (2 × TLC5940)
    // MSB first, channel 31 first
    for (int ch = 31; ch >= 0; ch--) {
        for (int bit = 11; bit >= 0; bit--) {
            digitalWrite(TLC_SIN_PIN, (value >> bit) & 1);
            digitalWrite(TLC_SCLK_PIN, HIGH);
            delayMicroseconds(1);
            digitalWrite(TLC_SCLK_PIN, LOW);
        }
    }
    // Latch data
    digitalWrite(TLC_XLAT_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(TLC_XLAT_PIN, LOW);
}

void tlc5940_leds_on(uint16_t intensity) {
    tlc5940_set_all(intensity);
    digitalWrite(TLC_BLANK_PIN, LOW);  // Enable outputs
    leds_on = true;
}

void tlc5940_leds_off() {
    digitalWrite(TLC_BLANK_PIN, HIGH);  // Disable outputs
    leds_on = false;
}

// ─── MLX90614 Functions ────────────────────────

float mlx90614_read_object_temp() {
    Wire.beginTransmission(MLX90614_ADDR);
    Wire.write(MLX90614_TOBJ1);
    Wire.endTransmission(false);
    Wire.requestFrom((uint8_t)MLX90614_ADDR, (uint8_t)3);

    if (Wire.available() < 2) return -999.0f;

    uint16_t raw = Wire.read();
    raw |= (Wire.read() << 8);
    Wire.read();  // PEC byte (ignored for simplicity)

    return (raw * 0.02f) - 273.15f;
}

// ─── Battery Voltage ───────────────────────────

float read_battery_voltage() {
    int adc_val = analogRead(BATTERY_ADC_PIN);
    // Voltage divider: 100k / 100k, so Vbat = ADC * 2 * 3.3 / 4095
    return (adc_val * 2.0f * 3.3f) / 4095.0f;
}

// ─── BLE Callbacks ─────────────────────────────

class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) override {
        ble_connected = true;
    }
    void onDisconnect(BLEServer* pServer) override {
        ble_connected = false;
        BLEDevice::startAdvertising();
    }
};

class ControlCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) override {
        String value = pCharacteristic->getValue();
        if (value.length() > 0) {
            uint8_t cmd = value[0];
            switch (cmd) {
                case 0x01:  // Start session
                    config.session_active = true;
                    session_start_ms = millis();
                    break;
                case 0x00:  // Stop session
                    config.session_active = false;
                    tlc5940_leds_off();
                    break;
                case 0x10:  // Set intensity (next 2 bytes = uint16 LE)
                    if (value.length() >= 3) {
                        config.led_intensity = value[1] | (value[2] << 8);
                        if (config.led_intensity > 4095)
                            config.led_intensity = 4095;
                    }
                    break;
                case 0x20:  // Set duty cycle (next 4 bytes: on_ms, off_ms)
                    if (value.length() >= 5) {
                        config.duty_on_ms = value[1] | (value[2] << 8);
                        config.duty_off_ms = value[3] | (value[4] << 8);
                    }
                    break;
            }
        }
    }
};

void ble_init() {
    BLEDevice::init("AVA-PBM-Glove");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());

    BLEService* pService = pServer->createService(SERVICE_UUID);

    pControlChar = pService->createCharacteristic(
        CHAR_CONTROL_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    pControlChar->setCallbacks(new ControlCallbacks());

    pTelemetryChar = pService->createCharacteristic(
        CHAR_TELEMETRY_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pTelemetryChar->addDescriptor(new BLE2902());

    pService->start();
    BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();
}

// ─── Telemetry ─────────────────────────────────

void send_telemetry() {
    if (!ble_connected) return;

    // Pack telemetry: skin_temp (float), battery_v (float),
    //                 session_elapsed_s (uint32), leds_on (uint8)
    uint8_t buf[13];
    memcpy(buf, &skin_temp_c, 4);
    memcpy(buf + 4, &battery_voltage, 4);
    memcpy(buf + 8, &session_elapsed_s, 4);
    buf[12] = leds_on ? 1 : 0;

    pTelemetryChar->setValue(buf, 13);
    pTelemetryChar->notify();
}

// ─── Main ──────────────────────────────────────

void setup() {
    Serial.begin(115200);
    Serial.println("AVA-PBM Glove v1.0");

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    pinMode(LED_STATUS_PIN, OUTPUT);
    analogReadResolution(12);

    tlc5940_init();
    ble_init();

    Serial.println("Ready. Waiting for BLE connection...");
}

void loop() {
    // Read sensors (every 500ms)
    static uint32_t last_sensor_ms = 0;
    if (millis() - last_sensor_ms >= 500) {
        last_sensor_ms = millis();
        skin_temp_c = mlx90614_read_object_temp();
        battery_voltage = read_battery_voltage();

        // Safety check: thermal cutoff
        if (skin_temp_c > config.temp_limit_c && config.session_active) {
            config.session_active = false;
            tlc5940_leds_off();
            Serial.println("SAFETY: Skin temp exceeded limit. Session stopped.");
        }

        // Send telemetry
        send_telemetry();
    }

    // Session logic
    if (config.session_active) {
        session_elapsed_s = (millis() - session_start_ms) / 1000;

        // Auto-stop at session duration
        if (session_elapsed_s >= config.session_duration_s) {
            config.session_active = false;
            tlc5940_leds_off();
            Serial.println("Session complete.");
            return;
        }

        // Duty cycle control
        uint32_t cycle_ms = config.duty_on_ms + config.duty_off_ms;
        uint32_t phase_ms = (millis() - session_start_ms) % cycle_ms;

        if (phase_ms < config.duty_on_ms) {
            if (!leds_on) {
                tlc5940_leds_on(config.led_intensity);
            }
        } else {
            if (leds_on) {
                tlc5940_leds_off();
            }
        }

        // Status LED blink
        digitalWrite(LED_STATUS_PIN, (millis() / 500) % 2);
    } else {
        // Idle
        digitalWrite(LED_STATUS_PIN, LOW);
        if (leds_on) tlc5940_leds_off();
    }

    delay(10);  // 100 Hz main loop
}
