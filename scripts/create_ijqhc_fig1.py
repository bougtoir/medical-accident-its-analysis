#!/usr/bin/env python3
"""Create IJQHC Figures 1 and 2 (EN/JP).

Figure 1: 2x2 composite of L008 / L004 / L002 / L003 SCR maps
          (Panels A, B, C, D).
Figure 2: 2-panel composite of (A) university hospital presence and
          (B) combined L008 + L003 SCR (general + continuous-epidural
          proxy for the combined GA+epidural technique).

The geopackage `gis_data/merged_enriched.gpkg` is used only for geometry;
SCR values are re-read from `data/scr_n_kubun.csv` to avoid an enrichment
bug that dropped L003 values for East Japan prefectures.

Output:
    output/maps_2d_en/en_map_L{002,003,004,008}_scr.png
    output/maps_2d_en/en_map_L008_L003_combined.png
    output/maps_2d_en/en_map_univ_presence.png
    output/rapm_fig1_en.png
    output/rapm_fig2_en.png
(and JP equivalents under maps_2d_jp / rapm_fig{1,2}_jp.png)
"""
import os
import csv
import io
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import geopandas as gpd
import numpy as np
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


def load_scr_from_csv(csv_path):
    """Return dict[area_code_zfill4] -> dict[L-code] -> SCR value, by
    re-parsing the public regional-variation CSV so we do not depend on
    the pre-enriched gpkg (which has missing L003 values)."""
    with open(csv_path, 'rb') as f:
        raw = f.read()
    for enc in ('shift_jis', 'cp932', 'utf-8'):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rows = list(csv.reader(io.StringIO(text)))
    area_codes = [x.strip().zfill(4) for x in rows[2][4:]]
    out = {ac: {} for ac in area_codes}
    wanted = {('L', '2', '1'): 'L002_scr',
              ('L', '3', '1'): 'L003_scr',
              ('L', '4', '1'): 'L004_scr',
              ('L', '8', '1'): 'L008_scr'}
    for r in rows[4:]:
        if len(r) < 5:
            continue
        key = (r[0].strip(), r[1].strip(), r[3].strip())
        if key not in wanted:
            continue
        col = wanted[key]
        for ac, v in zip(area_codes, r[4:]):
            s = v.strip()
            if s == '':
                continue
            try:
                out[ac][col] = float(s)
            except ValueError:
                pass
    return out


print("Re-reading SCR values from CSV (override any missing values in gpkg) ...")
scr_map = load_scr_from_csv(os.path.join(ROOT, 'data', 'scr_n_kubun.csv'))
# Overwrite SCR columns from CSV
for col in ('L002_scr', 'L003_scr', 'L004_scr', 'L008_scr'):
    gdf[col] = gdf['area_code'].astype(str).str.zfill(4).map(
        lambda ac, c=col: scr_map.get(ac, {}).get(c, np.nan))
# Combined L008 + L003 averaged SCR (both reported on the national-average=100
# scale, so an arithmetic mean gives the combined-technique proxy).
gdf['L008_L003_combined'] = gdf[['L008_scr', 'L003_scr']].mean(
    axis=1, skipna=False)
for col in ('L002_scr', 'L003_scr', 'L004_scr', 'L008_scr',
            'L008_L003_combined'):
    print(f"  {col}: non-null={gdf[col].notna().sum()} of {len(gdf)}")

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
    'L008_L003_combined': [0, 30, 50, 70, 90, 100, 110, 130, 160, 200, 450],
}
EN_TITLES = {
    'L008_scr': 'General Anaesthesia (L008) SCR by Secondary Medical Area',
    'L004_scr': 'Spinal Anaesthesia (L004) SCR by Secondary Medical Area',
    'L002_scr': 'Epidural Anaesthesia (L002) SCR by Secondary Medical Area',
    'L003_scr': 'Continuous Epidural Infusion (L003) SCR by Secondary Medical Area',
    'L008_L003_combined': 'Combined general + continuous-epidural (L008 + L003) mean SCR',
}
JP_TITLES = {
    'L008_scr': '全身麻酔 (L008) SCR 二次医療圏別',
    'L004_scr': '脊椎麻酔 (L004) SCR 二次医療圏別',
    'L002_scr': '硬膜外麻酔 (L002) SCR 二次医療圏別',
    'L003_scr': '持続硬膜外注入 (L003) SCR 二次医療圏別',
    'L008_L003_combined': '全身+持続硬膜外 (L008+L003) 平均 SCR',
}

