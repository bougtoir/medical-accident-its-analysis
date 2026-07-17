# What zeroing cannot fix — Blood Pressure Monitoring submission

Reproducible simulation study and manuscript for *Blood Pressure Monitoring*:
**"What zeroing cannot fix: detecting residual gain and dynamic-response
errors after zero calibration in invasive arterial pressure monitoring."**

Zero calibration of an invasive arterial pressure transducer removes the
direct-current (DC) offset but not sensor-gain (scale) error. This project
uses a **fully synthetic, seeded simulation** to quantify which of the
analyses commonly reported in device-validation studies actually detect a
residual gain error after zeroing, and to characterise the frequency-dependent
dynamic-response (damping) error.

> All data in this repository are **simulated**, not measured in patients or
> taken from published clinical datasets.

## Reproducing everything

```bash
pip install -r requirements.txt
python3 scripts/build_all.py      # or: make all
```

This regenerates, in order:

1. `data/*.csv` — synthetic static, dynamic and range-dependence datasets
2. `results/*.csv`, `results/summary.json` — machine-readable metrics
3. `figures/*.png` (English) and `figures/ja/*.png` (Japanese); `figures/tiff/*.tif` (English, 300 dpi, for journal submission as separate files)
4. `manuscripts/BPM_ZeroFree_Manuscript_EN.docx` / `_JA.docx`
5. `manuscripts/BPM_Tables_EN.docx` — editable tables
6. `manuscripts/BPM_Figures_EN.pptx` — editable figure deck
7. `cover_letter/BPM_Cover_Letter_EN.docx`

Every number, table and figure in the manuscripts is read from
`results/summary.json`; **no results are hard-coded** in the manuscript
generators.

## Layout

| Path | Contents |
|------|----------|
| `src/methods.py` | Pure statistics/signal functions (CCC, Bland–Altman + proportional-bias regression, Deming, Passing–Bablok, second-order dynamic response) |
| `src/simulate.py` | Seeded synthetic data generation |
| `src/analyze.py` | Consumes `data/`, writes `results/` |
| `src/figures.py` | Figures from `data/` + `results/` (EN + JA) |
| `scripts/manuscript_common.py` | Vancouver citation manager + results loader |
| `scripts/create_bpm_docx_en.py` / `_ja.py` | Manuscript generators |
| `scripts/create_tables_docx_en.py` | Editable tables |
| `scripts/create_figures_pptx_en.py` | Editable figure deck |
| `scripts/create_bpm_cover_letter.py` | Cover letter |
| `scripts/build_all.py` | One-command pipeline |

## Method summary

- **Static scenarios** (n per scenario fixed in `src/simulate.py`): offset
  only, ideal zeroing, uncompensated gain error, and a gain error masked by a
  compensating offset.
- **Analyses**: mean bias + limits of agreement, Bland–Altman
  difference-versus-mean regression, Deming and Passing–Bablok regression, and
  Lin's CCC with decomposition into precision (r), bias-correction factor
  (C_b), location shift (u) and scale shift (v).
- **Dynamic scenarios**: synthetic arterial waveforms passed through optimal,
  under-damped and over-damped second-order catheter–transducer models;
  fast-flush parameters (natural frequency, damping) are the direct diagnostic.
- **Range-dependence**: one fixed device sampled over pressure ranges of
  increasing width to illustrate CCC range-dependence.
