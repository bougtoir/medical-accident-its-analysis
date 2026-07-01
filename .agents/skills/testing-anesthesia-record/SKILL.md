---
name: testing-anesthesia-record
description: Test the anesthesia record chart pipeline end-to-end. Use when verifying chart rendering, fee calculation, drug master config, or output event changes.
---

# Testing Anesthesia Record

## Overview
The anesthesia-record module is a Python library (no web UI) for generating hospital-format anesthesia charts. All testing is shell-based.

## Quick Test Commands
```bash
cd anesthesia-record
python -m pytest -q          # 29 tests expected
ruff check .                 # lint
python demo.py               # E2E: generates demo_chart.png + demo_chart_erga.png
```

## Key Test Areas

### 1. Chart Rendering (`chart_erga.py`)
- Drug lanes: category sort order, color from `drug_master.yaml`, cumulative display
- Fluid lanes: `remaining_ml_start`/`remaining_ml_end` display
- Output bowling: gauze(g)/suction(cc)/urine(cc) with diff+cumulative and right-side totals
- 4-pane info section: cost(drugs+anesthesia) | events | time | post-op orders
- Vital signs: HR/BP on left axis, SpO2/Temp on right axis (inside ticks, no overlap)
- Floating latest panel: must be in front of twin axes

### 2. Anesthesia Fee Calculation (`anesthesia_fee.py`)
- Time-based billing with bracket crossing (e.g. 2h threshold for GA)
- Exclusivity rules: same category = only highest billed (e.g. spinal vs epidural)
- Position surcharges: lateral(100), prone(200), lithotomy(100), sitting(150)
- Severity surcharges: multiplier-based (e.g. 1.5x) and additional_points-based
- Config loaded from `data/anesthesia_fee.yaml`

### 3. Drug Master Config (`data/drug_master.yaml`)
- `color` field for drug line rendering
- `display_order` field for lane sort priority
- `category` field for grouping (fluid category goes to bottom)

### 4. PyInstaller Packaging
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "data:data" --name anesthesia_demo demo.py
./dist/anesthesia_demo  # should produce both chart PNGs
```

## Adversarial Edge Cases for Fee Calculation
```python
from anesthesia_record.anesthesia_fee import *
from datetime import datetime, timedelta

config = load_anesthesia_fee("data/anesthesia_fee.yaml")
t0 = datetime(2026, 6, 30, 9, 0)

# Exclusivity: spinal+epidural -> only spinal (higher)
# Time bracket: 3h GA -> 2h@900/30min + 1h@600/30min = 4800
# Nerve block: base_points=450, no time fee
# Emergency: additional_points=500 (not multiplier)
# GA+NB concurrent: both billed (different categories)
# Prone position: 200 points per case
```

## Common Issues
- Font warning "Failed to find font weight bold" is cosmetic (IPAGothic limitation), not an error
- Right axis tick labels may overlap if pad values aren't staggered per axis offset
- Drug name text at y=1.7 (above axes) to avoid overlap with infusion lines
- Cumulative text at y=1.7 right-aligned to avoid overlap with grid lines

## Devin Secrets Needed
None. This is a standalone Python library with no external services.
