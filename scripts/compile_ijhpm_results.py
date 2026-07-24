#!/usr/bin/env python3
"""Compile reproducible results for IJHPM manuscript from raw data.

Reads:
- data/scr_n_kubun.csv (FY2022 standardised claim ratios, shift-jis)
- data/univ_hospital_mapping_v2.json (university hospital -> SMA mapping)

Writes:
- output/ijhpm_results.json

All numeric values reported in the IJHPM manuscript are derived from this
script; the manuscript generator (create_ijhpm_en.py) reads this JSON and does
not embed estimated values as literals.
"""

import csv
import io
import json
import math
import os
import statistics
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLM

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(REPO_ROOT, 'data')
OUTPUT_DIR = os.path.join(REPO_ROOT, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def cohens_d(vals_a, vals_b):
    """Pooled SD Cohen's d."""
    a, b = np.asarray(vals_a), np.asarray(vals_b)
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float('nan')
    sd1 = np.std(a, ddof=1)
    sd2 = np.std(b, ddof=1)
    pooled = math.sqrt(((sd1**2 * (n1 - 1)) + (sd2**2 * (n2 - 1))) / (n1 + n2 - 2))
    if pooled == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled)


def fmt_p(p):
    """Format p-value for manuscript."""
    if np.isnan(p):
        return 'NA'
    if p < 0.001:
        return '<0.001'
    return f'{p:.3f}'


def fmt_num(x, decimals=1):
    if np.isnan(x):
        return 'NA'
    return f'{x:.{decimals}f}'


def confidence_interval_mean(arr, conf=0.95):
    """Return (lower, upper) for mean using t-distribution."""
    a = np.asarray(arr)
    n = len(a)
    if n < 2:
        return (float('nan'), float('nan'))
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t.ppf((1 + conf) / 2., n - 1)
    return (m - h, m + h)


# ============================================================
# 1. LOAD DATA
# ============================================================
scr_path = os.path.join(DATA_DIR, 'scr_n_kubun.csv')
with open(scr_path, 'rb') as f:
    raw = f.read().decode('shift_jis', errors='replace')
reader = list(csv.reader(io.StringIO(raw)))

pref_nums = [x.strip() for x in reader[0][4:]]
pref_names = [x.strip() for x in reader[1][4:]]
area_codes = [x.strip() for x in reader[2][4:]]
area_names = [x.strip() for x in reader[3][4:]]
n_areas = len(area_codes)

univ_path = os.path.join(DATA_DIR, 'univ_hospital_mapping_v2.json')
with open(univ_path) as f:
    univ_mapping = json.load(f)
univ_area_codes = set(univ_mapping.keys())

area_info = {}
for i, ac in enumerate(area_codes):
    area_info[ac] = {
        'pref_num': pref_nums[i],
        'pref_name': pref_names[i],
        'area_name': area_names[i],
        'has_univ': 1 if ac in univ_area_codes else 0,
    }

# Target procedure codes (inpatient/outpatient flag = 1)
target_codes = {
    ('L', '8', '1'):  'L008',
    ('L', '2', '1'):  'L002',
    ('L', '3', '1'):  'L003',
    ('L', '4', '1'):  'L004',
    ('L', '9', '1'):  'L009',
    ('L', '100', '1'): 'L100',
}

code_labels = {
    'L008': 'General anaesthesia (closed-circuit)',
    'L002': 'Epidural anaesthesia',
    'L003': 'Continuous epidural infusion',
    'L004': 'Spinal anaesthesia',
    'L009': 'Anaesthesia management fee I',
    'L100': 'Nerve block, inpatient',
}

# Parse values per code
data_by_code = {code: {} for code in target_codes.values()}
for row in reader[4:]:
    if len(row) < 5:
        continue
    chapter = row[0].strip()
    code_num = row[1].strip()
    inout = row[3].strip()
    key = (chapter, code_num, inout)
    if key not in target_codes:
        continue
    code = target_codes[key]
    for i, ac in enumerate(area_codes):
        idx = i + 4
        if idx >= len(row):
            continue
        v = row[idx].strip()
        if v:
            try:
                data_by_code[code][ac] = float(v)
            except ValueError:
                pass

