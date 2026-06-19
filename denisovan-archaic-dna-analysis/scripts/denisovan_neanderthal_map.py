import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

plt.rcParams['font.family'] = ['Noto Serif CJK JP', 'DejaVu Sans']

# Data compiled from:
# - Sankararaman et al. 2014 (Nature) - Neanderthal ancestry
# - Sankararaman et al. 2016 (Current Biology) - Denisovan + Neanderthal
# - Jacobs et al. 2019 (Cell) - ISEA Denisovan
# - Terao et al. 2024 (JEWEL/Science Advances) - Japanese
# - Reich et al. 2011 - Denisovan in Oceania
#
# Neanderthal %: based on genome-wide introgressed segment estimates
# Denisovan %: based on genome-wide introgressed segment estimates

populations = [
    # (name, lat, lon, neanderthal_pct, denisovan_pct)
    # Oceania / Island SE Asia
    ("Papuan", -5.5, 141.0, 1.8, 3.5),
    ("Australian Aboriginal", -25.0, 134.0, 1.7, 3.0),
    ("Bougainville", -6.2, 155.5, 1.7, 2.8),
    ("Fijian", -18.0, 178.0, 1.5, 1.9),
    ("Philippine Ayta", 15.0, 121.5, 1.6, 2.5),
    ("Nusa Tenggara", -9.5, 120.0, 1.5, 1.4),
    ("Moluccas", -2.5, 128.5, 1.5, 1.2),
    ("Polynesian", -15.0, -150.0, 1.3, 0.8),

    # East Asia
    ("Japanese", 36.0, 138.0, 1.38, 0.06),
    ("Han Chinese (N)", 39.0, 116.0, 1.40, 0.06),
    ("Han Chinese (S)", 23.0, 113.0, 1.37, 0.06),
    ("Korean", 37.5, 127.0, 1.38, 0.06),
    ("Vietnamese", 16.0, 106.0, 1.35, 0.07),
    ("Dai (SW China)", 22.0, 100.0, 1.35, 0.07),
    ("Mongolian", 47.0, 105.0, 1.35, 0.05),

    # South / Central Asia
    ("Sherpa / Tibetan", 28.5, 87.0, 1.30, 0.10),
    ("South Indian", 12.0, 78.0, 1.20, 0.05),
    ("Bengali", 23.5, 90.5, 1.25, 0.04),
    ("Pakistani", 30.0, 70.0, 1.20, 0.04),

    # Europe
    ("Northern European\n(FIN/GBR)", 60.0, 20.0, 1.20, 0.02),
    ("Western European\n(CEU/FRA)", 48.0, 2.0, 1.17, 0.02),
    ("Southern European\n(IBS/TSI)", 40.0, 12.0, 1.09, 0.02),
    ("Eastern European", 52.0, 35.0, 1.18, 0.02),

    # Middle East / Central Asia
    ("Middle Eastern", 33.0, 44.0, 1.15, 0.02),
    ("Central Asian", 42.0, 65.0, 1.25, 0.03),

    # Americas
    ("Native American\n(Mexico)", 20.0, -100.0, 1.22, 0.03),
    ("Native American\n(Colombia)", 5.0, -74.0, 1.14, 0.03),
    ("Native American\n(N. America)", 45.0, -105.0, 1.20, 0.03),

    # Africa (negligible for both)
    ("Sub-Saharan\nAfrican (W)", 8.0, 0.0, 0.08, 0.00),
    ("Sub-Saharan\nAfrican (E)", 0.0, 35.0, 0.08, 0.00),

    # SE Asia mainland
    ("Malay Peninsula", 4.0, 102.0, 1.30, 0.05),
    ("W. Indonesian", -6.0, 107.0, 1.30, 0.05),
]

fig = plt.figure(figsize=(18, 10))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
ax.set_global()

# Map features
ax.add_feature(cfeature.LAND, facecolor='#f5f5f5', edgecolor='none')
ax.add_feature(cfeature.OCEAN, facecolor='#e8f0f8')
ax.add_feature(cfeature.COASTLINE, linewidth=0.4, color='#999999')
ax.add_feature(cfeature.BORDERS, linewidth=0.2, color='#dddddd')

# Normalization
max_neanderthal = max(p[3] for p in populations)
max_denisovan = max(p[4] for p in populations)

