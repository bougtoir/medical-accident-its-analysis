# AI/ML researcher mobility ODE pilot

This repository builds a reproducible OpenAlex pipeline for an AI/ML (Computer Science subfield `1702`) researcher-cohort, estimates per-civilisation transition rates, and runs a coupled linear ODE model to identify intervention priorities and point-of-no-return thresholds.

## Pipeline

1. **Data extraction** (`src/openalex_client.py`)
   - Queries `https://api.openalex.org/works` with subfield `subfields/1702` and per-civilisation country filters.
   - Uses cursor pagination, on-disk cache in `data/cache/`, and batched author lookups.
   - `mailto=researcher-mobility-probe@example.org` is used for the polite pool.

2. **Cohort & rate estimation** (`src/cohort_extraction.py`)
   - Defines an AI/ML cohort with career start 2000–2016, `>=10` AI/ML works.
   - Reproduces the note's 2×2 trajectory logic (`D`, `A`, `H`, `P`) and adds `PI` (`last-author` on `>=6` author paper) and `dropout` (no publication after `DROPOUT_LATEST_YEAR`).
   - Stratified sampling by civilisation group.
   - Estimates hazard rates with Laplace smoothing and a rate cap.

3. **ODE model** (`src/ode_model.py`)
   - Six-state compartment model per civilisation: `D`, `A`, `H_D`, `H_A`, `P_D`, `P_A`.
   - Constant annual inflow `I` from observed new-entrant rates.
   - Equilibrium, transition-rate elasticities, and point-of-no-return scans against `M = k * c_bar`.

## Reproduce

```bash
# Requires Python 3.10+ and packages in src/requirements.txt (pandas, numpy, requests)
python src/openalex_client.py
python src/cohort_extraction.py
python src/ode_model.py
```

`data/cache/` is excluded from git; the API will re-populate it on first run.

## Outputs

- `data/cohort/cohort.csv` — classified cohort (273 authors in this pilot)
- `data/cohort/transition_rates.csv` — per-civilisation rates (`alpha`, `beta`, `h_D`, `h_A`, `p_D`, `p_A`, `d`)
- `data/cohort/raw_sampled_works.json` — sampled works used for coauthor statistics
- `results/equilibrium_summary.csv` — equilibrium `T = D + H_D + P_D` vs `M = k * c_bar`
- `results/sensitivity.csv` — elasticities of `T` and `P_D` to each transition rate
- `results/point_of_no_return.csv` — critical multipliers at which `T` reaches `M`
- `results/intervention_summary.md` — human-readable top interventions per civilisation

## Limitations

- Constant exogenous inflow. PI-driven endogenous recruitment (`I(P_D)`) would make `p_D` and `h_D` affect `T` more strongly.
- Dropout is treated as a single departure hazard; future versions will use Aalen-Johansen competing-events rates as in the original note.
- The cohort sample is small for some groups (`Other Western`, `Japanese`); confidence intervals are not yet computed.

## Sources

- OpenAlex API: <https://api.openalex.org>
- Subfield: `subfields/1702` (Artificial Intelligence) under `fields/17` (Computer Science)
- Civilisation grouping rationale: `docs/mapping_rationale.md`
