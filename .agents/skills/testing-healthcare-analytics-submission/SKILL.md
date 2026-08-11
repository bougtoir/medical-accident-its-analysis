---
name: testing-healthcare-analytics-submission
description: Test the Healthcare Analytics manuscript build pipeline end-to-end. Use when verifying that make ha_submission regenerates the submission package from primary data, produces all required docx/pptx/png/zip outputs, and contains the correct journal branding.
---

# Testing Healthcare Analytics Manuscript Build

## Prerequisites

- Python 3 with these packages importable: `docx`, `pptx`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `openpyxl`, `xlrd`, `pdfplumber`
- LibreOffice (for optional docx→PDF visual checks)
- poppler-utils (`pdftoppm`, `pdftotext`) for PDF page renders

If packages are missing: `pip install python-docx python-pptx pandas numpy scipy statsmodels matplotlib openpyxl xlrd pdfplumber`.

## Quick Start

```bash
cd medical_accident_its_analysis
make clean
rm -f data_primary/*.csv results/reanalysis_results.json output/ha_* manuscript/ha_*
make ha_submission 2>&1 | tee /tmp/ha_build.log
```

Expected final outputs:
- `results/reanalysis_results.json`
- `manuscript/ha_manuscript_en.docx`, `ha_title_page.docx`, `ha_cover_letter.docx`, `ha_highlights.docx`, `ha_supplementary.docx`
- `manuscript/ha_figures.pptx`, `ha_supplementary_figures.pptx`
- `output/ha_Figure_1.png`, `ha_Figure_2.png`, `ha_Supplementary_Figure_1.png`, `ha_Supplementary_Figure_2.png`
- `output/ha_submission.zip`

## Verification Checklist

### 1. Build completes without errors
- `make ha_submission` exit code is 0.
- No unhandled Python exceptions or missing-file errors.

### 2. All expected files are non-empty
```bash
for p in results/reanalysis_results.json manuscript/ha_*.docx manuscript/ha_*.pptx output/ha_*.png output/ha_submission.zip; do
  [ -s "$p" ] && echo OK "$p" || echo MISSING "$p"
done
```

### 3. Manuscript sections present
```python
from docx import Document
d = Document('manuscript/ha_manuscript_en.docx')
text = '\n'.join(p.text for p in d.paragraphs)
for s in ['Abstract','Keywords','Introduction','Materials and methods','Results','Discussion','Limitations','Conclusions','Declaration of generative AI use','Declarations','References']:
    assert s in text, f'missing {s}'
assert 'Litigation risk and specialty-level physician workforce' in text
```

### 4. No Health Policy branding
```python
from docx import Document
for fn in ['manuscript/ha_manuscript_en.docx','manuscript/ha_cover_letter.docx','manuscript/ha_title_page.docx']:
    text = '\n'.join(p.text for p in Document(fn).paragraphs)
    assert 'health policy' not in text.lower(), f'{fn} contains Health Policy'
```

### 5. Cover letter / title page target Healthcare Analytics
- `ha_title_page.docx` contains `Target journal: Healthcare Analytics (Elsevier)`.
- `ha_cover_letter.docx` is addressed to `Editor-in-Chief, Healthcare Analytics`.

### 6. Zip contents
```python
import zipfile
z = zipfile.ZipFile('output/ha_submission.zip')
assert len(z.namelist()) == 12
assert 'ha_manuscript_en.docx' in z.namelist()
```

### 7. Optional visual proof
```bash
libreoffice --headless --convert-to pdf --outdir /tmp/ha_screenshots manuscript/ha_manuscript_en.docx
pdftoppm -png -f 1 -l 1 -r 150 /tmp/ha_screenshots/ha_manuscript_en.pdf /tmp/ha_screenshots/ha_manuscript_en
```
Then open `/tmp/ha_screenshots/ha_manuscript_en-1.png` to visually confirm title and Abstract.

## Known Issues

- `make clean` only removes `__pycache__`; a full clean for reproducibility may also require removing `data_primary/*.csv`, `results/reanalysis_results.json`, `output/ha_*`, and `manuscript/ha_*`.
- `python-pptx` may emit `UserWarning: Duplicate name` messages from `zipfile` while saving PPTX files; this is usually benign and the resulting files remain valid (verify with `Presentation(...)`).
- Opening the generated `.docx` in LibreOffice with a fresh user profile can trigger a Tip-of-the-Day dialog; use `--headless --convert-to pdf` for automated visual capture.

## Devin Secrets Needed

None — this is a fully local reproducibility build.
