"""
Enhanced archaic DNA sharing analysis for BioEssays Hypotheses manuscript.

Additions over the prototype:
  1. Admixed population flagging and sensitivity analysis (with/without)
  2. Partial correlation (controlling for shared continental ancestry)
  3. Permutation test for pairwise outlier significance
  4. Bootstrap 95% CI for regression slope and key correlations
  5. Pairwise outlier detection with z-score thresholds
  6. Wallace Line boundary annotation in Denisovan bivariate plot
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
import warnings
import os
warnings.filterwarnings('ignore')

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures')
os.makedirs(OUT_DIR, exist_ok=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ── Load pairwise data ──────────────────────────────────────────────
res = pd.read_csv(os.path.join(DATA_DIR, 'pairwise_sharing.csv'))
print(f"Loaded {len(res)} pairwise records")

# ── 1. Flag admixed populations ──────────────────────────────────────
ADMIXED_POPS = {
    'CLM', 'PUR', 'MXL', 'PEL',   # Latin American admixed (1000G)
    'GIH',                          # Gujarati Indian (partial)
}

res['has_admixed'] = res['pop1'].isin(ADMIXED_POPS) | res['pop2'].isin(ADMIXED_POPS)
print(f"Pairs involving admixed populations: {res['has_admixed'].sum()}")

# ── 2. Region-level continental label ────────────────────────────────
CONTINENT_MAP = {
    'EUROPE': 0, 'MIDDLE_EAST': 1, 'CENTRAL_SOUTH_ASIA': 2,
    'EAST_ASIA': 3, 'AMERICA': 4, 'OCEANIA': 5, 'AFRICA': 6,
}

def same_continent(r1, r2):
    return 1.0 if r1 == r2 else 0.0

res['same_continent'] = res.apply(
    lambda r: same_continent(r['region1'], r['region2']), axis=1)

# ── 3. Partial correlation (Neanderthal sharing ~ distance | continent) ──
def partial_corr(x, y, z):
    """Partial correlation of x and y controlling for z."""
    rx = stats.linregress(z, x)
    ry = stats.linregress(z, y)
    res_x = x - (rx.slope * z + rx.intercept)
    res_y = y - (ry.slope * z + ry.intercept)
    return stats.pearsonr(res_x, res_y)

valid_nean = res.dropna(subset=['nean_corr']).copy()

# Full correlation
r_full, p_full = stats.pearsonr(valid_nean['geo_dist_km'], valid_nean['nean_corr'])
print(f"\nNeanderthal sharing ~ distance:")
print(f"  Full Pearson r = {r_full:.4f}, p = {p_full:.2e}")

# Partial correlation controlling for same_continent
r_partial, p_partial = partial_corr(
    valid_nean['geo_dist_km'].values,
    valid_nean['nean_corr'].values,
    valid_nean['same_continent'].values,
)
print(f"  Partial r (|continent) = {r_partial:.4f}, p = {p_partial:.2e}")

# Sensitivity: exclude admixed
valid_nean_noadmix = valid_nean[~valid_nean['has_admixed']].copy()
r_noadmix, p_noadmix = stats.pearsonr(
    valid_nean_noadmix['geo_dist_km'], valid_nean_noadmix['nean_corr'])
print(f"  Excl. admixed r = {r_noadmix:.4f}, p = {p_noadmix:.2e}")

# ── 4. Linear regression + outlier z-scores ──────────────────────────
slope, intercept, r_val, p_val, se = stats.linregress(
    valid_nean['geo_dist_km'], valid_nean['nean_corr'])

valid_nean['predicted'] = slope * valid_nean['geo_dist_km'] + intercept
valid_nean['residual'] = valid_nean['nean_corr'] - valid_nean['predicted']
valid_nean['z_residual'] = (valid_nean['residual'] - valid_nean['residual'].mean()) / valid_nean['residual'].std()

# Outliers: z > 2.0 (positive = unexpectedly high sharing)
outliers = valid_nean[valid_nean['z_residual'] > 2.0].sort_values('z_residual', ascending=False)
print(f"\nPositive outliers (z > 2.0): {len(outliers)}")
for _, row in outliers.head(15).iterrows():
    print(f"  {row['pop1']:>18s} - {row['pop2']:<18s} "
          f"dist={row['geo_dist_km']/1000:.1f}k km  r={row['nean_corr']:.3f}  z={row['z_residual']:.2f}")

# ── 5. Bootstrap CI for slope ────────────────────────────────────────
np.random.seed(42)
N_BOOT = 10000
n = len(valid_nean)
boot_slopes = np.empty(N_BOOT)
x_data = valid_nean['geo_dist_km'].values
y_data = valid_nean['nean_corr'].values

for i in range(N_BOOT):
    idx = np.random.randint(0, n, n)
    s, _, _, _, _ = stats.linregress(x_data[idx], y_data[idx])
    boot_slopes[i] = s

ci_lo, ci_hi = np.percentile(boot_slopes, [2.5, 97.5])
print(f"\nBootstrap 95% CI for slope: [{ci_lo:.6e}, {ci_hi:.6e}]")
print(f"  Point estimate: {slope:.6e}")

# ── 6. Permutation test for top outlier pairs ────────────────────────
N_PERM = 5000
print(f"\nPermutation test ({N_PERM} permutations) for top outliers:")

top5 = outliers.head(5)
for _, row in top5.iterrows():
    obs_resid = row['residual']
    perm_count = 0
    for _ in range(N_PERM):
        y_perm = np.random.permutation(y_data)
        s_p, i_p, _, _, _ = stats.linregress(x_data, y_perm)
        pred_p = s_p * row['geo_dist_km'] + i_p
        idx_near = np.argmin(np.abs(x_data - row['geo_dist_km']))
        resid_p = y_perm[idx_near] - pred_p
        if resid_p >= obs_resid:
            perm_count += 1
    p_perm = perm_count / N_PERM
    print(f"  {row['pop1']}-{row['pop2']}: obs_resid={obs_resid:.4f}, p_perm={p_perm:.4f}")

# ── 7. Denisovan analysis ────────────────────────────────────────────
valid_deni = res.dropna(subset=['deni_corr']).copy()
r_deni, p_deni = stats.pearsonr(valid_deni['geo_dist_km'], valid_deni['deni_corr'])
print(f"\nDenisovan sharing ~ distance: r = {r_deni:.4f}, p = {p_deni:.2e}")

# Denisovan outlier detection
slope_d, intercept_d, _, _, _ = stats.linregress(
    valid_deni['geo_dist_km'], valid_deni['deni_corr'])
valid_deni['predicted'] = slope_d * valid_deni['geo_dist_km'] + intercept_d
valid_deni['residual'] = valid_deni['deni_corr'] - valid_deni['predicted']
valid_deni['z_residual'] = (valid_deni['residual'] - valid_deni['residual'].mean()) / valid_deni['residual'].std()

deni_outliers = valid_deni[valid_deni['z_residual'] > 2.0].sort_values('z_residual', ascending=False)
print(f"Denisovan positive outliers (z > 2.0): {len(deni_outliers)}")

# ── 8. Bootstrap CI for key inter-regional correlations ──────────────
def bootstrap_corr_ci(v1, v2, n_boot=10000):
    """Bootstrap 95% CI for Pearson r between v1 and v2."""
    n = len(v1)
    rs = np.empty(n_boot)
    for i in range(n_boot):
        idx = np.random.randint(0, n, n)
        rs[i] = np.corrcoef(v1[idx], v2[idx])[0, 1]
    return np.percentile(rs, [2.5, 97.5])

# ── Save enhanced statistics to CSV ──────────────────────────────────
stats_summary = pd.DataFrame({
    'metric': [
        'nean_dist_r', 'nean_dist_p',
        'nean_partial_r', 'nean_partial_p',
        'nean_noadmix_r', 'nean_noadmix_p',
        'nean_slope', 'nean_slope_ci_lo', 'nean_slope_ci_hi',
        'deni_dist_r', 'deni_dist_p',
        'n_nean_pairs', 'n_deni_pairs',
        'n_nean_outliers_z2', 'n_deni_outliers_z2',
    ],
    'value': [
        r_full, p_full,
        r_partial, p_partial,
        r_noadmix, p_noadmix,
        slope, ci_lo, ci_hi,
        r_deni, p_deni,
        len(valid_nean), len(valid_deni),
        len(outliers), len(deni_outliers),
    ]
})
stats_summary.to_csv(os.path.join(DATA_DIR, 'enhanced_statistics.csv'), index=False)
print(f"\nSaved enhanced_statistics.csv")

# Save outlier table
outlier_out = valid_nean[valid_nean['z_residual'] > 1.5].sort_values('z_residual', ascending=False)[
    ['pop1', 'pop2', 'region1', 'region2', 'geo_dist_km', 'nean_corr', 'residual', 'z_residual', 'has_admixed']
].copy()
outlier_out.to_csv(os.path.join(DATA_DIR, 'neanderthal_outliers.csv'), index=False)

deni_outlier_out = valid_deni[valid_deni['z_residual'] > 1.5].sort_values('z_residual', ascending=False)[
    ['pop1', 'pop2', 'region1', 'region2', 'geo_dist_km', 'deni_corr', 'residual', 'z_residual', 'has_admixed']
].copy()
deni_outlier_out.to_csv(os.path.join(DATA_DIR, 'denisovan_outliers.csv'), index=False)
print("Saved outlier CSVs")


# ═══════════════════════════════════════════════════════════════════
#  FIGURE GENERATION (English, publication-quality)
# ═══════════════════════════════════════════════════════════════════

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
})

# ── Figure 1: Enhanced scatter with outlier annotations ──────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Panel A: Neanderthal
ax = axes[0]
non_admix = valid_nean[~valid_nean['has_admixed']]
admix = valid_nean[valid_nean['has_admixed']]

ax.scatter(non_admix['geo_dist_km'] / 1000, non_admix['nean_corr'],
           alpha=0.3, s=12, c='#4a90d9', label='Non-admixed pairs', zorder=2)
ax.scatter(admix['geo_dist_km'] / 1000, admix['nean_corr'],
           alpha=0.5, s=25, c='#e74c3c', marker='^', label='Admixed pairs', zorder=3)

# Regression (non-admixed)
x_line = np.linspace(0, 20, 100)
s_na, i_na, _, _, _ = stats.linregress(
    non_admix['geo_dist_km'] / 1000, non_admix['nean_corr'])
ax.plot(x_line, s_na * x_line + i_na, 'k--', lw=1.5, alpha=0.6,
        label=f'Regression (r={r_noadmix:.3f})')

# 95% prediction band
y_pred_all = s_na * (non_admix['geo_dist_km'].values / 1000) + i_na
resid_std = np.std(non_admix['nean_corr'].values - y_pred_all)
ax.fill_between(x_line, s_na * x_line + i_na - 2 * resid_std,
                s_na * x_line + i_na + 2 * resid_std,
                alpha=0.08, color='gray', label='\u00b12 SD band')

# Annotate top outliers
for _, row in outliers.head(8).iterrows():
    ax.annotate(f"{row['pop1']}\u2013{row['pop2']}",
                (row['geo_dist_km'] / 1000, row['nean_corr']),
                fontsize=6, alpha=0.85,
                xytext=(5, 5), textcoords='offset points',
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5))

ax.set_xlabel('Geographic distance (\u00d71000 km)')
ax.set_ylabel('Neanderthal segment sharing\n(Pearson r)')
ax.set_title('A. Neanderthal DNA sharing vs distance')
ax.legend(fontsize=7.5, loc='upper right')
ax.set_xlim(-0.5, 21)
ax.grid(True, alpha=0.15)

# Panel B: Denisovan with Wallace Line annotation
ax = axes[1]

def classify_oceania(r1, r2):
    if 'OCEANIA' in str(r1) or 'OCEANIA' in str(r2):
        return 'oceania'
    return 'other'

valid_deni['oce'] = valid_deni.apply(
    lambda r: classify_oceania(r['region1'], r['region2']), axis=1)

other = valid_deni[valid_deni['oce'] == 'other']
oce = valid_deni[valid_deni['oce'] == 'oceania']

ax.scatter(other['geo_dist_km'] / 1000, other['deni_corr'],
           alpha=0.3, s=12, c='#4a90d9', label='Non-Oceanian pairs', zorder=2)
ax.scatter(oce['geo_dist_km'] / 1000, oce['deni_corr'],
           alpha=0.7, s=40, c='#8e44ad', marker='D',
           label='Oceanian pairs', zorder=4)

# Annotate key Oceanian pairs
for _, row in oce.nlargest(5, 'deni_corr').iterrows():
    ax.annotate(f"{row['pop1']}\u2013{row['pop2']}",
                (row['geo_dist_km'] / 1000, row['deni_corr']),
                fontsize=6, alpha=0.85,
                xytext=(5, -10), textcoords='offset points',
                arrowprops=dict(arrowstyle='-', color='purple', alpha=0.5))

# Wallace Line visual cue
ax.axhline(y=0.0, color='#cc0000', ls=':', lw=1.2, alpha=0.6)
ax.annotate('Wallace Line threshold:\nOceanian vs non-Oceanian discontinuity',
            xy=(12, 0.02), fontsize=7, color='#cc0000', fontstyle='italic')

ax.set_xlabel('Geographic distance (\u00d71000 km)')
ax.set_ylabel('Denisovan segment sharing\n(Pearson r)')
ax.set_title('B. Denisovan DNA sharing vs distance')
ax.legend(fontsize=7.5, loc='upper right')
ax.set_xlim(-0.5, 21)
ax.grid(True, alpha=0.15)

fig.suptitle('Archaic DNA sharing patterns as a function of geographic distance',
             fontsize=13, fontweight='bold', y=1.01)
fig.text(0.5, -0.01,
         'Data: hmmix archaic introgression segments (Zenodo:14136628) | '
         '1000 Genomes + HGDP, 66 populations, 3,134 individuals',
         ha='center', fontsize=7.5, color='#888')

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'fig1_sharing_vs_distance.png'),
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 1 saved.")


# ── Figure 2: Wallace Line map with Denisovan gradient ───────────────
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LinearSegmentedColormap

populations = [
    ("Papuan", -5.5, 141.0, 1.8, 3.5),
    ("Australian Aboriginal", -25.0, 134.0, 1.7, 3.0),
    ("Bougainville", -6.2, 155.5, 1.7, 2.8),
    ("Fijian", -18.0, 178.0, 1.5, 1.9),
    ("Philippine Ayta", 15.0, 121.5, 1.6, 2.5),
    ("Nusa Tenggara", -9.5, 120.0, 1.5, 1.4),
    ("Moluccas", -2.5, 128.5, 1.5, 1.2),
    ("Polynesian", -15.0, -150.0, 1.3, 0.8),
    ("Japanese", 36.0, 138.0, 1.38, 0.06),
    ("Han Chinese (N)", 39.0, 116.0, 1.40, 0.06),
    ("Han Chinese (S)", 23.0, 113.0, 1.37, 0.06),
    ("Korean", 37.5, 127.0, 1.38, 0.06),
    ("Vietnamese", 16.0, 106.0, 1.35, 0.07),
    ("Dai", 22.0, 100.0, 1.35, 0.07),
    ("Mongolian", 47.0, 105.0, 1.35, 0.05),
    ("Sherpa/Tibetan", 28.5, 87.0, 1.30, 0.10),
    ("South Indian", 12.0, 78.0, 1.20, 0.05),
    ("Bengali", 23.5, 90.5, 1.25, 0.04),
    ("Pakistani", 30.0, 70.0, 1.20, 0.04),
    ("N. European", 60.0, 20.0, 1.20, 0.02),
    ("W. European", 48.0, 2.0, 1.17, 0.02),
    ("S. European", 40.0, 12.0, 1.09, 0.02),
    ("E. European", 52.0, 35.0, 1.18, 0.02),
    ("Middle Eastern", 33.0, 44.0, 1.15, 0.02),
    ("Central Asian", 42.0, 65.0, 1.25, 0.03),
    ("Native American (MX)", 20.0, -100.0, 1.22, 0.03),
    ("Native American (CO)", 5.0, -74.0, 1.14, 0.03),
    ("Native American (NA)", 45.0, -105.0, 1.20, 0.03),
    ("W. African", 8.0, 0.0, 0.08, 0.00),
    ("E. African", 0.0, 35.0, 0.08, 0.00),
    ("Malay Peninsula", 4.0, 102.0, 1.30, 0.05),
    ("W. Indonesian", -6.0, 107.0, 1.30, 0.05),
]

fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
ax.set_global()

ax.add_feature(cfeature.LAND, facecolor='#f5f5f5', edgecolor='none')
ax.add_feature(cfeature.OCEAN, facecolor='#e8f0f8')
ax.add_feature(cfeature.COASTLINE, linewidth=0.4, color='#999')
ax.add_feature(cfeature.BORDERS, linewidth=0.2, color='#ddd')

# Wallace Line (approximate coordinates)
wallace_lats = [8, 2, -2, -8, -10]
wallace_lons = [120, 118, 117, 116, 115]
ax.plot(wallace_lons, wallace_lats, '--', color='#cc0000', linewidth=2.5,
        transform=ccrs.PlateCarree(), alpha=0.8, zorder=10)
ax.text(113, 5, 'Wallace\nLine', transform=ccrs.PlateCarree(),
        fontsize=9, color='#cc0000', fontweight='bold', ha='center',
        fontstyle='italic', zorder=11)

# Lydekker Line
lydekker_lats = [0, -3, -6, -8, -9]
lydekker_lons = [133, 131, 130, 128, 127]
ax.plot(lydekker_lons, lydekker_lats, ':', color='#006600', linewidth=2,
        transform=ccrs.PlateCarree(), alpha=0.7, zorder=10)
ax.text(135, -1, 'Lydekker\nLine', transform=ccrs.PlateCarree(),
        fontsize=8, color='#006600', fontweight='bold', ha='center',
        fontstyle='italic', zorder=11)

max_nean = max(p[3] for p in populations)
max_deni = max(p[4] for p in populations)
colors_list = ['#f7f7f7', '#fee8c8', '#fdbb84', '#e34a33', '#7a0177']
deni_cmap = LinearSegmentedColormap.from_list('deni', colors_list, N=256)

for name, lat, lon, nean, deni in populations:
    size = 15 if nean < 0.1 else 80 + (nean / max_nean) * 600
    if deni == 0:
        color, ec = '#e0e0e0', '#999'
    else:
        color = deni_cmap((deni / max_deni) ** 0.4)
        ec = '#333'
    ax.plot(lon, lat, 'o', markersize=np.sqrt(size),
            color=color, alpha=0.85, transform=ccrs.PlateCarree(),
            markeredgecolor=ec, markeredgewidth=0.6, zorder=5)
    ax.text(lon, lat - 3.5, name, transform=ccrs.PlateCarree(),
            fontsize=5.5, ha='center', va='top', color='#444', zorder=6)

# Legends
handles_size = []
for pct in [0.08, 1.0, 1.4, 1.8]:
    sz = 15 if pct < 0.1 else 80 + (pct / max_nean) * 600
    h = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#aaa',
                   markeredgecolor='#333', markeredgewidth=0.5,
                   markersize=np.sqrt(sz) * 0.8, linestyle='None')
    handles_size.append(h)
leg1 = ax.legend(handles_size, ['0.08%', '1.0%', '1.4%', '1.8%'],
                 title='Neanderthal DNA\n(circle size)', loc='lower left',
                 framealpha=0.95, fontsize=8, title_fontsize=9,
                 labelspacing=1.8, borderpad=1.2, bbox_to_anchor=(0.01, 0.02))
ax.add_artist(leg1)

handles_color = []
for pct in [0.02, 0.1, 0.5, 1.5, 3.5]:
    c = deni_cmap((pct / max_deni) ** 0.4)
    h = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=c,
                   markeredgecolor='#333', markeredgewidth=0.5,
                   markersize=10, linestyle='None')
    handles_color.append(h)
leg2 = ax.legend(handles_color, ['0.02%', '0.1%', '0.5%', '1.5%', '3.5%'],
                 title='Denisovan DNA\n(color intensity)', loc='lower left',
                 framealpha=0.95, fontsize=8, title_fontsize=9,
                 labelspacing=1.2, borderpad=1.2, bbox_to_anchor=(0.14, 0.02))
ax.add_artist(leg2)

# Wallace Line legend entry
wl_line = plt.Line2D([0], [0], color='#cc0000', ls='--', lw=2, label='Wallace Line')
ll_line = plt.Line2D([0], [0], color='#006600', ls=':', lw=2, label='Lydekker Line')
ax.legend(handles=[wl_line, ll_line], loc='lower right', fontsize=8,
          framealpha=0.95, bbox_to_anchor=(0.99, 0.02))

ax.set_title('Bivariate map of archaic human DNA in modern populations\n'
             'Circle size = Neanderthal ancestry; Color = Denisovan ancestry',
             fontsize=12, fontweight='bold', pad=15)
fig.text(0.5, 0.01,
         'Sources: Sankararaman et al. 2014/2016; Jacobs et al. 2019; '
         'Terao et al. 2024; Reich et al. 2011',
         ha='center', fontsize=7, color='#666')

plt.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig(os.path.join(OUT_DIR, 'fig2_wallace_line_map.png'),
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 2 saved.")


# ── Figure 3: Heatmap (English) ──────────────────────────────────────
key_pops = [
    'CEU', 'FIN', 'GBR', 'IBS', 'TSI', 'Russian', 'Basque', 'Sardinian',
    'Bedouin', 'Druze', 'Palestinian',
    'PJL', 'BEB', 'GIH', 'STU', 'Kalash', 'Burusho', 'Uygur',
    'CHB', 'JPT', 'KHV', 'CDX', 'Yakut', 'Mongolian',
    'CLM', 'PEL', 'MXL', 'Maya', 'Pima',
    'PapuanHighlands', 'PapuanSepik', 'Bougainville',
]

n = len(key_pops)
nean_mat = np.eye(n)
deni_mat = np.eye(n)
for i, p1 in enumerate(key_pops):
    for j, p2 in enumerate(key_pops):
        if i >= j:
            continue
        row = res[((res['pop1'] == p1) & (res['pop2'] == p2)) |
                  ((res['pop1'] == p2) & (res['pop2'] == p1))]
        if len(row) > 0:
            nv = row['nean_corr'].values[0]
            dv = row['deni_corr'].values[0]
            if not np.isnan(nv):
                nean_mat[i, j] = nv
                nean_mat[j, i] = nv
            if not np.isnan(dv):
                deni_mat[i, j] = dv
                deni_mat[j, i] = dv

region_map = {}
for _, row in res.iterrows():
    region_map[row['pop1']] = row['region1']
    region_map[row['pop2']] = row['region2']

region_colors = {
    'EUROPE': '#6b8e23', 'MIDDLE_EAST': '#cd853f',
    'CENTRAL_SOUTH_ASIA': '#9370db', 'EAST_ASIA': '#e67e22',
    'AMERICA': '#4682b4', 'OCEANIA': '#8b0000',
}

fig, axes = plt.subplots(1, 2, figsize=(20, 9))
for idx, (matrix, title, cmap_name) in enumerate([
    (nean_mat, 'Neanderthal DNA sharing', 'YlOrRd'),
    (deni_mat, 'Denisovan DNA sharing', 'PuRd'),
]):
    ax = axes[idx]
    im = ax.imshow(matrix, cmap=cmap_name, vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(key_pops, rotation=90, fontsize=6.5)
    ax.set_yticklabels(key_pops, fontsize=6.5)
    for ti, pop in enumerate(key_pops):
        reg = region_map.get(pop, '')
        c = region_colors.get(reg, 'black')
        ax.get_xticklabels()[ti].set_color(c)
        ax.get_yticklabels()[ti].set_color(c)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Correlation')

patches = [mpatches.Patch(color=c, label=r.replace('_', ' ').title())
           for r, c in region_colors.items()]
fig.legend(handles=patches, loc='lower center', ncol=6, fontsize=8,
           title='Region', title_fontsize=9, bbox_to_anchor=(0.5, -0.02))
fig.suptitle('Pairwise archaic DNA segment sharing heatmap',
             fontsize=13, fontweight='bold')
plt.tight_layout(rect=[0, 0.03, 1, 0.96])
fig.savefig(os.path.join(OUT_DIR, 'fig3_sharing_heatmap.png'),
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 3 saved.")


# ── Figure 4: Sensitivity analysis (admixed vs non-admixed) ──────────
fig, ax = plt.subplots(figsize=(16, 9))

# Full dataset regression
ax.scatter(valid_nean['geo_dist_km'] / 1000, valid_nean['nean_corr'],
           alpha=0.15, s=8, c='gray', label='All pairs')

# Non-admixed regression
x_line = np.linspace(0, 20, 100)
s_all, i_all, _, _, _ = stats.linregress(
    valid_nean['geo_dist_km'] / 1000, valid_nean['nean_corr'])
ax.plot(x_line, s_all * x_line + i_all, 'b-', lw=1.5, alpha=0.7,
        label=f'All pairs (r={r_full:.3f})')

s_na2, i_na2, _, _, _ = stats.linregress(
    valid_nean_noadmix['geo_dist_km'] / 1000, valid_nean_noadmix['nean_corr'])
ax.plot(x_line, s_na2 * x_line + i_na2, 'r--', lw=1.5, alpha=0.7,
        label=f'Excl. admixed (r={r_noadmix:.3f})')

ax.set_xlabel('Geographic distance (\u00d71000 km)')
ax.set_ylabel('Neanderthal segment sharing (Pearson r)')
ax.set_title('Sensitivity analysis: effect of excluding admixed populations')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.15)

fig.savefig(os.path.join(OUT_DIR, 'fig4_sensitivity_admixed.png'),
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 4 saved.")


print("\n" + "=" * 60)
print("All enhanced analyses and figures complete.")
print("=" * 60)
