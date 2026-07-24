# Transport Policy submission requirements checked on 24 July 2026

Target journal: **Transport Policy** (Elsevier), hybrid open access, double-anonymized peer review.

## Scope and article positioning

Transport Policy publishes research on policy and strategy towards sustainable, safe, and efficient transport. This manuscript is submitted as a **Full Article**. It contributes:

1. a PRISMA-ScR evidence map of direct data-exposure evidence in shared micromobility;
2. a global, privacy-preserving audit of what public GBFS vehicle feeds actually disclose;
3. a structured audit of public operator lifecycle-disclosure documents; and
4. a reproducible lifecycle exposure model linking evidence strength to procurement, regulatory, and transparency choices.

## Format

- **Full Article**, normally up to 8,000 words excluding references.
- **Abstract** of no more than 250 words, unstructured.
- **Highlights**: 3-5 bullets, each no more than 85 characters including spaces.
- **1-7 keywords**, separated by semicolons; avoid multi-word keywords containing "and" or "of".
- **Author-date (Harvard) references**: in-text citations give author surname(s) and year separated by a comma (e.g. `(Elzer et al., 2025)`); three or more authors use `et al.`; the reference list is alphabetised by first author and works by the same author are ordered chronologically.
- The manuscript is **anonymized** (Transport Policy uses double-anonymized peer review); author details are supplied only on the separate title page and cover letter.

## Required disclosure statements

Placed after the main text and before the references:

- **Data availability statement** (required) — states where the registry snapshot, screening decisions, coding sheets, results, and code are available to reviewers, and the restrictions on raw identifiers/coordinates;
- **Funding statement** (required);
- **Competing interests** (required).

Additionally supplied as good practice: acknowledgements, author contributions, an ethical-standards statement, and a generative-AI use statement.

## Figures and tables

- Five figures and five tables, each cited in the body before or at first appearance and placed immediately after that paragraph.
- Figures are also supplied separately as editable PowerPoint, plus 600-dpi PNG, PDF, and TIFF; tables are supplied in a separate editable Word file.
- Numbered consecutively in Arabic numerals with captions supplied.

## Reproducibility

`build_submission.py` regenerates the whole package from the committed data, review, and results files. All reported counts, proportions, and confidence intervals are read from `results/`, `data/`, and `review/`; none are hard-coded. Source files are not required at initial submission but are retained and can be supplied if accepted.

## Sources

- Transport Policy guide for authors: <https://www.sciencedirect.com/journal/transport-policy/publish/guide-for-authors>
- Transport Policy Elsevier Harvard reference style example (Paperpile): <https://paperpile.com/s/transport-policy-citation-style/>

The author should recheck the live submission-system item list and the exact Transport Policy template immediately before upload.
