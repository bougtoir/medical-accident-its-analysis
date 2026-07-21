# Modern Re-examination of 52 Canonical Curves

**定説曲線の現代的再検証 — 外れ値依存性・サンプルサイズ・非線形関係の脆弱性**

Onishi T. 2026.

## Overview

This project systematically re-examines 52 "canonical" curvilinear relationships across 8 academic disciplines using modern model selection methods (F-test, AIC/BIC, LOOCV, Cook's distance sensitivity analysis).

## Key Findings

| Verdict | Count | % |
|---------|-------|---|
| Not Significant | 22 | 42% |
| Robust Nonlinear | 18 | 35% |
| Outlier-Dependent | 12 | 23% |

**~65% of textbook nonlinear relationships fail at least one modern robustness test.**

## Disciplines Covered

- **A. Economics (12)**: Phillips, Laffer, Kuznets, EKC, Beveridge, Okun, Engel, J-Curve, Rahn, Gravity, Great Gatsby, Balassa-Samuelson
- **B. Public Health (10)**: Preston, Easterlin, McKeown, LNT, Fries, Barker, Omran, Wilkinson, BMI-Mortality, Alcohol-Mortality
- **C. Demography (6)**: Demographic Transition, Bongaarts-Feeney, Lee-Carter, Coale-Trussell, Replacement Migration, Second Demographic Transition
- **D. Environmental Science (6)**: Species-Area, Hubbert Peak Oil, Keeling, HANPP, Jevons Paradox, Forest Transition
- **E. Psychology (5)**: Yerkes-Dodson, Ebbinghaus, Weber-Fechner, Dunning-Kruger, Happiness U-Curve
- **F. Physics (4)**: Hubble's Law, Kleiber's Law, Gutenberg-Richter, Moore's Law
- **G. Political Science (5)**: Lipset, Duverger, Zipf, Crime-Temperature, Putnam
- **H. Agriculture (4)**: Mitscherlich, Borlaug, Micronutrient U-shape, Body Weight Set-Point

## Methods

1. **Nested F-test**: Linear (restricted) vs quadratic (unrestricted)
2. **AIC/BIC**: Model selection across linear, quadratic, and log models
3. **LOOCV RMSE**: Out-of-sample predictive accuracy
4. **Cook's Distance**: Top 3 influential points removed; F-test repeated

## Structure

```
canonical_curves_reexamination/
├── README.md
├── manuscript_canonical_curves_en.docx    # English manuscript
├── manuscript_canonical_curves_ja.docx    # Japanese manuscript
├── figures_canonical_curves.pptx          # Editable figures
├── scripts/
│   ├── core_analysis.py                   # Statistical framework
│   ├── data_economics.py                  # Economics curves (1-12)
│   ├── data_health.py                     # Public health curves (13-22)
│   ├── data_demography.py                 # Demography curves (23-28)
│   ├── data_environment.py                # Environmental curves (29-34)
│   ├── data_psychology.py                 # Psychology curves (35-39)
│   ├── data_physics.py                    # Physics curves (40-43)
│   ├── data_political.py                  # Political science curves (44-48)
│   ├── data_agriculture.py                # Agriculture curves (49-52)
│   ├── run_all_analyses.py                # Master runner
│   ├── generate_figures.py                # Figure generation
│   ├── generate_manuscript.py             # English docx
│   ├── generate_manuscript_ja.py          # Japanese docx
│   └── generate_pptx.py                   # PPTX figures
├── results/
│   ├── summary_table.csv                  # Summary statistics
│   └── full_results.json                  # Complete results
└── figures/
    ├── fig1_verdict_distribution.png
    ├── fig2_sensitivity_analysis.png
    ├── fig3_model_comparison.png
    ├── fig4_loocv_comparison.png
    └── fig5_sample_size.png
```

## Reproduction

```bash
cd scripts
python fetch_real_data.py          # Fetch WDI/FRED real data -> data/*.csv
python fetch_additional_real.py    # Fetch NOAA, USGS, PWT, Karl Rupp -> data/*.csv
python run_all_analyses.py         # Run all 52 analyses (substitutes real data)
python generate_figures.py         # Generate figures
python generate_manuscript.py      # Generate English manuscript
python generate_manuscript_ja.py   # Generate Japanese manuscript
python generate_pptx.py            # Generate editable figures
```

The two `fetch_*` scripts download primary data from public sources and write
CSVs to `data/`. `run_all_analyses.py` then substitutes those real datasets for
the corresponding curves before computing all statistics.

Some fetchers in `fetch_additional_real.py` require a free API key exported as
an environment variable: `EIA_API_KEY` (#30 Hubbert, #33 Jevons) and
`CENSUS_API_KEY` (#46 Zipf). #5 Beveridge uses the BLS API and works without a
key (falling back to the keyless BLS v1 endpoint; set `BLS_API_KEY` to use v2).
#25 Lee-Carter requires HMD USA period death rates (`Mx_1x1`), which the
Human Mortality Database prohibits redistributing: download it with a free
account at mortality.org and place it at `data/hmd/USA.Mx_1x1.txt` (or point
`HMD_MX_FILE` at it). Only the derived `kappa_t` index is stored in the repo.
Fetchers whose inputs are missing are skipped, leaving those curves on their
previous hard-coded values.

## Data provenance (in progress)

Not all 52 curves currently use fully traceable real data. Status:

- **26 curves use fetched real data** (World Bank WDI/FRED, NOAA Mauna Loa,
  USGS FDSN earthquake catalog, Penn World Table 10.01, Karl Rupp transistor
  dataset, UNDP HDI, Freedom House FIW, US EIA Total Energy, US BLS, HMD,
  US Census, OWID/World Happiness Report, OWID/USDA, OWID/IMF, Hubble 1929,
  CEPII Gravity, OECD Tax Database + Revenue Statistics): #1 Phillips,
  #2 Laffer (OECD top PIT rate vs tax revenue % GDP, 2022),
  #3 Kuznets, #4 Environmental Kuznets (CO2),
  #5 Beveridge, #6 Okun, #7 Engel, #9 Rahn, #10 Gravity Model,
  #12 Balassa-Samuelson, #13 Preston, #14 Easterlin, #19 Omran,
  #23 & #28 Demographic Transition, #25 Lee-Carter, #30 Hubbert Peak Oil,
  #31 Keeling, #33 Jevons, #34 Forest Transition, #40 Hubble,
  #42 Gutenberg-Richter, #43 Moore's Law, #44 Lipset, #46 Zipf,
  #50 Green Revolution.
- **Public-data reconstructions / proxies** built from real primary data but
  NOT replications of the original figure's exact point set (labelled as such
  in `data/digitized_sources.md` and `data/source_metadata.json`):
  #11 Great Gatsby (World Bank GDIM income IGE, Munoz & van der Weide 2025, +
  OWID/World Bank Gini; reconstruction),
  #32 HANPP (country values computed by zonal aggregation of the Haberl et al.
  2007 PNAS gridded HANPP/NPP0, year 2000, + OWID/World Bank GDP per capita),
  #48 Putnam (European proxy: Eurostat HETUS TV-viewing time AC82 + OWID
  generalized trust).
