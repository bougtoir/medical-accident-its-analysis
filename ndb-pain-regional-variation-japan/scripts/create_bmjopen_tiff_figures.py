#!/usr/bin/env python3
"""Create TIFF figures for BMJ Open submission.

Converts existing EN PNG figures to 300 DPI TIFF files.
BMJ Open: min 300 DPI for photographs, 600 DPI for line art.
Accepted formats: TIFF, EPS, JPEG, PDF.
"""

import os
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
BMJOPEN_DIR = os.path.join(OUTPUT_DIR, 'bmjopen')
os.makedirs(BMJOPEN_DIR, exist_ok=True)

figure_map = {
    'fig1_neuropathic_unadjusted_en.png': 'BMJOpen_figure1.tiff',
    'fig2_confounder_correlations_en.png': 'BMJOpen_figure2.tiff',
    'fig4_region_unadj_vs_adj_en.png': 'BMJOpen_figure3.tiff',
}

for src_name, dst_name in figure_map.items():
    src_path = os.path.join(OUTPUT_DIR, src_name)
    dst_path = os.path.join(BMJOPEN_DIR, dst_name)

    if not os.path.exists(src_path):
        print(f'WARNING: Source not found: {src_path}')
        continue

    img = Image.open(src_path)
    if img.mode == 'RGBA':
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    img.save(dst_path, format='TIFF', dpi=(300, 300), compression='tiff_lzw')
    print(f'Saved: {dst_path} ({img.size[0]}x{img.size[1]} @ 300 DPI)')

print('\nDone. All TIFF figures created for BMJ Open submission.')
