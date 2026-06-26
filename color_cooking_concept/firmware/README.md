# TONGE Firmware — M5Stack CoreS3 + Unit Color

**TONGE**: **T**racking **O**f **N**uanced **G**astro-chromatic **E**volution

## Hardware Requirements

| Part | Model | Where to Buy |
|------|-------|-------------|
| Controller | M5Stack CoreS3 | [Switch Science](https://www.switch-science.com/products/8960) |
| Color Sensor | Unit Color (TCS3472) | [M5Stack Shop](https://shop.m5stack.com/products/color-unit) |
| Cable | HY2.0-4P Grove (included with Unit Color) | — |

## Setup

1. Install [Arduino IDE](https://www.arduino.cc/en/software) (2.x recommended)
2. Add M5Stack board manager URL: `https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/arduino/package_m5stack_index.json`
3. Install board: **M5Stack** → select **M5CoreS3**
4. Install library: **M5Unified** (v0.2.11+)
5. Connect Unit Color to PORT.A (I2C) on CoreS3
6. Open `tonge_cores3/tonge_cores3.ino` and upload

## Usage

1. **Menu**: Touch a color preset to select it. Long-press to start.
2. **Calibrate**: Place the sensor on a white surface (plate, paper) and touch to calibrate.
3. **Monitor**: The display shows current color vs target, ΔE progress bar, and trend graph.
4. **Alarm**: When ΔE drops below threshold, speaker alarm triggers.

## Color Presets

| Name | L\*a\*b\* Target | ΔE Threshold |
|------|------------------|-------------|
| きつね色 (Golden Brown) | 68.5, 12.3, 42.1 | 6.0 |
| 飴色 (Caramel) | 73.2, 8.7, 38.5 | 5.0 |
| ハシバミ色 (Hazelnut) | 65.0, 10.1, 30.2 | 5.0 |
| こんがり (Toasted) | 60.0, 15.2, 35.8 | 6.0 |
| べっこう色 (Amber) | 55.0, 20.3, 45.0 | 4.0 |
| 焦がしバター (Beurre Noisette) | 48.0, 12.5, 28.0 | 4.0 |

Note: L\*a\*b\* values are initial estimates. Calibrate with real cooking sessions.

## TONGINT Software Platform

The TONGE hardware device pairs with the **TONGINT** (**T**racking **O**f **N**uanced **G**astro-chromatic **INT**elligence) software platform for:
- Color preset dictionary management
- Remote monitoring via smartphone
- Cloud-based color data aggregation
- AI-assisted cooking state determination
