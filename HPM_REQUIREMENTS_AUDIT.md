# HPM_REQUIREMENTS_AUDIT

Date: 2026-10-06. Target: The International Journal of Health Planning
and Management (Wiley). Article type: Research Article.

| Requirement | Current guidance | Package status |
|---|---|---|
| Article type | Research Article | Yes |
| Submission portal | Wiley Research Exchange (submission.wiley.com) | Noted in handoff |
| Abstract | <=250 words | 205 words, structured flow (Objectives/Methods/Results/Conclusions) |
| Main-text limit | <=7,000 words excl. abstract/keywords/highlights/tables/figures/refs | ~3,350 (hard gate in build) |
| References | up to 50 | 26, Vancouver numbered, order of appearance, no orphans (build fails) |
| Highlights | exactly 4, each <=80 chars incl. spaces | HPM_HIGHLIGHTS.txt, 4 items, char counts asserted in build |
| Keywords | up to 7 | 6 |
| Running title | <70 chars | "Malpractice litigation and physician supply in Japan" (53) |
| Cover letter | must name most suitable editorial theme | Names Theme 3 (Global health, health planning and interventions) |
| Blinded manuscript | anonymised main document for peer review | HPM_main_manuscript_blinded.docx: no author names/affiliations/acknowledgements; declarations non-identifying; metadata defaults |
| Figures/tables | scientifically useful set; readable | 2 tables + 2 figures + separate legends doc; PNG + 300-dpi TIFF + editable PPTX |
| Supplement | supporting information allowed | single HPM_supplement.docx (Tables 1-4, Figures 1-2) |
| STROBE | expected for observational research | HPM_STROBE_CHECKLIST.docx, completed with section refs |
| AI disclosure | Wiley policy: disclose use, not an author | Declarations + cover letter |
| ORCID | required for submitting author | 0000-0001-7261-9062 on title page + cover letter |
| Funding / conflict / data availability | statements required | title page + Declarations in manuscript |
| British English / TNR 12pt / captions 10pt | consistent | enforced by builder |

## Diffs vs JHSRP build
- Limit 3,500 -> 7,000 (no artificial expansion; text stays ~3,350).
- Refs 30 -> 50 (26 kept; no cosmetic HPM citations added).
- Abstract 300 -> 250 (205 already compliant).
- Keywords 3 -> up to 7 (now 6).
- New: 4 highlights <=80 chars, running title, explicit theme in cover
  letter, ORCID surfaced, filenames switched to HPM_*/blinded naming,
  zip renamed HPM_SUBMISSION_FINAL.zip.
