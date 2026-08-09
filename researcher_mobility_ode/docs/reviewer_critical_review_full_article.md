# Reviewer-perspective critical review: full-article submission

Project: `researcher_mobility_ode` (OpenAlex AI/ML, Research Policy full-article format)  
Date: 2026-08-09  
Scope: Manuscript, statistical design, figures/tables, reproducibility, and strength of claims.

---

## 1. Manuscript

### Strengths
- IMRaD structure is complete: title, abstract, keywords, highlights, data/code availability, declarations, introduction, literature review, methods, results, discussion, conclusion, references.
- Word count ~7,900 (Research Policy full-article target ~8,000–10,000); just below the lower bound but within shouting distance.
- Historical counterfactual, saturating-inflow robustness, bootstrap CI, and policy counterfactuals are all reported.
- All 16 references were verified against real sources; one arXiv ID typo was fixed before submission.

### Critical issues

| Priority | Issue | Evidence / location | Suggested fix |
|---|---|---|---|
| Must fix | Causal language in policy counterfactuals | Results 5.3 / Discussion | Add explicit framing that counterfactuals are *mechanical* multipliers of observed transition rates, not identified causal effects of specific policy instruments. |
| Must fix | Word count slightly under 8,000 | `docx` word count 7,901 | Add one short paragraph on limitations/robustness or expand the literature-theory bridge to clear 8,000. |
| Should fix | Minimum viable coauthor threshold `M = k × c_bar` remains a conceptual borrow from ecology | Methods 4.3 / Discussion | Keep, but state more explicitly that `M` is a model-implied *sufficient* threshold for collapse, not a validated empirical minimum. |
| Should fix | Small group instability | Table 8 bootstrap CIs are very wide for `Other Civilizations` and `Japanese` | Keep reporting CIs; avoid strong group rankings in the abstract beyond what uncertainty supports. |
| Nice to have | Figure colours are not colour-blind safe | Figure 2/4 use default Matplotlib palette | Use Okabe-Ito or similar for final camera-ready figures. |

---

## 2. Statistical design

### Strengths
- Transition rates are estimated as constant hazards with Laplace smoothing and a rate cap; the assumptions are transparent.
- Endogenous inflow is capped at half the stability-critical value (`safety_factor = 0.5`), preventing explosive linear dynamics.
- Bootstrap CI resamples authors within civilisation groups, capturing at least some sampling uncertainty.

### Critical issues

| Priority | Issue | Evidence | Suggested fix |
|---|---|---|---|
| Must fix | Independence assumption | Each researcher is treated as an independent observation; authors with many works are over-weighted in the cohort. | Add robustness check with one-observation-per-author weighting or bootstrap stratified by number of works. |
| Should fix | `min_cohort=5` for time-varying rates | `time_varying.py` | Document the trade-off: smaller groups included, but rate estimates become noisy. |
| Should fix | No sensitivity to `safety_factor` or `epsilon` | `ode_model_endogenous.py` | Add a small table or figure showing how `T_eq` and `margin` vary with `safety_factor ∈ {0.25,0.5,0.75}` and with saturating `epsilon`. |
| Nice to have | OpenAlex affiliation noise | Methods limitations | Already noted; possible addition: compare a random subsample hand-verified for country assignment. |

---

## 3. Figures and tables

### Strengths
- All figures and tables are cited in the body before they appear and are placed immediately after first citation.
- Table/figure numbering is sequential (Figures 1–4, Tables 1–8).
- `manuscript_full_article_figures.pptx` provides editable versions.

### Critical issues

| Priority | Issue | Evidence | Suggested fix |
|---|---|---|---|
| Must fix | Some figures may not be colour-blind safe | `fig2_pnr_proximity.png`, `fig4_bootstrap_ci.png` | Replace default palette with colour-blind-safe palette. |
| Should fix | `fig3_historical_margin.png` shows large magnitude changes; without confidence bands, readers may over-read | Figure 3 caption | Add a note that the comparison is across two point estimates and that uncertainty is substantial. |
| Should fix | PPTX captions use decimal formatting that may not match final journal style | build script | Verify all numbers use consistent significant figures. |

---

## 4. Reproducibility

### Strengths
- `scripts/build_full_manuscript.py` reads every numeric value from `results/` CSVs; no empirical numbers are hard-coded in the manuscript text.
- The pipeline was re-run from the cached cohort: `time_varying.py`, `policy_counterfactuals.py --packages`, `bootstrap_ci.py --n-boot 200`, then `build_full_manuscript.py`.
- `libreoffice --headless --convert-to pdf` produces a PDF without errors.

### Critical issues

| Priority | Issue | Evidence | Suggested fix |
|---|---|---|---|
| Must fix | Public repo `bougtoir/researcher-mobility-ode` is stale (last sync before this commit) | `git_list_repos` shows last updated 08:23 UTC, current commit is later | After PR #334 is merged, confirm the sync workflow runs or manually trigger it; then clone the public repo and run the README reproduction steps. |
| Should fix | No single top-level command to regenerate everything | README lists individual scripts | Add a `Makefile` or `reproduce.sh` that runs scripts in order and exits on first failure. |
| Should fix | `data/cache/` is gitignored; reproducing from scratch requires OpenAlex API calls | `.gitignore` | Document expected run time, API polite-pool requirements, and `--force-resample` semantics. |

---

## 5. Strength of claims

### Current claims and their support

| Claim | Support | Assessment |
|---|---|---|
| All groups remain above their minimum viable coauthor threshold in equilibrium | Table 2 / `equilibrium_summary.csv` | Supported by model. |
| Dropout is the largest negative lever | Table 3 elasticities | Supported, but "lever" should be read as model sensitivity, not policy effect. |
| Other Civilizations is closest to PNR for active pool | Table 4 / Figure 2 | Supported by point estimate; bootstrap uncertainty makes ranking less certain. |
| Historical counterfactual shows heterogeneous temporal shifts | Table 6 / Figure 3 | Supported as a sensitivity exercise; not a forecast. |
| Early, safety-factor-bound interventions can preserve civilisational diversity | Discussion | Defensible as a *framework* claim; not empirically validated as a causal policy result. |

### Critical issues

| Priority | Issue | Suggested fix |
|---|---|---|
| Must fix | The abstract says "reducing dropout is the highest-leverage positive intervention" | Rephrase to "reducing dropout yields the largest simulated margin gain" or "the largest model-improved lever." |
| Must fix | Terms such as "policy counterfactual" and "intervention" can be read as causal | Add a Methods paragraph and a Discussion paragraph restating that these are proportional rate perturbations in a steady-state model, not causal estimates of real-world programmes. |
| Should fix | The historical counterfactual is described as what "would have happened" | Use "would have been implied by the steady-state model" and stress that the model does not capture policy shocks. |

---

## 6. Overall verdict

The manuscript is close to submission-ready. The main remaining risks are (1) a small amount of causal/overclaim language in the policy counterfactual sections, and (2) confirming that the public repository synchronises and reproduces the submitted numbers exactly. Once those two are addressed, it can be submitted to Research Policy as a full article.
