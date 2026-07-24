# Data sources & provenance (real data only)

Every value in this sub-project is derived from published figures by the
digitizer in `scripts/digitize.py`. No estimates are hard-coded. Original
figure images are stored under `data/figures/`.

## Scoping search & eligibility (reproducible)
- Search tool: `scripts/search_scoping.py` queries the public Europe PMC REST
  API and writes `results/scoping_search.csv` (hit count, search date, the exact
  query string, and a transparency sample of records). Re-run with `make search`.
- Snapshot: as recorded in `results/scoping_search.csv` (Europe PMC identified
  ~7.6k open-access TB/HIV LTFU/retention records mentioning a time-to-event
  curve on 2026-07-17).
- **Eligibility criterion (deliberately unusual):** a study must present a
  *time-resolved* treatment-dropout/retention curve as a single, cleanly
  separable, digitizable line (Kaplan–Meier survivor or competing-risk
  cumulative incidence) — not merely a final cumulative LTFU proportion.
- Screening was pragmatic (single-reviewer against the criterion), **not** a
  registered dual-reviewer scoping review; the count of eligible curves is a
  lower bound. Seven infectious-disease curves (six studies) qualified: TB
  Ethiopia, TB China, ART/HIV Ethiopia, HIV Maputo (ATT + BTT), HIV Malawi,
  HIV Gambella. One non-infectious antipsychotic curve is kept separately as a
  methodological contrast, outside the infectious-disease scope.

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

## Comparators (non-TB treatment dropout, real KM curves)

### ART / HIV
- Incidence & predictors of loss to follow-up among ART patients, *J Int Assoc
  Provid AIDS Care* 2026. PMCID **PMC12953970**, DOI 10.1177/23259582261426232.
- Figure **1A** "overall" Kaplan–Meier survival estimate (time to LTFU, months);
  panel B (by cotrimoxazole) and panel C (pie) not used.
- File: `data/figures/art_PMC12953970_fig1_km_retention.jpg`
  (from SAGE supplementary package, open access). → `data/art_ltfu_cif.csv`.

### HIV/ART — Maputo, Mozambique
- Mateus A, Waldman EA. Retention and predictors of loss-to-follow-up among ART
  patients in the Test-and-Treat Era, Maputo. *BMC Infect Dis* 2026;26:667.
  PMCID **PMC13037074**, DOI 10.1186/s12879-026-12949-9.
- Figure **3**: two retention KM curves. **navy** solid = After-Test-and-Treat
  (ATT); **maroon** = Before-Test-and-Treat (BTT). y-axis: retention S(t);
  x-axis: 0–80 months. Stored as F(t)=1−S(t).
- File: `data/figures/hiv_maputo_PMC13037074_fig3_km_retention.png`
  (media.springernature.com, open access, CC BY). →
  `data/hiv_maputo_att_ltfu_cif.csv`, `data/hiv_maputo_btt_ltfu_cif.csv`.

### HIV — Malawi
- Makonokaya L, et al. Retention in HIV care before and after a case-management
  program in Malawi. *BMC Public Health* 2026;26:1615.
  PMCID **PMC13191892**, DOI 10.1186/s12889-026-27295-3.
- Figure **1**: **navy** solid = pre-intervention remaining-in-care KM (used);
  orange dashed = post-intervention (NOT used). y-axis: remaining in care S(t);
  x-axis: 0–12 months. Stored as F(t)=1−S(t). Extraction is **capped at 11.5 mo**:
  a single terminal KM step at exactly 12 mo reflects the last event with very
  few at risk and is excluded as an artefact.
- File: `data/figures/hiv_malawi_PMC13191892_fig1_km_care.png`
  (media.springernature.com, open access, CC BY). → `data/hiv_malawi_pre_ltfu_cif.csv`.

### HIV — Gambella, Ethiopia (youth transitioning to adult care)
- Dorgi A, et al. Incidence and predictors of LTFU among youth living with HIV
  transitioning to adult care, Gambella. *BMC Infect Dis* 2026;26:336.
  PMCID **PMC12903592**, DOI 10.1186/s12879-026-12596-0.
- Figure **2**: overall **navy** KM survivor curve (time-to-LTFU). x-axis is
  *analysis time* in **years (1–4)**; stored as months (×12). y-axis: survival
  S(t). Stored as F(t)=1−S(t). The plot begins at 1 year, so the window is
  **left-truncated** and the fit describes the 12–48 month range only.
- File: `data/figures/hiv_gambella_PMC12903592_fig2_km_ltfu.png`
  (media.springernature.com, open access, CC BY). → `data/hiv_gambella_ltfu_cif.csv`.

### Antipsychotic
- Time to discontinuation of the initially prescribed antipsychotic in routine
  practice, *Eur Psychiatry* 2025. PMCID **PMC12437960**,
  DOI 10.1192/j.eurpsy.2025.… (Cambridge). Figure = KM "Any antipsychotic"
  (time to discontinuation, days). **Small sample (n≈42, 38 events)** — real but
  low-powered; treated as illustrative comparator.
- File: `data/figures/antipsychotic_PMC12437960_fig_km_survival.jpg`
  (Cambridge supplementary package). → `data/antipsychotic_ltfu_cif.csv`.

## Calibration
- Axis calibration anchors (pixel↔data) in `scripts/digitize.py` were read from
  the tick marks of each figure and are cross-checked at runtime against
  `detect_axis()`/`xticks()` output (printed). Curve **values** are extracted
  from the coloured pixels of each curve, not entered by hand.
- China x-axis tick spacing is mildly non-uniform near 12 mo in the source
  render; a piecewise map through the labelled ticks (0,3,6,9,12) is used.

## Sources considered but NOT used
- Several national-programme TB retention reports (e.g. Tola 2019, Kaplan
  2014, Parmar 2015, Lacerda 2014, Li 2018) report only a final cumulative
  LTFU proportion, not a time-resolved curve that can be digitized, so none
  could be included.
- Brazil PMC12219442: outcome is a **composite** "unfavorable outcome"
  (death+failure+LTFU), not pure LTFU — excluded pending separation.
- India / South Africa: no suitable open-access DS-TB LTFU time curve found.
