#!/usr/bin/env python3
"""One-command reproducible build for the BMJ Quality & Safety submission package.

Runs:
1. compile_ijhpm_results.py (data -> output/ijhpm_results.json)
2. create_bmjqs_en.py (manuscript docx + separate title page)
3. create_bmjqs_tables_docx.py (separate tables)
4. create_bmjqs_figures_pptx.py (editable figure deck)
5. create_bmjqs_cover_letter.py
6. create_bmjqs_end_matter.py
7. create_bmjqs_strobe.py

Requires: Python 3.10+, numpy, pandas, scipy, statsmodels, python-docx, python-pptx
"""
import subprocess
import sys
import os

scripts = [
    'scripts/compile_ijhpm_results.py',
    'scripts/create_bmjqs_en.py',
    'scripts/create_bmjqs_tables_docx.py',
    'scripts/create_bmjqs_figures_pptx.py',
    'scripts/create_bmjqs_cover_letter.py',
    'scripts/create_bmjqs_end_matter.py',
    'scripts/create_bmjqs_strobe.py',
]

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for s in scripts:
    path = os.path.join(root, s)
    print(f"\n=== Running {s} ===")
    subprocess.run([sys.executable, path], check=True, cwd=root)

print("\n=== BMJ Quality & Safety package built successfully in documents/BMJ_QS/ ===")
