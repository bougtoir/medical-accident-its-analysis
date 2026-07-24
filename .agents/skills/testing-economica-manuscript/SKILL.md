---
name: testing-economica-manuscript
description: Test the gdp_tempo_paper manuscript build pipeline and verify Economica format compliance. Use when verifying section headings, references, tables, or PDF output changes.
---

# Testing Economica Manuscript Build

## Prerequisites

- LibreOffice (libreoffice-writer, libreoffice-core) for docx→PDF conversion
- poppler-utils (pdftotext, pdffonts, pdftoppm, pdfinfo) for PDF verification
- These should be in the environment blueprint; if missing: `sudo apt-get install -y libreoffice-writer libreoffice-core poppler-utils`

## Quick Start

```bash
cd gdp_tempo_paper/scripts
python3 build_docx_pptx.py
```

Expected outputs in `gdp_tempo_paper/manuscript/`:
- `manuscript_en.docx`, `manuscript_en.pdf`
- `manuscript_ja.docx`, `manuscript_ja.pdf`
- `table1_model_metrics.docx` through `table5_tempo_artifact.docx`
- `figures_en.pptx`

## Economica Format Verification Checklist

### 1. Section Headings (Roman numerals, ALL CAPS, centered)
```bash
pdftotext manuscript_en.pdf - | grep -E '^(INTRODUCTION|[IVX]+ [A-Z])'
```
Expected: INTRODUCTION (no number), II RELATED LITERATURE, III THEORY, IV DATA AND METHODS, V RESULTS, VI DISCUSSION, VII CONCLUSION

### 2. Subsection Headings (Roman prefix)
```bash
pdftotext manuscript_en.pdf - | grep -E '^[IVX]+\.[0-9]+ ' | head -15
```
Expected: III.1, III.2, ..., VI.5 (no Arabic like 3.1, 4.2)

### 3. Cross-references in body text
```bash
# EN: should return 0 matches
grep -c 'Section [2-7]' manuscript_en.md
grep -c '§[2-7]\.' manuscript_en.md

# JA: should return 0 matches
grep -cP '第\s*[2-7]\s*節' manuscript_ja.md
grep -cP '[2-7]\.[0-9]+\s*節' manuscript_ja.md
```

### 4. References (Economica Harvard format)
```bash
pdftotext manuscript_en.pdf - | sed -n '/^REFERENCES/,$ p' | grep -E '^[A-Z]{2,},' | head -10
```
Expected: SURNAME, INITIALS. (year). format — e.g. `SOLOW, R.M. (1957).`

Watch for hyphenated names: KOHLER, H.-P. (not H.), LANGE, G.-M. (not G.), FITOUSSI, J.-P. (not J.)

### 5. JEL codes and keywords
```bash
pdftotext -l 2 manuscript_en.pdf - | grep 'JEL'
pdftotext -l 2 manuscript_en.pdf - | grep 'Keywords'
```
Expected: Max 3 JEL codes, max 5 keywords

### 6. Tables (no vertical rules)
Visual check — convert table page to image:
```bash
# Find table page
for p in $(seq 30 46); do
  pdftotext -f $p -l $p manuscript_en.pdf - 2>/dev/null | grep -q 'Table 1' && echo "Page $p" && break
done
pdftoppm -png -r 150 -f <page> -l <page> manuscript_en.pdf /tmp/table_check
```
Then view the image — tables should have horizontal lines only.

### 7. Font embedding
```bash
pdffonts manuscript_en.pdf
```
All fonts must show `emb=yes`. Linux LibreOffice uses Liberation Serif (metrically identical to Times New Roman). For actual Times New Roman, convert on Windows/Mac Word.

### 8. Data availability URL
```bash
pdftotext -l 2 manuscript_en.pdf - | grep 'gdp-tempo-paper'
```
Expected: `https://github.com/bougtoir/gdp-tempo-paper`

## Known Issues

- Table 1 CSV contains raw LaTeX notation (`$\mu^\star$`, `$K_I$`) that renders as plain text in the docx/PDF. This is a data source issue, not a build script issue.
- LibreOffice PDF conversion may take 30-60 seconds per file. The build script has a 120-second timeout per file.

## Devin Secrets Needed

None — this is a local build and verification workflow with no external service dependencies.
