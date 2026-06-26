#!/usr/bin/env python3
"""Create Figure 4: Demand-supply mismatch scatter plot.

Shows CSLC symptom prevalence (demand) vs NDB acute analgesic prescribing (supply)
for each prefecture, coloured by region. The absence of correlation demonstrates
Wennberg unwarranted variation.
"""

import os
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy import stats

# Use Noto Sans CJK JP for Japanese figures
_ja_font = None
for f in fm.fontManager.ttflist:
    if f.name == 'Noto Sans CJK JP':
        _ja_font = f.fname
        break

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Load merged data
rows = []
with open(os.path.join(OUTPUT_DIR, 'cslc_merged.csv'), 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for k in r:
            if k not in ('pref_name', 'region', 'is_tohoku', 'pref_code'):
                try:
                    r[k] = float(r[k])
                except (ValueError, TypeError):
                    pass
        r['pref_code'] = int(r['pref_code'])
        rows.append(r)

with open(os.path.join(OUTPUT_DIR, 'cslc_analysis.json'), 'r') as f:
    cslc = json.load(f)

REGION_EN = {
    '北海道': 'Hokkaido', '東北': 'Tohoku', '関東': 'Kanto',
    '北陸・甲信越': 'Hokuriku-Koshinetsu', '東海': 'Tokai', '近畿': 'Kinki',
    '中国': 'Chugoku', '四国': 'Shikoku', '九州・沖縄': 'Kyushu-Okinawa',
}
REGION_ORDER = ['Hokkaido', 'Tohoku', 'Kanto', 'Hokuriku-Koshinetsu',
                'Tokai', 'Kinki', 'Chugoku', 'Shikoku', 'Kyushu-Okinawa']
REGION_COLORS = {
    'Hokkaido': '#e41a1c', 'Tohoku': '#ff7f00', 'Kanto': '#4daf4a',
    'Hokuriku-Koshinetsu': '#377eb8', 'Tokai': '#984ea3', 'Kinki': '#a65628',
    'Chugoku': '#f781bf', 'Shikoku': '#999999', 'Kyushu-Okinawa': '#e6ab02',
}
# Distinct markers for B&W print compatibility (colour preserved for screen)
REGION_MARKERS = {
    'Hokkaido': 'o', 'Tohoku': 's', 'Kanto': '^',
    'Hokuriku-Koshinetsu': 'D', 'Tokai': 'v', 'Kinki': 'p',
    'Chugoku': 'h', 'Shikoku': 'X', 'Kyushu-Okinawa': '*',
}

PREF_EN = {
    1: 'Hokkaido', 2: 'Aomori', 3: 'Iwate', 4: 'Miyagi', 5: 'Akita',
    6: 'Yamagata', 7: 'Fukushima', 8: 'Ibaraki', 9: 'Tochigi', 10: 'Gunma',
    11: 'Saitama', 12: 'Chiba', 13: 'Tokyo', 14: 'Kanagawa', 15: 'Niigata',
    16: 'Toyama', 17: 'Ishikawa', 18: 'Fukui', 19: 'Yamanashi', 20: 'Nagano',
    21: 'Gifu', 22: 'Shizuoka', 23: 'Aichi', 24: 'Mie', 25: 'Shiga',
    26: 'Kyoto', 27: 'Osaka', 28: 'Hyogo', 29: 'Nara', 30: 'Wakayama',
    31: 'Tottori', 32: 'Shimane', 33: 'Okayama', 34: 'Hiroshima', 35: 'Yamaguchi',
    36: 'Tokushima', 37: 'Kagawa', 38: 'Ehime', 39: 'Kochi', 40: 'Fukuoka',
    41: 'Saga', 42: 'Nagasaki', 43: 'Kumamoto', 44: 'Oita', 45: 'Miyazaki',
    46: 'Kagoshima', 47: 'Okinawa',
}

symptom = np.array([r['cslc_symptom_rate'] for r in rows])
acute = np.array([r['acute_analgesic_per_surgery'] for r in rows])

fig, ax = plt.subplots(1, 1, figsize=(10, 7))

# Plot each region with grayscale markers
for reg_en in REGION_ORDER:
    mask = [REGION_EN.get(r['region'], '') == reg_en for r in rows]
    x = symptom[mask]
    y = acute[mask]
    ax.scatter(x, y, marker=REGION_MARKERS[reg_en], c=REGION_COLORS[reg_en],
               label=reg_en, s=70, edgecolors='black', linewidths=0.6, zorder=3)

# Annotate selected outlier prefectures
outlier_prefs = [1, 13, 46, 21, 43, 28]  # Hokkaido, Tokyo, Kagoshima, Gifu, Kumamoto, Hyogo
for r in rows:
    if r['pref_code'] in outlier_prefs:
        ax.annotate(PREF_EN[r['pref_code']],
                    (r['cslc_symptom_rate'], r['acute_analgesic_per_surgery']),
                    fontsize=7, ha='left', va='bottom',
                    xytext=(4, 4), textcoords='offset points')

# Regression line
slope, intercept, r_val, p_val, se = stats.linregress(symptom, acute)
x_line = np.linspace(symptom.min() - 5, symptom.max() + 5, 100)
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, '--', color='black', linewidth=1, alpha=0.5)

