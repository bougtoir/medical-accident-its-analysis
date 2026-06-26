/**
 * TONGE — Tracking Of Nuanced Gastro-chromatic Evolution
 * Color-based Cooking Timing Assistant
 * Target: M5Stack CoreS3 + Unit Color (TCS3472)
 *
 * Monitors food surface color in real-time via the TCS3472 RGBC sensor,
 * converts to CIE L*a*b*, computes ΔE against a user-selected target
 * color preset, and triggers an alarm when the target is reached.
 *
 * Hardware:
 *   - M5Stack CoreS3 (ESP32-S3, 2" touch LCD, speaker)
 *   - Unit Color (TCS3472 + white LED) on PORT.A (I2C)
 *
 * License: MIT
 */

#include <M5Unified.h>
#include <Wire.h>
#include <math.h>

// ─── TCS3472 I2C ────────────────────────────────────────────
#define TCS3472_ADDR     0x29
#define TCS3472_COMMAND  0x80
#define TCS3472_ENABLE   0x00
#define TCS3472_ATIME    0x01
#define TCS3472_CONTROL  0x0F
#define TCS3472_CDATAL   0x14  // Clear
#define TCS3472_RDATAL   0x16  // Red
#define TCS3472_GDATAL   0x18  // Green
#define TCS3472_BDATAL   0x1A  // Blue

// ─── CIE L*a*b* ────────────────────────────────────────────
struct Lab {
    float L;
    float a;
    float b;
};

// ─── Color Preset Definition ────────────────────────────────
struct ColorPreset {
    const char* name_ja;
    const char* name_en;
    Lab target;
    float tolerance;       // ΔE threshold
    const char* category;
    uint16_t display_color; // RGB565 for UI
};

// ─── Preset Dictionary ─────────────────────────────────────
// L*a*b* values are initial estimates; refine with real cooking data.
static const ColorPreset PRESETS[] = {
    {
        "きつね色", "Golden Brown",
        {68.5f, 12.3f, 42.1f}, 6.0f,
        "揚げ物・焼き物",
        M5.Display.color565(196, 136, 71)
    },
    {
        "飴色", "Caramel",
        {73.2f, 8.7f, 38.5f}, 5.0f,
        "炒め物",
        M5.Display.color565(222, 176, 104)
    },
    {
        "ハシバミ色", "Hazelnut",
        {65.0f, 10.1f, 30.2f}, 5.0f,
        "焼き菓子",
        M5.Display.color565(191, 164, 111)
    },
    {
        "こんがり", "Toasted",
        {60.0f, 15.2f, 35.8f}, 6.0f,
        "パン",
        M5.Display.color565(180, 120, 60)
    },
    {
        "べっこう色", "Amber",
        {55.0f, 20.3f, 45.0f}, 4.0f,
        "カラメル",
        M5.Display.color565(200, 140, 50)
    },
    {
        "焦がしバター", "Beurre Noisette",
        {48.0f, 12.5f, 28.0f}, 4.0f,
        "ソース",
        M5.Display.color565(140, 90, 45)
    },
};
static const int PRESET_COUNT = sizeof(PRESETS) / sizeof(PRESETS[0]);

// ─── State ──────────────────────────────────────────────────
enum AppState {
    STATE_MENU,
    STATE_CALIBRATE,
    STATE_MONITORING,
    STATE_REACHED,
};

static AppState       g_state       = STATE_MENU;
static int            g_selected    = 0;  // menu cursor
static Lab            g_current_lab = {0, 0, 0};
static float          g_current_de  = 100.0f;
static float          g_prev_de     = 100.0f;
static float          g_initial_de  = 100.0f;
static unsigned long  g_start_ms    = 0;

// White-balance reference (set during calibration)
static float g_ref_r = 1.0f;
static float g_ref_g = 1.0f;
static float g_ref_b = 1.0f;

// ─── ΔE History for trend display ───────────────────────────
#define HISTORY_LEN 60
static float g_de_history[HISTORY_LEN];
static int   g_hist_idx = 0;

// ─── TCS3472 Driver ─────────────────────────────────────────

static void tcs_write8(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(TCS3472_ADDR);
    Wire.write(TCS3472_COMMAND | reg);
    Wire.write(val);
    Wire.endTransmission();
}

static uint16_t tcs_read16(uint8_t reg) {
    Wire.beginTransmission(TCS3472_ADDR);
    Wire.write(TCS3472_COMMAND | 0x20 | reg);  // auto-increment
    Wire.endTransmission();
    Wire.requestFrom((uint8_t)TCS3472_ADDR, (uint8_t)2);
    uint16_t lo = Wire.read();
    uint16_t hi = Wire.read();
    return (hi << 8) | lo;
}

