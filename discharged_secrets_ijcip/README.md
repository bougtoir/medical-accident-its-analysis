# Discharged Secrets

## Current revision track

Following desk rejection of the conceptual IJCIP submission, the project is being rebuilt as a scoping review plus a reproducible, privacy-preserving audit of public shared-micromobility data.

- `PROTOCOL.md`: prospective study protocol;
- `REVISION_STRATEGY.md`: article redesign and claim boundaries;
- `review/`: open-metadata searches, screening codebook, candidate corpus, and extraction templates;
- `audit/`: GBFS collection, aggregation, document-audit, and framework-traceability tools;
- `data/`: frozen GBFS registry and privacy-preserving cross-sectional system-level observations;
- `results/`: aggregate preliminary audit results.

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

The audit never writes raw vehicle identifiers, coordinates, or deep links. Field-presence results are aggregate observations at the registered-system level. The outputs do not establish trip reconstruction, identifier-rotation nonconformity, hidden backend collection, compromise, or operator intent.

## Archived IJCIP submission package

Submission materials for the *International Journal of Critical Infrastructure Protection* (IJCIP).

## Build

```bash
python -m pip install -r requirements.txt
python build_submission.py
```

The build writes the complete submission package to `output/`, including:

- anonymized manuscript (`.docx` and reference `.pdf`) with inline figure and tables;
- separate title page, cover letter, highlights, and submission checklist;
- standalone editable tables (`.docx`);
- standalone figure (`.png`, `.tiff`, `.pdf`, and editable `.pptx`);
- reporting-guideline applicability statement;
- citation first-appearance audit;
- reference-verification report; and
- a ZIP archive containing the submission files.

## Validation

The build fails if:

- citations are not numbered in order of first appearance;
- a citation is missing from the reference list or a reference is uncited;
- a figure or table is absent from the manuscript text;
- the abstract exceeds 250 words;
- a highlight exceeds 85 characters; or
- an undefined abbreviation is detected from the configured abbreviation list.

The source article is a conceptual, structured evidence synthesis. It does not report human-participant research, a clinical study, or a systematic review; CONSORT, STROBE, and PRISMA are therefore not applicable.
