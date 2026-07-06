"""
TONGE Patent Figures - Matplotlib rendering for JPO submission
Black-and-white line drawings, A4 ready
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Arc
from matplotlib.lines import Line2D
import numpy as np
import os

# Japanese font support
import matplotlib.font_manager as fm
plt.rcParams['font.family'] = 'IPAGothic'

OUT_DIR = "/home/ubuntu/repos/wip/color_cooking_concept/patent_figures_png"
os.makedirs(OUT_DIR, exist_ok=True)

# Common styling
BOX_STYLE = dict(boxstyle="round,pad=0.3", facecolor="white",
                 edgecolor="black", linewidth=1.5)
RECT_STYLE = dict(boxstyle="square,pad=0.3", facecolor="white",
                  edgecolor="black", linewidth=1.5)


def save_fig(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {path}")


# ═══════════════════════════════════════════════════════════════════
# 【図1】全体構成ブロック図
# ═══════════════════════════════════════════════════════════════════
print("Fig 1: Block diagram...")

fig, ax = plt.subplots(1, 1, figsize=(12, 9))
ax.set_xlim(0, 12)
ax.set_ylim(0, 9)
ax.axis('off')
ax.set_aspect('equal')

# Title
ax.text(6, 8.7, '【図1】', fontsize=14, ha='center', fontweight='bold')

# Outer frame - device 100
outer = FancyBboxPatch((0.5, 1.5), 11, 6.8, boxstyle="round,pad=0.1",
                       facecolor="none", edgecolor="black", linewidth=2)
ax.add_patch(outer)
ax.text(1, 8.0, '調理タイミング判定装置 100', fontsize=11, fontweight='bold')

# Color sensor section 110
sensor = FancyBboxPatch((1, 5.5), 3, 2.3, boxstyle="round,pad=0.1",
                        facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(sensor)
ax.text(2.5, 7.4, '色彩センサー部 110', fontsize=9, ha='center', fontweight='bold')
ax.text(2.5, 6.8, 'RGBCセンサー 111', fontsize=8, ha='center')
ax.text(2.5, 6.4, '(TCS3472)', fontsize=7, ha='center')
ax.text(2.5, 5.9, '白色LED照明 112', fontsize=8, ha='center')

# MCU section 120
mcu = FancyBboxPatch((4.8, 5.5), 4.2, 2.3, boxstyle="round,pad=0.1",
                     facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(mcu)
ax.text(6.9, 7.4, 'マイクロコントローラ部 120', fontsize=9, ha='center', fontweight='bold')
ax.text(6.9, 6.9, '(ESP32-S3)', fontsize=7, ha='center')
ax.text(5.2, 6.4, '・色空間変換 (RGB→L*a*b*)', fontsize=7, ha='left')
ax.text(5.2, 6.0, '・色差ΔE判定', fontsize=7, ha='left')
ax.text(5.2, 5.6, '・予測通知 (変化率推定)', fontsize=7, ha='left')

# Display section 130
disp = FancyBboxPatch((1, 2.2), 3, 2.5, boxstyle="round,pad=0.1",
                      facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(disp)
ax.text(2.5, 4.3, '表示部 130', fontsize=9, ha='center', fontweight='bold')
ax.text(2.5, 3.8, '(タッチスクリーン)', fontsize=7, ha='center')
ax.text(2.5, 3.3, 'プリセット選択', fontsize=7, ha='center')
ax.text(2.5, 2.8, 'ΔEプログレスバー', fontsize=7, ha='center')
ax.text(2.5, 2.4, 'トレンドグラフ', fontsize=7, ha='center')

# Notification section 140
notif = FancyBboxPatch((4.8, 2.2), 2.8, 2.5, boxstyle="round,pad=0.1",
                       facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(notif)
ax.text(6.2, 4.3, '通知部 140', fontsize=9, ha='center', fontweight='bold')
ax.text(6.2, 3.6, 'スピーカー', fontsize=7, ha='center')
ax.text(6.2, 3.1, '(880Hz/1100Hz)', fontsize=7, ha='center')
ax.text(6.2, 2.6, 'Wi-Fi/BLE', fontsize=7, ha='center')

# Storage section 150
stor = FancyBboxPatch((8.2, 2.2), 3, 2.5, boxstyle="round,pad=0.1",
                      facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(stor)
ax.text(9.7, 4.3, '記憶部 150', fontsize=9, ha='center', fontweight='bold')
ax.text(9.7, 3.7, '(不揮発性メモリ)', fontsize=7, ha='center')
ax.text(9.7, 3.2, '目標色プリセット辞書', fontsize=7, ha='center')
ax.text(9.7, 2.7, 'きつね色[68.5,12.3,42.1]', fontsize=6, ha='center')
ax.text(9.7, 2.4, '飴色[73.2,8.7,38.5]', fontsize=6, ha='center')

# Input (user)
inp = FancyBboxPatch((9.5, 5.5), 2, 1.5, boxstyle="round,pad=0.1",
                     facecolor="#f0f0f0", edgecolor="black", linewidth=1.5)
ax.add_patch(inp)
ax.text(10.5, 6.5, '入力手段', fontsize=9, ha='center', fontweight='bold')
ax.text(10.5, 6.0, '(タッチパネル)', fontsize=7, ha='center')

# Arrows
arrow_style = dict(arrowstyle='->', lw=1.5, color='black')
# Sensor -> MCU
ax.annotate('', xy=(4.8, 6.5), xytext=(4.0, 6.5),
            arrowprops=arrow_style)
ax.text(4.4, 6.7, 'I2C', fontsize=7, ha='center')

# MCU -> Display
ax.annotate('', xy=(2.5, 4.7), xytext=(6.0, 5.5),
            arrowprops=arrow_style)

# MCU -> Notification
ax.annotate('', xy=(6.2, 4.7), xytext=(6.5, 5.5),
            arrowprops=arrow_style)

# MCU -> Storage (bidirectional)
ax.annotate('', xy=(9.0, 4.7), xytext=(8.0, 5.5),
            arrowprops=arrow_style)
ax.annotate('', xy=(8.5, 5.5), xytext=(9.5, 4.7),
            arrowprops=arrow_style)

# Input -> MCU
ax.annotate('', xy=(9.0, 6.5), xytext=(9.5, 6.3),
            arrowprops=arrow_style)

save_fig(fig, "fig1_block_diagram.png")


# ═══════════════════════════════════════════════════════════════════
# 【図2】色空間変換の処理フロー
# ═══════════════════════════════════════════════════════════════════
print("Fig 2: Color conversion flow...")

fig, ax = plt.subplots(1, 1, figsize=(8, 12))
ax.set_xlim(0, 8)
ax.set_ylim(0, 12)
ax.axis('off')
ax.set_aspect('equal')

ax.text(4, 11.7, '【図2】', fontsize=14, ha='center', fontweight='bold')

steps = [
    "TCS3472 RGBC値取得\n(R, G, B, C raw data)",
    "正規化\nr = R/C,  g = G/C,  b = B/C",
    "ホワイトバランス補正\nr' = r × coeff_R\ng' = g × coeff_G\nb' = b × coeff_B",
    "逆sRGBコンパンディング\nc > 0.04045 → ((c+0.055)/1.055)^{2.4}\nc <= 0.04045 → c / 12.92",
    "線形RGB → CIE XYZ (D65)\n[X]   [0.4124 0.3576 0.1805] [R_lin]\n[Y] = [0.2126 0.7152 0.0722] [G_lin]\n[Z]   [0.0193 0.1192 0.9505] [B_lin]",
    "CIE XYZ → L*a*b*\nL* = 116·f(Y/Yn) − 16\na* = 500·(f(X/Xn) − f(Y/Yn))\nb* = 200·(f(Y/Yn) − f(Z/Zn))",
    "出力: L*, a*, b*"
]

y_positions = [10.5, 9.3, 8.0, 6.5, 5.0, 3.3, 1.8]
box_heights = [0.8, 0.8, 1.0, 1.0, 1.2, 1.2, 0.6]

for i, (step, y, h) in enumerate(zip(steps, y_positions, box_heights)):
    box = FancyBboxPatch((1.5, y - h / 2), 5, h,
                         boxstyle="round,pad=0.1",
                         facecolor="white" if i < len(steps) - 1 else "#e0e0e0",
                         edgecolor="black", linewidth=1.5)
    ax.add_patch(box)
    ax.text(4, y, step, fontsize=8, ha='center', va='center')

    # Arrow to next
    if i < len(steps) - 1:
        next_y = y_positions[i + 1]
        next_h = box_heights[i + 1]
        ax.annotate('', xy=(4, next_y + next_h / 2 + 0.05),
                    xytext=(4, y - h / 2 - 0.05),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

save_fig(fig, "fig2_color_conversion_flow.png")


# ═══════════════════════════════════════════════════════════════════
# 【図3】目標色プリセット辞書のデータ構造
# ═══════════════════════════════════════════════════════════════════
print("Fig 3: Preset dictionary...")

fig, ax = plt.subplots(1, 1, figsize=(12, 7))
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis('off')

ax.text(6, 6.7, '【図3】', fontsize=14, ha='center', fontweight='bold')

# Table data
headers = ["ID", "色名_ja", "色名_en", "L*", "a*", "b*", "ΔE閾値", "カテゴリ"]
data = [
    ["1", "きつね色", "Golden Brown", "68.5", "12.3", "42.1", "6.0", "揚げ物・焼き物"],
    ["2", "飴色", "Caramel", "73.2", "8.7", "38.5", "5.0", "炒め物"],
    ["3", "ハシバミ色", "Hazelnut", "65.0", "10.1", "30.2", "5.0", "焼き菓子"],
    ["4", "こんがり", "Toasted", "60.0", "15.2", "35.8", "6.0", "パン"],
    ["5", "べっこう色", "Amber", "55.0", "20.3", "45.0", "4.0", "カラメル"],
    ["6", "焦がしバター色", "Beurre Noisette", "48.0", "12.5", "28.0", "4.0", "ソース"],
    ["N", "(ユーザー定義)", "(user-defined)", "—", "—", "—", "—", "—"],
]

col_widths = [0.5, 1.8, 1.8, 0.7, 0.7, 0.7, 1.0, 1.8]
x_start = 0.5
y_start = 6.0
row_h = 0.6

# Draw table
total_w = sum(col_widths)
for row_idx in range(-1, len(data)):
    y = y_start - (row_idx + 1) * row_h
    x = x_start

    if row_idx == -1:
        # Header
        for col_idx, (header, w) in enumerate(zip(headers, col_widths)):
            rect = Rectangle((x, y), w, row_h, facecolor="#d0d0d0",
                             edgecolor="black", linewidth=1)
            ax.add_patch(rect)
            ax.text(x + w / 2, y + row_h / 2, header,
                    fontsize=8, ha='center', va='center', fontweight='bold')
            x += w
    else:
        for col_idx, (val, w) in enumerate(zip(data[row_idx], col_widths)):
            fc = "#f8f8f8" if row_idx % 2 == 0 else "white"
            rect = Rectangle((x, y), w, row_h, facecolor=fc,
                             edgecolor="black", linewidth=0.8)
            ax.add_patch(rect)
            ax.text(x + w / 2, y + row_h / 2, val,
                    fontsize=7, ha='center', va='center')
            x += w

# Annotation
ax.text(0.5, 0.8, "※ ユーザーがカスタムプリセットを追加可能 (N行目以降)",
        fontsize=8, ha='left')
ax.text(0.5, 0.4, "※ クラウド経由で辞書更新・共有が可能 (請求項8)",
        fontsize=8, ha='left')

save_fig(fig, "fig3_preset_dictionary.png")


# ═══════════════════════════════════════════════════════════════════
# 【図4】調理タイミング判定方法の処理フロー
# ═══════════════════════════════════════════════════════════════════
print("Fig 4: Method flow...")

fig, ax = plt.subplots(1, 1, figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_aspect('equal')

ax.text(5, 13.7, '【図4】', fontsize=14, ha='center', fontweight='bold')

# Steps
flow = [
    ("S1: プリセットから目標色を選択\n(表示部130のメニュー画面)", 12.5),
    ("S2: 白色基準面の計測\n→ ホワイトバランス補正係数算出", 10.8),
    ("S3: 食品初期色を計測\n→ 初期L*a*b*値・初期ΔE算出", 9.1),
    ("S4: 食品色の連続監視\nRGBC取得 → L*a*b*変換 → ΔE算出", 7.4),
]

for text, y in flow:
    box = FancyBboxPatch((2, y - 0.6), 6, 1.2,
                         boxstyle="round,pad=0.15",
                         facecolor="white", edgecolor="black", linewidth=1.5)
    ax.add_patch(box)
    ax.text(5, y, text, fontsize=9, ha='center', va='center')

# Arrows between steps
for i in range(len(flow) - 1):
    y1 = flow[i][1] - 0.6
    y2 = flow[i + 1][1] + 0.6
    ax.annotate('', xy=(5, y2 + 0.05), xytext=(5, y1 - 0.05),
                arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# Decision diamond
diamond_y = 5.5
diamond_pts = np.array([[5, 6.2], [7.5, 5.5], [5, 4.8], [2.5, 5.5], [5, 6.2]])
ax.plot(diamond_pts[:, 0], diamond_pts[:, 1], 'k-', linewidth=1.5)
ax.text(5, 5.5, 'ΔE < 閾値？', fontsize=10, ha='center', va='center',
        fontweight='bold')

# Arrow from S4 to diamond
ax.annotate('', xy=(5, 6.2 + 0.05), xytext=(5, 7.4 - 0.6 - 0.05),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# No path (loop back)
ax.text(7.8, 5.7, 'No', fontsize=9)
ax.annotate('', xy=(8.5, 7.4), xytext=(7.5, 5.5),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black',
                            connectionstyle="arc3,rad=-0.3"))

# Yes path
ax.text(4.0, 4.5, 'Yes', fontsize=9)
ax.annotate('', xy=(5, 3.5 + 0.6 + 0.05), xytext=(5, 4.8 - 0.05),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

# Prediction branch
pred_box = FancyBboxPatch((0.3, 4.9), 2, 1.2,
                          boxstyle="round,pad=0.1",
                          facecolor="#f0f0f0", edgecolor="black",
                          linewidth=1.0, linestyle='dashed')
ax.add_patch(pred_box)
ax.text(1.3, 5.5, '予測判定:\n残り≈5cycles\n→予告通知', fontsize=7, ha='center', va='center')
ax.annotate('', xy=(2.3, 5.5), xytext=(2.5, 5.5),
            arrowprops=dict(arrowstyle='-', lw=1.0, color='black', linestyle='dashed'))

# S5 - Final
box = FancyBboxPatch((2, 2.9), 6, 1.2,
                     boxstyle="round,pad=0.15",
                     facecolor="#e0e0e0", edgecolor="black", linewidth=1.5)
ax.add_patch(box)
ax.text(5, 3.5, 'S5: 目標色到達通知\nアラーム音 + 到達画面表示', fontsize=9,
        ha='center', va='center')

# End
ax.text(5, 2.2, '終了', fontsize=10, ha='center',
        bbox=dict(boxstyle='circle', facecolor='#d0d0d0', edgecolor='black'))

ax.annotate('', xy=(5, 2.5), xytext=(5, 2.9 - 0.05),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))

save_fig(fig, "fig4_method_flow.png")


# ═══════════════════════════════════════════════════════════════════
# 【図5】ΔE時系列追跡および予測通知の動作説明図
# ═══════════════════════════════════════════════════════════════════
print("Fig 5: ΔE time series...")

fig, ax = plt.subplots(1, 1, figsize=(10, 7))

ax.set_title('【図5】', fontsize=14, fontweight='bold', pad=15)

# Generate ΔE curve (exponential decay-like)
cycles = np.arange(0, 35)
delta_e = 48 * np.exp(-0.1 * cycles) + 2

ax.plot(cycles, delta_e, 'k-', linewidth=2, marker='o', markersize=4,
        label='ΔE計測値')

# Threshold line
threshold = 5.0
ax.axhline(y=threshold, color='black', linestyle='--', linewidth=1.5,
           label=f'ΔE閾値 = {threshold}')

# Find prediction point (when remaining ≈ 5 cycles to threshold)
# threshold crossing around cycle 28-30
cross_idx = np.where(delta_e <= threshold)[0]
if len(cross_idx) > 0:
    reach_cycle = cross_idx[0]
    pred_cycle = max(0, reach_cycle - 5)

    # Mark prediction point
    ax.plot(pred_cycle, delta_e[pred_cycle], 'ko', markersize=12)
    ax.annotate('● 予告通知発動\n  (残り≈5サイクル)',
                xy=(pred_cycle, delta_e[pred_cycle]),
                xytext=(pred_cycle + 3, delta_e[pred_cycle] + 5),
                fontsize=9,
                arrowprops=dict(arrowstyle='->', lw=1.2))

    # Mark reached point
    ax.plot(reach_cycle, delta_e[reach_cycle], 'k*', markersize=15)
    ax.annotate('★ 目標到達\n  (ΔE < 閾値)',
                xy=(reach_cycle, delta_e[reach_cycle]),
                xytext=(reach_cycle - 8, delta_e[reach_cycle] - 3),
                fontsize=9,
                arrowprops=dict(arrowstyle='->', lw=1.2))

ax.set_xlabel('時間 (監視サイクル)', fontsize=11)
ax.set_ylabel('ΔE (色差)', fontsize=11)
ax.set_xlim(-1, 35)
ax.set_ylim(0, 55)
ax.legend(loc='upper right', fontsize=9)
ax.grid(True, alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

save_fig(fig, "fig5_delta_e_timeseries.png")


# ═══════════════════════════════════════════════════════════════════
# 【図6】外付けクリップオン型実装例の外観図
# ═══════════════════════════════════════════════════════════════════
print("Fig 6: External form factor...")

fig, ax = plt.subplots(1, 1, figsize=(8, 10))
ax.set_xlim(0, 8)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_aspect('equal')

ax.text(4, 9.7, '【図6】', fontsize=14, ha='center', fontweight='bold')

# CoreS3 body (top)
body = FancyBboxPatch((2.5, 6.5), 3, 2.5, boxstyle="round,pad=0.1",
                      facecolor="#f0f0f0", edgecolor="black", linewidth=2)
ax.add_patch(body)

# Screen on CoreS3
screen = Rectangle((3.0, 7.0), 2, 1.5, facecolor="white",
                   edgecolor="black", linewidth=1.5)
ax.add_patch(screen)
ax.text(4, 8.1, 'ΔE: 12.3', fontsize=8, ha='center', va='center')
ax.text(4, 7.7, '[====>   ] 62%', fontsize=7, ha='center', va='center')
ax.text(4, 7.3, 'きつね色', fontsize=7, ha='center', va='center')

ax.text(4, 9.2, '表示部 130', fontsize=9, ha='center')
ax.text(6.0, 7.5, '← CoreS3本体', fontsize=8)

# Grove cable
ax.plot([4, 4], [6.5, 5.8], 'k-', linewidth=2)
ax.text(4.5, 6.1, 'Grove\nケーブル', fontsize=7)

# Sensor unit
sensor_box = FancyBboxPatch((3, 4.5), 2, 1.3, boxstyle="round,pad=0.1",
                            facecolor="white", edgecolor="black", linewidth=2)
ax.add_patch(sensor_box)
ax.text(4, 5.3, '色彩センサー部 110', fontsize=7, ha='center')
ax.text(4, 4.8, '◉ RGBC  ◎ LED', fontsize=8, ha='center')

# Clip mechanism
clip_top = Rectangle((2.5, 4.0), 3, 0.3, facecolor="#808080",
                     edgecolor="black", linewidth=1.5)
ax.add_patch(clip_top)
clip_bot = Rectangle((2.5, 3.5), 3, 0.3, facecolor="#808080",
                     edgecolor="black", linewidth=1.5)
ax.add_patch(clip_bot)
# Spring indicator
ax.text(5.8, 3.8, '← クリップ機構', fontsize=8)

# Pan rim
pan = Rectangle((1.5, 3.5), 5, 0.5, facecolor="#d0d0d0",
                edgecolor="black", linewidth=1.5)
ax.add_patch(pan)
ax.text(6.8, 3.7, '← 鍋/フライパン縁', fontsize=8)

# Arrow showing measurement direction
ax.annotate('', xy=(4, 2.3), xytext=(4, 4.0),
            arrowprops=dict(arrowstyle='->', lw=2, color='black'))
ax.text(5, 3.0, '照射・計測方向', fontsize=8)

# Food surface
food = FancyBboxPatch((1.5, 1.0), 5, 1.2, boxstyle="round,pad=0.1",
                      facecolor="#e8e8e8", edgecolor="black", linewidth=1.5)
ax.add_patch(food)
ax.text(4, 1.6, '調理中の食品', fontsize=10, ha='center', va='center')
ax.text(4, 1.2, '(被計測対象)', fontsize=8, ha='center', va='center')

# Dimension annotation
ax.annotate('', xy=(1.2, 4.5), xytext=(1.2, 2.2),
            arrowprops=dict(arrowstyle='<->', lw=1, color='black'))
ax.text(0.3, 3.3, '数cm\n〜10cm', fontsize=8, ha='center')

save_fig(fig, "fig6_clip_on_form.png")


# ═══════════════════════════════════════════════════════════════════
# 【図7】ユーザーインターフェース画面遷移図
# ═══════════════════════════════════════════════════════════════════
print("Fig 7: UI screen transitions...")

fig, ax = plt.subplots(1, 1, figsize=(14, 8))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')

ax.text(7, 7.7, '【図7】', fontsize=14, ha='center', fontweight='bold')

# MENU screen
menu = Rectangle((0.5, 2.5), 2.8, 4.5, facecolor="white",
                 edgecolor="black", linewidth=2)
ax.add_patch(menu)
ax.text(1.9, 6.7, 'MENU画面', fontsize=9, ha='center', fontweight='bold')
ax.text(1.9, 6.2, 'TONGE', fontsize=8, ha='center', fontweight='bold')
items = ['▶ きつね色', '▶ 飴色', '▶ ハシバミ色', '▶ こんがり', '▶ べっこう色', '▶ 焦がしバター']
for i, item in enumerate(items):
    ax.text(1.0, 5.6 - i * 0.45, item, fontsize=7)

# CALIBRATE screen
cal = Rectangle((4.5, 3.5), 2.8, 3.5, facecolor="white",
                edgecolor="black", linewidth=2)
ax.add_patch(cal)
ax.text(5.9, 6.7, 'CALIBRATE', fontsize=9, ha='center', fontweight='bold')
ax.text(5.9, 5.8, '白い面を', fontsize=8, ha='center')
ax.text(5.9, 5.3, 'センサーに', fontsize=8, ha='center')
ax.text(5.9, 4.8, 'かざして', fontsize=8, ha='center')
ax.text(5.9, 4.3, 'ください', fontsize=8, ha='center')
ax.text(5.9, 3.7, '[タッチで開始]', fontsize=7, ha='center')

# MONITORING screen
mon = Rectangle((8.2, 2.5), 2.8, 4.5, facecolor="white",
                edgecolor="black", linewidth=2)
ax.add_patch(mon)
ax.text(9.6, 6.7, 'MONITORING', fontsize=9, ha='center', fontweight='bold')
ax.text(9.6, 6.1, '■Now  ■Target', fontsize=7, ha='center')
ax.text(9.6, 5.6, 'ΔE: 15.2', fontsize=9, ha='center', fontweight='bold')
ax.text(9.6, 5.1, '[======>  ] 62%', fontsize=7, ha='center')
ax.text(9.6, 4.5, 'L*=62 a*=11 b*=35', fontsize=7, ha='center')
ax.text(9.6, 3.9, '[トレンドグラフ]', fontsize=7, ha='center')
ax.text(9.6, 3.2, '経過: 03:45', fontsize=7, ha='center')
ax.text(9.6, 2.7, '[タッチ:停止]', fontsize=7, ha='center')

# REACHED screen
reach = Rectangle((11.7, 3.0), 2.0, 3.5, facecolor="white",
                  edgecolor="black", linewidth=2)
ax.add_patch(reach)
ax.text(12.7, 6.2, 'REACHED', fontsize=9, ha='center', fontweight='bold')
ax.text(12.7, 5.5, 'きつね色', fontsize=8, ha='center')
ax.text(12.7, 5.0, '到達！', fontsize=10, ha='center', fontweight='bold')
ax.text(12.7, 4.3, 'Time: 05:23', fontsize=7, ha='center')
ax.text(12.7, 3.8, 'ΔE: 4.8', fontsize=7, ha='center')
ax.text(12.7, 3.2, '♪ アラーム', fontsize=7, ha='center')

# Arrows
arrow_kw = dict(arrowstyle='->', lw=1.5, color='black')

# MENU -> CALIBRATE
ax.annotate('', xy=(4.5, 5.5), xytext=(3.3, 5.5), arrowprops=arrow_kw)
ax.text(3.9, 5.8, '長押し', fontsize=8, ha='center')

# CALIBRATE -> MONITORING
ax.annotate('', xy=(8.2, 4.5), xytext=(7.3, 4.5), arrowprops=arrow_kw)
ax.text(7.75, 4.8, 'タッチ', fontsize=8, ha='center')

# MONITORING -> REACHED
ax.annotate('', xy=(11.7, 4.8), xytext=(11.0, 4.8), arrowprops=arrow_kw)
ax.text(11.35, 5.1, 'ΔE<閾値', fontsize=7, ha='center')

# REACHED -> MENU (loop back)
ax.annotate('', xy=(1.9, 2.5), xytext=(12.7, 3.0),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='black',
                            connectionstyle="arc3,rad=0.4"))
ax.text(7, 1.8, 'タッチ → メニューに戻る', fontsize=8, ha='center')

# MONITORING -> MENU (stop)
ax.annotate('', xy=(1.9, 2.6), xytext=(9.6, 2.5),
            arrowprops=dict(arrowstyle='->', lw=1.2, color='black',
                            connectionstyle="arc3,rad=0.3",
                            linestyle='dashed'))
ax.text(5.5, 1.3, '停止 → メニューに戻る', fontsize=7, ha='center',
        style='italic')

save_fig(fig, "fig7_ui_transitions.png")

print("\n=== All 7 figures generated! ===")
print(f"Output directory: {OUT_DIR}")
