---
name: testing-healthcare-analytics-submission
description: Test the Healthcare Analytics manuscript build pipeline end-to-end. Use when verifying that the full reproducibility build regenerates the submission package from primary data, produces all required docx/pptx/png/zip outputs, and uses the correct global/Healthcare Analytics branding.
---

# Testing Healthcare Analytics Manuscript Build

## Prerequisites

- Python 3 with these packages importable: `docx`, `pptx`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `openpyxl`, `xlrd`, `pdfplumber`, `lxml`, and (optional) `latex2mathml`.
- LibreOffice (for optional docx→PDF visual checks)
- poppler-utils (`pdftoppm`, `pdftotext`) for PDF page renders
- ImageMagick (`display`, `montage`, `scrot` or `import`) for visual capture

If packages are missing: `pip install python-docx python-pptx pandas numpy scipy statsmodels matplotlib openpyxl xlrd pdfplumber lxml latex2mathml`.

## Quick Start

The Makefile no longer contains the `ha_submission` target; the HA submission script is run separately after `make all`.

```bash
cd medical_accident_its_analysis
make clean
rm -f data_primary/*.csv results/reanalysis_results.json output/ha_* output/fig*.png manuscript/ha_*
make all 2>&1 | tee /tmp/ha_make_all.log
python manuscript/build_healthcare_analytics_submission.py 2>&1 | tee /tmp/ha_submission.log
```

Expected final outputs:
- `results/reanalysis_results.json`
- `manuscript/ha_manuscript_en.docx`, `ha_title_page.docx`, `ha_cover_letter.docx`, `ha_highlights.docx`, `ha_supplementary.docx`
- `manuscript/ha_figures.pptx`, `ha_supplementary_figures.pptx`
- `output/ha_Figure_1.png`, `ha_Figure_2.png`
- `output/ha_Supplementary_Figure_1.png`, `ha_Supplementary_Figure_2.png`, `ha_Supplementary_Figure_3.png`
- `output/ha_submission.zip`

## Verification Checklist

### 1. Build completes without errors
- `make all` exit code is 0.
- `python manuscript/build_healthcare_analytics_submission.py` exit code is 0.
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

### 4. Content/branding checks
```python
import re
from docx import Document

# No "In Japan" sentence openings
text = '\n'.join(p.text for p in Document('manuscript/ha_manuscript_en.docx').paragraphs)
assert not re.findall(r'(?:^|[.!?]\s+|\n\s*)In Japan\b', text, re.IGNORECASE)

# No Japanese characters in the main manuscript
jap = r'[\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\uFF66-\uFF9F]'
assert len(re.findall(jap, text)) == 0

# No "health policy" branding anywhere
for fn in ['manuscript/ha_manuscript_en.docx','manuscript/ha_cover_letter.docx','manuscript/ha_title_page.docx']:
    t = '\n'.join(p.text for p in Document(fn).paragraphs)
    assert 'health policy' not in t.lower(), f'{fn} contains health policy'
```

### 5. Cover letter / title page target Healthcare Analytics
- `ha_title_page.docx` contains `Target journal: Healthcare Analytics (Elsevier)`.
- `ha_cover_letter.docx` is addressed to `Editor-in-Chief, Healthcare Analytics`.

### 6. Figure/table citation order in main manuscript
```python
import re
text = '\n'.join(p.text for p in Document('manuscript/ha_manuscript_en.docx').paragraphs)
main = [m for m in re.findall(r'(Table \d+|Figure \d+)', text) if not m.startswith('Supplementary')]
first = {m: main.index(m) for m in ['Table 1','Figure 1','Table 2','Figure 2']}
assert first['Table 1'] < first['Figure 1'] < first['Table 2'] < first['Figure 2']
```

### 7. Zip contents
```python
import zipfile
z = zipfile.ZipFile('output/ha_submission.zip')
assert len(z.namelist()) == 12
assert 'ha_manuscript_en.docx' in z.namelist()
```

The 12 expected basenames are:
`ha_manuscript_en.docx`, `ha_title_page.docx`, `ha_cover_letter.docx`, `ha_highlights.docx`, `ha_supplementary.docx`, `ha_figures.pptx`, `ha_supplementary_figures.pptx`, `ha_Figure_1.png`, `ha_Figure_2.png`, `ha_Supplementary_Figure_1.png`, `ha_Supplementary_Figure_2.png`, `ha_Supplementary_Figure_3.png`.

### 8. Optional visual proof
```bash
mkdir -p /tmp/ha_screenshots
libreoffice --headless --convert-to pdf --outdir /tmp/ha_screenshots manuscript/ha_manuscript_en.docx
pdftoppm -png -f 1 -l 1 -r 150 /tmp/ha_screenshots/ha_manuscript_en.pdf /tmp/ha_screenshots/ha_manuscript_en
```
Then open `/tmp/ha_screenshots/ha_manuscript_en-01.png` to visually confirm the global-framing title and Abstract.

## Known Issues

- `make clean` only removes `__pycache__`; a full clean for reproducibility may also require removing `data_primary/*.csv`, `results/reanalysis_results.json`, `output/ha_*`, `output/fig*.png`, and `manuscript/ha_*`.
- `python-pptx` may emit `UserWarning: Duplicate name` messages from `zipfile` while saving PPTX files; this is usually benign and the resulting files remain valid (verify with `Presentation(...)`).
- Opening the generated `.docx` in LibreOffice with a fresh user profile can trigger a Tip-of-the-Day dialog; use `--headless --convert-to pdf` for automated visual capture.

## Devin Secrets Needed

None — this is a fully local reproducibility build.