# Group areas by prefecture
pref_areas = defaultdict(list)
for ac in area_codes:
    pref_areas[area_info[ac]['pref_num']].append(ac)


def descriptive_stats(values):
    a = np.array(list(values))
    n = len(a)
    if n == 0:
        return None
    mn = float(np.min(a))
    mx = float(np.max(a))
    return {
        'n': n,
        'mean': float(np.mean(a)),
        'sd': float(np.std(a, ddof=1)),
        'median': float(np.median(a)),
        'q1': float(np.percentile(a, 25)),
        'q3': float(np.percentile(a, 75)),
        'min': mn,
        'max': mx,
        'range_ratio': float(mx / mn) if mn > 0 else float('nan'),
        'cv': float(np.std(a, ddof=1) / np.mean(a) * 100) if np.mean(a) != 0 else 0,
        'iqr': float(np.percentile(a, 75) - np.percentile(a, 25)),
    }


def group_stats(values, group_set):
    a = np.array([v for ac, v in values.items() if ac in group_set and ac in values])
    return a


results = {
    'metadata': {
        'data_source': 'data/scr_n_kubun.csv',
        'univ_mapping': 'data/univ_hospital_mapping_v2.json',
        'fiscal_year': 2022,
        'n_areas': n_areas,
        'n_prefectures': len(set(pref_nums)),
        'n_univ_areas': int(sum(1 for ac in area_codes if ac in univ_area_codes)),
        'n_nonuniv_areas': int(sum(1 for ac in area_codes if ac not in univ_area_codes)),
        'n_univ_areas_pct': round(100 * sum(1 for ac in area_codes if ac in univ_area_codes) / n_areas, 1),
    },
    'codes': {},
    'combined': {},
    'correlations': {},
    'empirical_bayes': {},
    'variance_decomposition': {},
    'audit_sensitivity': {},
    'outliers': {},
}

# ============================================================
# 2. PER-CODE DESCRIPTIVE AND COMPARATIVE STATISTICS
# ============================================================
analysis_codes = ['L008', 'L004', 'L002', 'L003', 'L009', 'L100']

for code in analysis_codes:
    values = data_by_code[code]
    desc = descriptive_stats(values.values())
    univ_vals = [v for ac, v in values.items() if ac in univ_area_codes]
    non_vals = [v for ac, v in values.items() if ac not in univ_area_codes]

    d_overall = cohens_d(univ_vals, non_vals)
    t_stat, t_p = stats.ttest_ind(univ_vals, non_vals, equal_var=False)
    try:
        u_stat, u_p = stats.mannwhitneyu(univ_vals, non_vals, alternative='two-sided')
    except ValueError:
        u_p = float('nan')

    # Within-prefecture comparison
    within_diffs = []
    for pref, areas in pref_areas.items():
        uv = [values[ac] for ac in areas if ac in univ_area_codes and ac in values]
        nv = [values[ac] for ac in areas if ac not in univ_area_codes and ac in values]
        if uv and nv:
            within_diffs.append(statistics.mean(uv) - statistics.mean(nv))
    if len(within_diffs) >= 2:
        paired_t, paired_p = stats.ttest_1samp(within_diffs, 0)
        n_pos = sum(1 for x in within_diffs if x > 0)
    else:
        paired_t, paired_p, n_pos = float('nan'), float('nan'), 0

    results['codes'][code] = {
        'label': code_labels[code],
        'overall': desc,
        'university': descriptive_stats(univ_vals),
        'non_university': descriptive_stats(non_vals),
        'cohens_d_overall': float(d_overall),
        'welch_t': float(t_stat) if not np.isnan(t_stat) else 0,
        'welch_p': float(t_p) if not np.isnan(t_p) else 1,
        'mannwhitney_u_p': float(u_p) if not np.isnan(u_p) else 1,
        'within_prefecture': {
            'mean_diff': float(np.mean(within_diffs)) if within_diffs else float('nan'),
            'sd_diff': float(np.std(within_diffs, ddof=1)) if len(within_diffs) >= 2 else float('nan'),
            't': float(paired_t) if not np.isnan(paired_t) else 0,
            'p': float(paired_p) if not np.isnan(paired_p) else 1,
            'n_positive': n_pos,
            'n_total': len(within_diffs),
        },
    }

