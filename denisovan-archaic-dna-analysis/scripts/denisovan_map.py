import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

plt.rcParams['font.family'] = ['Noto Serif CJK JP', 'DejaVu Sans']

# Data compiled from Sankararaman et al. 2016 (Current Biology),
# Jacobs et al. 2019 (Cell), JEWEL 2024, and other genomic studies.
# Values are approximate Denisovan ancestry proportions (%).
# Some values represent ranges; midpoints are used.

populations = [
    # (name, latitude, longitude, denisovan_pct)
    # Oceania / Island Southeast Asia (highest)
    ("Papuan", -5.5, 141.0, 3.5),
    ("Australian Aboriginal", -25.0, 134.0, 3.0),
    ("Bougainville", -6.2, 155.5, 2.8),
    ("Fijian", -18.0, 178.0, 1.9),
    ("Nusa Tenggara (E. Indonesia)", -9.5, 120.0, 1.4),
    ("Moluccas (E. Indonesia)", -2.5, 128.5, 1.2),
    ("Philippine Ayta/Mamanwa", 15.0, 121.5, 2.5),
    ("Polynesian", -15.0, -150.0, 0.8),

    # East Asia (low)
    ("Japanese", 36.0, 138.0, 0.06),
    ("Han Chinese", 35.0, 105.0, 0.06),
    ("Korean", 37.0, 127.0, 0.06),
    ("Vietnamese", 16.0, 106.0, 0.07),
    ("Dai (SW China)", 22.0, 100.0, 0.07),

    # South / Central Asia (slightly elevated)
    ("Sherpa / Tibetan", 28.5, 87.0, 0.10),
    ("South Indian", 12.0, 78.0, 0.05),
    ("Bengali", 23.5, 90.5, 0.04),

    # West Eurasia (very low / near zero)
    ("European (avg)", 50.0, 10.0, 0.02),
    ("Middle Eastern", 33.0, 44.0, 0.02),
    ("Central Asian", 42.0, 65.0, 0.03),

    # Americas (very low)
    ("Native American (avg)", 15.0, -90.0, 0.03),

    # Africa (none / negligible)
    ("Sub-Saharan African", 0.0, 20.0, 0.00),

    # Southeast Asia mainland
    ("Malay Peninsula", 4.0, 102.0, 0.05),
    ("W. Indonesian", -6.0, 107.0, 0.05),
]

fig = plt.figure(figsize=(16, 9))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
ax.set_global()

# Map features
ax.add_feature(cfeature.LAND, facecolor='#f0f0f0', edgecolor='none')
ax.add_feature(cfeature.OCEAN, facecolor='#d4e6f1')
ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='#888888')
ax.add_feature(cfeature.BORDERS, linewidth=0.3, color='#cccccc')

# Plot circles
max_pct = max(p[3] for p in populations)
scale_factor = 2000  # controls max circle size

for name, lat, lon, pct in populations:
    if pct == 0:
        size = 30
        color = '#cccccc'
        alpha = 0.7
    else:
        size = (pct / max_pct) * scale_factor + 30
        # Color gradient: low=blue, high=red
        norm_val = pct / max_pct
        color = plt.cm.YlOrRd(0.2 + 0.8 * norm_val)
        alpha = 0.75

    ax.plot(lon, lat, 'o',
            markersize=np.sqrt(size),
            color=color,
            alpha=alpha,
            transform=ccrs.PlateCarree(),
            markeredgecolor='#333333',
            markeredgewidth=0.5)

    # Label
    fontsize = 6.5 if pct < 0.5 else 7.5
    ax.text(lon, lat - 3.5, name,
            transform=ccrs.PlateCarree(),
            fontsize=fontsize,
            ha='center', va='top',
            color='#333333',
            fontweight='normal')

# Legend - size reference
legend_pcts = [0.05, 0.5, 1.0, 3.5]
legend_labels = []
legend_handles = []
for pct in legend_pcts:
    size = (pct / max_pct) * scale_factor + 30
    handle = plt.Line2D([0], [0], marker='o',
                        color='w',
                        markerfacecolor=plt.cm.YlOrRd(0.2 + 0.8 * (pct / max_pct)),
                        markeredgecolor='#333333',
                        markeredgewidth=0.5,
                        markersize=np.sqrt(size) * 0.7,
                        linestyle='None')
    legend_handles.append(handle)
    legend_labels.append(f'{pct}%')

legend = ax.legend(legend_handles, legend_labels,
                   title='Denisovan DNA (%)',
                   loc='lower left',
                   framealpha=0.9,
                   fontsize=9,
                   title_fontsize=10,
                   labelspacing=1.5,
                   borderpad=1.0)

ax.set_title('デニソワ人DNA痕跡の世界分布\n(円の大きさ = デニソワ人由来DNA割合 %)',
             fontsize=14, fontweight='bold', pad=15)

# Source annotation
fig.text(0.5, 0.02,
         'Sources: Sankararaman et al. 2016 (Current Biology), Jacobs et al. 2019 (Cell), '
         'Terao et al. 2024 (JEWEL/Science Advances), Reich et al. 2011',
         ha='center', fontsize=7, color='#666666')

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig('/home/ubuntu/denisovan_world_map.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.close()
print("Map saved to /home/ubuntu/denisovan_world_map.png")
