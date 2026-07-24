# Pre-submission reviewer-eye critique — IJHPM package

## Scope and policy framing
- **High priority**: IJHPM requires explicit "Implications for Policy Makers / Public". The manuscript includes a numbered "Implications for Policy Makers" box, an "Implications for Public" paragraph, and a dedicated Discussion subsection. The title frames the paper as a structural-versus-audit governance question, which fits the journal's health-policy focus.
- **Medium priority**: The Introduction begins with institutional history and then moves to the policy question. A reviewer might prefer the policy/equity framing to lead; the current version is acceptable but could be strengthened by opening with the equity/policy implication.

## Methods and statistics
- **High priority**: The ecological (area-level) design is explicitly noted in the Limitations, and causal language is avoided ("predominantly structural", "associated with"). Good.
- **Medium priority**: `statsmodels` `MixedLM` emits convergence warnings during fitting. The point estimates are stable across the three sensitivity analyses, but a short Methods note on convergence/optimizer stability would reassure reviewers. Consider reporting that models were run with the default restricted maximum-likelihood optimizer and that coefficient signs/magnitudes were unchanged across sensitivity checks.
- **Resolved**: A covariate-adjusted sensitivity model was added, including the natural logarithm of population density and the anaesthesiologist share of all physicians (both standardised) from public MLIT and MHLW data. The university-hospital coefficient remained positive and statistically significant for general, epidural and continuous-epidural anaesthesia; it was attenuated and no longer significant for spinal anaesthesia. This addresses the most likely omitted-variable concern without exceeding the IJHPM table limit.

## Data and reproducibility
- **High priority**: All empirical numbers in the manuscript, tables, figures, cover letter and STROBE checklist are generated from `output/ijhpm_results.json`, which is produced by `scripts/compile_ijhpm_results.py` from the CSVs in `data/`. No hand-typed estimates remain in the IJHPM scripts.
- **High priority**: The audit-sensitivity bound is no longer hard-coded. It is derived from the publicly reported Social Insurance Medical Fee Payment Fund prefectural point-audit rates (`data/audit_rates_r04.csv`; source cited as reference 6). The maximum observed difference is 0.28 percentage points, which translates into a ratio shift of <1% of the interquartile range for general anaesthesia.
- **High priority**: Running `python3 scripts/build_ijhpm.py` from a clean state (deleting `output/ijhpm_results.json` and `documents/IJHPM/*`) regenerates all outputs. Verified.
- **Low priority**: `output/ijhpm_results.json` is excluded from git by `.gitignore`; users must run the build script before inspecting numbers. This is intentional and reproducible.

## Figures and tables
- **Low priority**: All figures and tables are inline, numbered sequentially, and cited in the text (Tables 1–3, Figures 1–2; total 5, within the IJHPM limit).
- **Low priority**: Table 2 reports six procedure codes, but the Discussion focuses on L008, L002, L003 and L004. L009 and L100 are used as staffing/proxy indicators and are appropriately described. Given the 5-item combined figure+table limit, no further moving is needed.
- **Low priority**: Figure resolution should be checked against IJHPM print guidelines (≥300 dpi) before final upload. The editable `.pptx` is provided for easy replacement.

## References and formatting
- **Medium priority**: All 30 references are real and traceable. Two previous source issues were corrected:
  - Reference 6 now cites the Social Insurance Medical Fee Payment Fund FY2022 prefectural audit statistics.
  - Reference 10 cites the official MHLW 2026 fee-schedule master PDF that documents the L008 airway-device wording.
  - Reference 13 URL was updated to the live Cabinet Office regional-variation portal.
- **Low priority**: A final formatting scrub for consistent en-dashes in page ranges and issue numbers would polish the Vancouver/AMA style, but the current list is scientifically acceptable.

## Strength of claims
- **High priority**: The central claim — regional variation is structural, not an audit artefact — is supported by (a) the small between-prefecture variance, (b) the positive cross-code correlations, (c) the audit-impact bound being <1% of IQR, and (d) the persistence of the university-hospital effect after empirical Bayes shrinkage and after combining reclassifiable codes. The wording "predominantly structural" and "dominant measured structural determinant" appropriately limits causal inference.
- **Medium priority**: The Discussion compares Japan with Taiwan, South Korea, Germany, France and the NHS. These are reasonable illustrations of transferability but should be read as such, not as empirically tested cross-country comparisons. The current phrasing is appropriately cautious.

## Final priority ranking
1. **Final reference-format scrub** (en-dashes, issue numbers) before Editorial Manager submission; does not block the PR.
2. **Figure resolution check** before final upload.
3. **Optional Introduction lead revision** to put the governance/equity framing first.
4. **MixedLM convergence note** is already included in Methods.

## Overall assessment
The IJHPM package meets the journal's structural and policy requirements, stays within word, figure and reference limits, and is now fully reproducible from public data and committed code. After the minor polishing items above, it is ready for submission.
