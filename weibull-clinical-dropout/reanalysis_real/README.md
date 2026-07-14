# TB LTFU Weibull re-analysis — real data only (A1-min)

Reproducible re-analysis that **replaces the earlier hard-coded TB results**
(which were not derived from any real curve) with fits to genuinely digitized,
published time-to-event curves. See `data/SOURCES.md` for provenance.

## Pipeline (one command)

```bash
pip install numpy pandas scipy pillow matplotlib
make            # or: bash run.sh
```

Steps:
1. `scripts/digitize.py` — extract curve pixels from `data/figures/*` →
   `data/*_ltfu_cif.csv` (with axis calibration verified at runtime).
2. `scripts/fit_weibull.py` — fit F(t)=1−exp(−(t/λ)^k); bootstrap CI for k;
   compare with exponential & log-normal by AIC → `results/weibull_fits.csv`.
3. `scripts/make_figures.py` — `figures/weibull_real_fits.png` from the CSVs.

No result numbers are hard-coded; everything regenerates from the figures.

## Headline finding (honest)

The two real datasets show **opposite** LTFU hazard shapes: Ethiopia's 6-month
competing-risk CIF accelerates (k>1, IFR) whereas China's 12-month all-patient
retention is strongly front-loaded (k<1, DFR). The fitted values are written by
the pipeline to `results/weibull_fits.csv` and summarised in
`results/SUMMARY.md` (source of truth — not restated here to avoid hard-coding).

→ The original manuscript's central claim that TB treatment LTFU uniformly
shows an **increasing** hazard (k≈1.22–1.31 across five countries) is **not
reproduced** in real data.

## Limitations
- Only 2 datasets; no India/South Africa/Brazil curve met the inclusion bar.
- Aggregate published curves, not individual patient data.
- Digitization error; China x-axis mildly non-uniform near 12 mo.
- Ethiopia is a **competing-risk subdistribution** CIF; k describes the
  subdistribution-hazard shape, not the cause-specific hazard.
- Different outcome definitions/time windows (6 vs 12 mo) limit direct
  cross-country comparison.