static bool tcs_init() {
    Wire.beginTransmission(TCS3472_ADDR);
    if (Wire.endTransmission() != 0) return false;

    // Integration time: 154ms (0xC0), Gain: 4x (0x01)
    tcs_write8(TCS3472_ATIME, 0xC0);
    tcs_write8(TCS3472_CONTROL, 0x01);
    // Enable: PON + AEN
    tcs_write8(TCS3472_ENABLE, 0x01);
    delay(3);
    tcs_write8(TCS3472_ENABLE, 0x03);
    delay(154);  // wait for first integration cycle
    return true;
}

struct RGBC {
    uint16_t r, g, b, c;
};

static RGBC tcs_read() {
    RGBC d;
    d.c = tcs_read16(TCS3472_CDATAL);
    d.r = tcs_read16(TCS3472_RDATAL);
    d.g = tcs_read16(TCS3472_GDATAL);
    d.b = tcs_read16(TCS3472_BDATAL);
    return d;
}

// ─── Color Conversion ───────────────────────────────────────

/**
 * Convert TCS3472 raw RGBC to normalized [0,1] RGB,
 * applying white-balance correction.
 */
static void rgbc_to_rgb01(RGBC raw, float& r, float& g, float& b) {
    if (raw.c == 0) { r = g = b = 0; return; }
    r = (float)raw.r / (float)raw.c;
    g = (float)raw.g / (float)raw.c;
    b = (float)raw.b / (float)raw.c;
    // Apply white-balance
    r *= g_ref_r;
    g *= g_ref_g;
    b *= g_ref_b;
    // Clamp
    r = constrain(r, 0.0f, 1.0f);
    g = constrain(g, 0.0f, 1.0f);
    b = constrain(b, 0.0f, 1.0f);
}

/**
 * sRGB [0,1] → CIE XYZ (D65 illuminant)
 */
static void rgb_to_xyz(float r, float g, float b,
                       float& x, float& y, float& z) {
    // Inverse sRGB companding
    auto inv_gamma = [](float c) -> float {
        return (c > 0.04045f)
            ? powf((c + 0.055f) / 1.055f, 2.4f)
            : c / 12.92f;
    };
    r = inv_gamma(r);
    g = inv_gamma(g);
    b = inv_gamma(b);
    x = r * 0.4124564f + g * 0.3575761f + b * 0.1804375f;
    y = r * 0.2126729f + g * 0.7151522f + b * 0.0721750f;
    z = r * 0.0193339f + g * 0.1191920f + b * 0.9503041f;
}

/**
 * CIE XYZ → CIE L*a*b* (D65 reference white)
 */
static Lab xyz_to_lab(float x, float y, float z) {
    // D65 reference
    x /= 0.95047f;
    y /= 1.00000f;
    z /= 1.08883f;
    auto f = [](float t) -> float {
        return (t > 0.008856f)
            ? cbrtf(t)
            : (7.787f * t + 16.0f / 116.0f);
    };
    Lab lab;
    lab.L = 116.0f * f(y) - 16.0f;
    lab.a = 500.0f * (f(x) - f(y));
    lab.b = 200.0f * (f(y) - f(z));
    return lab;
}

static Lab rgb01_to_lab(float r, float g, float b) {
    float x, y, z;
    rgb_to_xyz(r, g, b, x, y, z);
    return xyz_to_lab(x, y, z);
}

static float delta_e(Lab c1, Lab c2) {
    float dL = c1.L - c2.L;
    float da = c1.a - c2.a;
    float db = c1.b - c2.b;
    return sqrtf(dL * dL + da * da + db * db);
}

// ─── UI Drawing ─────────────────────────────────────────────

