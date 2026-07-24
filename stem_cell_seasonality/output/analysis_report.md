# Exploratory Analysis: GEO iPSC/ESC Data × Season & Solar Activity

*Generated: 2026-06-10 12:15 UTC*

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Total GEO Series (iPSC/ESC differentiation) | **6,101** |
| Date range | 2001-11 – 2026-06 |
| Records with country data | 600 (10%) |
| Northern Hemisphere | 584 |
| Southern Hemisphere | 16 |

### Top contributing countries (from sample)

- USA: 265
- China: 59
- United Kingdom: 44
- Germany: 43
- Japan: 36
- Netherlands: 16
- Australia: 13
- Italy: 12
- Spain: 11
- Canada: 11

## 2. Key Findings

### Finding 1: Non-uniform seasonal distribution (p < 0.001)

GEO dataset submissions show a statistically significant departure from uniform monthly distribution (χ²=32.3, p=0.0007).

- **Peak month**: Mar (561 datasets)
- **Trough month**: Nov (437 datasets)
- **Amplitude**: 124 datasets (24% of mean)

| Month | Count | % of total |
|-------|-------|------------|
| Jan | 559 | 9.2% |
| Feb | 471 | 7.7% |
| Mar | 561 | 9.2% |
| Apr | 528 | 8.7% |
| May | 501 | 8.2% |
| Jun | 535 | 8.8% |
| Jul | 505 | 8.3% |
| Aug | 484 | 7.9% |
| Sep | 507 | 8.3% |
| Oct | 469 | 7.7% |
| Nov | 437 | 7.2% |
| Dec | 544 | 8.9% |

### Finding 2: Hemisphere imbalance limits comparison

The iPSC/ESC research landscape is heavily Northern Hemisphere–biased. From our sample of 600 datasets with country data:

- NH: 584 (97%)
- SH: 16 (3%)

This ~97:3 ratio means the global dataset is effectively a Northern Hemisphere dataset. Hemisphere-inverted seasonal patterns cannot be robustly tested with GEO data alone — **IVF registry data (HFEA, ANZARD) would provide the critical Southern Hemisphere sample size.**

### Finding 3: Raw solar correlation is confounded by secular trend

| Correlation | r | p |
|-------------|---|---|
| F10.7 flux vs. dataset count (raw) | 0.478 | 1.8e-15 |
| Sunspot number vs. dataset count (raw) | 0.402 | 5.4e-11 |
| SSN vs. dataset count (**detrended**) | 0.020 | 0.753 |

The raw positive correlation (r≈0.4–0.5) is driven by the secular growth of iPSC research coinciding with Solar Cycle 24/25. After removing the 12-month rolling trend, **the correlation vanishes** (r≈0.02, p=0.75), indicating no direct relationship between solar activity and GEO submission rates.

**Important caveat**: GEO submission date ≠ experiment date. The delay between experiment execution and data deposition (typically 6–18 months) obscures any true temporal signal. The absence of correlation here does **not** rule out solar/geomagnetic effects on cell biology — it only shows that GEO metadata is too noisy a proxy for experiment timing.

## 3. Implications for the Perspective

1. **Seasonal non-uniformity exists** — the χ² result supports the hypothesis that PSC research has temporal structure
2. **Hemisphere test requires IVF data** — GEO is too NH-biased for the natural experiment design
3. **Solar cycle proxy is inadequate** — direct experiment-date metadata would be needed (not submission dates)
4. **These limitations are themselves arguments for the Perspective's proposed Phase I (environmental monitoring) and Phase II (retrospective mining)**

## 4. Data Files

| File | Description |
|------|-------------|
| `geo_psc_metadata.csv` | Full GEO dataset metadata (6,101 records) |
| `geo_country_full.csv` | Country data from GEO SOFT headers |
| `noaa_solar_indices.csv` | NOAA monthly solar indices (1749–2026) |
| `geo_solar_comprehensive.png` | 6-panel analysis figure |
