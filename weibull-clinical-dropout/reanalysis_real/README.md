# TB LTFU Weibull re-analysis — real data only (A1-min)

Reproducible re-analysis that **replaces the earlier hard-coded TB results**
(which were not derived from any real curve) with fits to genuinely digitized,
published time-to-event curves. See `data/SOURCES.md` for provenance.

## Pipeline (one command)

```bash
pip install numpy pandas scipy pillow matplotlib python-docx python-pptx
make            # regenerates data CSVs, results, figure, and the short-communication docx/pptx
```

Steps:
1. `scripts/digitize.py` — extract curve pixels from `data/figures/*` →
   `data/*_ltfu_cif.csv` (with axis calibration verified at runtime).
2. `scripts/fit_weibull.py` — fit F(t)=1−exp(−(t/λ)^k); bootstrap CI for k;
   compare with exponential & log-normal by AIC → `results/weibull_fits.csv`.
3. `scripts/make_figures.py` — `figures/weibull_real_fits.png` from the CSVs.

No result numbers are hard-coded; everything regenerates from the figures.

## Headline finding (honest)

Four real, digitized curves — two TB (Ethiopia, China) and two non-TB
comparators (ART/HIV retention, antipsychotic time-to-discontinuation). Fitted
values are written to `results/weibull_fits.csv` / `results/SUMMARY.md` (source
of truth — not restated here to avoid hard-coding). Qualitatively:

- **TB is heterogeneous**: Ethiopia's 6-month competing-risk CIF accelerates
  (k>1, IFR); China's 12-month all-patient retention is strongly front-loaded
  (k<1, DFR).
- **Both comparators are DFR (k<1)**: dropout/LTFU risk is highest early then
  decelerates (ART/HIV and antipsychotic).

→ The original manuscript's central claim — TB treatment LTFU uniformly shows an
**increasing** hazard (k≈1.22–1.31 across five countries) while comparators are
DFR — is **not reproduced**. The comparators are indeed DFR, but real TB is
*not* uniformly IFR; the clean TB-vs-rest dichotomy collapses.

## Limitations
- Few datasets (2 TB, 2 comparators); India/South Africa/Brazil TB curves did
  not meet the inclusion bar.
- Aggregate published curves, not individual patient data.
- Digitization error; China x-axis mildly non-uniform near 12 mo; KM plateaus
  (administrative censoring) are sampled as flat tails.
- Ethiopia is a **competing-risk subdistribution** CIF; k describes the
  subdistribution-hazard shape, not the cause-specific hazard.
- The antipsychotic cohort is small (n≈42) — illustrative only.
- Different outcome definitions, time windows and units (months vs days) limit
  direct cross-study comparison; k (shape) is unit-free and is the comparison
  target, not lambda.
