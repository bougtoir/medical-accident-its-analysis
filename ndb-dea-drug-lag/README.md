# New-treatment anticipation and practical drug lag: the hepatitis C DAA transition in Japan's NDB Open Data

Does a newly reported / newly reimbursed treatment actually pull patients off the
prior standard therapy at the population level? If new-treatment anticipation
("待望論") is real and population-wide, the count receiving the *old* standard
therapy should fall sharply once the awaited option arrives. If nothing changes,
either the anticipation/practical lag does not exist, or the decision-makers who
choose therapy are not reacting to the news.

We test this with a natural experiment where substitution is nearly complete:
**chronic hepatitis C**, where interferon (IFN)-based therapy was the standard of
care until interferon-free **direct-acting antivirals (DAAs)** arrived in Japan in
2014-2015.

## Data
- **NDB Open Data** (National Database of Health Insurance Claims), editions 1-10,
  covering fiscal years **FY2014-FY2023**. Source: MHLW,
  https://www.mhlw.go.jp/ndb/opendatasite/
- Tables used: 処方薬 「性年齢別薬効分類別数量」 (内服/外用/注射 × 外来院内・外来院外・入院).
- Metric: **総計 (処方数量)** = national dispensed quantity per drug (tablets/capsules
  for oral drugs; pre-filled syringes/vials for injections). This is *not* a patient
  count; quantities are comparable within a product over time but are not additive
  across products with different dosage units.

Drug groups (identified from the real drug names present in the files):
- **IFN-based standard therapy** — peginterferon (ペガシス, ペグイントロン),
  ribavirin (レベトール, コペガス); conventional interferon (スミフェロン, フエロン,
  イントロンA) reported separately as it is not HCV-specific.
- **DAAs** — 12 products: sofosbuvir, ledipasvir/sofosbuvir, daclatasvir,
  asunaprevir, glecaprevir/pibrentasvir, sofosbuvir/velpatasvir, elbasvir,
  grazoprevir, ombitasvir/paritaprevir/ritonavir, telaprevir, simeprevir, vaniprevir.

## Headline findings
- Peginterferon dispensing fell **-99.2%** from FY2014 to FY2023; ribavirin reached
  ~0 by **FY2018**. The IFN-based standard therapy effectively disappeared within
  ~2 years of interferon-free DAAs becoming available.
- Total DAA dispensing **peaked in FY2015** (+158% vs FY2014), then fell **-92%** to
  FY2023. This surge-then-decay is the signature of a finite stock of long-waiting
  patients being cured in a burst (pent-up demand / "待望論"), rather than a steady
  replacement flow.
- Interpretation: for HCV DAAs there was no population-level practical lag — the
  decision-makers reacted rapidly to approval/reimbursement, and anticipated demand
  was realized quickly.

Formal trend models with uncertainty intervals (`results/its_summary.json`): because
NDB begins in FY2014 (coincident with IFN-free DAA launch) there is no internal
pre-intervention baseline and a conventional pre/post interrupted time series is not
identifiable, so with n=10 annual points we fit descriptive trend models. Peginterferon
declined **~36%/yr** (95% CI ~24-47%), ribavirin **~76%/yr**, conventional IFN **~25%/yr**;
total DAA dispensing fell **~25%/yr** after the FY2015 peak (segmented log-linear
regression, post- vs pre-peak slope change P≈0.003). Intervals are Newey-West (HAC)
and residual-bootstrap based.

All numbers above are regenerated into `results/summary.json` and
`results/its_summary.json`; do not hard-code.

## "News / announcement" side (`data/announcement_events.csv`)
Primary intervention markers are official **NHI drug-price listings (薬価収載)** and
**PMDA approvals**, supplemented by major press coverage:
1. **2014-07** daclatasvir + asunaprevir approved — world-first all-oral,
   IFN/ribavirin-free regimen for chronic hepatitis C (Bristol-Myers Squibb).
2. **2015-05 / 2015-08** sofosbuvir (Sovaldi) / ledipasvir-sofosbuvir (Harvoni),
   widely reported as near-100%-cure regimens — the core anticipation moment.
3. **2017-11** glecaprevir/pibrentasvir (Maviret), pangenotypic.

(Exact approval/listing dates are being finalized against PMDA / Chuikyo records.)

## Reproduce
```bash
python3 scripts/download_ndb.py      # fetch raw NDB workbooks into data/ndb_raw/
python3 scripts/build_dataset.py     # -> data/target_drugs_long.csv, hcv_timeseries.csv, hcv_product_timeseries.csv
python3 scripts/analyze.py           # -> results/summary.json
python3 scripts/its_analysis.py      # -> results/its_summary.json (trend models + 95% intervals)
python3 scripts/make_figures.py --lang en
python3 scripts/make_figures.py --lang ja
python3 scripts/make_manuscript.py   # -> output/ JA+EN manuscript docx, table docx, figure pptx
```

## Limitations
- NDB Open Data begins in FY2014, the same period IFN-free DAAs launched, so there is
  no pre-DAA IFN baseline *within* NDB; the FY2014 value already reflects decline from
  the pre-2014 peak.
- The metric is dispensed quantity, not patient counts; units differ across products,
  so summed DAA quantity is not a patient count.
- Annual resolution only (no within-year interrupted time series); reported trend
  rates carry wide uncertainty intervals given the small number of annual
  observations (n=10), and there is no control condition or placebo event.
- Descriptive evidence only: consistent with population-level anticipation, but does
  not establish that media coverage caused individual treatment choices.
