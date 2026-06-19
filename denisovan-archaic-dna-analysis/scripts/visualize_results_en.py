"""
English visualization of corrected archaic introgression sharing analysis.
Generates publication-quality figures for BioEssays Hypotheses submission.

Outputs (to figures/):
  fig1_sharing_vs_distance.png   — Scatter: sharing correlation vs geographic distance
  fig2_sharing_heatmap.png       — Heatmap: pairwise sharing for key populations
  fig3_minard_migration.png      — Minard-style Out-of-Africa flow with admixture events
  fig4_bivariate_world_map.png   — Bivariate world map: Neanderthal (size) + Denisovan (color)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import statsmodels.api as sm

plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['font.size'] = 10

OUTDIR = 'figures'

# ===== Load corrected data =====
res = pd.read_csv('data/pairwise_sharing_corrected.csv')

# ========================================================================
# Figure 1: Sharing correlation vs geographic distance (corrected)
# ========================================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# --- Panel A: Neanderthal ---
ax = axes[0]
valid = res.dropna(subset=['nean_corr']).copy()
valid['pair_type'] = np.where(valid['same_continent'] == 1, 'intra', 'inter')

# Separate admixed
admixed = valid[valid['any_admixed'] == 1]
non_admixed_intra = valid[(valid['any_admixed'] == 0) & (valid['pair_type'] == 'intra')]
non_admixed_inter = valid[(valid['any_admixed'] == 0) & (valid['pair_type'] == 'inter')]

ax.scatter(non_admixed_intra['geo_dist_km'] / 1000, non_admixed_intra['nean_corr'],
           alpha=0.35, s=18, c='#4a90d9', label='Same continent', zorder=3)
ax.scatter(non_admixed_inter['geo_dist_km'] / 1000, non_admixed_inter['nean_corr'],
           alpha=0.35, s=18, c='#e74c3c', label='Cross-continent', zorder=3)
ax.scatter(admixed['geo_dist_km'] / 1000, admixed['nean_corr'],
           alpha=0.5, s=30, c='#f39c12', marker='^', label='Admixed pop. involved', zorder=4)

# Corrected regression line (multiple regression prediction at admix=0, same_cont=0)
x_line = np.linspace(0, 22, 100)
y_pred_inter = 0.5440 + (-0.0155) * x_line  # from OLS results
y_pred_intra = 0.5440 + (-0.0155) * x_line + 0.2971
ax.plot(x_line, y_pred_inter, 'k--', linewidth=1.2, alpha=0.5, label='Regression (cross-cont.)')
ax.plot(x_line, y_pred_intra, 'b--', linewidth=1.2, alpha=0.5, label='Regression (same cont.)')

# Annotate key outlier pairs
outlier_pairs_n = [
    ('KHV', 'PEL'), ('CHS', 'PEL'), ('KHV', 'Maya'), ('CHS', 'Maya'),
    ('Hazara', 'JPT'), ('Hazara', 'Yakut'),
]
for p1, p2 in outlier_pairs_n:
    row = valid[((valid['pop1'] == p1) & (valid['pop2'] == p2)) |
                ((valid['pop1'] == p2) & (valid['pop2'] == p1))]
    if len(row) > 0:
        r = row.iloc[0]
        ax.annotate(f"{p1}-{p2}",
                    (r['geo_dist_km']/1000, r['nean_corr']),
                    fontsize=6.5, alpha=0.85,
                    xytext=(5, 5), textcoords='offset points',
                    arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5))

ax.set_xlabel('Geographic distance (x1,000 km)', fontsize=11)
ax.set_ylabel('Neanderthal segment sharing\n(Pearson correlation)', fontsize=11)
ax.set_title('A. Neanderthal DNA sharing vs. distance', fontsize=12, fontweight='bold')
ax.legend(fontsize=7.5, loc='upper right')
ax.set_xlim(-0.5, 22)
ax.set_ylim(-0.15, 1.05)
ax.grid(True, alpha=0.15)

# --- Panel B: Denisovan ---
ax = axes[1]
valid_d = res.dropna(subset=['deni_corr']).copy()
valid_d['pair_type'] = np.where(valid_d['same_continent'] == 1, 'intra', 'inter')

def has_oceania(r1, r2):
    if 'OCEANIA' in str(r1) or 'OCEANIA' in str(r2):
        return 'oce'
    elif r1 == r2:
        return 'intra'
    else:
        return 'inter'

valid_d['oce_type'] = valid_d.apply(
    lambda r: has_oceania(r['region1'], r['region2']), axis=1)

oce = valid_d[valid_d['oce_type'] == 'oce']
non_oce_intra = valid_d[(valid_d['oce_type'] == 'intra')]
non_oce_inter = valid_d[(valid_d['oce_type'] == 'inter')]

ax.scatter(non_oce_intra['geo_dist_km'] / 1000, non_oce_intra['deni_corr'],
           alpha=0.35, s=18, c='#4a90d9', label='Same continent', zorder=3)
ax.scatter(non_oce_inter['geo_dist_km'] / 1000, non_oce_inter['deni_corr'],
           alpha=0.35, s=18, c='#e74c3c', label='Cross-continent', zorder=3)
ax.scatter(oce['geo_dist_km'] / 1000, oce['deni_corr'],
           alpha=0.7, s=50, c='#8e44ad', marker='D', label='Oceania involved', zorder=4)

ax.set_xlabel('Geographic distance (x1,000 km)', fontsize=11)
ax.set_ylabel('Denisovan segment sharing\n(Pearson correlation)', fontsize=11)
ax.set_title('B. Denisovan DNA sharing vs. distance', fontsize=12, fontweight='bold')
ax.legend(fontsize=7.5, loc='upper right')
ax.set_xlim(-0.5, 22)
ax.set_ylim(-0.25, 1.05)
ax.grid(True, alpha=0.15)

fig.suptitle('Archaic DNA sharing patterns vs. geographic distance\n'
             'after controlling for admixture and continental grouping',
             fontsize=13, fontweight='bold', y=1.01)

fig.text(0.5, -0.02,
         'Data: hmmix archaic introgression segments (Zenodo:14136628) | '
         '1000 Genomes + HGDP, 66 populations, 3,134 individuals | '
         '500kb bins, corrected for admixture & continental grouping',
         ha='center', fontsize=7.5, color='#888888')

plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig1_sharing_vs_distance.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 1 saved.")

# ========================================================================
# Figure 2: Heatmap of sharing for key populations
# ========================================================================
key_pops = [
    'CEU', 'FIN', 'GBR', 'IBS', 'TSI', 'Russian', 'Basque', 'Sardinian',
    'Bedouin', 'Druze', 'Palestinian',
    'PJL', 'BEB', 'GIH', 'STU', 'Kalash', 'Burusho', 'Uygur',
    'CHB', 'JPT', 'KHV', 'CDX', 'Yakut', 'Mongolian',
    'Colombian', 'PEL', 'Maya', 'Pima',
    'PapuanHighlands', 'PapuanSepik', 'Bougainville',
]

# Use original sharing data
res_orig = pd.read_csv('data/pairwise_sharing.csv')

n = len(key_pops)
nean_matrix = np.eye(n)
deni_matrix = np.eye(n)

for i, p1 in enumerate(key_pops):
    for j, p2 in enumerate(key_pops):
        if i >= j:
            continue
        row = res_orig[((res_orig['pop1'] == p1) & (res_orig['pop2'] == p2)) |
                       ((res_orig['pop1'] == p2) & (res_orig['pop2'] == p1))]
        if len(row) > 0:
            nv = row['nean_corr'].values[0]
            dv = row['deni_corr'].values[0]
            if not np.isnan(nv):
                nean_matrix[i, j] = nv
                nean_matrix[j, i] = nv
            if not np.isnan(dv):
                deni_matrix[i, j] = dv
                deni_matrix[j, i] = dv

region_map = {}
for _, row in res_orig.iterrows():
    region_map[row['pop1']] = row['region1']
    region_map[row['pop2']] = row['region2']

region_colors = {
    'EUROPE': '#6b8e23', 'MIDDLE_EAST': '#cd853f',
    'CENTRAL_SOUTH_ASIA': '#9370db', 'EAST_ASIA': '#e67e22',
    'AMERICA': '#4682b4', 'OCEANIA': '#8b0000'
}

fig, axes = plt.subplots(1, 2, figsize=(22, 10))

for idx, (matrix, title, cmap_name) in enumerate([
    (nean_matrix, 'Neanderthal DNA sharing', 'YlOrRd'),
    (deni_matrix, 'Denisovan DNA sharing', 'PuRd'),
]):
    ax = axes[idx]
    im = ax.imshow(matrix, cmap=cmap_name, vmin=0, vmax=1, aspect='auto')

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(key_pops, rotation=90, fontsize=7)
    ax.set_yticklabels(key_pops, fontsize=7)

    for tick_idx, pop in enumerate(key_pops):
        reg = region_map.get(pop, '')
        color = region_colors.get(reg, 'black')
        ax.get_xticklabels()[tick_idx].set_color(color)
        ax.get_yticklabels()[tick_idx].set_color(color)

    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Correlation')

legend_patches = [mpatches.Patch(color=c, label=r.replace('_', ' ').title())
                  for r, c in region_colors.items()]
fig.legend(handles=legend_patches, loc='lower center', ncol=6, fontsize=9,
           title='Region', title_fontsize=10, bbox_to_anchor=(0.5, -0.02))

fig.suptitle('Pairwise archaic DNA segment sharing across 31 key populations',
             fontsize=14, fontweight='bold')

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig(f'{OUTDIR}/fig2_sharing_heatmap.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 2 saved.")

# ========================================================================
# Figure 3: Minard-style migration flow (English version)
# ========================================================================
fig, ax = plt.subplots(figsize=(20, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.set_axis_off()

# Time axis
ax.plot([5, 95], [5, 5], 'k-', linewidth=0.5)
time_points = [
    (5, '70,000'), (15, '60,000'), (25, '50,000'), (35, '45,000'),
    (50, '40,000'), (65, '35,000'), (75, '25,000'), (85, '15,000'), (95, 'Present')
]
for x, label in time_points:
    ax.plot([x, x], [4.5, 5.5], 'k-', linewidth=0.5)
    ax.text(x, 3, label, ha='center', fontsize=7)
ax.text(50, 1, 'Years ago', ha='center', fontsize=9)

# Neanderthal zone
rect_n = plt.Rectangle((18, 28), 25, 18, facecolor='#ffffcc', alpha=0.3, edgecolor='#cccc00', linewidth=1)
ax.add_patch(rect_n)
ax.text(30.5, 46.5, 'Neanderthal range', fontsize=8, color='#999900', ha='center', style='italic')

# Denisovan zone
rect_d = plt.Rectangle((25, 10), 35, 20, facecolor='#ffe0e0', alpha=0.3, edgecolor='#cc6666', linewidth=1)
ax.add_patch(rect_d)
ax.text(42.5, 9, 'Denisovan range', fontsize=8, color='#cc4444', ha='center', style='italic')

# Migration flows (bandwidth ~ relative pop size / genetic diversity)
from matplotlib.patches import FancyArrowPatch

# Main Out-of-Africa flow
flows = [
    # (start_xy, end_xy, width, color, label)
    ((5, 38), (25, 38), 12, '#1a237e', 'Out of Africa'),         # main trunk
    ((25, 44), (55, 52), 5, '#2e7d32', 'To Europe'),             # Europe branch
    ((25, 38), (40, 30), 6, '#6a1b9a', 'To South Asia'),         # South Asia
    ((40, 30), (55, 18), 4.5, '#b71c1c', 'To Oceania'),          # Oceania
    ((40, 34), (60, 38), 5, '#e65100', 'To East Asia'),          # East Asia
    ((60, 40), (75, 48), 3.5, '#d84315', 'To Japan (Jomon)'),    # Japan
    ((60, 36), (85, 36), 3, '#1565c0', 'To Americas'),           # Americas
]

for (x1, y1), (x2, y2), w, color, label in flows:
    xs = np.linspace(x1, x2, 50)
    # gentle curve
    mid = len(xs) // 2
    ys_base = np.linspace(y1, y2, 50)
    curve_offset = np.sin(np.linspace(0, np.pi, 50)) * 2
    ys = ys_base + curve_offset

    for k in range(len(xs) - 1):
        # taper width along flow
        curr_w = w * (1 - 0.3 * k / len(xs))
        ax.fill_between([xs[k], xs[k+1]],
                        [ys[k] - curr_w/2, ys[k+1] - curr_w/2],
                        [ys[k] + curr_w/2, ys[k+1] + curr_w/2],
                        color=color, alpha=0.5)
    ax.text(x2 + 1, y2, label, fontsize=7.5, color=color, fontweight='bold',
            va='center')

# Admixture events
admix_events = [
    (28, 40, 'Neanderthal\nadmixture\n~47 kya\n(1.0-1.8%)', '#cc9900'),
    (37, 22, 'Denisovan\nadmixture 1\n~45 kya\n(Oceania: 3-5%)', '#cc3333'),
    (52, 34, 'Denisovan\nadmixture 2\n~30 kya\n(E. Asia: ~0.06%)', '#cc3333'),
]
for x, y, text, color in admix_events:
    ax.plot(x, y, '*', markersize=15, color=color, zorder=10)
    ax.text(x + 1.5, y - 2, text, fontsize=6.5, color=color, va='top')

# Location labels
locations = [
    (3, 38, 'Africa\n(origin)', '#333'),
    (55, 55, 'Europe\n~45 kya', '#2e7d32'),
    (75, 51, 'Japan\n~38 kya\n(Jomon)', '#d84315'),
    (60, 42, 'East Asia\n~40 kya', '#e65100'),
    (55, 14, 'Oceania\n(Papua/Australia)\n~50 kya', '#b71c1c'),
    (88, 36, 'Americas\n~15 kya', '#1565c0'),
]
for x, y, text, color in locations:
    ax.text(x, y, text, fontsize=8, color=color, fontweight='bold',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor=color))

# Key finding box
textbox = ('Key archaic DNA proportions:\n'
           'Neanderthal: Europeans ~1.1%, E. Asians ~1.4%\n'
           'Denisovan: Oceania 3-5%, E. Asia ~0.06%, Europe ~0.02%\n'
           'Japan: Neanderthal ~1.4%, Denisovan ~0.06%')
ax.text(68, 55, textbox, fontsize=7, fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
        va='top')

# Legend
legend_text = ('Band width = relative population size\n'
               '(reflecting genetic diversity decline)')
ax.text(5, 52, legend_text, fontsize=7, color='#666',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

ax.set_title('Homo sapiens Out-of-Africa migration and archaic admixture events\n'
             '-- Minard-style flow visualization --',
             fontsize=13, fontweight='bold', pad=10)

fig.text(0.5, 0.01,
         'Sources: Sankararaman et al. 2014/2016, Jacobs et al. 2019, '
         'Terao et al. 2024 (JEWEL), Prufer et al. 2021, Hajdinjak et al. 2024 | '
         'Timelines are approximate',
         ha='center', fontsize=7, color='#888')

plt.savefig(f'{OUTDIR}/fig3_minard_migration.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 3 saved.")

# ========================================================================
# Figure 4: Bivariate world map (Neanderthal size + Denisovan color)
# ========================================================================
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False
    print("cartopy not available; skipping Fig 4 world map")

if HAS_CARTOPY:
    pop_data = [
        # (name, lat, lon, nean%, deni%)
        ('Japanese', 35.7, 139.7, 1.40, 0.06),
        ('Han Chinese (N)', 39.9, 116.4, 1.45, 0.06),
        ('Han Chinese (S)', 23.1, 113.3, 1.40, 0.08),
        ('Korean', 37.5, 127.0, 1.42, 0.06),
        ('Vietnamese', 16.0, 106.0, 1.35, 0.09),
        ('Dai (SW China)', 21.0, 100.0, 1.30, 0.10),
        ('Bengali', 23.7, 90.4, 1.25, 0.08),
        ('South Indian', 13.1, 80.3, 1.10, 0.05),
        ('Sherpa / Tibetan', 28.5, 86.7, 1.35, 0.15),
        ('Mongolian', 47.0, 107.0, 1.40, 0.06),
        ('Malay Peninsula', 3.0, 102.0, 1.20, 0.35),
        ('W. Indonesian', -2.0, 106.0, 1.15, 0.50),
        ('Philippine Ayta', 15.0, 120.5, 1.30, 2.50),
        ('Nusa Tenggara (E. Indonesia)', -8.5, 120.0, 1.25, 1.50),
        ('Moluccas (E. Indonesia)', -2.5, 128.0, 1.20, 2.00),
        ('Papuan', -5.0, 141.0, 1.80, 3.50),
        ('Bougainville', -6.2, 155.5, 1.70, 3.20),
        ('Australian Aboriginal', -25.0, 134.0, 1.60, 3.00),
        ('Fijian', -18.0, 178.0, 1.40, 1.90),
        ('Polynesian', -15.0, -150.0, 1.10, 0.40),
        ('Northern European (FIN/GBR)', 55.0, 10.0, 1.15, 0.02),
        ('Western European (CEU/FRA)', 48.0, 3.0, 1.12, 0.02),
        ('Southern European (IBS/TSI)', 42.0, 5.0, 1.20, 0.02),
        ('Eastern European', 52.0, 28.0, 1.18, 0.02),
        ('Middle Eastern', 33.0, 42.0, 1.05, 0.03),
        ('Central Asian', 40.0, 65.0, 1.15, 0.05),
        ('Pakistani', 30.0, 68.0, 1.10, 0.04),
        ('Sub-Saharan African (W)', -5.0, 15.0, 0.08, 0.00),
        ('Sub-Saharan African (E)', -3.0, 37.0, 0.10, 0.00),
        ('Native American (N. America)', 45.0, -100.0, 1.12, 0.03),
        ('Native American (Mexico)', 19.0, -99.0, 1.08, 0.04),
        ('Native American (Colombia)', 4.0, -73.0, 1.05, 0.04),
    ]

    fig = plt.figure(figsize=(18, 10))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor='#f0f0f0', edgecolor='#cccccc', linewidth=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='#e8f0fe')
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.3)
    ax.coastlines(linewidth=0.5, color='#999999')

    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    nean_norm = Normalize(vmin=0, vmax=2.0)
    deni_norm = Normalize(vmin=0, vmax=4.0)
    cmap = plt.cm.YlOrRd

    for name, lat, lon, nean, deni in pop_data:
        size = max(nean * 100, 8)
        color = cmap(deni_norm(deni))
        ax.plot(lon, lat, 'o', markersize=np.sqrt(size) * 2,
                color=color, markeredgecolor='#333', markeredgewidth=0.3,
                transform=ccrs.PlateCarree(), zorder=5, alpha=0.85)
        ax.text(lon + 3, lat - 2, name, fontsize=5.5, transform=ccrs.PlateCarree(),
                color='#333', alpha=0.8, zorder=6)

    # Legends
    # Size legend (Neanderthal)
    legend_ax = fig.add_axes([0.08, 0.12, 0.12, 0.18])
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    legend_ax.axis('off')
    legend_ax.text(0.5, 0.98, 'Neanderthal DNA\n(circle size)', fontsize=8,
                   fontweight='bold', ha='center', va='top')
    for i, (val, label) in enumerate([(0.08, '0.08%'), (1.0, '1.0%'),
                                       (1.4, '1.4%'), (1.8, '1.8%')]):
        y = 0.75 - i * 0.2
        size = max(val * 100, 8)
        legend_ax.plot(0.25, y, 'o', markersize=np.sqrt(size) * 2,
                       color='#cccccc', markeredgecolor='#333', markeredgewidth=0.3)
        legend_ax.text(0.55, y, label, fontsize=7, va='center')

    # Color legend (Denisovan)
    legend_ax2 = fig.add_axes([0.21, 0.12, 0.12, 0.18])
    legend_ax2.set_xlim(0, 1)
    legend_ax2.set_ylim(0, 1)
    legend_ax2.axis('off')
    legend_ax2.text(0.5, 0.98, 'Denisovan DNA\n(color intensity)', fontsize=8,
                    fontweight='bold', ha='center', va='top')
    for i, (val, label) in enumerate([(0.02, '0.02%'), (0.1, '0.1%'),
                                       (0.5, '0.5%'), (1.5, '1.5%'), (3.5, '3.5%')]):
        y = 0.75 - i * 0.15
        color = cmap(deni_norm(val))
        legend_ax2.plot(0.25, y, 'o', markersize=10,
                        color=color, markeredgecolor='#333', markeredgewidth=0.3)
        legend_ax2.text(0.55, y, label, fontsize=7, va='center')

    ax.set_title('Global distribution of archaic human DNA\n'
                 'Circle size = Neanderthal DNA proportion / Color = Denisovan DNA proportion',
                 fontsize=12, fontweight='bold', pad=15)

    fig.text(0.5, 0.02,
             'Sources: Sankararaman et al. 2014 (Nature), Sankararaman et al. 2016 (Current Biology), '
             'Jacobs et al. 2019 (Cell), Terao et al. 2024 (JEWEL), Reich et al. 2011',
             ha='center', fontsize=7, color='#888')

    plt.savefig(f'{OUTDIR}/fig4_bivariate_world_map.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Figure 4 saved.")

print("All English figures generated.")
