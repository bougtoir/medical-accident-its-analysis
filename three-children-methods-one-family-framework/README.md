# Three Children Methods, One Family Framework (ONISHI)

Reproducible analysis pipeline for the ONISHI evidence-integration
framework, which chains three companion methods — **LINKO**, **IONE**, and **KOTHA** —
into a single pipeline and demonstrates it on public individual-patient data from the
**International Stroke Trial (IST)**.

Every figure, table, and statistical quantity is derived from public data through the code
in this repository. No statistical value is hardcoded: the flow is
`public data -> analysis -> results.json -> figures/tables`.

## Methods

| Method | Level | Role in the demo |
|---|---|---|
| **IONE** | within-study (subgroups) | latent risk stratification; effect (in)coherence C1, within-stratum homogeneity W |
| **LINKO** | between-study (information weights) | endpoint information contribution ratio (ICR) across strata / countries |
| **KOTHA** | across evidence (integration) | counterfactual power, Bayesian harmonization, OIS/TSA/GRADE |

## Data

- **Source**: International Stroke Trial database (Sandercock et al. 2011, *Trials* 12:101;
  https://datashare.ed.ac.uk/handle/10283/124, open access).
- Treatment: randomized aspirin allocation (`RXASP`); outcome: 14-day death (`DIED`).
- Complete-case analysis frame after dropping records with missing baseline covariates.

The dataset (`integration_analysis/data/IST_corrected.csv`) is included for convenience and
can also be re-downloaded with `integration_analysis/download_data.sh`.

## Requirements

Python 3 with:

```bash
pip install numpy pandas scipy statsmodels matplotlib Pillow
```

## Reproduce

```bash
# 1. (optional) re-download the public IST data
cd integration_analysis
bash download_data.sh

# 2. run the analysis: regenerates figures/ and results.json
python3 run_integration.py
```

Step 2 regenerates the six figures (`figures/`) and `results.json`, from which every
number, figure, and table in the analysis is produced.

## Layout

```
integration_analysis/
  download_data.sh        # fetch public IST IPD
  linko_icr.py linko_pca.py   # LINKO (information contribution ratio)
  ione_core.py            # IONE (stratification, coherence)
  kotha_core.py           # KOTHA (power, harmonization, OIS/TSA)
  run_integration.py      # runs the four patterns -> figures + results.json
  schematic_figures.py    # conceptual overview / pipeline figures
  data/IST_corrected.csv  # public IST dataset
  results.json            # analysis outputs (regenerated)
  table3_stratum.csv table3_summary.csv  # stratum / summary tables
  figures/                # generated figures
```

## Notes

- No `.dot`/Graphviz files are used; all figures are PNG/TIFF.
- Figure artwork carries no baked-in figure numbers or prose captions; legends live in the
  manuscript. Figures are supplied separately per journal (AJE) requirements.
