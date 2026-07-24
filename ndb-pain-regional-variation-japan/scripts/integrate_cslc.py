#!/usr/bin/env python3
"""Integrate CSLC (Comprehensive Survey of Living Conditions) symptom
prevalence data with NDB prescription data for demand-supply mismatch analysis.

Data source: MHLW 国民生活基礎調査 令和4年 (2022), Table 135
  有訴者率（人口千対）by prefecture (e-Stat ID: 0002041077)

This script:
1. Merges CSLC symptom prevalence with existing NDB prescription data
2. Computes demand-supply mismatch indices
3. Runs correlation / regression analyses
4. Saves results to output/cslc_analysis.json and output/cslc_merged.csv
"""

import os
import json
import csv
import numpy as np
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# ============================================================
# CSLC Data: 有訴者率（人口千対）, 2022, by prefecture
# Source: e-Stat Table 0002041077 (CSLC 2022, Table 135)
# ============================================================
CSLC_DATA = {
    # pref_code: symptom_rate (per 1000 population)
    1: 279.4,   # 北海道
    2: 282.3,   # 青森県
    3: 298.0,   # 岩手県
    4: 291.4,   # 宮城県
    5: 292.8,   # 秋田県
    6: 287.6,   # 山形県
    7: 281.2,   # 福島県
    8: 276.4,   # 茨城県
    9: 266.9,   # 栃木県
    10: 272.2,  # 群馬県
    11: 246.4,  # 埼玉県
    12: 284.4,  # 千葉県
    13: 244.0,  # 東京都
    14: 250.6,  # 神奈川県
    15: 287.2,  # 新潟県
    16: 292.6,  # 富山県
    17: 288.7,  # 石川県
    18: 289.2,  # 福井県
    19: 262.3,  # 山梨県
    20: 289.3,  # 長野県
    21: 311.2,  # 岐阜県
    22: 278.2,  # 静岡県
    23: 249.7,  # 愛知県
    24: 302.5,  # 三重県
    25: 314.3,  # 滋賀県
    26: 306.7,  # 京都府
    27: 270.7,  # 大阪府
    28: 314.9,  # 兵庫県
    29: 303.2,  # 奈良県
    30: 293.5,  # 和歌山県
    31: 291.3,  # 鳥取県
    32: 286.6,  # 島根県
    33: 297.4,  # 岡山県
    34: 302.4,  # 広島県
    35: 313.4,  # 山口県
    36: 304.1,  # 徳島県
    37: 293.8,  # 香川県
    38: 294.8,  # 愛媛県
    39: 301.3,  # 高知県
    40: 287.7,  # 福岡県
    41: 298.7,  # 佐賀県
    42: 294.2,  # 長崎県
    43: 310.5,  # 熊本県
    44: 293.4,  # 大分県
    45: 294.8,  # 宮崎県
    46: 265.4,  # 鹿児島県
    47: 272.2,  # 沖縄県
}

NATIONAL_RATE = 276.5  # per 1000

