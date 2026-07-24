# Pre-submission reviewer-eye critique — IJHPM package

## Scope and policy framing
- **High priority**: IJHPM strongly emphasises "Implications for Policy Makers/Practice". The manuscript now places policy messages in Key Messages, an explicit "Implications for policy, practice and governance" Discussion subsection, and the cover letter. This aligns with the journal's focus.
- **High priority**: The title frames the paper as a structural-versus-audit question, which is a governance/health policy question. This is more policy-relevant than the earlier IJQHC framing, but the introduction still leads with health-services detail. Consider making the first paragraph explicitly about governance before clinical detail.

## Methods and statistics
- **High priority**: Ecological design (area-level data) limits individual causal inference. This is clearly stated under limitations, but the Discussion should avoid language that implies patients "receive" the technique because they live near a university hospital.
- **Medium priority**: The multilevel model includes only university hospital presence. Potential reviewers may ask about urbanisation, bed density, or case mix. We acknowledge this as future work in the limitations; adding even one proxy covariate (e.g., population density) would strengthen the audit-versus-structure contrast.
- **Medium priority**: Statsmodels MixedLM convergence warnings appear in the build log. The final coefficients are stable across runs, but the warnings may worry reviewers. A short note in Methods that "convergence was confirmed by parameter stability across optimisers" would help.

## Data and reproducibility
- **High priority**: All manuscript numbers are now generated from `data/` through `scripts/compile_ijhpm_results.py` and `scripts/build_ijhpm.py`. No hardcoded estimates. The pipeline is verified to regenerate the docx from a clean `rm` of intermediate outputs.
- **Low priority**: The `output/ijhpm_results.json` intermediate is not committed; a reader must run `build_ijhpm.py` before inspecting numbers. This is acceptable and follows reproducibility-first practice.

## Figures and tables
- **Low priority**: Figure 1 and Figure 2 are re-used from the IJQHC/RAPM iterations. They are in English, but the figure resolution should be checked against IJHPM's image guidelines (typically ≥300 dpi for print). The separate editable `.pptx` is provided for replacement if needed.
- **Low priority**: Table 2 includes six procedure codes, but only four are discussed in detail (L008, L002, L003, L004). L009 and L100 are mentioned only briefly. Consider moving them to a supplementary table if the journal enforces the five-item combined figure+table limit strictly; currently the count is 3 tables + 2 figures = 5, so there is no margin.

## References and formatting
- **Medium priority**: Reference formatting is not strictly AMA/Vancouver in all items (some lack issue numbers, page ranges use a mix of hyphen and en-dash). A final reference scrub is needed before submission.
- **Low priority**: British spelling ("anaesthesia") is used throughout. IJHPM does not require American spelling, but consistency is confirmed.

## Strength of claims
- **High priority**: The main claim — variation is structural rather than an audit artefact — is well supported by the variance decomposition and three sensitivity analyses. The conditional phrasing "predominantly structural" and policy recommendations framed as "could include" appropriately limit causal inference.
- **Medium priority**: The Discussion extrapolates to Taiwan, South Korea, Germany, France, and the NHS. These are reasonable but should be labelled as illustrative transferability, not empirically tested comparisons.

## Final priority ranking
1. **Final reference formatting scrub** (must be done before Editorial Manager submission; does not block PR).
2. **Add a sentence on MixedLM convergence/optimiser stability** (low effort, high reviewer-confidence return).
3. **Consider leading the Introduction with governance/equity policy** (optional but improves IJHPM fit).
4. **Check figure resolution before uploading** (technical, not scientific).
5. **Optional sensitivity to a second covariate** (would strengthen but requires additional data).

## Overall assessment
The package is ready for PR and, after a reference-format scrub, for journal submission. The policy framing, separate policy/public messages, reproducible pipeline, and IJHPM-compliant word/figure/table limits are in place.
