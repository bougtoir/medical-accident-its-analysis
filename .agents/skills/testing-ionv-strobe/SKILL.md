---
name: testing-ionv-strobe
description: Test the IONV STROBE manuscript build pipeline end-to-end. Use when verifying flowchart generation, editable PPTX output, manuscript docx, or data consistency changes in yago_ionv.
---

# Testing: IONV STROBE Manuscript Pipeline

## Prerequisites

- Python 3.12+ with python-pptx, python-docx, numpy, pandas, scipy, matplotlib, statsmodels
- Data file: `yago_ionv/yago.xlsx` (source data, already in repo)
- No secrets or credentials needed

## Quick Start

```bash
cd /home/ubuntu/repos/wip/yago_ionv

# Step 1: Run analysis (generates stats JSON + CSV tables)
python3 analysis_def_e.py
python3 analysis_excl_sensitivity.py

# Step 2: Generate flowchart (produces fig_flowchart.png + flowchart_counts.json)
python3 create_flowchart.py

# Step 3: Generate manuscript (produces manuscript_strobe.docx with inline figures)
python3 create_manuscript_strobe.py

# Step 4: Generate editable PPTX (produces figures_strobe.pptx)
python3 create_pptx_strobe.py
```

## Expected Outputs

| File | Description | Expected Size |
|------|-------------|---------------|
| `flowchart_counts.json` | N-in/N-out flow data | > 500 bytes |
| `figures_strobe/fig_flowchart.png` | STROBE flowchart image | > 100KB |
| `manuscript_strobe.docx` | Japanese manuscript with inline figures | > 100KB |
| `figures_strobe.pptx` | Editable PPTX (7 slides, zero PNGs) | > 10KB |
| `def_e_stats.json` | Full cohort statistics | > 1KB |
| `excl_sensitivity_stats.json` | Subgroup statistics | > 1KB |

## Key Verification Checks

### 1. Flowchart N Counts Arithmetic

Parse `flowchart_counts.json` and verify:
- total(3479) - excluded(236) = eligible(3243)
- eligible(3243) - preop_antiemetic(55) = primary_analysis(3188)
- primary_analysis(3188) - sensitivity_excluded(2525) = subgroup_analysis(663)
- At each level: n_s + n_t == n (singleton + twin = total)

### 2. PPTX Editability (Zero PNG Embeds)

This is the most critical check. The PPTX must contain only editable shapes and native charts, never embedded PNG/JPG images.

```python
from pptx import Presentation
prs = Presentation("figures_strobe.pptx")
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        assert shape.shape_type != 13, f"Slide {i+1} has embedded picture!"
```

Expected slide structure:
- Slide 1 (Flowchart): ~20+ editable shapes (MSO_SHAPE rectangles, arrows, textboxes)
- Slide 2 (Bar chart): Native PowerPoint chart (has_chart=True)
- Slides 3-5, 7 (Forest plots): Editable shapes (rectangles for CI lines, diamonds for point estimates)
- Slide 6 (Bar chart): Native PowerPoint chart (has_chart=True)

### 3. Chart Data vs Source JSON

Extract chart series values from Slides 2 and 6 and compare against `def_e_stats.json` and `excl_sensitivity_stats.json` respectively. Tolerance: ±0.1 percentage points.

### 4. Forest Plot Annotations

On Slide 4 (Broad vs Narrow comparison), verify text shapes contain:
- aOR values: "3.18" (narrow-definition), "0.92" (broad-definition)
- P values: "0.007", "0.624"

### 5. Manuscript Content

- At least 5 inline images in docx
- References to Fig. 1 through Fig. 7 and Table 1 in text
- "STROBE" mentioned in text

### 6. Terminology Compliance

Per user instruction, outputs must NOT contain "定義E", "Definition E", or "Def E". Instead use:
- Japanese: "制吐薬（狭義）" or "制吐薬（狭義）：5-HT3受容体拮抗薬"
- English (figures): "Narrow-definition antiemetic" or "5-HT3 antagonist"

```python
# Check both PPTX and docx for forbidden terms
for term in ["定義E", "Definition E", "Def E"]:
    assert term not in pptx_text, f"Found forbidden term: {term}"
    assert term not in docx_text, f"Found forbidden term: {term}"
```

## Data Flow

```
yago.xlsx
  → analysis_def_e.py → def_e_stats.json + tables_e/*.csv + figures_strobe/fig_*.png
  → analysis_excl_sensitivity.py → excl_sensitivity_stats.json + tables_excl/*.csv + fig_excl_*.png
  → create_flowchart.py → flowchart_counts.json + fig_flowchart.png
  → create_manuscript_strobe.py → manuscript_strobe.docx (reads all JSON/PNG above)
  → create_pptx_strobe.py → figures_strobe.pptx (reads JSON/CSV, generates editable objects)
```

## Known Issues

- Forest plot CI lines for extreme confidence intervals (e.g., aOR 106) might be clipped at the chart boundary. This is expected behavior.
- The subgroup analysis (n=663) has very few events (8 for narrow-definition IONV), resulting in wide confidence intervals (aOR 1.74–106.04). The CIs are correct but visually may appear extreme.
- Editable PPTX forest plots use MSO_SHAPE.RECTANGLE for CI bars and MSO_SHAPE.DIAMOND for point estimates. These might need manual color/size adjustment in PowerPoint for publication quality.

## Devin Secrets Needed

None — this is a local analysis and build workflow with no external service dependencies.
