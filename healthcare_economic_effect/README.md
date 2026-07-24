# Evaluating Healthcare Expenditure Sustainability in Japan

A dual-return framework that reframes healthcare spending from a "cost to be
contained" to an activity with measurable, but bounded, economic returns.
This repository contains the complete, executable analysis code and input
data underlying the manuscript submitted to *Environmental Health and
Preventive Medicine* (EHPM-D-26-00106R1) and **supersedes the earlier
minimum proof-of-concept**: every quantitative result in the manuscript can
be regenerated from a clean clone.

## Core framework

Healthcare expenditure is simultaneously a **cost** and an **economic
effect**. The analysis integrates:

1. **Input-Output (I-O) multipliers** -- healthcare spending as demand
   stimulus. We distinguish **output multipliers** (total output per unit of
   final demand; upper bound) from **value-added multipliers** (GDP
   contribution; conservative lower bound).
2. **Fiscal return ratio** -- FR = (tau * m) / pf, the induced tax revenue
   from the demand-side multiplier relative to the public financing share,
   reported under progressively conservative treatments (import leakage,
   deficit financing, value added).
3. **Health-capital tempo model** -- a spending-to-outcome lag estimated from
   public World Bank data (39 countries, 2000-2019), with full model
   selection (level RMSE, change RMSE, LOOCV RMSE, AIC, BIC).
4. **Equipment stock & import leakage** -- Japan's diagnostic imaging density
   (~170.9 CT+MRI/million) as a health-capital asset, and import leakage
   reducing the effective multiplier.

## Key results (reproducible)

- **Fiscal return, Japan.** Under the gross output multiplier the ratio is
  **1.09**; import-leakage-adjusted **1.04**; **deficit-adjusted 0.67**
  (crediting only the non-deficit part of the return against full public
  cost, delta = 0.35); value-added **0.60**. The economic return is
  **material and near break-even**, robust in direction, but does not by
  itself prove unconditional self-financing under conservative treatments.
- **Tempo lag (robust).** Introducing a spending-to-outcome lag (M1) improves
  fit over the flow-only model (M0): median level RMSE 0.253 -> 0.208, LOOCV
  0.304 -> 0.250; M1 is favoured over M0 by AIC/BIC/LOOCV in **64%/64%/69%**
  of countries. Median constant lag ~2 years.
- **No stable tempo drift.** The time-varying model (M2) is **not** favoured
  over M1 by AIC or BIC in any country (**0%/0%**); the drift parameter is
  poorly identified (grid-boundary dominated, median -0.10 yr/yr). M2 is
  reported as exploratory only.

> **Correction note (R2).** A previous revision reported RMSE values of
> 0.510/0.441/0.434 and a positive drift of +0.15 yr/yr. Those values were
> traced to a 2000-2023 sample that inadvertently included the 2020-2022
> COVID-19 mortality shock; running the identical code over 2000-2023
> reproduces them exactly. The manuscript specifies the 2000-2019
> pre-pandemic period, and all results here use that period.

## Reproduce

```bash
cd healthcare_economic_effect
pip install numpy pandas matplotlib python-docx python-pptx

# 1. (optional) refresh the World Bank inputs from the live API.
#    A committed subset already ships in data/wb, so this is only needed
#    to update the data; the analysis runs offline without it.
python scripts/fetch_wb_health.py

# 2. compute the tempo model-selection statistics (writes
#    data/tempo_model_selection.json and _bycountry.csv)
python scripts/tempo_model_selection.py

# 3. run the full economic-effect analysis (fiscal return, deficit cascade,
#    equipment/leakage, figures) -- consumes the JSON from step 2
python scripts/analyze_healthcare_economic_effect.py

# 4. build the manuscript, response letter, cover letter, and figure PPTX
python scripts/create_manuscript_ehpm_r2.py
```

`tempo_model_selection.py` resolves its World Bank cache in this order:
`$WB_DIR` if set, otherwise the committed `data/wb/`.

## Structure

```
healthcare_economic_effect/
  scripts/
    fetch_wb_health.py                      # Download WB indicators -> data/wb
    tempo_model_selection.py                # M0/M1/M2 fit + AIC/BIC/LOOCV
    analyze_healthcare_economic_effect.py   # Fiscal return, deficit cascade, figures
    create_manuscript_ehpm_r2.py            # Manuscript + response + cover + PPTX
  data/
    wb/                                     # Committed World Bank input subset
    tempo_model_selection.json              # Computed model-selection summary
    neutral_sustainability.csv              # Fiscal-return table (Table 2)
    ...                                     # Other CSV/JSON outputs
  output/
    docx/     # Manuscript, response-to-reviewers, cover letter
    pptx/     # Editable English figures (1 slide per figure)
    figures/  # PNG figures (10 EN + JA variants)
  README.md
```

## Data sources

- **World Bank World Development Indicators** (SH.XPD.CHEX.PP.CD,
  SH.XPD.CHEX.GD.ZS, SP.DYN.LE00.IN): committed subset in `data/wb/`;
  refreshable via `fetch_wb_health.py`.
- **OECD Health at a Glance 2023**: CT/MRI density, workforce, financing.
- **Published I-O studies**: healthcare-sector output multipliers per country
  (see manuscript references).

## Model selection (methods summary)

For each country the life-expectancy production function
`LE(t) = a + b*ln H(t) + c*ln GDPpc(t) + e(t)` is fit under three nested
specifications of the health-capital stock `H(t)` (perpetual inventory,
delta_H = 0.10, geometric lag weights):

| Model | Lag structure | Params |
|---|---|---:|
| M0 | flow only (`H = E`) | 3 |
| M1 | constant lag `mu*` (grid 0-19 yr) | 4 |
| M2 | time-varying lag `mu0 + mu1*(year - t0)` (grid) | 5 |

LOOCV RMSE is exact for the linear model conditional on the full-sample-
selected lag structure; it is not a fully nested re-estimation of the
nonlinear lag selection inside each fold (stated as a limitation in Methods).
