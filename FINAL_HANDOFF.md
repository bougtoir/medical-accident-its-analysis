# FINAL_HANDOFF — Public Health submission package (v2, finishing pass)

Date: 2026-09-30. Prepared from branch `devin/1790751667-public-health-submission`
in `bougtoir/wip`, synced to `bougtoir/medical-accident-its-analysis` via
sync-to-repos.yml after merge.

## Final title (identical across manuscript, title page, cover letter)

**Malpractice litigation, physician supply and service capacity in Japan,
2008–2024: a national equivalence analysis**

Refined in the finishing pass from "...and specialty-level physician and
hospital supply..." for consistency with the manuscript's service-capacity
terminology. No scientific claim changed.

## Package

`output/PUBLIC_HEALTH_submission_FINAL_v3.zip` (27 files; supersedes v2:

- ph_manuscript_en_v3.docx — anonymised manuscript, AMA superscript citations,
  "[Table/Figure n near here]" placement markers, main body ~2,734 words
- ph_manuscript_en_inline_v3.docx — same text with figures/tables embedded
- ph_title_page.docx — title, author (Onishi Tatsuki), institution (DSAI
  Promotion Center, Shiga University), DoI, corresponding-author block,
  running title, word count, article type, AI declaration, data availability,
  CRediT statement
- ph_cover_letter_v3.docx — dated 30 September 2026; fit / what is known / what
  study adds / single transfer-provenance sentence / originality declarations
- ph_declaration_of_interests.docx — standalone DoI ("none")
- ph_tables.docx, ph_figure_legends.docx, ph_supplementary.docx
- ph_figures.pptx, ph_supplementary_figures.pptx — editable figures
- ph_Figure_1/2.png+.tiff, ph_Supplementary_Figure_1/2.png+.tiff — 300 dpi
- DEVIN_PUBLIC_HEALTH_TRANSFER_PROMPT.txt, DEVIN_PUBLIC_HEALTH_FINISHING_PASS.txt, DEVIN_PUBLIC_HEALTH_CONTRIBUTION_ALIGNMENT_PROMPT.txt
- _internal_QC/ — the five audit files (internal only, not for journal upload)

## Verified limits (Public Health Guide for Authors, fetched 2026-09-30)

- Original Research: main body 2,734 words ≤ 3,000; structured abstract
  195 words ≤ 250 with required headings; 6 keywords.
- 2 tables + 2 figures = 4 display items ≤ 5; 26 references ≤ 50, AMA order.
- Zero CJK chars; no HPT/resubmission text; British English; DoI in title
  page AND separate document; standard funding sentence; ethics statement;
  Elsevier AI disclosure (states author reviewed/edited and takes full
  responsibility).

## Analysis integrity

- Analyses changed: **NO** (frozen; `make ph_submission` regenerates all
  numbers from `data_primary/`).
- Numerical corrections in this pass: none — audit found all values matching
  `results/reanalysis_results.json`, including hospital growth 95% CI
  −0.0050 to +0.0056 (prompt verification set).
- Final key estimates: physician growth coef −0.0009 (95% CI −0.0043 to
  +0.0025, p=0.56); hospital growth coef +0.0003 (p=0.90); physician
  equivalence ±1% TOST p=0.023 (point −0.21%, 90% CI −0.84% to +0.42%);
  hospital equivalence ±2% TOST p=0.002 (±1% not equivalent, p=0.059);
  JOCS-CP hospital coef +0.0242, p=0.013 (exploratory).
- Final equivalence interpretation: "equivalent within the specified
  policy-relevant margin" — margins "specified for the present analysis",
  not a priori/preregistered.
- Preferred implication preserved: litigation exposure alone is unlikely to
  explain specialty-level workforce change of a magnitude relevant to
  workforce planning in Japan.

## Exact remaining manual fields (only two, both on the title page)

1. `[main degrees (two only)]`
2. `[corresponding author email]`
3. `[telephone]`

(Cover letter no longer contains placeholders; dated; signed "Tatsuki Onishi".)

## Verdict

**READY FOR PUBLIC HEALTH TRANSFER.**

Accept the Elsevier transfer offer (HLPT-D-26-01803, deadline 2026-10-30) via
the link in the transfer e-mail, then replace the transferred files with the
contents of `PUBLIC_HEALTH_submission_FINAL_v2.zip` (fill the three title-page
fields first).