# ============================================================
# 3. MULTILEVEL MODELS
# ============================================================
for code in analysis_codes:
    values = data_by_code[code]
    records = []
    for ac, v in values.items():
        if ac not in area_info:
            continue
        records.append({
            'scr': v,
            'has_univ': area_info[ac]['has_univ'],
            'pref_num': area_info[ac]['pref_num'],
        })
    df = pd.DataFrame(records)
    if len(df) < 30 or df['has_univ'].nunique() < 2:
        continue

    # Null model (random intercept only)
    try:
        m0 = MixedLM.from_formula('scr ~ 1', groups='pref_num', data=df).fit(reml=True)
        var_pref = float(m0.cov_re.iloc[0, 0]) if hasattr(m0.cov_re, 'iloc') else float(m0.cov_re)
        var_resid = float(m0.scale)
        icc = var_pref / (var_pref + var_resid) if (var_pref + var_resid) > 0 else 0
    except Exception as e:
        var_pref = var_resid = icc = float('nan')

    # University effect model
    try:
        m1 = MixedLM.from_formula('scr ~ has_univ', groups='pref_num', data=df).fit(reml=True)
        coef = float(m1.fe_params.get('has_univ', np.nan))
        pval = float(m1.pvalues.get('has_univ', np.nan))
        ci = m1.conf_int().loc['has_univ'] if 'has_univ' in m1.conf_int().index else [np.nan, np.nan]
        ci_low, ci_high = float(ci.iloc[0]), float(ci.iloc[1])
        var_pref1 = float(m1.cov_re.iloc[0, 0]) if hasattr(m1.cov_re, 'iloc') else float(m1.cov_re)
        var_resid1 = float(m1.scale)
        r2 = 1 - (var_pref1 + var_resid1) / (var_pref + var_resid) if (var_pref + var_resid) > 0 else 0
    except Exception as e:
        coef = pval = ci_low = ci_high = r2 = float('nan')

    results['codes'][code]['multilevel'] = {
        'n': len(df),
        'icc_null': float(icc),
        'coef_univ': float(coef) if not np.isnan(coef) else 0,
        'ci_low': float(ci_low) if not np.isnan(ci_low) else 0,
        'ci_high': float(ci_high) if not np.isnan(ci_high) else 0,
        'p': float(pval) if not np.isnan(pval) else 1,
        'marginal_r2': float(r2) if not np.isnan(r2) else 0,
    }

# ============================================================
# 4. COMBINED L008 + L003 MEASURE
# ============================================================
combined = {}
for ac in area_codes:
    if ac in data_by_code['L008'] and ac in data_by_code['L003']:
        combined[ac] = (data_by_code['L008'][ac] + data_by_code['L003'][ac]) / 2

c_univ = [v for ac, v in combined.items() if ac in univ_area_codes]
c_non = [v for ac, v in combined.items() if ac not in univ_area_codes]
results['combined']['L008_L003'] = {
    'n': len(combined),
    'overall': descriptive_stats(combined.values()),
    'university': descriptive_stats(c_univ),
    'non_university': descriptive_stats(c_non),
    'cohens_d': float(cohens_d(c_univ, c_non)),
    'fold_ratio': float(descriptive_stats(c_univ)['mean'] / descriptive_stats(c_non)['mean'])
        if descriptive_stats(c_univ) and descriptive_stats(c_non) and descriptive_stats(c_non)['mean'] else float('nan'),
}

# L008 + L004 combined (general + spinal, alternative audit-insensitive combination)
combined_l008_l004 = {}
for ac in area_codes:
    if ac in data_by_code['L008'] and ac in data_by_code['L004']:
        combined_l008_l004[ac] = (data_by_code['L008'][ac] + data_by_code['L004'][ac]) / 2

