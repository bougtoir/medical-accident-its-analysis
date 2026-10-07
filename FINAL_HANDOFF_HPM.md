# FINAL_HANDOFF_HPM

Date: 2026-10-06. Branch: devin/1791333840-hpm-submission.

## Final status: READY FOR HPM SUBMISSION

- Final title: Malpractice litigation, physician supply and service
  capacity in Japan, 2008–2024: a national equivalence analysis
- Running title: Malpractice litigation and physician supply in Japan (53 chars)
- Target journal: The International Journal of Health Planning and
  Management (Wiley); portal: Wiley Research Exchange (submission.wiley.com)
- Article type: Research Article
- Selected theme: **Theme 3 — Global health, health planning and
  interventions**. Rationale: the paper asks a health-planning question
  (how systems should evaluate a widely invoked workforce determinant)
  using national longitudinal data; it is not a financing/economics
  paper (Theme 1) and not a management/digital-health/analytics paper
  (Theme 2). Named explicitly in the cover letter.
- Abstract word count: 205 (≤250; structured flow, no citations)
- Main-text word count: ~3,352 (≤7,000; no artificial expansion)
- Reference count: 26 (≤50; Vancouver, order of appearance, no orphans)
- Figures/tables/boxes: 2 tables + 2 figures; online supplement 1 file
- Keywords: 6 (≤7): physician supply; malpractice litigation;
  equivalence testing; workforce planning; health policy; Japan

## Highlights (all ≤80 chars, counts verified in build)
- Litigation rates and workforce supply in 12 Japanese specialties,
  2008-2024 (75)
- Exposure scaled to specialty size; measured biennial census waves
  only (70)
- Physician-supply effect bounded within ±1% biennial change (TOST) (65)
- Equivalence bounds help planners rank candidate workforce
  determinants (70)

## Freeze confirmations
- Analysis changed: NO. Numerical results changed: NO. Equivalence
  margins changed: NO.
- p values and CIs retained; TOST interpretation correct (bounds, not
  "no effect"); ecological caveat in abstract + Limitations; JOCS-CP
  exploratory/non-causal; no no-fault superiority claim; no
  individual-level inference.

## Final key estimates (unchanged)
- Physician: coef −0.0009, 95% CI −0.0043 to +0.0025, p=0.56, n=96
- Hospital: coef +0.0003, 95% CI −0.0050 to +0.0056, p=0.90
- Physician equivalence: ±1% margin, TOST p=0.023 (point −0.21%, 90% CI
  −0.84 to +0.42%)
- Service-capacity equivalence: ±2% margin, TOST p=0.002 (±1% not
  equivalent, p=0.059 — reported)

## Exact planning-relevance statement
"For health-services workforce planning, the implication is that
specialty maldistribution is likely shaped by multiple structural
determinants—remuneration, training pipelines, workload and working
conditions, and geographic incentives—and that routine civil-litigation
exposure contributes at most a small share of measured supply change."

## Exact international-relevance statement
"The transferable question is not specific to Japan: how should a health
system evaluate a widely invoked workforce determinant when the decision
that matters is whether its effect is large enough to be operationally
relevant?"
Cover-letter comparative-value line: "country-specific estimates can
inform international planning when they bound mechanisms that are often
assumed, rather than measured, to influence workforce supply."

## Exact "what this study adds" statement
"the analysis narrows the plausible contribution of litigation to
specialty-level workforce change: rather than merely failing to detect
an association, it places an empirical bound on the magnitude that such
an association could reasonably take within this setting."

## Unresolved manual metadata
- Corresponding author telephone: not available in source files; not
  listed (email bougtoir@gmail.com and ORCID 0000-0001-7261-9062 are
  populated). Add in the Research Exchange form if required.
- No other placeholders.

## Files in HPM_SUBMISSION_FINAL.zip
- HPM_main_manuscript_blinded.docx (anonymised, placement markers)
- HPM_main_manuscript_inline.docx (review copy)
- HPM_title_page.docx, HPM_cover_letter.docx (Theme 3 named)
- HPM_HIGHLIGHTS.txt, HPM_tables.docx, HPM_figure_legends.docx
- HPM_supplement.docx (Supplementary Tables 1–4, Figures 1–2)
- HPM_STROBE_CHECKLIST.docx (completed, section-referenced)
- hpm_figures.pptx, hpm_supplementary_figures.pptx (editable)
- hpm_Figure_1.png/.tiff, hpm_Figure_2.png/.tiff,
  hpm_Supplementary_Figure_1.png/.tiff, hpm_Supplementary_Figure_2.png/.tiff
- DEVIN_HPM_REVISION_PROMPT.txt
- _internal_QC/: HPM_REQUIREMENTS_AUDIT.md, HPM_HOSTILE_EDITOR_REVIEW.md,
  HPM_REFERENCE_AUDIT.md, HPM_CLAIM_CALIBRATION.md, this file

## Build
`cd medical_accident_its_analysis && python3 manuscript/build_hpm_submission.py`
(or `make hpm_submission`). Hard gates: ≤7,000 words, ≤250-word abstract,
exactly 4 highlights ≤80 chars, no orphan references, missing result
keys fail.
