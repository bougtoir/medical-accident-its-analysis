# Pre-submission reviewer review — Journal of Epidemiology & Community Health

Manuscript: *Regional variation in anaesthesia practice under universal coverage in Japan: a cross-sectional ecological study of secondary medical areas*

## 1. Novelty, focus and logic
- **Scope fit**: JECH publishes epidemiologic and public-health research on health-system performance, small-area variation, and policy-relevant observational studies. The manuscript explicitly frames administrative claims as population-health surveillance, uses an ecological cross-sectional design, and draws international implications for universal-coverage systems.
- **Focus**: The paper shifts from the BMJ Q&S quality-improvement framing to a population-health / health-services epidemiology framing: separating documented service-delivery variation from coding/audit artefacts.
- **Logic**: The four research questions (variation size, audit explanation, between/within prefecture variance, and structural determinants) are all raised in the Introduction and answered in Results/Discussion.
- **Novelty**: First multilevel small-area analysis of anaesthesia technique variation in Japan that exploits prefecture-specific auditing as a natural experiment; the variance-decomposition approach is transferable to other UHC systems.

## 2. Statistical design
- **Unit of analysis**: Secondary medical area (ecological). The ecological fallacy and cross-sectional limitation are stated clearly.
- **Methods**: Multilevel linear mixed models, variance decomposition, empirical Bayes shrinkage, audit-impact sensitivity, and covariate-adjusted sensitivity (population density + anaesthesiologist share).
- **Convergence**: Some MixedLM optimiser warnings appeared for the covariate-adjusted models; a short note is included in Methods and the point estimates are stable across sensitivity analyses.
- **Effect size**: Cohen's d, marginal R² and 95% CIs are reported for key coefficients.

## 3. Figures and tables
- All three tables and two figures are cited in the body before they appear.
- Table 1: code definitions.
- Table 2: distribution of standardised claim ratios.
- Table 3: multilevel model results.
- Figure 1: geographic distribution maps.
- Figure 2: university-hospital effect / combined measure.
- Per JECH guidance, figure legends are placed at the end of the manuscript and the figures are also supplied as a separate editable PPTX file.

## 4. Reproducibility
- One-command build: `python3 scripts/build_jech.py` regenerates `output/ijhpm_results.json`, all tables/figures and the manuscript from `data/`.
- No hard-coded numeric results in the manuscript generator; all values are read from `ijhpm_results.json` via `Template` substitution.
- All data sources are public and cited.

## 5. Strength of claims
- Claims are calibrated: "predominantly structural", "documented-service-delivery gradient", "underpowered model" for spinal anaesthesia.
- Limitations (ecological fallacy, cross-sectional design, reimbursed-claim data, lack of code-specific audit rates, urban-university overlap) are explicitly stated.
- The "claims are not care" concern is addressed directly: the paper describes documented service delivery, and audit-sensitivity analyses are used to argue that the gradient is unlikely to be a pure coding/audit artefact.

## Response to BMJ Q&S internal review points
1. **Documentation vs care**: The Introduction and Discussion now state that the outcome is a reimbursed claim ratio and therefore captures documented service delivery. The audit-sensitivity analyses and within-prefecture structure support interpreting the residual variation as real geographic variation in service provision, not a coding artefact.
2. **Japan-only focus**: The Discussion now explicitly extends the findings to Taiwan, South Korea, Germany, France and the English NHS, and frames the variance-decomposition method as a transferable epidemiologic tool for any UHC system with a uniform fee schedule and regional audit variation.
3. **Limitations**: Limitations are grouped and discussed as inherent to ecological claims studies. The residual risk is that JECH may still view the topic as more clinical than public-health, but the epidemiologic framing, UHC focus and transferable variance-decomposition method should mitigate this.

## Pre-submission checklist
- [x] Title indicates study design.
- [x] Structured abstract ≤ 250 words.
- [x] Key messages after abstract; 3–5 sentences.
- [x] Body ≤ 3500 words (excluding abstract, references, tables, figures).
- [x] Tables + figures ≤ 5.
- [x] Vancouver/numbered citations; no orphan references; 20 references.
- [x] Separate title page and declarations/end-matter file.
- [x] STROBE checklist attached.
- [x] Cover letter included, emphasising public-health / epidemiology fit.

## Residual risks for desk reject
1. **Scope fit**: JECH emphasises international public-health relevance. The cover letter and Discussion explicitly address this.
2. **Claims-data interpretation**: Some editors may still feel the paper is "about billing, not patients". The Introduction and Discussion directly confront this and use sensitivity analyses to support the interpretation.
3. **Single-anonymised review**: Ensure the main manuscript file contains no author names or institutions.

## Recommendation
Proceed with submission. Monitor the MixedLM convergence note; if reviewers request it, a supplementary appendix can show optimizer settings and sensitivity of coefficients to optimizer choice.
