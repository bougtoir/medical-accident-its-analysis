#!/usr/bin/env python3
"""Create IJQHC Figure 1: 2x2 composite of L008/L004/L002/L003 SCR maps (EN/JP).

- Generates single-panel L002 maps for EN and JP if not already present.
- Combines existing L008/L004/L003 and new L002 maps into a 2x2 composite
  (Panels A-D) for both languages.
- Output:
    output/rapm_fig1_en.png  (overwritten)
    output/rapm_fig1_jp.png  (overwritten)
"""
import os
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import geopandas as gpd
from matplotlib.colors import BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
try:
    import japanize_matplotlib  # noqa: F401
except ImportError:
    pass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GIS = os.path.join(ROOT, 'gis_data')
OUT_EN = os.path.join(ROOT, 'output', 'maps_2d_en')
OUT_JP = os.path.join(ROOT, 'output', 'maps_2d_jp')
FIG_OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT_EN, exist_ok=True)
os.makedirs(OUT_JP, exist_ok=True)

print("Loading data...")
gdf = gpd.read_file(os.path.join(GIS, 'merged_enriched.gpkg'))
gdf_pref = gpd.read_file(os.path.join(GIS, 'pref_simplified.gpkg'))
gdf_nt = gpd.read_file(os.path.join(GIS, 'northern_territories.gpkg'))

all_b = {'x': (122.5, 149.2), 'y': (24.0, 46.0)}


def make_map(column, title, boundaries, legend_label, filename):
    fig, ax = plt.subplots(1, 1, figsize=(14, 18))
    norm = BoundaryNorm(boundaries, ncolors=256)
    valid = gdf[gdf[column].notna()]
    nodata = gdf[gdf[column].isna()]
    if len(nodata) > 0:
        nodata.plot(ax=ax, color='#e0e0e0', edgecolor='none')
    if len(valid) > 0:
        valid.plot(ax=ax, column=column, cmap='RdYlBu_r', norm=norm,
                   edgecolor='none', legend=False)
    gdf_nt.plot(ax=ax, color='white', edgecolor='#333333', linewidth=0.5)
    gdf.boundary.plot(ax=ax, linewidth=0.3, color='#888888',
                      linestyle=(0, (2, 3)))
    gdf_pref.boundary.plot(ax=ax, linewidth=0.8, color='#333333',
                           linestyle='solid')

    # University hospital overlay
    univ = gdf[gdf['has_univ'] == 1]
    c = univ.geometry.centroid
    ax.scatter(c.x, c.y, s=18, c='red', marker='o', zorder=5,
               linewidths=0.5, edgecolors='darkred', alpha=0.8)

    ax.set_xlim(all_b['x']); ax.set_ylim(all_b['y'])
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=15)

    sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.15, 0.06, 0.55, 0.015])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
    cbar.set_label(legend_label, fontsize=12)

    plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {filename}")


# Single-panel maps. The generate_maps_*.py scripts historically wrote to
# /home/ubuntu; here we canonicalise the outputs to output/maps_2d_{en,jp}/
# and regenerate any missing single-panel PNG from the geopackage on the fly
# so the script is self-contained and safe to run on a fresh clone.
SCR_BOUNDS = {
    'L008_scr': [0, 30, 50, 70, 90, 100, 110, 130, 160, 200, 500],
    'L004_scr': [0, 30, 50, 70, 90, 100, 110, 130, 160, 200, 400],
    'L002_scr': [0, 30, 50, 70, 90, 100, 110, 130, 160, 200, 600],
    'L003_scr': [0, 30, 50, 70, 90, 100, 110, 130, 160, 200, 450],
}
EN_TITLES = {
    'L008_scr': 'General Anaesthesia (L008) SCR by Secondary Medical Area',
    'L004_scr': 'Spinal Anaesthesia (L004) SCR by Secondary Medical Area',
    'L002_scr': 'Epidural Anaesthesia (L002) SCR by Secondary Medical Area',
    'L003_scr': 'Continuous Epidural Infusion (L003) SCR by Secondary Medical Area',
}
JP_TITLES = {
    'L008_scr': '全身麻酔 (L008) SCR 二次医療圏別',
    'L004_scr': '脊椎麻酔 (L004) SCR 二次医療圏別',
    'L002_scr': '硬膜外麻酔 (L002) SCR 二次医療圏別',
    'L003_scr': '持続硬膜外注入 (L003) SCR 二次医療圏別',
}

en_paths = {}
for col, bounds in SCR_BOUNDS.items():
    fn = os.path.join(OUT_EN, f'en_map_{col}.png')
    if not os.path.exists(fn):
        make_map(col, EN_TITLES[col], bounds,
                 'SCR (100 = national average)', fn)
    en_paths[col] = fn

jp_paths = {}
for col, bounds in SCR_BOUNDS.items():
    fn = os.path.join(OUT_JP, f'map_{col}.png')
    if not os.path.exists(fn):
        make_map(col, JP_TITLES[col], bounds,
                 'SCR (100=全国平均)', fn)
    jp_paths[col] = fn


def create_2x2(panel_paths, labels, output_path, figsize=(16, 18), dpi=250):
    fig, axes = plt.subplots(2, 2, figsize=figsize, dpi=dpi)
    fig.subplots_adjust(wspace=0.02, hspace=0.08,
                        left=0.01, right=0.99, top=0.97, bottom=0.01)
    for ax, path, label in zip(axes.flat, panel_paths, labels):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(label, fontsize=14, fontweight='bold', pad=6, loc='left')
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


# EN 4-panel
create_2x2(
    [en_paths['L008_scr'], en_paths['L004_scr'],
     en_paths['L002_scr'], en_paths['L003_scr']],
    ['A. General anaesthesia (L008) SCR',
     'B. Spinal anaesthesia (L004) SCR',
     'C. Epidural anaesthesia (L002) SCR',
     'D. Continuous epidural infusion (L003) SCR'],
    os.path.join(FIG_OUT, 'rapm_fig1_en.png')
)

# JP 4-panel
create_2x2(
    [jp_paths['L008_scr'], jp_paths['L004_scr'],
     jp_paths['L002_scr'], jp_paths['L003_scr']],
    ['A. 全身麻酔 (L008) SCR',
     'B. 脊椎麻酔 (L004) SCR',
     'C. 硬膜外麻酔 (L002) SCR',
     'D. 持続硬膜外注入 (L003) SCR'],
    os.path.join(FIG_OUT, 'rapm_fig1_jp.png')
)

print("Done.")
