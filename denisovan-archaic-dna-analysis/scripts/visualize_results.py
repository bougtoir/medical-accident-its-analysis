import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams['font.family'] = ['Noto Serif CJK JP', 'DejaVu Sans']

res = pd.read_csv('pairwise_sharing.csv')

# ===== Figure 1: Neanderthal sharing vs geographic distance =====
fig, axes = plt.subplots(1, 2, figsize=(20, 9))

# --- Panel A: Neanderthal ---
ax = axes[0]
valid = res.dropna(subset=['nean_corr'])

# Color by region pair type
def region_pair_type(r1, r2):
    if r1 == r2:
        return 'intra'
    else:
        return 'inter'

valid = valid.copy()
valid['pair_type'] = valid.apply(lambda r: region_pair_type(r['region1'], r['region2']), axis=1)

intra = valid[valid['pair_type'] == 'intra']
inter = valid[valid['pair_type'] == 'inter']

ax.scatter(intra['geo_dist_km'] / 1000, intra['nean_corr'], 
           alpha=0.4, s=20, c='#4a90d9', label='同一地域内', zorder=3)
ax.scatter(inter['geo_dist_km'] / 1000, inter['nean_corr'], 
           alpha=0.4, s=20, c='#e74c3c', label='異なる地域間', zorder=3)

# Regression line
x_all = valid['geo_dist_km'].values / 1000
y_all = valid['nean_corr'].values
coeffs = np.polyfit(x_all, y_all, 1)
x_line = np.linspace(0, 20, 100)
ax.plot(x_line, np.polyval(coeffs, x_line), 'k--', linewidth=1.5, alpha=0.6, label='回帰直線')

# Annotate key outliers (inter-regional, high residual)
predicted = np.polyval(coeffs, valid['geo_dist_km'].values / 1000)
valid['residual'] = valid['nean_corr'].values - predicted

# Top inter-regional outliers
inter_outliers = valid[(valid['pair_type'] == 'inter') & (valid['residual'] > 0.35)]
for _, row in inter_outliers.head(8).iterrows():
    ax.annotate(f"{row['pop1']}-{row['pop2']}", 
                (row['geo_dist_km']/1000, row['nean_corr']),
                fontsize=6.5, alpha=0.9, 
                xytext=(5, 5), textcoords='offset points',
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5))

