# Healthcare tempo-effect PoC — sustainable healthcare spending composition

A sister subproject to [`gdp_tempo_poc`](../gdp_tempo_poc) that transfers the
same **tempo effect + forgotten parameter (σ)** framework — originally from
the population-demography paper, extended to GDP — to the question of
**sustainable healthcare expenditure composition**.

## Core hypothesis

Current-period health outcomes (life expectancy, healthy life expectancy,
age-specific mortality) are measured as **period indicators**, but they
reflect an underlying **stock of health capital** built up from many past
periods of spending, prevention, and accumulated medical knowledge. The
analogy to the GDP paper:

| Population paper | GDP paper | Healthcare paper |
|---|---|---|
| AFB shift → period TFR biased | Investment-to-output lag μ(t) drifts → period GDP biased | Healthcare spend → outcome lag μ_H(t) drifts → period health outcomes biased |
| σ (fertility dispersion) forgotten | Intangible capital forgotten | Health-capital components forgotten (prevention ≠ treatment, R&D, long-term care infrastructure) |
| Same-living population | Same-working population | Same-healthy population (effective labour-capable population, age-adjusted) |

The practical question: **can a country achieve the same health outcomes at
lower cost by shifting the composition of spending toward stock-building
items (prevention, R&D, long-term care infrastructure) versus flow-heavy
curative expenditure?** The tempo framework predicts that countries with
faster drift of the outcome-lag μ_H (indicating spending not translating to
outcomes in the current period) are under-investing in the stock components.

## Three-candidate structure (mirrors GDP PoC)

### Candidate A-H: Spending-to-outcome tempo
- Build **health-capital stock** `H(t+1) = (1-δ_H) H(t) + Σ w_s(μ_H) E(t-s)` where `E(t)` is
  current health expenditure (from WB SH.XPD.CHEX.GD.ZS scaled by GDP)
- Test whether life expectancy and healthy-life-expectancy fit improve when
  μ_H is (M0) zero — flow only, (M1) constant per country, (M2) time-varying
  μ_H(t) = μ_H0 + μ_H1 · (year − t0)

### Candidate B-H: Same-healthy population (demographic tempo of care)
- Ageing shifts the population's care needs; "effective care-days" depends on
  age-specific morbidity.
- Build effective-care-need index `N_H(t) = Σ_a w(a, t) · N_a(t)` where w(a,t)
  is age-specific morbidity weight that itself drifts.

### Candidate D-H: Forgotten health-capital components
- Decompose health spending into four buckets: curative, preventive, R&D,
  long-term care / infrastructure.
- `H_total = H_cur + λ_p H_prev + λ_R H_R&D + λ_L H_LTC` where λ parameters
  represent the outcome-contribution multiplier of non-curative items.
- Analogous to intangible capital in GDP: the "forgotten" buckets carry
  systematically larger multipliers than their expenditure share.

## Outcome variable candidates

- Life expectancy at birth (WB SP.DYN.LE00.IN) — baseline
- Healthy life expectancy (WHO GHO) — preferred if available
- Age-adjusted mortality (WB SP.DYN.AMRT.MA / .FE)

## Data sources (planned)

- **WB WDI**: current health expenditure (% GDP, PPP), life expectancy,
  mortality by age & sex, public vs. private health spending split
- **OECD Health Statistics** (SDMX): spending by function (HC.1 curative,
  HC.6 prevention, HC.3 long-term care, HC.R R&D), healthy life years
- **WHO GHO**: healthy life expectancy, DALYs per capita

## Minimum PoC (this branch)

The minimum reproducible PoC (scripts below) runs Candidate A-H (spending-lag
tempo) across a subset of OECD countries using only WB public data to
demonstrate the framework. Full three-candidate analysis requires OECD SHA
spending-by-function breakdowns (not freely scrape-able via API without
authentication) — that is scoped for a follow-up PR.

## Files (as of this initial commit)

- `reports/concept_note.md` — longer writeup of the framework, links to the
  GDP paper's results and how they extend to healthcare policy.
- `scripts/fetch_wb_health.py` — fetches WB health indicators to
  `/home/ubuntu/healthcare_tempo_data/wb/`.
- `scripts/run_poc_AH.py` — minimum demonstrator: Candidate A-H only.
- `data/` — outputs from the PoC.
- `figures/` — charts.

Not yet filled: Candidate B-H, D-H implementations (pending OECD/SHA data).

## Reproduce

```bash
cd healthcare_tempo_poc
python scripts/fetch_wb_health.py
python scripts/run_poc_AH.py
```

## Connection to the "flow + stock unified accounting" message

Healthcare is the clearest single domain where the user's proposal — that
**hidden (tempo / forgotten) parameters unify flow and stock accounting** —
has practical policy implications. If health outcomes today reflect a stock
that was *accumulated differently across countries*, then:

1. Cross-country cost-effectiveness comparisons based on current spending
   are systematically biased — the low-spender today may be living off stock
   built decades ago.
2. The sustainability frontier is defined by the **stock maintenance
   requirement**, not by this-period expenditure.
3. Countries with negative μ_H drift (outcomes deteriorating relative to
   spending) are effectively **decumulating health stock**, a signal
   invisible to period indicators.

The GDP PoC showed that an analogous diagnostic works for economic growth.
This sister project operationalises it for healthcare.
