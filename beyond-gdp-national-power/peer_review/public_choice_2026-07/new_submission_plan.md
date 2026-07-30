# Plan for a new submission on network exclusion and state collapse

The Public Choice rejection is a de novo rejection: the editor explicitly invites a *new paper* on the same topic, not a revision of the current manuscript. The two referee reports identify the same core weaknesses, so the next version must address all of them before any resubmission.

## 1. Core problems to solve

### 1.1 The classification must be defensible and blind
- **Issue (R2)**: The seven "technologically excluded" polities are historically contestable (e.g., Timurid Empire not landlocked; Han Empire on the Silk Road). Moving seven conquered cases from open to closed mechanically inflates the closure-conquest association.
- **Issue (R1)**: No explanation of how the stock/flow classification or the geographic-barrier index was constructed; no maps or summary statistics.
- **Fix**: Write a pre-specified coding rubric *before* looking at outcomes. Apply it blind to all 96 cases (or to a smaller, well-documented subset). Record the source and exact quotation for every classification. Report inter-coder reliability if more than one coder is available. Then re-run the analysis on the blind-coded data.

### 1.2 The mechanism must be demonstrated, not assumed
- **Issue (R1, R2)**: The paper assumes technological exclusion → weaker economic performance / state capacity → conquest, but does not show the intermediate steps.
- **Fix**: For the excluded and matched control polities, collect direct proxies for
  - **technological transmission**: timing of adoption of key military, agricultural, and navigational technologies; literacy/numeracy; presence of craftsman guilds or technical schools.
  - **economic performance**: urbanization, real wages (where available), agricultural surplus, trade volume proxies.
  - **state capacity**: tax extraction, army size/quality, fortification, administrative reach, mint output.
  Then estimate whether excluded polities deteriorate *relative to matched open and policy-closed comparators* before being conquered.

### 1.3 The empirical strategy must be transparent and appropriate for a small sample
- **Issue (R1)**: 2SLS/IV is underpowered and the exclusion restriction is asserted, not argued; PSM lacks balance tests; no first-stage regression is reported.
- **Fix**:
  - Prefer **coarse exact matching (CEM)** or **Mahalanobis matching** with full balance diagnostics, given the small number of observations and mostly discrete covariates.
  - If IV is used, report the first stage, F-statistic, and an explicit justification for the exclusion restriction; consider dropping IV if the instrument is weak.
  - Use **randomization inference** with **spatial correlation adjustments** (Conley–Kelly 2025) and report effective regression weights / omitted-variable-bias diagnostics (Bastos 2025, Public Choice).

### 1.4 The literature review must situate the paper in Public Choice and economic history
- **Issue (R1)**: The paper omits Public Choice/state-capacity literature (Piano 2019; Boettke & Candela 2020; Hendrickson, Salter & Albrecht 2018; Geloso & Salter 2020; Piano & Salter 2021) and relevant empirical work (Bologna Pavlik & Young 2019; Olsson & Hibbs 2005; Flückiger et al. 2022; Fernández-Villaverde et al. 2023; Young 2016; Bastos 2025; Rodríguez & Imam 2025; Comin et al. 2010).
- **Fix**: Add a focused literature review that frames the paper as a contribution to the political economy of state capacity, technological diffusion, and geographic determinism. Show how the mechanism differs from plunder/institutional theories and from pure geographic determinism.

## 2. Proposed phases

| Phase | Task | Deliverable | Approximate effort |
|-------|------|-------------|--------------------|
| 0 | **Decide scope** | Keep the 96-case AI-assisted dataset as a pilot, or start a smaller, source-anchored sample. | 1–2 days |
| 1 | **Coding rubric** | Written rubric for structural exclusion, policy closure, and open-network status; blind application to cases. | 1–2 weeks |
| 2 | **Source collection** | Record-level source table for entity, period, classification, and outcome; map of cases; summary stats. | 2–4 weeks |
| 3 | **Mechanism data** | Time-series proxies for technology adoption, economic performance, and state capacity for excluded and matched controls. | 3–6 weeks |
| 4 | **Analysis** | Reproducible scripts for CEM/Mahalanobis, randomization inference, and spatial correlation; sensitivity tests. | 2–3 weeks |
| 5 | **Rewrite** | New manuscript with literature review, clear mechanism, transparent methods, and conservative causal language. | 2–3 weeks |
| 6 | **Journal choice** | Public Choice (new submission) or a comparable journal (J. Inst. Econ., EJPE, Expl. Econ. Hist., J. Econ. Hist., Cliometrica). | 1 week |

## 3. Journal options for a new paper

1. **Public Choice** (first choice if the rewrite is strong). The editor explicitly invited a new submission; the topic is squarely within the journal's scope.
2. **Journal of Institutional Economics**. Strong fit for institutions, state capacity, and long-run development.
3. **European Journal of Political Economy**. Good fit for political economy of state formation and collapse.
4. **Explorations in Economic History** / **Journal of Economic History** / **Cliometrica**. Fit if the empirical mechanism and historical data become the paper's center of gravity.
5. **Journal of Economic Behavior & Organization**. Fit for institutional and organizational aspects of state collapse.

A decision on the target journal should be made **after Phase 0–1**, once the feasible sample size and data quality are clear.

## 4. Immediate next action

The most urgent decision is whether to **salvage the 96-case dataset** (by rebuilding sources and applying a blind rubric) or to **start a smaller, well-documented sample** (e.g., 20–30 polities with rich historical records) and treat the 96-case set as an exploratory robustness check. The latter is less ambitious but more likely to survive referee scrutiny about historical accuracy and mechanism.
