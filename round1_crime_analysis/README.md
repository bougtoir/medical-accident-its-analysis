# Round1 × Crime Rate Analysis

**Research question:** Does the opening of Round1 (bowling/arcade/amusement chain) stores reduce local crime rates?

## Background

Round1 (ラウンドワン) is a Japan-based indoor leisure chain operating bowling alleys, arcade games, karaoke, and sports facilities. The company expanded to the US starting in 2010 (Puente Hills Mall, CA) and now operates 60+ locations across 28 states. A common claim in the US is that Round1 openings reduce crime by providing positive recreational outlets, particularly for youth.

This project uses publicly available data to test this hypothesis at the state level as a preliminary/scoping analysis, with the goal of motivating a future collaboration with Round1 Corporation to obtain more granular (store-level) data.

## Data Sources

| Data | Source | Granularity | Period |
|------|--------|-------------|--------|
| Round1 USA store locations | round1usa.com, Round1 Group IR, news articles, Malls & Retail Wiki | Store-level (64 locations) | 2010–2024 |
| FBI UCR crime statistics | CORGIS/FBI Uniform Crime Reports | State-level, rate per 100k | 1960–2019 |

## Methods

1. **Event study**: Normalise crime rates to t−1 (year before first Round1 opening) for each treated state; plot crime trajectory from t−5 to t+5.
2. **Difference-in-Differences (DiD)**: Two-way fixed-effects model (state + year FE) with clustered standard errors. Treatment = states with Round1 stores, post = after first store opening.
3. **Parallel trends test**: Verify pre-treatment trends are similar between R1 and non-R1 states (interaction of time trend × treatment, 2005–2009).
4. **Dose–response**: Compare crime rates across states grouped by Round1 store density (0, 1–2, 3–5, 6+ stores).

Crime categories analysed:
- Violent crime (all), murder, robbery, aggravated assault
- Property crime (all), burglary, larceny, motor vehicle theft

## Key Results (Open Data, State-Level)

| Crime Type | DiD Coefficient | p-value | Direction |
|-----------|----------------|---------|-----------|
| Violent Crime | −16.7 | 0.360 | ↓ (n.s.) |
| Property Crime | −124.1 | 0.083 | ↓ (marginal) |
| Murder | −0.34 | 0.090 | ↓ (marginal) |
| Robbery | −4.7 | 0.610 | ↓ (n.s.) |
| Assault | −11.7 | 0.280 | ↓ (n.s.) |
| Burglary | −35.7 | 0.150 | ↓ (n.s.) |

**Interpretation**: All coefficients point in the "crime-reducing" direction, but none reach statistical significance at the 5% level. Property crime and murder are marginally significant (p < 0.10). This is consistent with a real but modest effect that is attenuated by the coarse (state-level) granularity of the open data. Parallel trends test passes (p > 0.05), supporting the validity of the DiD design.

## Implications for Collaboration

These results provide a credible basis for approaching Round1 Corporation:

1. **Suggestive evidence**: The direction of all coefficients is consistent with the crime-reduction hypothesis.
2. **Power limitation**: State-level data cannot detect effects that operate at the neighbourhood/city level. With Round1-provided data (store-level foot traffic, opening dates, mall characteristics), we can conduct a properly powered analysis at the city or zip-code level.
3. **Methodological foundation**: The DiD framework, event study, and dose–response analyses demonstrated here can be directly applied to more granular data.

## Directory Structure

```
round1_crime_analysis/
├── README.md
├── data/
│   ├── round1_usa_stores.csv      # Compiled store list
│   ├── round1_usa_stores.json
│   └── state_crime_full.csv       # FBI UCR state-level crime data
├── scripts/
│   ├── 01_compile_round1_stores.py # Store data compilation
│   └── 02_analyze_crime.py        # Main analysis & figures
├── figures/
│   ├── fig1_expansion_timeline.png
│   ├── fig2_crime_trends_comparison.png
│   ├── fig3_event_study.png
│   ├── fig4_did_forest_plot.png
│   ├── fig5_state_heatmap.png
│   └── fig6_dose_response.png
└── output/
    ├── did_results.json
    ├── parallel_trends_test.json
    ├── crime_change_by_state.csv
    └── summary_table.csv
```

## Reproduction

```bash
pip install pandas numpy scipy statsmodels matplotlib
cd round1_crime_analysis
python scripts/01_compile_round1_stores.py
python scripts/02_analyze_crime.py
```

## Next Steps (with Round1 collaboration)

- Obtain store-level opening dates, foot traffic, and mall characteristics
- Match to FBI NIBRS incident-level data or local police open data (city level)
- Conduct zip-code or census-tract level DiD with synthetic control methods
- Analyse crime type heterogeneity (youth crime, property vs violent)
- Explore spatial spillover effects (displacement vs diffusion of benefits)