static uint16_t lab_to_rgb565(Lab lab) {
    // Approximate reverse for display purposes
    float fy = (lab.L + 16.0f) / 116.0f;
    float fx = lab.a / 500.0f + fy;
    float fz = fy - lab.b / 200.0f;
    auto inv_f = [](float t) -> float {
        return (t > 0.206893f)
            ? t * t * t
            : (t - 16.0f / 116.0f) / 7.787f;
    };
    float x = inv_f(fx) * 0.95047f;
    float y = inv_f(fy);
    float z = inv_f(fz) * 1.08883f;
    float r = x *  3.2404542f + y * -1.5371385f + z * -0.4985314f;
    float g = x * -0.9692660f + y *  1.8760108f + z *  0.0415560f;
    float b = x *  0.0556434f + y * -0.2040259f + z *  1.0572252f;
    auto gamma = [](float c) -> float {
        c = constrain(c, 0.0f, 1.0f);
        return (c > 0.0031308f)
            ? 1.055f * powf(c, 1.0f / 2.4f) - 0.055f
            : 12.92f * c;
    };
    r = gamma(r); g = gamma(g); b = gamma(b);
    return M5.Display.color565(
        (uint8_t)(r * 255), (uint8_t)(g * 255), (uint8_t)(b * 255));
}

static void draw_menu() {
    M5.Display.fillScreen(TFT_BLACK);
    M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Display.setTextSize(1);

    // Title
    M5.Display.setCursor(10, 5);
    M5.Display.setTextSize(2);
    M5.Display.print("TONGE");
    M5.Display.setTextSize(1);
    M5.Display.setCursor(80, 10);
    M5.Display.print(" - Select Target Color");

    int y = 35;
    for (int i = 0; i < PRESET_COUNT; i++) {
        bool sel = (i == g_selected);
        // Selection highlight
        if (sel) {
            M5.Display.fillRect(0, y - 2, 320, 28, TFT_DARKGREY);
        }
        // Color swatch
        M5.Display.fillRect(10, y, 24, 24, PRESETS[i].display_color);
        M5.Display.drawRect(10, y, 24, 24, TFT_WHITE);
        // Name
        M5.Display.setTextColor(sel ? TFT_YELLOW : TFT_WHITE, sel ? TFT_DARKGREY : TFT_BLACK);
        M5.Display.setCursor(42, y + 4);
        M5.Display.setTextSize(2);
        M5.Display.print(PRESETS[i].name_ja);
        M5.Display.setTextSize(1);
        M5.Display.setCursor(200, y + 8);
        M5.Display.printf("dE<%.0f", PRESETS[i].tolerance);

        y += 30;
    }

    // Instructions
    M5.Display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    M5.Display.setCursor(10, 220);
    M5.Display.setTextSize(1);
    M5.Display.print("Touch: select | Long press: start");
}

static void draw_calibrate() {
    M5.Display.fillScreen(TFT_NAVY);
    M5.Display.setTextColor(TFT_WHITE, TFT_NAVY);
    M5.Display.setTextSize(2);
    M5.Display.setCursor(20, 40);
    M5.Display.print("Calibration");
    M5.Display.setTextSize(1);
    M5.Display.setCursor(20, 80);
    M5.Display.print("Place sensor on a WHITE surface");
    M5.Display.setCursor(20, 100);
    M5.Display.print("(white plate, paper, etc.)");
    M5.Display.setCursor(20, 140);
    M5.Display.setTextSize(2);
    M5.Display.print("Touch to calibrate");
}