# Codes whose cached PNG should always be regenerated because the
# underlying data were corrected in this script (enrichment bug in the
# gpkg dropped East Japan L003 SCRs and the combined metric is new).
FORCE_REGENERATE = {'L003_scr', 'L008_L003_combined'}


def panel_png_path(col, lang):
    if lang == 'en':
        return os.path.join(OUT_EN, f'en_map_{col}.png')
    return os.path.join(OUT_JP, f'map_{col}.png')


en_paths = {}
for col, bounds in SCR_BOUNDS.items():
    fn = panel_png_path(col, 'en')
    if col in FORCE_REGENERATE or not os.path.exists(fn):
        make_map(col, EN_TITLES[col], bounds,
                 'SCR (100 = national average)', fn)
    en_paths[col] = fn

jp_paths = {}
for col, bounds in SCR_BOUNDS.items():
    fn = panel_png_path(col, 'jp')
    if col in FORCE_REGENERATE or not os.path.exists(fn):
        make_map(col, JP_TITLES[col], bounds,
                 'SCR (100=全国平均)', fn)
    jp_paths[col] = fn


# --- University hospital presence map (for Figure 2 Panel A) --------------
def make_univ_map(lang, filename):
    fig, ax = plt.subplots(1, 1, figsize=(14, 18))
    univ = gdf[gdf['has_univ'] == 1]
    non = gdf[gdf['has_univ'] != 1]
    non.plot(ax=ax, color='#d0e0f0', edgecolor='none')
    univ.plot(ax=ax, color='#d62728', edgecolor='none')
    gdf_nt.plot(ax=ax, color='white', edgecolor='#333333', linewidth=0.5)
    gdf.boundary.plot(ax=ax, linewidth=0.3, color='#888888',
                      linestyle=(0, (2, 3)))
    gdf_pref.boundary.plot(ax=ax, linewidth=0.8, color='#333333',
                           linestyle='solid')
    ax.set_xlim(all_b['x']); ax.set_ylim(all_b['y'])
    ax.set_aspect('equal'); ax.axis('off')
    if lang == 'en':
        ax.set_title('University Hospital Presence by Secondary Medical Area',
                     fontsize=15, fontweight='bold', pad=15)
        leg = [Patch(facecolor='#d62728',
                     label=f'University hospital present ({len(univ)} SMAs)'),
               Patch(facecolor='#d0e0f0',
                     label=f'No university hospital ({len(non)} SMAs)')]
    else:
        ax.set_title('大学病院の所在 二次医療圏別',
                     fontsize=15, fontweight='bold', pad=15)
        leg = [Patch(facecolor='#d62728',
                     label=f'大学病院あり ({len(univ)} 医療圏)'),
               Patch(facecolor='#d0e0f0',
                     label=f'大学病院なし ({len(non)} 医療圏)')]
    ax.legend(handles=leg, loc='lower left', fontsize=11,
              frameon=True, framealpha=0.95)
    plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {filename}")


en_univ_png = os.path.join(OUT_EN, 'en_map_univ_presence.png')
jp_univ_png = os.path.join(OUT_JP, 'map_univ_presence.png')
make_univ_map('en', en_univ_png)
make_univ_map('jp', jp_univ_png)


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


def create_side_by_side(panel_paths, labels, output_path,
                        figsize=(20, 12), dpi=250):
    fig, axes = plt.subplots(1, 2, figsize=figsize, dpi=dpi)
    fig.subplots_adjust(wspace=0.02, left=0.01, right=0.99,
                        top=0.95, bottom=0.03)
    for ax, path, label in zip(axes, panel_paths, labels):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(label, fontsize=14, fontweight='bold', pad=6, loc='left')
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_path}")


# Figure 2 EN: university hospital presence + combined L008+L003 map
create_side_by_side(
    [en_univ_png, en_paths['L008_L003_combined']],
    ['A. University hospital presence',
     'B. Combined general + continuous-epidural (L008 + L003) mean SCR'],
    os.path.join(FIG_OUT, 'rapm_fig2_en.png')
)

# Figure 2 JP
create_side_by_side(
    [jp_univ_png, jp_paths['L008_L003_combined']],
    ['A. 大学病院の所在',
     'B. 全身+持続硬膜外 (L008+L003) 平均 SCR'],
    os.path.join(FIG_OUT, 'rapm_fig2_jp.png')
)

print("Done.")
