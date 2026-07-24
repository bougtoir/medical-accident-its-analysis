# Archaic Introgression × Language Typology

Does archaic hominin introgression (Neanderthal/Denisovan) predict language typological features?

## Key Finding

- **Denisovan introgression ~ morphological type**: KW p = 0.034 (significant raw)
- **After geographic control**: partial Mantel r = -0.025, p = 0.66 (null)
- **Interpretation**: Geography mediates the signal; archaic DNA shaped linguistic *capacity* (FOXP2 desert), not specific typology

## Contents

```
scripts/
  archaic_language_analysis.py    Main analysis (Mantel, KW, MWU, bootstrap)
  create_manuscript_en.py         English manuscript generator
  create_manuscript_ja.py         Japanese manuscript generator
  create_figures_pptx.py          Editable figures PPTX
data/
  population_language_map.csv     65 populations with language typology annotations
  analysis_results.csv            Statistical test results
figures/
  fig1-5_*.png                    Analysis figures (300 dpi)
docs/
  literature_review.md            Prior work summary
```

## Data Sources

- **Archaic introgression**: hmmix (1000G + HGDP, 66 populations) via `../denisovan-archaic-dna-analysis/`
- **Language typology**: WALS (World Atlas of Language Structures) v2020.4

## Usage

```bash
# Run full analysis
python scripts/archaic_language_analysis.py

# Generate manuscripts
python scripts/create_manuscript_en.py
python scripts/create_manuscript_ja.py
python scripts/create_figures_pptx.py
```

## Requirements

```
pip install matplotlib numpy pandas scipy cartopy python-docx python-pptx
```
