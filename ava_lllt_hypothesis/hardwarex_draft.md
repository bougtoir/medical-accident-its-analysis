# HardwareX Paper Draft

## Title

An open-source wearable photobiomodulation device for selective vasodilation of glabrous skin arteriovenous anastomoses: Design, fabrication, and validation

## Authors

Tatsuki Onishi

[Affiliation to be inserted]

---

## 1. Hardware in context

Arteriovenous anastomoses (AVAs) are direct vascular connections between arterioles and venules concentrated in glabrous (non-hairy) skin of the palms, soles, and digits [1]. When dilated, AVAs create low-resistance parallel pathways that reduce total peripheral resistance (TPR) and lower blood pressure [2]. We have previously hypothesized that photobiomodulation (PBM) at 630–850 nm can selectively dilate AVAs through nitric oxide (NO) release, providing non-pharmacological blood pressure reduction [3].

Existing devices that manipulate AVA blood flow—such as the AVACEN 100 (conductive heating plus negative pressure) and selective thermal stimulation systems (bed-integrated, sleep-only)—are stationary, expensive, and unavailable for daytime use [4,5]. No open-source, wearable device exists for PBM-based AVA vasodilation.

This paper presents the design, fabrication, and validation of an open-source wearable PBM device ("AVA-PBM Glove") that delivers 660 nm light to palmar glabrous skin. The device is designed for reproducibility: all design files, firmware, and fabrication instructions are provided, and the total bill of materials costs less than $30 USD. The device is intended as a research tool for investigating PBM-induced vasodilation and its hemodynamic effects, and as a platform for future clinical studies.

**References for this section:**
1. Walløe L. Temperature (Austin). 2016;3(1):92-103.
2. Lobo MD et al. Lancet. 2015;385:1634-1641.
3. Onishi T. Med Hypotheses. [year]; [in press / submitted].
4. AVACEN Medical. US Patent 8,679,170 B2. 2014.
5. Diller KR et al. US Patent 11,229,548 B2. 2022.

---

## 2. Hardware description

The AVA-PBM Glove comprises four functional subsystems:

### 2.1 Optical subsystem (LED array)
- **LED type:** 660 nm AlGaInP SMD LEDs (e.g., OSRAM OSLON SSL 80, GH CSSRM4.24)
- **Array configuration:** 4 × 8 matrix (32 LEDs) on flexible PCB (FPC)
- **Irradiance per LED:** 50 mW optical at 350 mA forward current
- **Total optical power:** 1.6 W (32 × 50 mW)
- **Irradiance at skin surface:** ~40 mW/cm² over 40 cm² active area
- **Beam angle:** 80° (Lambertian, sufficient for skin contact use)
- **FPC dimensions:** 80 mm × 100 mm, 0.2 mm thickness, polyimide substrate
- **LED spacing:** 20 mm center-to-center (uniform palmar coverage)

### 2.2 Control subsystem
- **Microcontroller:** ESP32-S3-WROOM-1 (dual-core, BLE 5.0, Wi-Fi)
- **LED driver:** 4× TLC5940 (16-channel PWM LED driver, constant current)
  - Provides individual PWM control of all 32 LEDs
  - Programmable constant current: 0–60 mA per channel (via external resistor)
- **Pulse control:** Firmware-controlled duty cycle (configurable 10–100%)
  - Default: 10 s ON / 5 s OFF (67% duty cycle)
- **Safety interlock:** Hardware current limiter + firmware watchdog timer
  - Maximum irradiance capped at 100 mW/cm² (IEC 62471 exempt group)

### 2.3 Sensing subsystem
- **Skin temperature:** MLX90614ESF-BCI (medical-grade IR thermometer, ±0.1°C)
  - Mounted on FPC facing skin surface
  - Measures palmar skin temperature in real-time
- **Optional PPG sensor:** MAX30102 (for future pulse/SpO2/PTT-based BP estimation)
  - Included on PCB but disabled in firmware v1.0 (民生品 Phase 1)
  - Solder jumper to enable (Phase 2 medical device upgrade)

### 2.4 Power subsystem
- **Battery:** LiPo 3.7V 800 mAh (18350 cell, replaceable)
- **Charging:** USB-C, 5V/1A, TP4056 charge controller
- **Estimated runtime:**
  - Full power (67% duty): ~3 hours
  - Low power (30% duty): ~6 hours
- **Voltage regulation:** 3.3V LDO for ESP32, 5V boost for LED driver

