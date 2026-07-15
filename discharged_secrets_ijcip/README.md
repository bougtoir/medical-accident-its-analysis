# Discharged Secrets

## Current revision track

The project is an empirical, reproducible package: a PRISMA-ScR scoping review, a global field audit of public GBFS vehicle feeds, and a structured disclosure audit of public operator privacy notices. It was first prepared for *Computers & Security* (Elsevier); after desk rejection for scope mismatch it was reformatted for **Data & Policy** (Cambridge University Press) as a Research Article — author-date (Cambridge A) references, a Policy Significance Statement, single-blind (non-anonymized), ≤250-word abstract, and the journal's required disclosure statements. The next fallback target is *International Journal of Information Security*. `REVIEWER_REVIEW.md` records the pre-submission reviewer-perspective assessment and residual caveats.

- `PROTOCOL.md`: prospective study protocol;
- `REVISION_STRATEGY.md`: article redesign and claim boundaries;
- `REVIEWER_REVIEW.md`: critical reviewer-perspective review performed before finalization;
- `review/`: open-metadata searches, screening codebook, candidate corpus, abstract retrieval, screening, extraction, and document retrieval;
- `audit/`: GBFS collection, aggregation, document coding, and framework-traceability tools;
- `data/`: frozen GBFS registry, privacy-preserving cross-sectional observations, and coded document audit;
- `results/`: aggregate audit results.

### Rebuild the bibliographic candidate corpus

```bash
python review/search_open_metadata.py \
  --config review/search_queries.json \
  --output review/candidates.csv \
  --log review/search_log.csv

python review/initialize_screening.py \
  --candidates review/candidates.csv \
  --seeds review/direct_evidence_seeds.csv \
  --output review/screening.csv

python review/validate_screening.py \
  --screening review/screening.csv
```

Abstracts, deterministic screening, and study-level extraction are then produced by:

```bash
python review/fetch_abstracts.py      # OpenAlex abstracts -> review/.abstract_cache.csv (git-ignored)
python review/screen_records.py       # deterministic title/abstract + full-text decisions
python review/build_extraction.py     # 18-study extraction -> review/evidence_extraction.csv
```

### Rebuild the GBFS cross-sectional audit

```bash
python audit/gbfs_cross_sectional_audit.py \
  --registry-output data/gbfs_registry.csv \
  --audit-output data/gbfs_cross_sectional_audit.csv \
  --metadata-output data/gbfs_audit_metadata.csv

python audit/summarize_gbfs_audit.py \
  --audit data/gbfs_cross_sectional_audit.csv \
  --summary-csv results/gbfs_summary.csv \
  --operator-csv results/gbfs_operator_summary.csv \
  --summary-md results/gbfs_preliminary_summary.md

python audit/select_operator_sample.py \
  --operator-summary results/gbfs_operator_summary.csv \
  --output audit/operator_sample.csv
```

### Rebuild the public-document disclosure audit

```bash
python review/fetch_documents.py      # cache operator privacy notices under review/.doc_cache/ (git-ignored)
python audit/code_documents.py        # deterministic 14-domain coding -> data/document_audit.csv
```

Document coding is computer-assisted and single-reviewer. `not_found` denotes silence in a document, not evidence that a practice is absent; every coding carries a short verbatim locator quotation. Full document bodies are never committed.

The audit never writes raw vehicle identifiers, coordinates, or deep links. Field-presence results are aggregate observations at the registered-system level. The outputs do not establish trip reconstruction, identifier-rotation nonconformity, hidden backend collection, compromise, or operator intent.

## Build

```bash
python -m pip install -r requirements.txt
python build_submission.py
```

The build writes the complete submission package to `output/`, including:

- the non-anonymized manuscript (`Manuscript_DataPolicy.docx`) with the abstract, a 120-word Policy Significance Statement, five figures and five tables placed inline, the required disclosure statements, and an alphabetised author-date reference list;
- separate title/author page, cover letter, and submission checklist;
- standalone editable tables (`Tables_DataPolicy_editable.docx`);
- five standalone figures (`.png`, `.tiff`, `.pdf` at 600 dpi) and an editable `Figures_DataPolicy_editable.pptx` (one figure per slide);
- PRISMA-ScR reporting-guideline statement;
- author-date citation audit;
- reference-verification report (live DOI/URL resolution with offline fallback); and
- `DataPolicy_submission_package.zip` containing the submission files.

## Validation

The build fails if:

- any in-text citation does not resolve to a reference, or a reference is uncited (no orphan/phantom references);
- the reference list is not alphabetised by author;
- an unresolved `[[...]]` citation marker leaks into the rendered text;
- a figure or table is absent from the manuscript text;
- the abstract exceeds 250 words;
- the Policy Significance Statement is not ~120 words;
- more than five keywords are supplied;
- a required disclosure statement (data availability, funding, competing interests) is missing;
- all five figures or five tables are not present and cited; or
- an undefined abbreviation is detected from the configured abbreviation list.

The review component is reported in line with PRISMA-ScR. The study analyses only publicly accessible feeds and documents; it does not report human-participant research, so CONSORT and STROBE are not applicable.
