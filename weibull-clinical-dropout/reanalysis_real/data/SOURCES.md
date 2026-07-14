# Data sources & provenance (A1-min, real data only)

Every value in this sub-project is derived from published figures by the
digitizer in `scripts/digitize.py`. No estimates are hard-coded. Original
figure images are stored under `data/figures/`.

## Ethiopia
- Citation: Ambo General Hospital DR-TB / TB treatment cohort, *Archives of
  Public Health* 2023.
- PMCID: **PMC10290796**  · DOI: 10.1186/s13690-023-01130-2
- Figure: **Fig. 1a** ("Type of event"), **red** curve = *Loss to follow up*
  competing-risk **cumulative incidence** (blue = death, competing event).
- x-axis: Time in months (0–6, DS-TB treatment window). y-axis: Cumulative
  incidence (0–0.20).
- File: `data/figures/ethiopia_PMC10290796_fig1_cif.png`
  (source: media.springernature.com, open access, CC BY).
- Extracted: `data/ethiopia_ltfu_cif.csv` (competing-risk **subdistribution**;
  fit interpreted as subdistribution-hazard shape, not cause-specific hazard).

## China
- Citation: Five-year retrospective TB cohort (n=24,265), *Frontiers in
  Medicine* 2023.
- PMCID: **PMC10167013**  · DOI: 10.3389/fmed.2023.1136094
- Figure: **Fig. 3**, **"All TB patients"** (salmon) Kaplan–Meier curve.
  y-axis: *Probability of being non-LTFU* (retention S(t)); x-axis: Duration of
  anti-TB treatment, 0–12 months. Stored as F(t)=1−S(t).
- File: `data/figures/china_PMC10167013_fig3_km_nonLTFU.jpg`
  (source: frontiersin.org, open access, CC BY).
- Extracted: `data/china_ltfu_cif.csv`.

## Calibration
- Axis calibration anchors (pixel↔data) in `scripts/digitize.py` were read from
  the tick marks of each figure and are cross-checked at runtime against
  `detect_axis()`/`xticks()` output (printed). Curve **values** are extracted
  from the coloured pixels of each curve, not entered by hand.
- China x-axis tick spacing is mildly non-uniform near 12 mo in the source
  render; a piecewise map through the labelled ticks (0,3,6,9,12) is used.

## Sources considered but NOT used
- Original manuscript's five national-programme citations (Tola 2019, Kaplan
  2014, Parmar 2015, Lacerda 2014, Li 2018): none provide a time-resolved
  DS-TB LTFU curve matching the claimed populations — see
  `../../DATA_INTEGRITY_AUDIT.md` and `tb_weibull_data_source_audit.md`.
- Brazil PMC12219442: outcome is a **composite** "unfavorable outcome"
  (death+failure+LTFU), not pure LTFU — excluded pending separation.
- India / South Africa: no suitable open-access DS-TB LTFU time curve found.
