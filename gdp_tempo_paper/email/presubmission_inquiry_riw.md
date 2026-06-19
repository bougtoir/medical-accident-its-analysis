# Pre-submission inquiry — Review of Income and Wealth

**To:** Dr. Robert Inklaar, Editor, Review of Income and Wealth
**From:** Tatsuki Onishi
**Subject:** Pre-submission inquiry: Revised manuscript with observable asset-composition-based tempo correction (MS 3413547)

---

Dear Dr. Inklaar,

Thank you for your detailed and constructive feedback on my manuscript 3413547, "The Forgotten Tempo Effect in Capital Accounting." Your assessment identified critical weaknesses that I believe I have now substantially addressed. I am writing to inquire whether a revised manuscript would be considered for submission.

## Summary of your key critiques and my response

Your rejection letter raised three core objections:

1. **The PIM treats μ as a single aggregate mean lag, without engagement with asset-specific service lives, age-efficiency profiles, or vintage corrections.**
2. **The tempo analogy is a reframing rather than a measurement contribution**, because the PIM stock is well-defined regardless of μ.
3. **Empirically, M3 (intangible β) worsens OOS fit (4.72%) and M4 (joint) returns to M0 levels (4.61%)**, so the central methodological payoff does not materialise.

I have conducted new analysis that directly addresses all three points.

## New approach: Observable μ(t) from OECD asset composition

Instead of estimating μ as a free parameter, I now **construct** it from observable OECD Gross Fixed Capital Formation data by asset type:

$$\mu_{obs}(t) = \sum_a \frac{\text{GFCF}_a(t)}{\text{GFCF}_{total}(t)} \times \mu_a$$

where μ_a are literature-based gestation periods per asset class:

| Asset class (SNA) | μ_a (years) | Source |
|---|---|---|
| Dwellings + Other structures (N111G, N112G) | 2.0 | Kydland & Prescott (1982) |
| Transport equipment (N1131G) | 0.5 | BEA capital flow tables |
| ICT equipment (N1132G) | 0.3 | BEA; Jorgenson et al. (2005) |
| IP products incl. R&D (N117G) | 3.0 | DiMasi et al. (2003); Hall et al. (2010) |

This approach has **zero free parameters** — μ(t) is entirely determined by observable investment composition and published gestation lags. It directly engages with asset-specific information as you recommended.

## Key empirical results (35 OECD countries, OOS 2015–2019)

| Model | Free parameters | OOS MAPE (median) | vs M0 |
|---|---|---|---|
| M0 (instant PIM) | 0 | 4.60 % | — |
| M1 (constant lag) | 1 | 4.41 % | −4.3 % |
| **M_obs (asset composition)** | **0** | **4.17 %** | **−9.5 %** |
| M2 (estimated linear drift) | 2 | 3.99 % | −13.4 % |
| M3 (intangible β only) | 1 | 4.72 % | +2.6 % |
| M4 (joint μ + β) | 3+ | 4.61 % | 0.0 % |

Three findings are noteworthy:

1. **M_obs improves OOS prediction by 9.5% over M0 with zero free parameters.** This is not a fitting exercise — the improvement comes entirely from observable data. M_obs also outperforms M1 (1 parameter), M3 (1 parameter), and M4 (3+ parameters).

2. **The observable μ(t) shows a secular upward trend across all major economies** (approximately +0.005 yr/yr), driven by the well-documented shift from structures and equipment toward IP products and R&D. This structural change in investment composition is precisely the kind of asset-specific variation your letter called for.

3. **The result is robust to substantial perturbation of the assigned μ_a values.** Scaling all μ_a by 0.5× still beats M0 (4.39% vs 4.60%); scaling by 1.5× approaches M2 performance (4.04%).

## How this addresses your specific critiques

**On asset-specific engagement:** The revised framework is built entirely on asset-level GFCF decomposition, directly incorporating the heterogeneity in service lives and gestation periods that you noted was missing.

**On the tempo analogy as "reframing":** The new results show that accounting for the time-varying investment gestation lag — constructed from observable asset composition shifts — produces a measurably different and more accurate capital stock series. The PIM stock may be "well-defined regardless of μ," but the M_obs stock predicts GDP growth better than the M0 stock. The tempo concept thus delivers a quantifiable measurement improvement, not merely a reframing.

**On M3/M4 empirical failure:** The revised manuscript would de-emphasise M3 and M4 in favour of M_obs as the central contribution. The intangible-capital extension remains available as a robustness check, but the core message is simpler: observable investment composition shifts generate a parameter-free tempo correction that improves capital measurement.

## Proposed revised manuscript structure

The revised manuscript would be restructured around the observable μ(t) approach:

1. Introduction: time-to-build as an asset-composition phenomenon
2. Framework: PIM with observable gestation lag from GFCF decomposition
3. Data: PWT 10.01 + OECD GFCF by asset type (35 countries, 1970–2019)
4. Results: M0 vs M_obs comparison (OOS, Solow decomposition, RPIM)
5. Robustness: μ_a sensitivity, comparison with estimated models (M1, M2)
6. Discussion: implications for capital measurement practice

Would you be willing to consider a revised manuscript along these lines for the Review of Income and Wealth?

Thank you for your time and consideration.

Sincerely,
Tatsuki Onishi
