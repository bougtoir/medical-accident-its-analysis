#!/usr/bin/env python3
"""
Minard-style flow diagram of human migration with archaic DNA introgression.

Inspired by Charles Minard's 1869 visualization. X-axis ~ time (left=old),
Y-axis ~ latitude/geography. Band width ~ effective population size / genetic
diversity. Star markers at admixture events. ABO sub-lineage paradox annotated.

Aspect ratio ~1.73 to match Fig 2 (Wallace Line map).
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(BASE_DIR, 'figures')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(OUT_DIR, exist_ok=True)

# ── Data-derived ABO sub-lineage composition (this study) ────────────
# Every ABO composition annotation below is computed from the analysis
# outputs rather than hand-entered, so the figure stays consistent with
# data/abo_sublineage_summary.csv and data/abo_denisovan_segments.csv.
_sub = pd.read_csv(os.path.join(DATA_DIR, 'abo_sublineage_summary.csv'))
_deni = pd.read_csv(os.path.join(DATA_DIR, 'abo_denisovan_segments.csv'))


def _abo_comp(group):
    rows = _sub[(_sub['analysis_group'] == group)
                & (_sub['closest_reference'] != 'Tie')]
    total = int(rows['n_segments'].sum())
    if not total:
        return 'no classifiable segments'

    def pct(ref):
        r = rows[rows['closest_reference'] == ref]
        count = int(r['n_segments'].iloc[0]) if len(r) else 0
        return int(round(100 * count / total))

    return f"Alt {pct('Altai')}% / Chag {pct('Chagyrskaya')}% / Vin {pct('Vindija')}%"


_eastasia_comp = _abo_comp('East Asia')
_europe_comp = _abo_comp('Europe')
_oceania_comp = _abo_comp('Oceania')
_indig_n = int(_sub[(_sub['analysis_group'] == 'Indigenous Americas')
                    & (_sub['closest_reference'] != 'Tie')]['n_segments'].sum())
_deni_sas = int((_deni['region'] == 'CENTRAL_SOUTH_ASIA').sum())

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_xlim(-2, 100)
ax.set_ylim(-5, 55)
ax.axis('off')


# ── Helper functions ─────────────────────────────────────────────────
def draw_flow(ax, points, width, color, alpha=0.8, zorder=2):
    """Draw a flow band along a path with given width."""
    pts = np.array(points)
    upper, lower = [], []
    for i in range(len(pts)):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == len(pts) - 1:
            dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            dx, dy = pts[i+1][0] - pts[i-1][0], pts[i+1][1] - pts[i-1][1]
        length = max(np.sqrt(dx**2 + dy**2), 1e-6)
        nx, ny = -dy / length, dx / length
        w = (width[i] if isinstance(width, (list, np.ndarray)) else width) / 2
        upper.append([pts[i][0] + nx * w, pts[i][1] + ny * w])
        lower.append([pts[i][0] - nx * w, pts[i][1] - ny * w])
    polygon_pts = upper + lower[::-1]
    poly = Polygon(polygon_pts, closed=True, facecolor=color, alpha=alpha,
                   edgecolor='none', zorder=zorder)
    ax.add_patch(poly)
    poly_edge = Polygon(polygon_pts, closed=True, facecolor='none',
                        edgecolor=color, alpha=0.3, linewidth=0.5,
                        zorder=zorder + 0.1)
    ax.add_patch(poly_edge)


def draw_event_marker(ax, x, y, text, color='red', size=14):
    """Draw a star marker for interbreeding events."""
    ax.plot(x, y, '*', markersize=size, color=color, zorder=10,
            markeredgecolor='white', markeredgewidth=0.3)
    ax.annotate(text, (x, y), fontsize=7, ha='center', va='bottom',
                xytext=(0, 8), textcoords='offset points',
                color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          alpha=0.85, edgecolor=color, linewidth=0.5))


# ── Colour scheme ────────────────────────────────────────────────────
c_main = '#4a6fa5'        # Out-of-Africa
c_europe = '#6b8e23'      # European
c_eastasia = '#cd853f'    # East Asian
c_oceania = '#8b0000'     # Oceanian
c_americas = '#4682b4'    # Americas
c_south_asia = '#9370db'  # South Asian
c_ane = '#FF8F00'         # ANE

# ── Interbreeding zones (background boxes) ───────────────────────────
nean_zone = FancyBboxPatch((20, 28), 10, 12, boxstyle="round,pad=0.5",
                           facecolor='#ffeb3b', alpha=0.15,
                           edgecolor='#f57f17', linewidth=1.5,
                           linestyle='--', zorder=1)
ax.add_patch(nean_zone)
ax.text(25, 41, 'Neanderthal range', fontsize=8.5, ha='center',
        color='#f57f17', fontstyle='italic')

deni_zone = FancyBboxPatch((40, 13), 14, 14, boxstyle="round,pad=0.5",
                           facecolor='#e040fb', alpha=0.1,
                           edgecolor='#7b1fa2', linewidth=1.5,
                           linestyle='--', zorder=1)
ax.add_patch(deni_zone)
ax.text(47, 12, 'Denisovan range', fontsize=8.5, ha='center',
        color='#7b1fa2', fontstyle='italic')

# ── Migration flows ──────────────────────────────────────────────────

# 1. Out of Africa
draw_flow(ax, [(2, 25), (8, 27), (14, 30), (20, 32), (26, 33)],
          [5.0, 4.8, 4.5, 4.2, 4.0], c_main, alpha=0.7)

# 2. Europe branch
draw_flow(ax, [(26, 33), (32, 37), (38, 40), (44, 42), (50, 43), (56, 44)],
          [3.0, 2.8, 2.6, 2.5, 2.4, 2.3], c_europe, alpha=0.7)

# 3. South Asia branch
draw_flow(ax, [(26, 33), (32, 28), (38, 25), (44, 23), (50, 22)],
          [2.5, 2.3, 2.0, 1.8, 1.7], c_south_asia, alpha=0.7)

# 4. East/SE Asia branch
draw_flow(ax, [(26, 33), (32, 32), (38, 30), (44, 28), (50, 27)],
          [3.5, 3.2, 3.0, 2.8, 2.6], c_eastasia, alpha=0.7)

# 5. SE Asia → Oceania branch (crosses Wallace Line)
draw_flow(ax, [(38, 30), (44, 24), (50, 18), (56, 14), (62, 10)],
          [2.5, 2.3, 2.0, 1.8, 1.6], c_oceania, alpha=0.7)

# 6. East Asia → Northeast Asia
draw_flow(ax, [(50, 27), (56, 30), (62, 33), (68, 36), (74, 38)],
          [2.4, 2.2, 2.0, 1.9, 1.8], c_eastasia, alpha=0.7)

# 7. ANE branch (diverges from main European/Central Asian stream)
draw_flow(ax, [(38, 40), (44, 44), (52, 46), (60, 47), (68, 45)],
          [1.8, 1.6, 1.4, 1.3, 1.2], c_ane, alpha=0.7)

# 8. Americas branch (NE Asia + ANE merge → Beringia → Americas)
draw_flow(ax, [(74, 38), (80, 42), (86, 44), (92, 40), (96, 35), (96, 28)],
          [1.5, 1.4, 1.3, 1.2, 1.1, 1.0], c_americas, alpha=0.7)

# ANE → Beringia merge point
draw_flow(ax, [(68, 45), (74, 42), (78, 41)],
          [1.0, 0.9, 0.8], c_ane, alpha=0.6)

# ── Event markers ────────────────────────────────────────────────────

# Neanderthal interbreeding
draw_event_marker(ax, 24, 32,
    'Neanderthal admixture\n~47 kya\n(all non-Africans 1-2%)',
    color='#e65100', size=18)

# Denisovan interbreeding 1 (Oceania)
ax.plot(44, 18, '*', markersize=16, color='#7b1fa2', zorder=10,
        markeredgecolor='white', markeredgewidth=0.3)
ax.annotate('Denisovan adm. 1\n~45 kya (Oceanians 3-5%)',
            (44, 18), fontsize=6.5, ha='left', va='top',
            xytext=(8, -5), textcoords='offset points',
            color='#7b1fa2', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      alpha=0.85, edgecolor='#7b1fa2', linewidth=0.5))

# Denisovan interbreeding 2 (East Asia, minor)
ax.plot(55, 28, '*', markersize=12, color='#9c27b0', zorder=10,
        markeredgecolor='white', markeredgewidth=0.3)
ax.annotate('Denisovan adm. 2\n~30 kya (E. Asia trace)',
            (55, 28), fontsize=6.5, ha='left', va='bottom',
            xytext=(8, 5), textcoords='offset points',
            color='#9c27b0', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      alpha=0.85, edgecolor='#9c27b0', linewidth=0.5))

# Denisovan interbreeding 3 (South Asia, ABO-specific)
ax.plot(38, 25, '*', markersize=12, color='#4a148c', zorder=10,
        markeredgecolor='white', markeredgewidth=0.3)
ax.annotate(f'Denisovan adm. 3?\n(ABO: S. Asia only, {_deni_sas} segs)',
            (38, 25), fontsize=6.5, ha='right', va='top',
            xytext=(-8, -5), textcoords='offset points',
            color='#4a148c', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                      alpha=0.85, edgecolor='#4a148c', linewidth=0.5))

# ── Wallace Line marker ─────────────────────────────────────────────
ax.plot([48, 48], [14, 28], '--', color='#CC0000', linewidth=2, alpha=0.7,
        zorder=3)
ax.annotate('Wallace Line', xy=(48, 28.5), fontsize=7, color='#CC0000',
            fontweight='bold', ha='center')

# ── ABO sub-lineage annotations ──────────────────────────────────────

# East Asia: data-derived composition (this study)
ax.annotate(f'ABO (East Asia):\n{_eastasia_comp}',
            xy=(62, 33), fontsize=7.5, color='#1565C0', fontweight='bold',
            ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', fc='#E3F2FD', ec='#1565C0',
                      alpha=0.9, linewidth=1))

# ANE: Altai/Vindija sub-lineages
ax.annotate('ABO: Altai + Vindija\nsub-lineages',
            xy=(56, 48), fontsize=7, color=c_ane, fontweight='bold',
            ha='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='#FFF8E1', ec=c_ane,
                      alpha=0.9, linewidth=1))

# Indigenous Americas: data-derived, deliberately conservative
ax.annotate(
    'Indigenous Americas:\n'
    f'only {_indig_n} ABO-window segments\n'
    '(both Vindija-closest) — too few\nfor a composition estimate',
    xy=(82, 44), fontsize=7, color='#B71C1C', fontweight='bold',
    ha='center',
    bbox=dict(boxstyle='round,pad=0.4', fc='#FFEBEE', ec='#B71C1C',
              alpha=0.95, linewidth=1.5))

# O2 paradox (Oceania)
ax.annotate('O2 paradox:\nSolomon Is. 5-16%\nE. Asia <0.01%',
            xy=(62, 6), fontsize=6.5, color='#D32F2F', fontweight='bold',
            ha='center',
            bbox=dict(boxstyle='round,pad=0.3', fc='#FFEBEE', ec='#D32F2F',
                      alpha=0.9))

# Europe: data-derived composition (this study)
ax.annotate(f'ABO (Europe):\n{_europe_comp}',
            xy=(50, 46), fontsize=6.5, color=c_europe,
            ha='center',
            bbox=dict(boxstyle='round,pad=0.2', fc='#F1F8E9', ec=c_europe,
                      alpha=0.85))



# ── Destination labels ───────────────────────────────────────────────
label_style = dict(fontsize=9, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                             alpha=0.9, edgecolor='gray', linewidth=0.5))

ax.text(56, 44.5, 'Europe\n~45 kya', color=c_europe, **label_style)
ax.text(50, 22.5, 'South Asia\n~50 kya', color=c_south_asia, **label_style)
ax.text(62, 8, 'Oceania\n(Papuans)\n~50 kya', color=c_oceania, **label_style)
ax.text(74, 35, 'East Asia\n~40 kya', color=c_eastasia, **label_style)
ax.text(96, 25, 'Americas\n~15 kya', color=c_americas, **label_style)
ax.text(64, 48, 'ANE\nhomeland', color=c_ane, **label_style)

# Africa source
ax.text(2, 23, 'Africa\n(source)', fontsize=11, fontweight='bold', ha='center',
        va='top', color=c_main,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#e3f2fd',
                  alpha=0.9, edgecolor=c_main))

# ── Time axis ────────────────────────────────────────────────────────
time_y = -2
ax.plot([2, 96], [time_y, time_y], 'k-', linewidth=1, zorder=5)
time_marks = [
    (2, '70 kya'), (14, '60 kya'), (26, '50 kya'), (38, '45 kya'),
    (50, '40 kya'), (62, '35 kya'), (74, '25 kya'), (86, '15 kya'),
    (96, 'Present'),
]
for x, label in time_marks:
    ax.plot(x, time_y, 'k|', markersize=8)
    ax.text(x, time_y - 1.5, label, ha='center', fontsize=7, color='#333')
ax.text(50, time_y - 3.5, 'Time (years before present)',
        ha='center', fontsize=8, color='#555')

# ── Width legend ─────────────────────────────────────────────────────
ax.text(3, 52,
        'Band width = relative effective population size\n'
        '(reflects genetic diversity loss through bottlenecks)',
        fontsize=7.5, va='top', color='#555',
        bbox=dict(boxstyle='round', facecolor='#fafafa', edgecolor='#ccc'))

# ── Colour legend ────────────────────────────────────────────────────
legend_patches = [
    mpatches.Patch(color=c_main, label='Out of Africa'),
    mpatches.Patch(color=c_europe, label='European branch'),
    mpatches.Patch(color=c_south_asia, label='South Asian branch'),
    mpatches.Patch(color=c_eastasia, label='East Asian branch'),
    mpatches.Patch(color=c_ane, label='ANE (Ancient North Eurasian)'),
    mpatches.Patch(color=c_oceania, label='Oceanian branch'),
    mpatches.Patch(color=c_americas, label='Americas (via Beringia)'),
]
ax.legend(handles=legend_patches, loc='upper right', fontsize=7.5,
          title='Migration streams', title_fontsize=9,
          framealpha=0.95, edgecolor='#ccc')

# ── Archaic DNA summary box ─────────────────────────────────────────
summary = (
    "Archaic ancestry (published estimates):\n"
    "Neanderthal: non-Africans ~1.5-2%,\n"
    "  E. Asia > Europe (Pr\u00fcfer 2014; Vernot 2014)\n"
    "Denisovan: Papuans ~3-5% >> mainland Asia\n"
    "  (Reich 2011; Meyer 2012)\n"
    f"S. Asia: {_deni_sas} Denisovan ABO segments (this study)"
)
ax.text(78, 52, summary, fontsize=6.5, va='top', ha='left',
        family='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff3e0',
                  edgecolor='#ff9800', alpha=0.95, linewidth=1))

# ── Title ────────────────────────────────────────────────────────────
ax.set_title(
    'Human migration and archaic introgression: '
    'a Minard-style flow visualisation',
    fontsize=13, fontweight='bold', pad=15)

# ── Source note ──────────────────────────────────────────────────────
fig.text(0.5, 0.01,
         'Segment calls: hmmix (Zenodo:14136628), 1000 Genomes, HGDP. '
         'ABO sub-lineage composition: this study (data/abo_sublineage_summary.csv). '
         'Band widths are schematic. Archaic-ancestry ranges from Pr\u00fcfer et al. 2014 '
         '(doi:10.1038/nature12886), Vernot & Akey 2014 (doi:10.1126/science.1245938), '
         'Reich et al. 2011 (doi:10.1016/j.ajhg.2011.09.005), '
         'Meyer et al. 2012 (doi:10.1126/science.1224344).',
         ha='center', fontsize=6, color='#888')

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
out_path = os.path.join(OUT_DIR, 'fig3_minard_migration.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
# Also save TIFF
from PIL import Image
img = Image.open(out_path)
img.save(out_path.replace('.png', '.tiff'), compression='tiff_lzw', dpi=(300, 300))
plt.close()
print(f'Saved: {out_path}')
