import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path
import matplotlib.patheffects as pe
import numpy as np

plt.rcParams['font.family'] = ['Noto Serif CJK JP', 'DejaVu Sans']

fig, ax = plt.subplots(figsize=(22, 13))
ax.set_xlim(-2, 100)
ax.set_ylim(-5, 55)
ax.axis('off')

# ===== Helper functions =====
def draw_flow(ax, points, width, color, alpha=0.8, zorder=2):
    """Draw a flow band along a path with given width."""
    from matplotlib.patches import Polygon
    pts = np.array(points)
    # Create upper and lower boundaries
    # Simple approach: offset perpendicular to path direction
    upper = []
    lower = []
    for i in range(len(pts)):
        if i == 0:
            dx = pts[1][0] - pts[0][0]
            dy = pts[1][1] - pts[0][1]
        elif i == len(pts) - 1:
            dx = pts[-1][0] - pts[-2][0]
            dy = pts[-1][1] - pts[-2][1]
        else:
            dx = pts[i+1][0] - pts[i-1][0]
            dy = pts[i+1][1] - pts[i-1][1]
        length = np.sqrt(dx**2 + dy**2)
        if length == 0:
            nx, ny = 0, 1
        else:
            nx, ny = -dy/length, dx/length
        # Width can be a list (varying width) or constant
        if isinstance(width, (list, np.ndarray)):
            w = width[i] / 2
        else:
            w = width / 2
        upper.append([pts[i][0] + nx*w, pts[i][1] + ny*w])
        lower.append([pts[i][0] - nx*w, pts[i][1] - ny*w])
    
    polygon_pts = upper + lower[::-1]
    poly = Polygon(polygon_pts, closed=True, facecolor=color, alpha=alpha, 
                   edgecolor='none', zorder=zorder)
    ax.add_patch(poly)
    # Add thin edge
    poly_edge = Polygon(polygon_pts, closed=True, facecolor='none', 
                        edgecolor=color, alpha=0.3, linewidth=0.5, zorder=zorder+0.1)
    ax.add_patch(poly_edge)

def draw_event_marker(ax, x, y, text, color='red', size=12):
    """Draw a star/burst marker for interbreeding events."""
    ax.plot(x, y, '*', markersize=size, color=color, zorder=10,
            markeredgecolor='white', markeredgewidth=0.3)
    ax.annotate(text, (x, y), fontsize=7, ha='center', va='bottom',
                xytext=(0, 8), textcoords='offset points',
                color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor=color, linewidth=0.5))

# ===== Define migration routes =====
# X-axis roughly represents time (left=old, right=recent) but also geography
# Y-axis represents rough latitude/geography (higher = north)

# Color scheme
c_main = '#4a6fa5'       # Main OOA stream
c_europe = '#6b8e23'     # European branch
c_eastasia = '#cd853f'   # East Asian branch
c_seasia = '#d2691e'     # SE Asian branch  
c_oceania = '#8b0000'    # Oceanian branch
c_americas = '#4682b4'   # Americas branch
c_south_asia = '#9370db' # South Asian branch

# ===== Main flow: Out of Africa =====
# Starting thick (large effective pop in Africa), thinning as groups split off
main_path = [(2, 25), (8, 27), (14, 30), (20, 32), (26, 33)]
main_width = [5.0, 4.8, 4.5, 4.2, 4.0]
draw_flow(ax, main_path, main_width, c_main, alpha=0.7)

# ===== Neanderthal interbreeding zone =====
# Around x=22-28 (representing ~50-45 kya, Levant/W. Asia)
nean_zone = FancyBboxPatch((20, 28), 10, 12, boxstyle="round,pad=0.5",
                            facecolor='#ffeb3b', alpha=0.15, edgecolor='#f57f17',
                            linewidth=1.5, linestyle='--', zorder=1)
ax.add_patch(nean_zone)
ax.text(25, 41, 'ネアンデルタール人\n生息域', fontsize=9, ha='center', va='center',
        color='#f57f17', fontstyle='italic')

# ===== Split point (after Neanderthal mixing) =====
# Western route -> Europe
europe_path = [(26, 33), (32, 37), (38, 40), (44, 42), (50, 43), (56, 44)]
europe_width = [3.0, 2.8, 2.6, 2.5, 2.4, 2.3]
draw_flow(ax, europe_path, europe_width, c_europe, alpha=0.7)

# Southern route -> South Asia
south_asia_path = [(26, 33), (32, 28), (38, 25), (44, 23), (50, 22)]
south_asia_width = [2.5, 2.3, 2.0, 1.8, 1.7]
draw_flow(ax, south_asia_path, south_asia_width, c_south_asia, alpha=0.7)

# Eastern route -> East/SE Asia
east_path = [(26, 33), (32, 32), (38, 30), (44, 28), (50, 27)]
east_width = [3.5, 3.2, 3.0, 2.8, 2.6]
draw_flow(ax, east_path, east_width, c_eastasia, alpha=0.7)

# SE Asia -> Oceania branch (splits from eastern route in SE Asia)
oceania_path = [(38, 30), (44, 24), (50, 18), (56, 14), (62, 10)]
oceania_width = [2.5, 2.3, 2.0, 1.8, 1.6]
draw_flow(ax, oceania_path, oceania_width, c_oceania, alpha=0.7)

# East Asia continues north
ne_asia_path = [(50, 27), (56, 30), (62, 33), (68, 36), (74, 38)]
ne_asia_width = [2.4, 2.2, 2.0, 1.9, 1.8]
draw_flow(ax, ne_asia_path, ne_asia_width, c_eastasia, alpha=0.7)

# Japan branch
japan_path = [(68, 36), (74, 40), (80, 42)]
japan_width = [1.2, 1.1, 1.0]
draw_flow(ax, japan_path, japan_width, '#e67e22', alpha=0.7)