# Size: Neanderthal (circle area proportional)
# Color: Denisovan (darker = more)
# Use a custom colormap from light yellow to deep purple
from matplotlib.colors import LinearSegmentedColormap
colors_list = ['#f7f7f7', '#fee8c8', '#fdbb84', '#e34a33', '#7a0177']
denisovan_cmap = LinearSegmentedColormap.from_list('denisovan', colors_list, N=256)

for name, lat, lon, nean_pct, deni_pct in populations:
    # Size based on Neanderthal %
    # Scale so that the smallest non-zero is visible and largest is prominent
    if nean_pct < 0.1:
        size = 15  # very small for Africa
    else:
        # map 1.0-1.8 to reasonable marker sizes
        size = 80 + (nean_pct / max_neanderthal) * 600

    # Color based on Denisovan %
    if deni_pct == 0:
        color = '#e0e0e0'
        edgecolor = '#999999'
    else:
        # Log-ish scale to better differentiate low values
        # Use power transform for better visual separation
        norm_deni = (deni_pct / max_denisovan) ** 0.4
        color = denisovan_cmap(norm_deni)
        edgecolor = '#333333'

    ax.plot(lon, lat, 'o',
            markersize=np.sqrt(size),
            color=color,
            alpha=0.85,
            transform=ccrs.PlateCarree(),
            markeredgecolor=edgecolor,
            markeredgewidth=0.6)

    # Label
    fontsize = 6.0
    offset_y = -3.0 if nean_pct > 0.5 else -2.5
    ax.text(lon, lat + offset_y, name,
            transform=ccrs.PlateCarree(),
            fontsize=fontsize,
            ha='center', va='top',
            color='#444444',
            linespacing=0.9)

# ---- Legend for SIZE (Neanderthal) ----
legend_nean = [0.08, 1.0, 1.4, 1.8]
legend_handles_size = []
for pct in legend_nean:
    if pct < 0.1:
        sz = 15
    else:
        sz = 80 + (pct / max_neanderthal) * 600
    handle = plt.Line2D([0], [0], marker='o', color='w',
                        markerfacecolor='#aaaaaa',
                        markeredgecolor='#333333',
                        markeredgewidth=0.5,
                        markersize=np.sqrt(sz) * 0.8,
                        linestyle='None')
    legend_handles_size.append(handle)

legend1 = ax.legend(legend_handles_size,
                    [f'{p}%' for p in legend_nean],
                    title='ネアンデルタール人DNA\n(円の大きさ)',
                    loc='lower left',
                    framealpha=0.95,
                    fontsize=8.5,
                    title_fontsize=9.5,
                    labelspacing=1.8,
                    borderpad=1.2,
                    bbox_to_anchor=(0.01, 0.02))

ax.add_artist(legend1)

# ---- Legend for COLOR (Denisovan) ----
legend_deni = [0.02, 0.1, 0.5, 1.5, 3.5]
legend_handles_color = []
for pct in legend_deni:
    norm_deni = (pct / max_denisovan) ** 0.4
    c = denisovan_cmap(norm_deni)
    handle = plt.Line2D([0], [0], marker='o', color='w',
                        markerfacecolor=c,
                        markeredgecolor='#333333',
                        markeredgewidth=0.5,
                        markersize=10,
                        linestyle='None')
    legend_handles_color.append(handle)

legend2 = ax.legend(legend_handles_color,
                    [f'{p}%' for p in legend_deni],
                    title='デニソワ人DNA\n(色の濃さ)',
                    loc='lower left',
                    framealpha=0.95,
                    fontsize=8.5,
                    title_fontsize=9.5,
                    labelspacing=1.2,
                    borderpad=1.2,
                    bbox_to_anchor=(0.14, 0.02))

ax.add_artist(legend2)

ax.set_title('古代人類DNA痕跡の世界分布\n円の大きさ＝ネアンデルタール人DNA割合 ／ 色の濃さ＝デニソワ人DNA割合',
             fontsize=13, fontweight='bold', pad=15)

# Source annotation
fig.text(0.5, 0.01,
         'Sources: Sankararaman et al. 2014 (Nature), Sankararaman et al. 2016 (Current Biology), '
         'Jacobs et al. 2019 (Cell), Terao et al. 2024 (JEWEL), Reich et al. 2011',
         ha='center', fontsize=7, color='#666666')

plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig('/home/ubuntu/archaic_dna_world_map.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.close()
print("Map saved to /home/ubuntu/archaic_dna_world_map.png")
