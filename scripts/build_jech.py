#!/usr/bin/env python3
"""One-command reproducible build for the Journal of Epidemiology & Community Health submission package.

Runs:
1. compile_ijhpm_results.py (data -> output/ijhpm_results.json)
2. create_ijqhc_fig1.py (regenerates figure PNGs from public GIS/SCR data)
3. create_jech_en.py (manuscript docx + separate title page)
4. create_jech_tables_docx.py (separate tables)
5. create_jech_figures_pptx.py (editable figure deck)
6. create_jech_cover_letter.py
7. create_jech_end_matter.py
8. create_jech_strobe.py
9. Packages documents/JECH/ + figure PNGs into jech_submission_package.zip

Requires: Python 3.10+, numpy, pandas, scipy, statsmodels, geopandas, matplotlib,
          shapely, python-docx, python-pptx
Optional: LibreOffice + pdftotext (poppler-utils) for STROBE page-number inference.
          Without them the STROBE checklist is still generated, but page numbers are blank.
"""
import os
import shutil
import subprocess
import sys
import zipfile

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
scripts = [
    'scripts/compile_ijhpm_results.py',
    'scripts/create_ijqhc_fig1.py',
    'scripts/create_jech_en.py',
    'scripts/create_jech_tables_docx.py',
    'scripts/create_jech_figures_pptx.py',
    'scripts/create_jech_cover_letter.py',
    'scripts/create_jech_end_matter.py',
    'scripts/create_jech_strobe.py',
]

for s in scripts:
    path = os.path.join(root, s)
    print(f"\n=== Running {s} ===")
    subprocess.run([sys.executable, path], check=True, cwd=root)

# Copy high-resolution English figure PNGs into the submission folder so they can
# be uploaded separately as JECH requires.
jech_dir = os.path.join(root, 'documents', 'JECH')
for src_name, dst_name in [
    ('rapm_fig1_en.png', 'figure1.png'),
    ('rapm_fig2_en.png', 'figure2.png'),
]:
    src = os.path.join(root, 'output', src_name)
    dst = os.path.join(jech_dir, dst_name)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")
    else:
        print(f"Warning: missing figure file {src}")

# Assemble submission zip
zip_path = os.path.join(root, 'jech_submission_package.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, _, filenames in os.walk(jech_dir):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            arc = os.path.relpath(full, root)
            zf.write(full, arc)

print(f"\n=== JECH package built successfully in {jech_dir} ===")
print(f"=== Submission zip: {zip_path} ===")