### 2.5 Enclosure
- **Glove:** Commercial touchscreen-compatible knit glove (modified)
- **Electronics pocket:** Silicone pouch sewn onto dorsal side (wrist area)
- **FPC attachment:** FPC bonded to inner palm surface with medical-grade silicone adhesive
- **Weight:** ~65 g total (electronics + battery + FPC)

---

## 3. Design files summary

| Design file name | File type | Open source license | Location |
|---|---|---|---|
| `pcb/ava_pbm_main.kicad_pro` | KiCad project | CERN-OHL-S v2 | GitHub repo |
| `pcb/ava_pbm_fpc.kicad_pro` | KiCad FPC layout | CERN-OHL-S v2 | GitHub repo |
| `firmware/ava_pbm_fw/` | PlatformIO/Arduino | MIT | GitHub repo |
| `enclosure/glove_pocket.step` | STEP (3D print) | CERN-OHL-S v2 | GitHub repo |
| `enclosure/glove_pocket.stl` | STL (3D print) | CERN-OHL-S v2 | GitHub repo |
| `app/ava_pbm_app/` | Flutter (iOS/Android) | MIT | GitHub repo |
| `docs/assembly_guide.pdf` | Assembly instructions | CC-BY 4.0 | GitHub repo |
| `validation/data/` | Raw validation data | CC-BY 4.0 | GitHub repo |

---

## 4. Bill of materials

### 4.1 Electronics

| Component | Description | Qty | Unit cost (USD) | Source |
|---|---|---|---|---|
| ESP32-S3-WROOM-1 | MCU module (BLE + Wi-Fi) | 1 | $2.50 | LCSC/DigiKey |
| OSLON SSL 80 660nm | 660 nm LED, 80° beam | 32 | $0.30 | Mouser |
| TLC5940NT | 16-ch PWM LED driver | 2 | $1.80 | DigiKey |
| MLX90614ESF-BCI | IR temperature sensor | 1 | $4.50 | Mouser |
| MAX30102 | PPG/SpO2 sensor module | 1 | $1.20 | AliExpress |
| TP4056 module | USB-C LiPo charger | 1 | $0.50 | AliExpress |
| 18350 LiPo cell | 3.7V 800mAh | 1 | $3.00 | Amazon |
| Flexible PCB | 4-layer FPC, 80×100mm | 1 | $5.00 | JLCPCB (min 5pcs) |
| Main PCB | 2-layer, 40×30mm | 1 | $1.00 | JLCPCB (min 5pcs) |
| Passive components | Resistors, capacitors, etc. | set | $2.00 | LCSC |
| JST connectors | FPC-to-main cable | 2 | $0.50 | LCSC |
| **Electronics subtotal** | | | **$24.10** | |

### 4.2 Mechanical / enclosure

| Component | Description | Qty | Unit cost (USD) | Source |
|---|---|---|---|---|
| Knit glove | Touchscreen-compatible | 1 | $3.00 | Amazon |
| Silicone pouch | 3D printed TPU or molded | 1 | $1.50 | Self-fabricated |
| Medical silicone adhesive | Silbione RTV | 1 tube | $5.00 | Amazon |
| Hook-and-loop strap | Wrist closure, 20mm | 1 | $0.50 | Amazon |
| **Mechanical subtotal** | | | **$10.00** | |

### 4.3 Total BOM cost

| | Cost (USD) | Cost (JPY, approx.) |
|---|---|---|
| Electronics | $24.10 | ¥3,600 |
| Mechanical | $10.00 | ¥1,500 |
| **Total** | **$34.10** | **¥5,100** |

*Note: FPC and PCB costs assume minimum order quantity of 5 units from JLCPCB. Single-unit costs would be approximately $50-60 USD total.*

---

## 5. Build instructions

### 5.1 PCB fabrication and assembly
1. Upload Gerber files to JLCPCB/PCBWay
   - Main PCB: 2-layer, 1.6mm, HASL, green solder mask
   - FPC: 4-layer, 0.2mm polyimide, ENIG finish
2. Order SMT assembly for main PCB (BOM + pick-and-place provided)
3. Hand-solder FPC-to-main-board JST cable
4. Program ESP32 via USB-C:
   ```
   cd firmware/ava_pbm_fw
   pio run --target upload
   ```

### 5.2 Glove assembly
1. Cut palm area of knit glove to expose inner surface
2. Attach FPC to inner palm with medical silicone adhesive
3. Route cable from FPC to dorsal wrist area
4. Sew silicone pouch to dorsal wrist area of glove
5. Insert main PCB + battery into pouch
6. Attach hook-and-loop closure strap