c04_u = [v for ac, v in combined_l008_l004.items() if ac in univ_area_codes]
c04_n = [v for ac, v in combined_l008_l004.items() if ac not in univ_area_codes]
results['combined']['L008_L004'] = {
    'n': len(combined_l008_l004),
    'overall': descriptive_stats(combined_l008_l004.values()),
    'university': descriptive_stats(c04_u),
    'non_university': descriptive_stats(c04_n),
    'cohens_d': float(cohens_d(c04_u, c04_n)),
    'fold_ratio': float(descriptive_stats(c04_u)['mean'] / descriptive_stats(c04_n)['mean'])
        if descriptive_stats(c04_u) and descriptive_stats(c04_n) and descriptive_stats(c04_n)['mean'] else float('nan'),
}

# ============================================================
# 5. CROSS-CODE CORRELATIONS
# ============================================================
def pairwise_corr(code_a, code_b):
    vals_a, vals_b = [], []
    for ac in area_codes:
        if ac in data_by_code[code_a] and ac in data_by_code[code_b]:
            vals_a.append(data_by_code[code_a][ac])
            vals_b.append(data_by_code[code_b][ac])
    if len(vals_a) < 3:
        return {'r': float('nan'), 'p': float('nan'), 'n': len(vals_a)}
    r, p = stats.pearsonr(vals_a, vals_b)
    return {'r': float(r), 'p': float(p), 'n': len(vals_a)}

results['correlations']['L008_L002'] = pairwise_corr('L008', 'L002')
results['correlations']['L008_L004'] = pairwise_corr('L008', 'L004')
results['correlations']['L008_L003'] = pairwise_corr('L008', 'L003')

# ============================================================
# 6. EMPIRICAL BAYES SHRINKAGE
# ============================================================
for code in ['L008', 'L002', 'L004', 'L003']:
    values = data_by_code[code]
    all_v = [(ac, values[ac]) for ac in area_codes if ac in values]
    if not all_v:
        continue
    df_eb = pd.DataFrame({'scr': [v for _, v in all_v],
                          'pref': [area_info[ac]['pref_num'] for ac, _ in all_v]})
    try:
        null_m = smf.mixedlm('scr ~ 1', df_eb, groups=df_eb['pref']).fit(reml=True)
        sigma2 = float(null_m.scale)
    except Exception:
        continue

    pref_groups = defaultdict(list)
    for ac, v in all_v:
        pref_groups[area_info[ac]['pref_num']].append((ac, v))

    eb_values = {}
    for pref, items in pref_groups.items():
        if len(items) < 2:
            for ac, v in items:
                eb_values[ac] = v
            continue
        pref_mean = np.mean([v for _, v in items])
        pref_var_obs = np.var([v for _, v in items], ddof=0)
        tau2 = max(pref_var_obs - sigma2, 1e-6)
        shrink_factor = tau2 / (tau2 + sigma2)
        for ac, v in items:
            eb_values[ac] = shrink_factor * v + (1 - shrink_factor) * pref_mean

    raw_u = [values[ac] for ac in values if ac in univ_area_codes]
    raw_n = [values[ac] for ac in values if ac not in univ_area_codes]
    eb_u = [eb_values[ac] for ac in eb_values if ac in univ_area_codes]
    eb_n = [eb_values[ac] for ac in eb_values if ac not in univ_area_codes]

    if len(raw_u) > 2 and len(raw_n) > 2 and len(eb_u) > 2 and len(eb_n) > 2:
        raw_d = cohens_d(raw_u, raw_n)
        eb_d = cohens_d(eb_u, eb_n)
        attenuation = (1 - eb_d / raw_d) * 100 if raw_d != 0 else 0
        results['empirical_bayes'][code] = {
            'raw_cohens_d': float(raw_d),
            'shrunk_cohens_d': float(eb_d),
            'attenuation_pct': float(attenuation),
        }