ax.set_xlabel('地理的距離 (×1000 km)', fontsize=12)
ax.set_ylabel('ネアンデルタール人セグメント共有度\n(相関係数)', fontsize=12)
ax.set_title('A. ネアンデルタール人DNA共有 vs 地理的距離', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.set_xlim(-0.5, 21)
ax.grid(True, alpha=0.2)

# --- Panel B: Denisovan ---
ax = axes[1]
valid_d = res.dropna(subset=['deni_corr'])
valid_d = valid_d.copy()
valid_d['pair_type'] = valid_d.apply(lambda r: region_pair_type(r['region1'], r['region2']), axis=1)

# Color by whether Oceania is involved
def has_oceania(r1, r2):
    if 'OCEANIA' in r1 or 'OCEANIA' in r2:
        return 'oce'
    elif r1 == r2:
        return 'intra'
    else:
        return 'inter'

valid_d['oce_type'] = valid_d.apply(lambda r: has_oceania(r['region1'], r['region2']), axis=1)

oce = valid_d[valid_d['oce_type'] == 'oce']
intra_d = valid_d[valid_d['oce_type'] == 'intra']
inter_d = valid_d[valid_d['oce_type'] == 'inter']

ax.scatter(intra_d['geo_dist_km'] / 1000, intra_d['deni_corr'],
           alpha=0.4, s=20, c='#4a90d9', label='同一地域内', zorder=3)
ax.scatter(inter_d['geo_dist_km'] / 1000, inter_d['deni_corr'],
           alpha=0.4, s=20, c='#e74c3c', label='異なる地域間', zorder=3)
ax.scatter(oce['geo_dist_km'] / 1000, oce['deni_corr'],
           alpha=0.7, s=50, c='#8e44ad', marker='D', label='オセアニア含む', zorder=4)

# Annotate Oceania pairs
for _, row in oce.head(10).iterrows():
    ax.annotate(f"{row['pop1']}-{row['pop2']}", 
                (row['geo_dist_km']/1000, row['deni_corr']),
                fontsize=6.5, alpha=0.9,
                xytext=(5, -10), textcoords='offset points',
                arrowprops=dict(arrowstyle='-', color='purple', alpha=0.5))

ax.set_xlabel('地理的距離 (×1000 km)', fontsize=12)
ax.set_ylabel('デニソワ人セグメント共有度\n(相関係数)', fontsize=12)
ax.set_title('B. デニソワ人DNA共有 vs 地理的距離', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, loc='upper right')
ax.set_xlim(-0.5, 21)
ax.grid(True, alpha=0.2)

fig.suptitle('古代人類DNA共有パターンと地理的距離の関係\n— 回帰直線からの乖離 ＝ 予想外の集団間接触の可能性 —',
             fontsize=14, fontweight='bold', y=1.02)

fig.text(0.5, -0.02,
         'Data: hmmix archaic introgression segments (Zenodo:14136628) | '
         '1000 Genomes + HGDP, 66 populations, 3,134 individuals | '
         '500kb bins, Pearson correlation of introgression frequency profiles',
         ha='center', fontsize=7.5, color='#888888')

plt.tight_layout()
plt.savefig('/home/ubuntu/archaic_sharing_vs_distance.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 1 saved.")

# ===== Figure 2: Heatmap of sharing for key populations =====
# Select representative populations
key_pops = [
    # Europe
    'CEU', 'FIN', 'GBR', 'IBS', 'TSI', 'Russian', 'Basque', 'Sardinian',
    # Middle East
    'Bedouin', 'Druze', 'Palestinian',
    # Central/South Asia
    'PJL', 'BEB', 'GIH', 'STU', 'Kalash', 'Burusho', 'Uygur',
    # East Asia
    'CHB', 'JPT', 'KHV', 'CDX', 'Yakut', 'Mongolian',
    # Americas
    'CLM', 'PEL', 'MXL', 'Maya', 'Pima',
    # Oceania
    'PapuanHighlands', 'PapuanSepik', 'Bougainville',
]

# Build sharing matrix
n = len(key_pops)
nean_matrix = np.eye(n)
deni_matrix = np.eye(n)

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
                nean_matrix[i, j] = nv
                nean_matrix[j, i] = nv
            if not np.isnan(dv):
                deni_matrix[i, j] = dv
                deni_matrix[j, i] = dv

# Region labels for coloring
region_map = {}
for _, row in res.iterrows():
    region_map[row['pop1']] = row['region1']
    region_map[row['pop2']] = row['region2']

region_colors = {
    'EUROPE': '#6b8e23', 'MIDDLE_EAST': '#cd853f', 
    'CENTRAL_SOUTH_ASIA': '#9370db', 'EAST_ASIA': '#e67e22',
    'AMERICA': '#4682b4', 'OCEANIA': '#8b0000'
}

fig, axes = plt.subplots(1, 2, figsize=(22, 10))

for idx, (matrix, title, cmap_name) in enumerate([
    (nean_matrix, 'ネアンデルタール人DNA共有', 'YlOrRd'),
    (deni_matrix, 'デニソワ人DNA共有', 'PuRd'),
]):
    ax = axes[idx]
    im = ax.imshow(matrix, cmap=cmap_name, vmin=0, vmax=1, aspect='auto')
    
    # Labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(key_pops, rotation=90, fontsize=7)
    ax.set_yticklabels(key_pops, fontsize=7)
    
    # Color labels by region
    for tick_idx, pop in enumerate(key_pops):
        reg = region_map.get(pop, '')
        color = region_colors.get(reg, 'black')
        ax.get_xticklabels()[tick_idx].set_color(color)
        ax.get_yticklabels()[tick_idx].set_color(color)
    
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='相関係数')

# Region legend
import matplotlib.patches as mpatches
legend_patches = [mpatches.Patch(color=c, label=r.replace('_', ' ').title()) 
                  for r, c in region_colors.items()]
fig.legend(handles=legend_patches, loc='lower center', ncol=6, fontsize=9,
           title='地域', title_fontsize=10, bbox_to_anchor=(0.5, -0.02))

fig.suptitle('主要集団間の古代人類DNAセグメント共有ヒートマップ',
             fontsize=14, fontweight='bold')

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig('/home/ubuntu/archaic_sharing_heatmap.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 2 saved.")
print("All done!")