static void draw_monitoring() {
    const ColorPreset& preset = PRESETS[g_selected];
    M5.Display.fillScreen(TFT_BLACK);

    // Header
    M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Display.setTextSize(1);
    M5.Display.setCursor(5, 5);
    M5.Display.printf("Target: %s", preset.name_ja);

    unsigned long elapsed = (millis() - g_start_ms) / 1000;
    M5.Display.setCursor(240, 5);
    M5.Display.printf("%02lu:%02lu", elapsed / 60, elapsed % 60);

    // Current color vs Target color swatches
    uint16_t cur_col = lab_to_rgb565(g_current_lab);
    M5.Display.fillRect(10, 25, 60, 60, cur_col);
    M5.Display.drawRect(10, 25, 60, 60, TFT_WHITE);
    M5.Display.setCursor(15, 90);
    M5.Display.setTextSize(1);
    M5.Display.print("Now");

    M5.Display.fillRect(80, 25, 60, 60, preset.display_color);
    M5.Display.drawRect(80, 25, 60, 60, TFT_WHITE);
    M5.Display.setCursor(85, 90);
    M5.Display.print("Target");

    // ΔE numeric display
    M5.Display.setTextSize(3);
    uint16_t de_color = (g_current_de < preset.tolerance * 1.5f) ? TFT_GREEN
                      : (g_current_de < preset.tolerance * 3.0f) ? TFT_YELLOW
                      : TFT_RED;
    M5.Display.setTextColor(de_color, TFT_BLACK);
    M5.Display.setCursor(160, 35);
    M5.Display.printf("dE:%4.1f", g_current_de);
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    M5.Display.setCursor(160, 65);
    M5.Display.printf("Goal: < %.1f", preset.tolerance);

    // Progress bar
    float progress = 1.0f - (g_current_de / g_initial_de);
    progress = constrain(progress, 0.0f, 1.0f);
    int bar_w = (int)(progress * 300);
    M5.Display.fillRect(10, 110, 300, 20, TFT_DARKGREY);
    uint16_t bar_col = (progress > 0.8f) ? TFT_GREEN
                     : (progress > 0.5f) ? TFT_YELLOW
                     : TFT_ORANGE;
    M5.Display.fillRect(10, 110, bar_w, 20, bar_col);
    M5.Display.drawRect(10, 110, 300, 20, TFT_WHITE);
    M5.Display.setCursor(130, 113);
    M5.Display.setTextColor(TFT_WHITE, bar_col);
    M5.Display.printf("%d%%", (int)(progress * 100));

    // L*a*b* values
    M5.Display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    M5.Display.setCursor(10, 140);
    M5.Display.printf("L*=%.1f a*=%.1f b*=%.1f",
        g_current_lab.L, g_current_lab.a, g_current_lab.b);

    // ΔE trend graph
    M5.Display.drawRect(10, 160, 300, 60, TFT_DARKGREY);
    // threshold line
    float th_norm = preset.tolerance / 50.0f;  // normalize to graph height
    int th_y = 220 - (int)(constrain(th_norm, 0.0f, 1.0f) * 58);
    M5.Display.drawFastHLine(10, th_y, 300, TFT_GREEN);

    for (int i = 1; i < HISTORY_LEN; i++) {
        int idx0 = (g_hist_idx + i - 1) % HISTORY_LEN;
        int idx1 = (g_hist_idx + i) % HISTORY_LEN;
        if (g_de_history[idx0] < 0 || g_de_history[idx1] < 0) continue;
        float n0 = constrain(g_de_history[idx0] / 50.0f, 0.0f, 1.0f);
        float n1 = constrain(g_de_history[idx1] / 50.0f, 0.0f, 1.0f);
        int x0 = 10 + (i - 1) * 300 / HISTORY_LEN;
        int x1 = 10 + i * 300 / HISTORY_LEN;
        int y0 = 220 - (int)(n0 * 58);
        int y1 = 220 - (int)(n1 * 58);
        M5.Display.drawLine(x0, y0, x1, y1, TFT_CYAN);
    }

    // Footer
    M5.Display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    M5.Display.setCursor(10, 225);
    M5.Display.print("Touch to stop");
}

static void draw_reached() {
    const ColorPreset& preset = PRESETS[g_selected];
    unsigned long elapsed = (millis() - g_start_ms) / 1000;

    M5.Display.fillScreen(TFT_DARKGREEN);
    M5.Display.setTextColor(TFT_WHITE, TFT_DARKGREEN);
    M5.Display.setTextSize(3);
    M5.Display.setCursor(30, 30);
    M5.Display.print(preset.name_ja);

    M5.Display.setTextSize(2);
    M5.Display.setCursor(30, 80);
    M5.Display.print("Reached!");

    M5.Display.setCursor(30, 120);
    M5.Display.printf("Time: %02lu:%02lu", elapsed / 60, elapsed % 60);

    M5.Display.setCursor(30, 160);
    M5.Display.printf("dE: %.1f", g_current_de);

    M5.Display.setTextSize(1);
    M5.Display.setCursor(30, 200);
    M5.Display.print("Touch to return to menu");
}

// ─── Alarm ──────────────────────────────────────────────────

static void play_alarm() {
    M5.Speaker.tone(880, 200);
    delay(250);
    M5.Speaker.tone(1100, 200);
    delay(250);
    M5.Speaker.tone(880, 200);
    delay(250);
    M5.Speaker.tone(1100, 400);
}

// ─── Setup & Loop ───────────────────────────────────────────

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);
    M5.Display.setRotation(1);
    M5.Display.setBrightness(200);
    M5.Speaker.setVolume(200);

    Serial.begin(115200);
    Serial.println("[TONGE] Starting...");

    Wire.begin();
    if (!tcs_init()) {
        M5.Display.fillScreen(TFT_RED);
        M5.Display.setTextColor(TFT_WHITE, TFT_RED);
        M5.Display.setTextSize(2);
        M5.Display.setCursor(20, 100);
        M5.Display.print("Unit Color not found!");
        M5.Display.setCursor(20, 130);
        M5.Display.print("Check PORT.A connection");
        Serial.println("[TONGE] ERROR: TCS3472 not found");
        while (1) delay(1000);
    }
    Serial.println("[TONGE] TCS3472 initialized");

    // Init history
    for (int i = 0; i < HISTORY_LEN; i++) g_de_history[i] = -1.0f;

    g_state = STATE_MENU;
    draw_menu();
}

