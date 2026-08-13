#!/usr/bin/env python3
"""One-command reproducible build for the Health Policy submission package.

Runs:
1. compile_ijhpm_results.py (data -> output/ijhpm_results.json)
2. create_ijqhc_fig1.py (regenerates figure PNGs from public GIS/SCR data)
3. create_health_policy_en.py (manuscript docx + separate title page)
4. create_health_policy_tables_docx.py (separate tables)
5. create_health_policy_figures_pptx.py (editable figure deck)
6. create_health_policy_highlights.py (Highlights / Key Points)
7. create_health_policy_cover_letter.py
8. create_health_policy_strobe.py
9. Copies figure PNGs into documents/Health_Policy/
10. Packages documents/Health_Policy/ into health_policy_submission_package.zip

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
    'scripts/create_health_policy_en.py',
    'scripts/create_health_policy_tables_docx.py',
    'scripts/create_health_policy_figures_pptx.py',
    'scripts/create_health_policy_highlights.py',
    'scripts/create_health_policy_cover_letter.py',
    'scripts/create_health_policy_strobe.py',
]

for s in scripts:
    path = os.path.join(root, s)
    print(f"\n=== Running {s} ===")
    subprocess.run([sys.executable, path], check=True, cwd=root)

# Copy high-resolution English figure PNGs into the submission folder so they can
# be uploaded separately.
hp_dir = os.path.join(root, 'documents', 'Health_Policy')
for src_name, dst_name in [
    ('rapm_fig1_en.png', 'figure1.png'),
    ('rapm_fig2_en.png', 'figure2.png'),
]:
    src = os.path.join(root, 'output', src_name)
    dst = os.path.join(hp_dir, dst_name)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {src} -> {dst}")
    else:
        print(f"Warning: missing figure file {src}")

# Generate TIFF versions at 300 dpi for Elsevier artwork upload.
try:
    from PIL import Image
    for png_name in ['figure1.png', 'figure2.png']:
        png_path = os.path.join(hp_dir, png_name)
        tiff_path = os.path.join(hp_dir, png_name.replace('.png', '.tiff'))
        if os.path.exists(png_path):
            im = Image.open(png_path)
            # Preserve alpha if present; most journals prefer RGB for TIFF.
            if im.mode == 'RGBA':
                # Composite onto white background to avoid black background in TIFF.
                bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
                im = Image.alpha_composite(bg, im).convert('RGB')
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            im.save(tiff_path, 'TIFF', dpi=(300, 300), compression='tiff_lzw')
            print(f"Saved {tiff_path}")
except Exception as e:
    print(f"Warning: could not generate TIFF figures: {e}")

# Assemble submission zip
zip_path = os.path.join(root, 'health_policy_submission_package.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, _, filenames in os.walk(hp_dir):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            arc = os.path.relpath(full, root)
            zf.write(full, arc)

print(f"\n=== Health Policy package built successfully in {hp_dir} ===")
print(f"=== Submission zip: {zip_path} ===")