# Americas branch (from NE Asia via Beringia)
americas_path = [(74, 38), (80, 42), (86, 44), (92, 40), (96, 35), (96, 28)]
americas_width = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0]
draw_flow(ax, americas_path, americas_width, c_americas, alpha=0.7)

# ===== Denisovan interbreeding zone =====
# In SE Asia around x=42-52
deni_zone = FancyBboxPatch((40, 13), 14, 14, boxstyle="round,pad=0.5",
                            facecolor='#e040fb', alpha=0.1, edgecolor='#7b1fa2',
                            linewidth=1.5, linestyle='--', zorder=1)
ax.add_patch(deni_zone)
ax.text(47, 12, 'デニソワ人\n生息域', fontsize=9, ha='center', va='center',
        color='#7b1fa2', fontstyle='italic')

# ===== Event markers =====
# Neanderthal interbreeding (~47 kya)
draw_event_marker(ax, 24, 32, 'ネアンデルタール人と混血\n~47,000年前\n(全非アフリカ人の祖先)', color='#e65100', size=18)

# Denisovan interbreeding 1 (Oceania ancestors, ~45 kya)
draw_event_marker(ax, 46, 22, 'デニソワ人と混血①\n~45,000年前\n(オセアニア祖先: 3-5%)', color='#7b1fa2', size=16)

# Denisovan interbreeding 2 (East Asians, smaller, ~30-40 kya)
draw_event_marker(ax, 55, 28, 'デニソワ人と混血②\n~30,000年前\n(東アジア: ~0.06%)', color='#9c27b0', size=12)

# ===== Labels for destinations =====
label_style = dict(fontsize=10, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='gray', linewidth=0.5))

ax.text(56, 46, 'ヨーロッパ\n~45,000年前', color=c_europe, **label_style)
ax.text(50, 20, '南アジア\n~50,000年前', color=c_south_asia, **label_style)
ax.text(62, 8, 'オセアニア\n(パプア・豪州)\n~50,000年前', color=c_oceania, **label_style)
ax.text(80, 44, '日本\n~38,000年前\n(縄文人)', color='#e67e22', **label_style)
ax.text(74, 35, '東アジア\n~40,000年前', color=c_eastasia, **label_style)
ax.text(96, 25, 'アメリカ大陸\n~15,000年前', color=c_americas, **label_style)

# Africa source
ax.text(2, 23, 'アフリカ\n(起源)', fontsize=12, fontweight='bold', ha='center', va='top',
        color=c_main,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#e3f2fd', alpha=0.9, edgecolor=c_main))

# ===== Time axis at bottom =====
time_y = -2
ax.plot([2, 96], [time_y, time_y], 'k-', linewidth=1, zorder=5)
time_marks = [(2, '70,000'), (14, '60,000'), (26, '50,000'), (38, '45,000'), 
              (50, '40,000'), (62, '35,000'), (74, '25,000'), (86, '15,000'), (96, '現在')]
for x, label in time_marks:
    ax.plot(x, time_y, 'k|', markersize=8)
    ax.text(x, time_y - 1.5, label, ha='center', fontsize=8, color='#333333')
ax.text(50, time_y - 3.5, '年前 (years ago)', ha='center', fontsize=9, color='#555555')

# ===== Width legend =====
ax.text(3, 50, '帯の太さ = 集団の相対的サイズ\n（遺伝的多様性の減少を反映）', fontsize=9,
        va='top', color='#555555',
        bbox=dict(boxstyle='round', facecolor='#fafafa', edgecolor='#cccccc'))

# ===== Color legend =====
legend_patches = [
    mpatches.Patch(color=c_main, label='出アフリカ本流'),
    mpatches.Patch(color=c_europe, label='ヨーロッパ系'),
    mpatches.Patch(color=c_south_asia, label='南アジア系'),
    mpatches.Patch(color=c_eastasia, label='東アジア系'),
    mpatches.Patch(color='#e67e22', label='日本（縄文）'),
    mpatches.Patch(color=c_oceania, label='オセアニア系'),
    mpatches.Patch(color=c_americas, label='アメリカ先住民'),
]
legend = ax.legend(handles=legend_patches, loc='upper right', fontsize=9,
                   title='移動経路', title_fontsize=10, framealpha=0.95,
                   edgecolor='#cccccc')

# ===== Title =====
ax.set_title('ホモ・サピエンスの出アフリカと古代人類との混血\n— ミナール図風フロー可視化 —',
             fontsize=16, fontweight='bold', pad=20)

# ===== Archaic DNA summary box =====
summary_text = (
    "【混血による獲得DNA】\n"
    "ネアンデルタール人: 全非アフリカ人 1.0-1.8%\n"
    "  └ 東アジア人 ~1.4% > ヨーロッパ人 ~1.2%\n"
    "デニソワ人: パプア人 3-5% >> 東アジア人 ~0.06%\n"
    "  └ 日本人(縄文系)にはほぼ痕跡なし"
)
ax.text(78, 52, summary_text, fontsize=8.5, va='top', ha='left',
        family='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff3e0', edgecolor='#ff9800',
                  alpha=0.95, linewidth=1))

fig.text(0.5, 0.01,
         'Sources: Sankararaman et al. 2014/2016, Jacobs et al. 2019, Terao et al. 2024 (JEWEL), '
         'Prüfer et al. 2021, Hajdinjak et al. 2024 | 帯幅は概念的な図示であり厳密な定量値ではない',
         ha='center', fontsize=7, color='#888888')

plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig('/home/ubuntu/minard_human_migration.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.close()
print("Done: /home/ubuntu/minard_human_migration.png")