void loop() {
    M5.update();

    auto touch = M5.Touch.getDetail();
    bool touched = touch.wasPressed();
    bool long_pressed = touch.wasHold();

    switch (g_state) {
    case STATE_MENU: {
        if (touched) {
            // Determine which preset was tapped
            int tap_y = touch.y;
            int idx = (tap_y - 33) / 30;
            if (idx >= 0 && idx < PRESET_COUNT) {
                g_selected = idx;
                draw_menu();
            }
        }
        if (long_pressed) {
            g_state = STATE_CALIBRATE;
            draw_calibrate();
        }
        break;
    }

    case STATE_CALIBRATE: {
        if (touched) {
            // Take white reference reading
            RGBC raw = tcs_read();
            if (raw.c > 0) {
                float r = (float)raw.r / (float)raw.c;
                float g = (float)raw.g / (float)raw.c;
                float b = (float)raw.b / (float)raw.c;
                // Target: equal r,g,b for white
                float avg = (r + g + b) / 3.0f;
                g_ref_r = (r > 0) ? avg / r : 1.0f;
                g_ref_g = (g > 0) ? avg / g : 1.0f;
                g_ref_b = (b > 0) ? avg / b : 1.0f;
                Serial.printf("[TONGE] WB ref: R=%.3f G=%.3f B=%.3f\n",
                    g_ref_r, g_ref_g, g_ref_b);
            }

            // Take initial food color reading
            delay(200);
            RGBC food_raw = tcs_read();
            float fr, fg, fb;
            rgbc_to_rgb01(food_raw, fr, fg, fb);
            g_current_lab = rgb01_to_lab(fr, fg, fb);
            g_current_de = delta_e(g_current_lab, PRESETS[g_selected].target);
            g_initial_de = g_current_de;
            g_prev_de = g_current_de;

            // Reset history
            for (int i = 0; i < HISTORY_LEN; i++) g_de_history[i] = -1.0f;
            g_hist_idx = 0;
            g_de_history[g_hist_idx] = g_current_de;

            g_start_ms = millis();
            g_state = STATE_MONITORING;
            draw_monitoring();
        }
        break;
    }

    case STATE_MONITORING: {
        // Read sensor
        RGBC raw = tcs_read();
        float r, g, b;
        rgbc_to_rgb01(raw, r, g, b);
        g_current_lab = rgb01_to_lab(r, g, b);
        g_prev_de = g_current_de;
        g_current_de = delta_e(g_current_lab, PRESETS[g_selected].target);

        // Update history (every ~1s given 154ms integration + draw time)
        g_hist_idx = (g_hist_idx + 1) % HISTORY_LEN;
        g_de_history[g_hist_idx] = g_current_de;

        // Serial log
        Serial.printf("[TONGE] L*=%.1f a*=%.1f b*=%.1f dE=%.1f\n",
            g_current_lab.L, g_current_lab.a, g_current_lab.b,
            g_current_de);

        // Check if target reached
        if (g_current_de < PRESETS[g_selected].tolerance) {
            g_state = STATE_REACHED;
            play_alarm();
            draw_reached();
            break;
        }

        // Pre-alarm: estimate time to reach based on trend
        if (g_prev_de > g_current_de) {
            float rate = g_prev_de - g_current_de;  // ΔE decrease per cycle
            if (rate > 0.01f) {
                float remaining = g_current_de - PRESETS[g_selected].tolerance;
                float cycles_left = remaining / rate;
                // Pre-notify ~5 cycles before reaching
                if (cycles_left < 5.0f && cycles_left > 0.0f) {
                    M5.Speaker.tone(660, 100);
                }
            }
        }

        draw_monitoring();

        if (touched) {
            // Stop monitoring
            g_state = STATE_MENU;
            draw_menu();
        }
        break;
    }

    case STATE_REACHED: {
        // Periodic alarm repeat
        static unsigned long last_alarm = 0;
        if (millis() - last_alarm > 5000) {
            play_alarm();
            last_alarm = millis();
        }

        if (touched) {
            g_state = STATE_MENU;
            draw_menu();
        }
        break;
    }
    }

    delay(50);
}