# Correlation annotation
corr_r = cslc['correlations']['symptom_vs_acute']['pearson_r']
corr_p = cslc['correlations']['symptom_vs_acute']['pearson_p']
ax.text(0.03, 0.97, f'r = {corr_r:.3f}, P = {corr_p:.3f}',
        transform=ax.transAxes, fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

ax.set_xlabel('CSLC symptom prevalence rate (per 1,000 population)', fontsize=11)
ax.set_ylabel('Acute analgesic prescribing per surgery', fontsize=11)
ax.set_title('Demand\u2013supply dissociation: symptom burden vs analgesic prescribing',
             fontsize=12, fontweight='bold')
handles = [plt.Line2D([0], [0], marker=REGION_MARKERS[r], color='w',
           markerfacecolor=REGION_COLORS[r], markeredgecolor='black',
           markeredgewidth=0.6, markersize=8, label=r) for r in REGION_ORDER]
ax.legend(handles=handles, loc='lower right', fontsize=8, ncol=2, framealpha=0.9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
out_path = os.path.join(OUTPUT_DIR, 'fig_cslc_demand_supply_en.png')
fig.savefig(out_path, dpi=300, bbox_inches='tight')
print(f'Saved: {out_path}')
plt.close()

# ============================================================
# Japanese version
# ============================================================
PREF_JA = {
    1: '北海道', 2: '青森', 3: '岩手', 4: '宮城', 5: '秋田',
    6: '山形', 7: '福島', 8: '茨城', 9: '栃木', 10: '群馬',
    11: '埼玉', 12: '千葉', 13: '東京', 14: '神奈川', 15: '新潟',
    16: '富山', 17: '石川', 18: '福井', 19: '山梨', 20: '長野',
    21: '岐阜', 22: '静岡', 23: '愛知', 24: '三重', 25: '滋賀',
    26: '京都', 27: '大阪', 28: '兵庫', 29: '奈良', 30: '和歌山',
    31: '鳥取', 32: '島根', 33: '岡山', 34: '広島', 35: '山口',
    36: '徳島', 37: '香川', 38: '愛媛', 39: '高知', 40: '福岡',
    41: '佐賀', 42: '長崎', 43: '熊本', 44: '大分', 45: '宮崎',
    46: '鹿児島', 47: '沖縄',
}
REGION_JA = {
    'Hokkaido': '北海道', 'Tohoku': '東北', 'Kanto': '関東',
    'Hokuriku-Koshinetsu': '北陸・甲信越', 'Tokai': '東海', 'Kinki': '近畿',
    'Chugoku': '中国', 'Shikoku': '四国', 'Kyushu-Okinawa': '九州・沖縄',
}

ja_prop = fm.FontProperties(fname=_ja_font) if _ja_font else None
fig, ax = plt.subplots(1, 1, figsize=(10, 7))
for reg_en in REGION_ORDER:
    mask = [REGION_EN.get(r['region'], '') == reg_en for r in rows]
    x = symptom[mask]
    y = acute[mask]
    ax.scatter(x, y, marker=REGION_MARKERS[reg_en], c=REGION_COLORS[reg_en],
               label=REGION_JA[reg_en], s=70, edgecolors='black', linewidths=0.6, zorder=3)

for r in rows:
    if r['pref_code'] in outlier_prefs:
        ax.annotate(PREF_JA[r['pref_code']],
                    (r['cslc_symptom_rate'], r['acute_analgesic_per_surgery']),
                    fontsize=7, ha='left', va='bottom',
                    xytext=(4, 4), textcoords='offset points',
                    fontproperties=ja_prop)

ax.plot(x_line, y_line, '--', color='black', linewidth=1, alpha=0.5)
ax.text(0.03, 0.97, f'r = {corr_r:.3f}, P = {corr_p:.3f}',
        transform=ax.transAxes, fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))
ax.set_xlabel('国民生活基礎調査 有訴者率（人口千対）', fontsize=11, fontproperties=ja_prop)
ax.set_ylabel('急性鎮痛薬処方数/手術件数', fontsize=11, fontproperties=ja_prop)
ax.set_title('需要\u2013供給の乖離：症状有訴率と鎮痛薬処方', fontsize=12, fontweight='bold', fontproperties=ja_prop)
handles = [plt.Line2D([0], [0], marker=REGION_MARKERS[r], color='w',
           markerfacecolor=REGION_COLORS[r], markeredgecolor='black',
           markeredgewidth=0.6, markersize=8, label=REGION_JA[r]) for r in REGION_ORDER]
ax.legend(handles=handles, loc='lower right', fontsize=8, ncol=2, framealpha=0.9, prop=ja_prop)
ax.grid(True, alpha=0.3)
plt.tight_layout()
out_path_ja = os.path.join(OUTPUT_DIR, 'fig_cslc_demand_supply_ja.png')
fig.savefig(out_path_ja, dpi=300, bbox_inches='tight')
print(f'Saved: {out_path_ja}')
plt.close()
