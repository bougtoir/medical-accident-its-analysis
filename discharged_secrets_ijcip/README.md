# Discharged Secrets — IJCIP submission package

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
