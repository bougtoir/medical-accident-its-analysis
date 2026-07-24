# GDP tempo effect and intangible capital

Public replication materials for **“What the Solow Residual Has Been Hiding: Tempo Drift and the Missing Intangible Share in National Capital Stocks.”**

## Reproduce everything

Requirements: Python 3.10 or newer, `make`, and optionally LibreOffice for PDF conversion.

```bash
git clone https://github.com/bougtoir/gdp-tempo.git
cd gdp-tempo
make
```

`make` creates `.venv`, installs pinned Python dependencies, verifies the source-data checksums, reruns every analysis, regenerates Figures 1–14 and Tables 1–6, rebuilds DOCX/PPTX submission files, and validates the regenerated metrics. PDF conversion is attempted when `libreoffice` is installed; its absence does not affect the numerical reproduction.

For numerical results, figures, and tables without the document build:

```bash
make setup
make reproduce-analysis
```

A successful run ends with:

```text
Complete reproduction passed. See reproduction/reproduction_report.json
```

The complete run can take several minutes because the model grids and bootstrap are recomputed country by country. Step logs are written under `reproduction/logs/`.

## Data provenance

Exact research-vintage inputs are committed under `source_data/`; no private filesystem paths or untracked inputs are required.

| Input | Public source | Use |
|---|---|---|
| Penn World Table 10.01 | DOI: [10.34894/QT5BCC](https://doi.org/10.34894/QT5BCC) | Output, investment, capital, labour, human capital, labour share, depreciation |
| World Development Indicators | Indicator `GB.XPD.RSDV.GD.ZS` | R&D expenditure share |
| Changing Wealth of Nations | Indicators `NW.PCA.TO`, `NW.HCA.TO`, `NW.TOW.TO` | Produced, human, and total wealth |
| OECD Annual National Accounts | Dataflow `DSD_NAMAIN10@DF_TABLE1_EXPENDITURE_GFCF_ASSET` | Investment composition and observable gestation lag |

`source_data/manifest.json` records source URLs, transformations, row counts, licenses, and SHA-256 checksums. `make verify-sources` checks the frozen files. `make verify-online` independently downloads current PWT and World Bank copies and compares them with the frozen research vintage. Provider APIs are mutable, so the analysis always uses the checksummed committed inputs unless a new vintage is explicitly created.

All inputs are publicly released aggregate macroeconomic observations. The repository contains no synthetic observations presented as measured data.

## Pipeline

```text
source_data/
  -> scripts/run_full_analysis_mobs.py
  -> scripts/run_paper_analyses.py
  -> scripts/make_fig3_and_fig5.py
  -> scripts/solow_decomposition.py
  -> scripts/k_level_analysis.py
  -> scripts/build_docx_pptx.py
  -> scripts/validate_reproduction.py
```

`GDP_TEMPO_SOURCE_DATA=/path/to/source_data` may be set to test an alternative research vintage. By default, every loader resolves paths relative to this repository.

## Methodological constants versus empirical results

Fixed values such as the intangible-capital depreciation rate and literature-based asset gestation periods are model assumptions, not fitted empirical results. They are declared near the top of the analysis scripts and described in the manuscript. Country estimates, model metrics, confidence intervals, figures, and tables are calculated from the source data.

`reproduction/expected_metrics.json` is an output-validation baseline. Analysis and document-generation code never reads it; only `validate_reproduction.py` compares newly calculated results against it, preventing the baseline from influencing estimation.

## Principal regenerated checks

The automated validator confirms, among other results:

- 35-country M_obs/K-level sample;
- median capital-level difference of −4.29%;
- median TFP shift of −1.74 percentage points;
- median implied labour-share shift of +1.736 percentage points;
- all 35 countries have `K_obs < K_M0`;
- maximum tempo-only TFP-variance share of 13.8%;
- maximum joint tempo-plus-intangible share of 29.7%;
- maximum produced-capital counterfactual gap of 1.1%.

See `reproduction/reproduction_report.json` for the machine-readable comparison.

## Repository layout

- `source_data/`: frozen, checksummed public inputs and provenance manifest.
- `scripts/`: acquisition, analysis, figure/table, document, and validation code.
- `data/`: regenerated intermediate and result data.
- `figures/`: regenerated English and Japanese figures.
- `tables/`: regenerated manuscript tables.
- `manuscript/`: manuscript sources and generated submission files.
- `reproduction/`: expected metrics, validation report, and run logs.