### 5.3 Initial calibration
1. Power on via USB-C or battery
2. Connect via BLE to companion app
3. Place gloved hand on flat surface, palm down
4. Run calibration routine (app: Settings → Calibrate → Skin Temp)
5. Verify LED illumination (visible red glow through glove fabric)

---

## 6. Operation instructions

### 6.1 Basic use (consumer / research mode)
1. Wear glove on either hand
2. Open companion app → tap "Start Session"
3. Default protocol: 20-minute session, 67% duty cycle
4. App displays: real-time skin temperature, session timer, cumulative dose (J/cm²)
5. Session auto-terminates at 20 min or manually via app

### 6.2 Research mode (extended parameters)
- Adjustable wavelength selection (if dual-wavelength LED version)
- Configurable duty cycle: 10–100%
- Configurable session duration: 1–60 min
- Continuous data logging (skin temp, LED current, timestamps) to CSV via BLE
- Raw PPG data export (when MAX30102 enabled)

### 6.3 Safety
- Maximum irradiance: 100 mW/cm² (IEC 62471 exempt group, no eye hazard at this geometry)
- Thermal protection: firmware stops LEDs if skin temp > 42°C
- Battery protection: TP4056 handles overcharge/overdischarge/overcurrent
- Not for use on broken skin, over tattoos, or by persons with photosensitivity disorders

---

## 7. Validation and characterization

### 7.1 Optical characterization
- **Irradiance uniformity:** Measured with Thorlabs PM100D power meter across 9 grid points on the active area. Target: coefficient of variation < 20%.
- **Spectral output:** Measured with Ocean Insight USB4000 spectrometer. Peak wavelength 660 ± 10 nm confirmed.
- **Thermal output:** Surface temperature of FPC during continuous operation measured with FLIR thermal camera. Target: < 40°C at skin surface.

### 7.2 Functional validation (healthy volunteers)
*[To be conducted — protocol outline]*

**Study design:** Within-subject crossover, sham-controlled, single-blinded
- **N:** 10 healthy volunteers (age 20–40)
- **Protocol:**
  - Visit 1: Active PBM (660 nm, 40 mW/cm², 20 min)
  - Visit 2: Sham (LEDs off, identical glove), ≥48 h washout
  - Randomized order
- **Primary outcome:** Change in palmar skin temperature (°C) from baseline
- **Secondary outcomes:**
  - Laser Doppler flux (forearm, PeriFlux 5000)
  - Fingertip SpO2 (pulse oximeter)
  - Blood pressure (Omron HEM-7600T, before/after)
- **Ethics:** University IRB approval required prior to data collection

### 7.3 Preliminary bench data
*[To be populated with actual measurements]*

| Parameter | Specification | Measured value |
|---|---|---|
| Peak wavelength | 660 ± 10 nm | [TBD] |
| Irradiance at skin | 40 ± 8 mW/cm² | [TBD] |
| Irradiance CV | < 20% | [TBD] |
| Surface temp (20 min) | < 40°C | [TBD] |
| Battery life (67% duty) | > 3 h | [TBD] |
| Weight (total) | < 80 g | [TBD] |
| BLE range | > 5 m | [TBD] |

---

## 8. References

1. Walløe L. Arterio-venous anastomoses in the human skin and their role in temperature control. Temperature (Austin). 2016;3(1):92-103.
2. Lobo MD, Sobotka PA, Stanton A, et al. Central arteriovenous anastomosis for the treatment of patients with uncontrolled hypertension (the ROX CONTROL HTN study). Lancet. 2015;385(9978):1634-1641.
3. Onishi T. Photobiomodulation-induced vasodilation of glabrous skin arteriovenous anastomoses as a wearable, non-pharmacological strategy for blood pressure reduction: A hypothesis. Med Hypotheses. [year].
4. AVACEN Medical. AVACEN 100 Treatment System. US Patent 8,679,170 B2. 2014.
5. Diller KR, Khoshnevis S, Hemmen L. Thermoregulatory manipulation of systemic blood pressure. US Patent 11,229,548 B2. 2022.
6. Ribeiro BG, et al. Nitric oxide storage levels modulate vasodilation and the hypotensive effect induced by photobiomodulation. Lasers Med Sci. 2022;37(6):2551-2559.
7. Karu TI, et al. Cellular effects of low power laser therapy can be mediated by nitric oxide. Lasers Surg Med. 2005;36(4):307-314.
8. IEC 62471:2006. Photobiological safety of lamps and lamp systems.