- **Curves digitized/transcribed from the original published figure or table**
  (values verifiable against the cited source; see `data/digitized_sources.md`):
  #21 BMI-Mortality (Global BMI Mortality Collaboration 2016 Lancet),
  #27 Replacement Migration (UN 2000 Replacement Migration report, Tables IV.1
  & IV.6, Scenario IV — UN **model outputs**, not empirical observations),
  #29 Species-Area (Johnson & Raven 1973 Galapagos plant species),
  #36 Ebbinghaus Forgetting Curve (Ebbinghaus 1885 original savings table),
  #41 Kleiber's Law (AnAge database, 422 mammal species),
  #45 Duverger's Law (Bormann & Golder DES 5.0, 1660 elections).
- **The remaining curves still use hard-coded arrays** in `scripts/data_*.py`
  and are being migrated to real, primary-source data. Until a curve appears in
  the lists above, treat its values as provisional.
- **#35 Yerkes-Dodson has been EXCLUDED** from the analysis: its former
  implementation generated synthetic data with `numpy.random` and no traceable
  primary dataset was available, so it is dropped rather than presented as
  empirical. The analysis therefore covers **51** curves (originally 52).

Each curve's claimed source is recorded in `data/source_metadata.json`.

## Dependencies

```
numpy scipy pandas statsmodels scikit-learn matplotlib seaborn python-docx python-pptx
wbgapi requests openpyxl rasterio geopandas
```
