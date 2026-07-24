"""
Archaic Introgression × Language Typology Analysis

Tests whether Neanderthal/Denisovan introgression levels correlate with
language typological features (morphological type, word order, tone)
beyond what geographic distance alone explains.

Methods:
  1. Population-level archaic introgression data (hmmix, 66 populations)
  2. Language typological features (WALS-derived)
  3. Mantel test: typological distance ~ introgression distance | geography
  4. ANOVA/Kruskal-Wallis: introgression by morphological type
  5. Wallace Line discontinuity test
  6. Partial correlation controlling for geography
  7. Bootstrap confidence intervals
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from itertools import combinations
import warnings
import os

warnings.filterwarnings('ignore')

np.random.seed(42)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
FIG_DIR = os.path.join(BASE_DIR, 'figures')
ARCHAIC_DATA = os.path.join(
    os.path.dirname(BASE_DIR), 'denisovan-archaic-dna-analysis', 'data',
    'pairwise_sharing.csv')
os.makedirs(FIG_DIR, exist_ok=True)

# ============================================================
# 1. Load data
# ============================================================
print("=" * 60)
print("ARCHAIC INTROGRESSION × LANGUAGE TYPOLOGY ANALYSIS")
print("=" * 60)

# Load archaic pairwise data
archaic = pd.read_csv(ARCHAIC_DATA)
print(f"\nLoaded {len(archaic)} pairwise archaic sharing records")

# Load population-language mapping
lang_map = pd.read_csv(os.path.join(DATA_DIR, 'population_language_map.csv'))
print(f"Loaded {len(lang_map)} population-language mappings")

# Get unique populations from archaic data
pops_in_archaic = set(archaic['pop1'].unique()) | set(archaic['pop2'].unique())
pops_in_lang = set(lang_map['population'])
matched = pops_in_archaic & pops_in_lang
print(f"Populations in archaic data: {len(pops_in_archaic)}")
print(f"Populations with language mapping: {len(pops_in_lang)}")
print(f"Matched: {len(matched)}")

# Filter to matched populations
lang_map = lang_map[lang_map['population'].isin(matched)].copy()
lang_map = lang_map.set_index('population')

# ============================================================
# 2. Compute population-level mean introgression
# ============================================================
# From pairwise data, compute mean sharing per population
pop_means = {}
for pop in matched:
    rows = archaic[(archaic['pop1'] == pop) | (archaic['pop2'] == pop)]
    pop_means[pop] = {
        'nean_mean': rows['nean_corr'].mean(),
        'deni_mean': rows['deni_corr'].mean() if 'deni_corr' in rows.columns else np.nan,
        'geo_dist_mean': rows['geo_dist_km'].mean(),
    }

pop_stats = pd.DataFrame(pop_means).T
pop_stats.index.name = 'population'
lang_data = lang_map.join(pop_stats)
lang_data = lang_data.dropna(subset=['nean_mean'])
print(f"\nFinal analysis dataset: {len(lang_data)} populations")

# ============================================================
# 3. Morphological type vs. introgression (ANOVA)
# ============================================================
print("\n" + "=" * 60)
print("3. MORPHOLOGICAL TYPE vs. ARCHAIC INTROGRESSION")
print("=" * 60)

morph_types = lang_data['morphological_type'].unique()
print(f"\nMorphological types: {morph_types}")

for morph in sorted(morph_types):
    subset = lang_data[lang_data['morphological_type'] == morph]
    print(f"  {morph:15s}: n={len(subset):2d}, "
          f"Nean={subset['nean_mean'].mean():.4f} (±{subset['nean_mean'].std():.4f}), "
          f"Deni={subset['deni_mean'].mean():.4f} (±{subset['deni_mean'].std():.4f})")

# Kruskal-Wallis test (non-parametric ANOVA)
groups_nean = [lang_data[lang_data['morphological_type'] == m]['nean_mean'].values
               for m in sorted(morph_types) if len(lang_data[lang_data['morphological_type'] == m]) > 1]
groups_deni = [lang_data[lang_data['morphological_type'] == m]['deni_mean'].dropna().values
               for m in sorted(morph_types) if len(lang_data[lang_data['morphological_type'] == m]) > 1]

kw_nean = stats.kruskal(*groups_nean)
kw_deni = stats.kruskal(*groups_deni)
print(f"\nKruskal-Wallis (Neanderthal ~ morphological type): H={kw_nean.statistic:.4f}, p={kw_nean.pvalue:.6f}")
print(f"Kruskal-Wallis (Denisovan ~ morphological type):   H={kw_deni.statistic:.4f}, p={kw_deni.pvalue:.6f}")

# ============================================================
# 4. Tone languages vs. introgression
# ============================================================
print("\n" + "=" * 60)
print("4. TONE vs. ARCHAIC INTROGRESSION")
print("=" * 60)

tone_yes = lang_data[lang_data['tone'] == 'yes']
tone_no = lang_data[lang_data['tone'] == 'no']
print(f"\nTone languages: n={len(tone_yes)}")
print(f"  Nean mean: {tone_yes['nean_mean'].mean():.4f} (±{tone_yes['nean_mean'].std():.4f})")
print(f"  Deni mean: {tone_yes['deni_mean'].mean():.4f} (±{tone_yes['deni_mean'].std():.4f})")
print(f"Non-tone languages: n={len(tone_no)}")
print(f"  Nean mean: {tone_no['nean_mean'].mean():.4f} (±{tone_no['nean_mean'].std():.4f})")
print(f"  Deni mean: {tone_no['deni_mean'].mean():.4f} (±{tone_no['deni_mean'].std():.4f})")

mwu_nean = stats.mannwhitneyu(tone_yes['nean_mean'], tone_no['nean_mean'], alternative='two-sided')
mwu_deni = stats.mannwhitneyu(tone_yes['deni_mean'].dropna(), tone_no['deni_mean'].dropna(), alternative='two-sided')
print(f"\nMann-Whitney U (Neanderthal: tone vs non-tone): U={mwu_nean.statistic:.1f}, p={mwu_nean.pvalue:.6f}")
print(f"Mann-Whitney U (Denisovan: tone vs non-tone):   U={mwu_deni.statistic:.1f}, p={mwu_deni.pvalue:.6f}")

# ============================================================
# 5. Word order vs. introgression
# ============================================================
print("\n" + "=" * 60)
print("5. WORD ORDER vs. ARCHAIC INTROGRESSION")
print("=" * 60)

for wo in sorted(lang_data['word_order'].unique()):
    subset = lang_data[lang_data['word_order'] == wo]
    if len(subset) > 0:
        print(f"  {wo:5s}: n={len(subset):2d}, "
              f"Nean={subset['nean_mean'].mean():.4f}, "
              f"Deni={subset['deni_mean'].mean():.4f}")

# ============================================================
# 6. Language family vs. introgression
# ============================================================
print("\n" + "=" * 60)
print("6. LANGUAGE FAMILY vs. ARCHAIC INTROGRESSION")
print("=" * 60)

family_stats = lang_data.groupby('language_family').agg(
    n=('nean_mean', 'count'),
    nean_mean=('nean_mean', 'mean'),
    nean_std=('nean_mean', 'std'),
    deni_mean=('deni_mean', 'mean'),
    deni_std=('deni_mean', 'std'),
).sort_values('nean_mean', ascending=False)

print(f"\n{'Family':<22s} {'n':>3s} {'Nean':>8s} {'±':>6s} {'Deni':>8s} {'±':>6s}")
print("-" * 60)
for fam, row in family_stats.iterrows():
    print(f"{fam:<22s} {row['n']:3.0f} {row['nean_mean']:8.4f} {row['nean_std']:6.4f} "
          f"{row['deni_mean']:8.4f} {row['deni_std']:6.4f}")

# ============================================================
# 7. Mantel test: Typological distance ~ Introgression distance
# ============================================================
print("\n" + "=" * 60)
print("7. MANTEL TEST: TYPOLOGICAL DISTANCE ~ INTROGRESSION DISTANCE")
print("=" * 60)

# Encode typological features as numeric vector per population
def encode_typology(row):
    """Encode typological features as binary/ordinal vector."""
    morph_map = {'isolating': 0, 'fusional': 1, 'agglutinative': 2}
    wo_map = {'SVO': 0, 'SOV': 1, 'VSO': 2, 'VOS': 3, 'free': 4}
    tone_map = {'no': 0, 'yes': 1}
    return np.array([
        morph_map.get(row['morphological_type'], 1),
        wo_map.get(row['word_order'], 0),
        tone_map.get(row['tone'], 0),
    ])

# Build distance matrices
pops_list = sorted(lang_data.index.tolist())
n_pops = len(pops_list)

# Typological distance (Gower-like: proportion of differing features)
typo_dist = np.zeros((n_pops, n_pops))
for i, p1 in enumerate(pops_list):
    for j, p2 in enumerate(pops_list):
        if i < j:
            v1 = encode_typology(lang_data.loc[p1])
            v2 = encode_typology(lang_data.loc[p2])
            # Normalized Hamming distance
            d = np.sum(v1 != v2) / len(v1)
            typo_dist[i, j] = d
            typo_dist[j, i] = d

# Introgression distance (absolute difference in mean sharing)
nean_dist = np.zeros((n_pops, n_pops))
deni_dist = np.zeros((n_pops, n_pops))
for i, p1 in enumerate(pops_list):
    for j, p2 in enumerate(pops_list):
        if i < j:
            nd = abs(lang_data.loc[p1, 'nean_mean'] - lang_data.loc[p2, 'nean_mean'])
            nean_dist[i, j] = nd
            nean_dist[j, i] = nd
            dd = abs(lang_data.loc[p1, 'deni_mean'] - lang_data.loc[p2, 'deni_mean'])
            deni_dist[i, j] = dd
            deni_dist[j, i] = dd

# Geographic distance (haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

geo_dist = np.zeros((n_pops, n_pops))
for i, p1 in enumerate(pops_list):
    for j, p2 in enumerate(pops_list):
        if i < j:
            d = haversine(
                lang_data.loc[p1, 'latitude'], lang_data.loc[p1, 'longitude'],
                lang_data.loc[p2, 'latitude'], lang_data.loc[p2, 'longitude'])
            geo_dist[i, j] = d
            geo_dist[j, i] = d

def mantel_test(D1, D2, n_perms=9999):
    """Mantel test: correlation between two distance matrices."""
    # Extract upper triangle
    idx = np.triu_indices(D1.shape[0], k=1)
    x = D1[idx]
    y = D2[idx]
    r_obs = np.corrcoef(x, y)[0, 1]
    # Permutation test
    count = 0
    for _ in range(n_perms):
        perm = np.random.permutation(D1.shape[0])
        D1_perm = D1[np.ix_(perm, perm)]
        x_perm = D1_perm[idx]
        r_perm = np.corrcoef(x_perm, y)[0, 1]
        if r_perm >= r_obs:
            count += 1
    p_val = (count + 1) / (n_perms + 1)
    return r_obs, p_val

def partial_mantel(D1, D2, D_control, n_perms=9999):
    """Partial Mantel: correlation between D1 and D2 controlling for D_control."""
    idx = np.triu_indices(D1.shape[0], k=1)
    x = D1[idx]
    y = D2[idx]
    z = D_control[idx]
    # Residualize
    slope_xz = stats.linregress(z, x)
    slope_yz = stats.linregress(z, y)
    res_x = x - (slope_xz.slope * z + slope_xz.intercept)
    res_y = y - (slope_yz.slope * z + slope_yz.intercept)
    r_obs = np.corrcoef(res_x, res_y)[0, 1]
    # Permutation
    count = 0
    for _ in range(n_perms):
        perm = np.random.permutation(D1.shape[0])
        D1_perm = D1[np.ix_(perm, perm)]
        x_perm = D1_perm[idx]
        slope_xz_perm = stats.linregress(z, x_perm)
        res_x_perm = x_perm - (slope_xz_perm.slope * z + slope_xz_perm.intercept)
        r_perm = np.corrcoef(res_x_perm, res_y)[0, 1]
        if r_perm >= r_obs:
            count += 1
    p_val = (count + 1) / (n_perms + 1)
    return r_obs, p_val

# Simple Mantel tests
print("\n--- Simple Mantel Tests ---")
r_typo_nean, p_typo_nean = mantel_test(typo_dist, nean_dist)
print(f"Typological dist ~ Neanderthal dist: r={r_typo_nean:.4f}, p={p_typo_nean:.4f}")

r_typo_deni, p_typo_deni = mantel_test(typo_dist, deni_dist)
print(f"Typological dist ~ Denisovan dist:   r={r_typo_deni:.4f}, p={p_typo_deni:.4f}")

r_typo_geo, p_typo_geo = mantel_test(typo_dist, geo_dist)
print(f"Typological dist ~ Geographic dist:  r={r_typo_geo:.4f}, p={p_typo_geo:.4f}")

r_nean_geo, p_nean_geo = mantel_test(nean_dist, geo_dist)
print(f"Neanderthal dist ~ Geographic dist:  r={r_nean_geo:.4f}, p={p_nean_geo:.4f}")

# Partial Mantel (controlling for geography)
print("\n--- Partial Mantel Tests (controlling for geographic distance) ---")
r_partial_nean, p_partial_nean = partial_mantel(typo_dist, nean_dist, geo_dist)
print(f"Typological ~ Neanderthal | Geography: r={r_partial_nean:.4f}, p={p_partial_nean:.4f}")

r_partial_deni, p_partial_deni = partial_mantel(typo_dist, deni_dist, geo_dist)
print(f"Typological ~ Denisovan | Geography:   r={r_partial_deni:.4f}, p={p_partial_deni:.4f}")

# ============================================================
# 8. Wallace Line Discontinuity Test
# ============================================================
print("\n" + "=" * 60)
print("8. WALLACE LINE DISCONTINUITY TEST")
print("=" * 60)

# Populations east vs west of Wallace Line (approx 117°E - 120°E)
# Restrict to ISEA/Oceania latitude band (-15° to 15°) to avoid misclassifying
# NE Asian populations (Japan, Yakut, etc.) as "east of Wallace Line"
WALLACE_LONG = 120.0
ISEA_LON_MIN = 95.0
ISEA_LAT_MIN = -15.0
ISEA_LAT_MAX = 15.0
isea_mask = ((lang_data['latitude'] >= ISEA_LAT_MIN) &
             (lang_data['latitude'] <= ISEA_LAT_MAX) &
             (lang_data['longitude'] >= ISEA_LON_MIN))
lang_data['east_wallace'] = (lang_data['longitude'] > WALLACE_LONG) & isea_mask
lang_data['west_wallace_isea'] = (lang_data['longitude'] <= WALLACE_LONG) & isea_mask

east = lang_data[lang_data['east_wallace'] == True]
west = lang_data[lang_data['west_wallace_isea'] == True]

print(f"\nWest of Wallace Line: n={len(west)}")
print(f"  Deni mean: {west['deni_mean'].mean():.4f} (±{west['deni_mean'].std():.4f})")
print(f"  Language families: {west['language_family'].nunique()} families")
print(f"  Morphological types: {dict(west['morphological_type'].value_counts())}")

print(f"\nEast of Wallace Line: n={len(east)}")
print(f"  Deni mean: {east['deni_mean'].mean():.4f} (±{east['deni_mean'].std():.4f})")
print(f"  Language families: {east['language_family'].nunique()} families")
print(f"  Morphological types: {dict(east['morphological_type'].value_counts())}")

if len(east) > 1 and len(west) > 1:
    mwu_wallace = stats.mannwhitneyu(
        east['deni_mean'].dropna(), west['deni_mean'].dropna(), alternative='greater')
    print(f"\nMann-Whitney U (Deni east > west): U={mwu_wallace.statistic:.1f}, p={mwu_wallace.pvalue:.6f}")

# ============================================================
# 9. Bootstrap CI for key correlations
# ============================================================
print("\n" + "=" * 60)
print("9. BOOTSTRAP 95% CI")
print("=" * 60)

def bootstrap_correlation(x, y, n_boot=5000):
    """Bootstrap 95% CI for Pearson r."""
    n = len(x)
    r_boots = []
    for _ in range(n_boot):
        idx = np.random.choice(n, n, replace=True)
        r_boots.append(np.corrcoef(x[idx], y[idx])[0, 1])
    r_boots = np.array(r_boots)
    return np.percentile(r_boots, [2.5, 97.5])

# Nean ~ morphological type (point-biserial: agglutinative vs others)
is_agglut = (lang_data['morphological_type'] == 'agglutinative').astype(int).values
nean_vals = lang_data['nean_mean'].values
r_agglut = np.corrcoef(is_agglut, nean_vals)[0, 1]
ci_agglut = bootstrap_correlation(is_agglut, nean_vals)
print(f"r(is_agglutinative, Nean): {r_agglut:.4f}, 95% CI [{ci_agglut[0]:.4f}, {ci_agglut[1]:.4f}]")

# Tone ~ Nean
is_tone = (lang_data['tone'] == 'yes').astype(int).values
r_tone = np.corrcoef(is_tone, nean_vals)[0, 1]
ci_tone = bootstrap_correlation(is_tone, nean_vals)
print(f"r(is_tone, Nean): {r_tone:.4f}, 95% CI [{ci_tone[0]:.4f}, {ci_tone[1]:.4f}]")

# ============================================================
# 10. Figures
# ============================================================
print("\n" + "=" * 60)
print("10. GENERATING FIGURES")
print("=" * 60)

# --- Figure 1: Boxplot of introgression by morphological type ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

morph_order = ['isolating', 'fusional', 'agglutinative']
colors = {'isolating': '#2196F3', 'fusional': '#FF9800', 'agglutinative': '#4CAF50'}

# Neanderthal
data_nean = [lang_data[lang_data['morphological_type'] == m]['nean_mean'].values for m in morph_order]
bp1 = axes[0].boxplot(data_nean, tick_labels=morph_order, patch_artist=True)
for patch, m in zip(bp1['boxes'], morph_order):
    patch.set_facecolor(colors[m])
    patch.set_alpha(0.7)
axes[0].set_ylabel('Mean Neanderthal Sharing')
axes[0].set_title(f'Neanderthal Introgression by Morphological Type\n(KW H={kw_nean.statistic:.2f}, p={kw_nean.pvalue:.4f})')
axes[0].set_xlabel('Language Morphological Type')

# Denisovan
data_deni = [lang_data[lang_data['morphological_type'] == m]['deni_mean'].dropna().values for m in morph_order]
bp2 = axes[1].boxplot(data_deni, tick_labels=morph_order, patch_artist=True)
for patch, m in zip(bp2['boxes'], morph_order):
    patch.set_facecolor(colors[m])
    patch.set_alpha(0.7)
axes[1].set_ylabel('Mean Denisovan Sharing')
axes[1].set_title(f'Denisovan Introgression by Morphological Type\n(KW H={kw_deni.statistic:.2f}, p={kw_deni.pvalue:.4f})')
axes[1].set_xlabel('Language Morphological Type')

plt.tight_layout()
fig1_path = os.path.join(FIG_DIR, 'fig1_morphology_vs_introgression.png')
plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig1_path}")

# --- Figure 2: Scatter plot Nean/Deni colored by typology ---
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
for morph in morph_order:
    subset = lang_data[lang_data['morphological_type'] == morph]
    ax.scatter(subset['nean_mean'], subset['deni_mean'],
               c=colors[morph], label=morph, s=80, alpha=0.7, edgecolors='k', linewidth=0.5)
    for pop in subset.index:
        ax.annotate(pop, (subset.loc[pop, 'nean_mean'], subset.loc[pop, 'deni_mean']),
                    fontsize=6, alpha=0.7, ha='left', va='bottom')

ax.set_xlabel('Mean Neanderthal Sharing')
ax.set_ylabel('Mean Denisovan Sharing')
ax.set_title('Archaic Introgression by Language Morphological Type')
ax.legend(title='Morphological Type', fontsize=10)
ax.grid(True, alpha=0.3)

fig2_path = os.path.join(FIG_DIR, 'fig2_nean_deni_scatter_morphology.png')
plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig2_path}")

# --- Figure 3: Tone vs. Non-tone ---
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
tone_data = [tone_no['nean_mean'].values, tone_yes['nean_mean'].values]
bp3 = axes[0].boxplot(tone_data, tick_labels=['Non-tonal', 'Tonal'], patch_artist=True)
bp3['boxes'][0].set_facecolor('#90CAF9')
bp3['boxes'][1].set_facecolor('#EF5350')
axes[0].set_ylabel('Mean Neanderthal Sharing')
axes[0].set_title(f'Neanderthal by Tone\n(MWU p={mwu_nean.pvalue:.4f})')

tone_data_d = [tone_no['deni_mean'].dropna().values, tone_yes['deni_mean'].dropna().values]
bp4 = axes[1].boxplot(tone_data_d, tick_labels=['Non-tonal', 'Tonal'], patch_artist=True)
bp4['boxes'][0].set_facecolor('#90CAF9')
bp4['boxes'][1].set_facecolor('#EF5350')
axes[1].set_ylabel('Mean Denisovan Sharing')
axes[1].set_title(f'Denisovan by Tone\n(MWU p={mwu_deni.pvalue:.4f})')

plt.tight_layout()
fig3_path = os.path.join(FIG_DIR, 'fig3_tone_vs_introgression.png')
plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig3_path}")

# --- Figure 4: Language family bar chart ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fam_order = family_stats.index.tolist()
x_pos = range(len(fam_order))

axes[0].barh(x_pos, family_stats['nean_mean'], xerr=family_stats['nean_std'],
             color='#5C6BC0', alpha=0.8, capsize=3)
axes[0].set_yticks(x_pos)
axes[0].set_yticklabels(fam_order, fontsize=8)
axes[0].set_xlabel('Mean Neanderthal Sharing')
axes[0].set_title('Neanderthal Introgression by Language Family')

axes[1].barh(x_pos, family_stats['deni_mean'], xerr=family_stats['deni_std'],
             color='#AB47BC', alpha=0.8, capsize=3)
axes[1].set_yticks(x_pos)
axes[1].set_yticklabels(fam_order, fontsize=8)
axes[1].set_xlabel('Mean Denisovan Sharing')
axes[1].set_title('Denisovan Introgression by Language Family')

plt.tight_layout()
fig4_path = os.path.join(FIG_DIR, 'fig4_language_family_introgression.png')
plt.savefig(fig4_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig4_path}")

# --- Figure 5: World map with typology + introgression ---
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    fig, ax = plt.subplots(1, 1, figsize=(16, 9),
                            subplot_kw={'projection': ccrs.Robinson()})
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
    ax.add_feature(cfeature.OCEAN, facecolor='#e8f4f8')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')

    # Plot populations: size=Neanderthal, color=morphological type
    marker_map = {'isolating': 'o', 'fusional': 's', 'agglutinative': '^'}
    for morph in morph_order:
        subset = lang_data[lang_data['morphological_type'] == morph]
        sizes = subset['nean_mean'] * 200 + 30
        ax.scatter(subset['longitude'], subset['latitude'],
                   c=colors[morph], s=sizes, marker=marker_map[morph],
                   alpha=0.8, edgecolors='k', linewidth=0.5,
                   transform=ccrs.PlateCarree(), label=morph, zorder=5)

    # Wallace Line
    wallace_lats = [-10, 10]
    ax.plot([WALLACE_LONG, WALLACE_LONG], wallace_lats,
            'r--', linewidth=2, transform=ccrs.PlateCarree(),
            label='Wallace Line (~120°E)', zorder=4)

    ax.legend(loc='lower left', fontsize=9, title='Morphological Type')
    ax.set_title('Global Distribution: Language Typology × Archaic Introgression\n'
                 '(marker size ∝ Neanderthal sharing)', fontsize=12)

    fig5_path = os.path.join(FIG_DIR, 'fig5_world_map_typology.png')
    plt.savefig(fig5_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {fig5_path}")
except ImportError:
    print("  [SKIP] cartopy not available for world map")

# ============================================================
# 11. Summary statistics output
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY OF KEY RESULTS")
print("=" * 60)

results = {
    'KW_nean_morph_H': kw_nean.statistic,
    'KW_nean_morph_p': kw_nean.pvalue,
    'KW_deni_morph_H': kw_deni.statistic,
    'KW_deni_morph_p': kw_deni.pvalue,
    'MWU_nean_tone_U': mwu_nean.statistic,
    'MWU_nean_tone_p': mwu_nean.pvalue,
    'MWU_deni_tone_U': mwu_deni.statistic,
    'MWU_deni_tone_p': mwu_deni.pvalue,
    'Mantel_typo_nean_r': r_typo_nean,
    'Mantel_typo_nean_p': p_typo_nean,
    'Mantel_typo_deni_r': r_typo_deni,
    'Mantel_typo_deni_p': p_typo_deni,
    'Mantel_typo_geo_r': r_typo_geo,
    'Mantel_typo_geo_p': p_typo_geo,
    'PartialMantel_typo_nean_geo_r': r_partial_nean,
    'PartialMantel_typo_nean_geo_p': p_partial_nean,
    'PartialMantel_typo_deni_geo_r': r_partial_deni,
    'PartialMantel_typo_deni_geo_p': p_partial_deni,
    'r_agglutinative_nean': r_agglut,
    'CI_agglut_lo': ci_agglut[0],
    'CI_agglut_hi': ci_agglut[1],
    'r_tone_nean': r_tone,
    'CI_tone_lo': ci_tone[0],
    'CI_tone_hi': ci_tone[1],
}

results_df = pd.DataFrame(list(results.items()), columns=['metric', 'value'])
results_path = os.path.join(DATA_DIR, 'analysis_results.csv')
results_df.to_csv(results_path, index=False)
print(f"\nResults saved to: {results_path}")

print("\n--- Key Findings ---")
print(f"1. Morphology ~ Neanderthal (KW): p={kw_nean.pvalue:.4f} {'***' if kw_nean.pvalue<0.001 else '**' if kw_nean.pvalue<0.01 else '*' if kw_nean.pvalue<0.05 else 'ns'}")
print(f"2. Morphology ~ Denisovan (KW):   p={kw_deni.pvalue:.4f} {'***' if kw_deni.pvalue<0.001 else '**' if kw_deni.pvalue<0.01 else '*' if kw_deni.pvalue<0.05 else 'ns'}")
print(f"3. Tone ~ Neanderthal (MWU):      p={mwu_nean.pvalue:.4f} {'***' if mwu_nean.pvalue<0.001 else '**' if mwu_nean.pvalue<0.01 else '*' if mwu_nean.pvalue<0.05 else 'ns'}")
print(f"4. Mantel (Typo~Nean):            r={r_typo_nean:.4f}, p={p_typo_nean:.4f}")
print(f"5. Partial Mantel (Typo~Nean|Geo): r={r_partial_nean:.4f}, p={p_partial_nean:.4f}")
print(f"6. Partial Mantel (Typo~Deni|Geo): r={r_partial_deni:.4f}, p={p_partial_deni:.4f}")

print("\nDone.")