# ============================================================
# 7. VARIANCE DECOMPOSITION
# ============================================================
for code in ['L008', 'L002', 'L004', 'L003']:
    values = data_by_code[code]
    all_vals = [values[ac] for ac in area_codes if ac in values]
    if not all_vals:
        continue
    grand_mean = np.mean(all_vals)
    ss_total = sum((v - grand_mean) ** 2 for v in all_vals)
    ss_between_pref = 0
    ss_univ_effect = 0
    ss_residual = 0

    for pref, areas in pref_areas.items():
        pref_vals = [values[ac] for ac in areas if ac in values]
        if not pref_vals:
            continue
        pref_mean = np.mean(pref_vals)
        ss_between_pref += len(pref_vals) * (pref_mean - grand_mean) ** 2

        uv = [values[ac] for ac in areas if ac in univ_area_codes and ac in values]
        nv = [values[ac] for ac in areas if ac not in univ_area_codes and ac in values]
        if uv and nv:
            u_mean = np.mean(uv)
            n_mean = np.mean(nv)
            ss_univ_effect += len(uv) * (u_mean - pref_mean) ** 2 + len(nv) * (n_mean - pref_mean) ** 2
            ss_residual += sum((values[ac] - u_mean) ** 2 for ac in areas if ac in univ_area_codes and ac in values)
            ss_residual += sum((values[ac] - n_mean) ** 2 for ac in areas if ac not in univ_area_codes and ac in values)
        else:
            ss_residual += sum((v - pref_mean) ** 2 for v in pref_vals)

    if ss_total > 0:
        pct_p = 100 * ss_between_pref / ss_total
        pct_u = 100 * ss_univ_effect / ss_total
        pct_r = 100 * ss_residual / ss_total
        pct_w = 100 * (ss_total - ss_between_pref) / ss_total
        results['variance_decomposition'][code] = {
            'between_prefecture_pct': float(pct_p),
            'university_effect_pct': float(pct_u),
            'residual_pct': float(pct_r),
            'within_prefecture_pct': float(pct_w),
            'univ_explains_within_pct': float(100 * pct_u / pct_w) if pct_w > 0 else 0,
        }

# ============================================================
# 8. AUDIT SENSITIVITY ESTIMATE
# ============================================================
# Published prefectural audit rates range from 0.07% to 0.28%.
# The maximum audit-rate difference (percentage points) is used as a bound on
# the ratio shift attributable to differential auditing. See ref 6.
max_audit_diff_pp = 0.21  # percentage points (1 pp = 1 SCR unit since national mean = 100)

results['audit_sensitivity'] = {
    'max_audit_rate_difference_pp': max_audit_diff_pp,
    'max_ratio_shift_approx': float(max_audit_diff_pp),
    'source': 'Cabinet Office (2023), see manuscript reference 6',
}

# Express the bound as a percentage of each code's IQR and mean
for code in ['L008', 'L002', 'L003', 'L004']:
    vals = list(data_by_code[code].values())
    iqr = np.percentile(vals, 75) - np.percentile(vals, 25)
    mean = np.mean(vals)
    results['audit_sensitivity'][code] = {
        'iqr': float(iqr),
        'percent_of_iqr': float(100 * max_audit_diff_pp / iqr) if iqr else 0,
        'percent_of_mean': float(100 * max_audit_diff_pp / mean) if mean else 0,
    }

# ============================================================
# 9. OUTLIERS
# ============================================================
l008_values = list(data_by_code['L008'].values())
l008_mean = np.mean(l008_values)
l008_sd = np.std(l008_values, ddof=1)
outliers = []
for ac, v in data_by_code['L008'].items():
    if abs(v - l008_mean) > 3 * l008_sd:
        outliers.append({
            'area_code': ac,
            'pref_name': area_info[ac]['pref_name'],
            'area_name': area_info[ac]['area_name'],
            'scr': float(v),
        })
results['outliers']['L008'] = outliers

# ============================================================
# 10. SAVE
# ============================================================
out_path = os.path.join(OUTPUT_DIR, 'ijhpm_results.json')
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Saved: {out_path}")