# ============================================================
# Load existing NDB data
# ============================================================
rows = []
with open(os.path.join(OUTPUT_DIR, 'cpsp_integrated_results.csv'), 'r',
          encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for k in r:
            if k not in ('pref_name', 'region', 'is_tohoku', 'pref_code'):
                try:
                    r[k] = float(r[k])
                except (ValueError, TypeError):
                    pass
        r['pref_code'] = int(r['pref_code'])
        r['is_tohoku'] = int(float(r['is_tohoku']))
        rows.append(r)

# ============================================================
# Merge CSLC symptom rate
# ============================================================
for r in rows:
    pc = r['pref_code']
    r['cslc_symptom_rate'] = CSLC_DATA.get(pc, np.nan)

# ============================================================
# Compute demand-supply mismatch indices
# ============================================================
# Standardise both axes to z-scores for comparability
symptom_rates = np.array([r['cslc_symptom_rate'] for r in rows])
acute_rates = np.array([r['acute_analgesic_per_surgery'] for r in rows])
neuro_rates = np.array([r['neuropathic_per_capita'] for r in rows])

symptom_z = (symptom_rates - np.mean(symptom_rates)) / np.std(symptom_rates, ddof=1)
acute_z = (acute_rates - np.mean(acute_rates)) / np.std(acute_rates, ddof=1)
neuro_z = (neuro_rates - np.mean(neuro_rates)) / np.std(neuro_rates, ddof=1)

for i, r in enumerate(rows):
    r['symptom_z'] = float(symptom_z[i])
    r['acute_z'] = float(acute_z[i])
    r['neuro_z'] = float(neuro_z[i])
    # Mismatch = supply z - demand z
    # Positive = over-supply relative to symptom burden
    # Negative = under-supply relative to symptom burden
    r['acute_mismatch'] = float(acute_z[i] - symptom_z[i])
    r['neuro_mismatch'] = float(neuro_z[i] - symptom_z[i])

# ============================================================
# Correlations: CSLC symptom rate vs NDB prescription
# ============================================================
# 1. Symptom rate vs acute analgesic prescribing
corr_symptom_acute = stats.pearsonr(symptom_rates, acute_rates)
corr_symptom_acute_spearman = stats.spearmanr(symptom_rates, acute_rates)

# 2. Symptom rate vs neuropathic pain prescribing (per capita)
corr_symptom_neuro = stats.pearsonr(symptom_rates, neuro_rates)
corr_symptom_neuro_spearman = stats.spearmanr(symptom_rates, neuro_rates)

# 3. Symptom rate vs adjusted CPSP index (confounder-adjusted)
adj_cpsp = np.array([r['adjusted_cpsp_index'] for r in rows])
corr_symptom_adjcpsp = stats.pearsonr(symptom_rates, adj_cpsp)

# ============================================================
# Regression: neuropathic prescribing ~ symptom rate + confounders
# ============================================================
diabetes = np.array([r['diabetes_per_surgery'] for r in rows])
herpes = np.array([r['herpes_per_surgery'] for r in rows])
antidep = np.array([r['antidep_per_surgery'] for r in rows])
anxiolytic = np.array([r['anxiolytic_per_surgery'] for r in rows])

# Model A: neuropathic ~ symptom_rate (unadjusted)
X_a = np.column_stack([np.ones(len(rows)), symptom_rates])
beta_a = np.linalg.lstsq(X_a, neuro_rates, rcond=None)[0]
pred_a = X_a @ beta_a
ss_res_a = np.sum((neuro_rates - pred_a) ** 2)
ss_tot = np.sum((neuro_rates - np.mean(neuro_rates)) ** 2)
R2_a = 1 - ss_res_a / ss_tot

# Model B: neuropathic ~ symptom_rate + diabetes + herpes + antidep + anxiolytic
X_b = np.column_stack([np.ones(len(rows)), symptom_rates,
                        diabetes, herpes, antidep, anxiolytic])
beta_b = np.linalg.lstsq(X_b, neuro_rates, rcond=None)[0]
pred_b = X_b @ beta_b
ss_res_b = np.sum((neuro_rates - pred_b) ** 2)
R2_b = 1 - ss_res_b / ss_tot
n = len(rows)
p_b = X_b.shape[1] - 1
R2_adj_b = 1 - (1 - R2_b) * (n - 1) / (n - p_b - 1)

# Mismatch summary statistics
acute_mm = np.array([r['acute_mismatch'] for r in rows])
neuro_mm = np.array([r['neuro_mismatch'] for r in rows])

# Regions for summary
REGION_EN = {
    '北海道': 'Hokkaido', '東北': 'Tohoku', '関東': 'Kanto',
    '北陸・甲信越': 'Hokuriku-Koshinetsu', '東海': 'Tokai', '近畿': 'Kinki',
    '中国': 'Chugoku', '四国': 'Shikoku', '九州・沖縄': 'Kyushu-Okinawa',
}

# Regional mismatch means
from collections import defaultdict
region_acute_mm = defaultdict(list)
region_neuro_mm = defaultdict(list)
for r in rows:
    region_acute_mm[r['region']].append(r['acute_mismatch'])
    region_neuro_mm[r['region']].append(r['neuro_mismatch'])

region_summary = {}
for reg_jp in region_acute_mm:
    region_summary[REGION_EN.get(reg_jp, reg_jp)] = {
        'acute_mismatch_mean': float(np.mean(region_acute_mm[reg_jp])),
        'neuro_mismatch_mean': float(np.mean(region_neuro_mm[reg_jp])),
    }

# ============================================================
# Save results
# ============================================================
results = {
    'data_source': 'CSLC 2022 (e-Stat Table 0002041077)',
    'national_symptom_rate': NATIONAL_RATE,
    'symptom_rate_stats': {
        'mean': float(np.mean(symptom_rates)),
        'sd': float(np.std(symptom_rates, ddof=1)),
        'min': float(np.min(symptom_rates)),
        'max': float(np.max(symptom_rates)),
        'range_ratio': float(np.max(symptom_rates) / np.min(symptom_rates)),
        'min_pref': [r['pref_name'] for r in rows
                     if r['cslc_symptom_rate'] == np.min(symptom_rates)][0],
        'max_pref': [r['pref_name'] for r in rows
                     if r['cslc_symptom_rate'] == np.max(symptom_rates)][0],
    },
    'correlations': {
        'symptom_vs_acute': {
            'pearson_r': float(corr_symptom_acute[0]),
            'pearson_p': float(corr_symptom_acute[1]),
            'spearman_rho': float(corr_symptom_acute_spearman.statistic),
            'spearman_p': float(corr_symptom_acute_spearman.pvalue),
        },
        'symptom_vs_neuro_percapita': {
            'pearson_r': float(corr_symptom_neuro[0]),
            'pearson_p': float(corr_symptom_neuro[1]),
            'spearman_rho': float(corr_symptom_neuro_spearman.statistic),
            'spearman_p': float(corr_symptom_neuro_spearman.pvalue),
        },
        'symptom_vs_adjusted_cpsp': {
            'pearson_r': float(corr_symptom_adjcpsp[0]),
            'pearson_p': float(corr_symptom_adjcpsp[1]),
        },
    },
    'regression': {
        'model_a_symptom_only': {
            'R2': float(R2_a),
            'symptom_coef': float(beta_a[1]),
        },
        'model_b_symptom_plus_confounders': {
            'R2': float(R2_b),
            'R2_adj': float(R2_adj_b),
            'symptom_coef': float(beta_b[1]),
        },
    },
    'mismatch': {
        'acute_mismatch_range': [float(np.min(acute_mm)), float(np.max(acute_mm))],
        'neuro_mismatch_range': [float(np.min(neuro_mm)), float(np.max(neuro_mm))],
        'region_summary': region_summary,
    },
}

out_json = os.path.join(OUTPUT_DIR, 'cslc_analysis.json')
with open(out_json, 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f'Saved: {out_json}')

# Save merged CSV
fieldnames = list(rows[0].keys())
out_csv = os.path.join(OUTPUT_DIR, 'cslc_merged.csv')
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
print(f'Saved: {out_csv}')

# Print summary
print(f'\n=== CSLC Integration Summary ===')
print(f'Symptom rate range: {np.min(symptom_rates):.1f}–{np.max(symptom_rates):.1f} '
      f'({np.max(symptom_rates)/np.min(symptom_rates):.2f}-fold)')
print(f'\nCorrelations (symptom rate vs):')
print(f'  Acute analgesic: r={corr_symptom_acute[0]:.3f}, P={corr_symptom_acute[1]:.4f}')
print(f'  Neuro per capita: r={corr_symptom_neuro[0]:.3f}, P={corr_symptom_neuro[1]:.4f}')
print(f'  Adjusted CPSP:   r={corr_symptom_adjcpsp[0]:.3f}, P={corr_symptom_adjcpsp[1]:.4f}')
print(f'\nRegression (neuro ~ symptom):')
print(f'  Model A (symptom only): R²={R2_a:.3f}')
print(f'  Model B (+confounders): R²={R2_b:.3f}, R²adj={R2_adj_b:.3f}')
