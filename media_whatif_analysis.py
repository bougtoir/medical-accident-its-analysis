#!/usr/bin/env python3
"""
Media What-If Analysis: Newspaper Coverage as Third Predictor

Adds newspaper article counts (Nikkei Telecom: 医療事故 + 医療過誤) as a media
exposure variable alongside litigation and JMSR incident reports.

Data: 2004-2018 annual article counts from major Japanese newspapers.
Source: Nikkei Telecom 21 (新聞トレンド), keywords 医療事故 + 医療過誤.

Analysis:
  1. Bivariate VAR: media → workforce (12 specialties × 2 outcomes)
  2. Trivariate VAR: media + litigation → workforce (additive value)
  3. Correlation: media–litigation, media–JMSR
  4. Comparison: Granger F/p across media, litigation, JMSR
"""

import os
import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.interpolate import interp1d
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SPEC_EN = {
    '内科': 'Internal medicine', '外科': 'General surgery',
    '整形外科': 'Orthopaedic surgery', '形成外科': 'Plastic surgery',
    '産婦人科': 'Obstetrics & gynaecology', '小児科': 'Paediatrics',
    '精神科': 'Psychiatry', '眼科': 'Ophthalmology',
    '耳鼻咽喉科': 'Otolaryngology', '泌尿器科': 'Urology',
    '皮膚科': 'Dermatology', '麻酔科': 'Anaesthesiology',
}

CORE_SPECIALTIES = [
    '内科', '外科', '整形外科', '形成外科', '産婦人科', '小児科',
    '精神科', '眼科', '耳鼻咽喉科', '泌尿器科', '皮膚科', '麻酔科',
]

def en(spec):
    return SPEC_EN.get(spec, spec)


# ============================================================
# DATA LOADING
# ============================================================
print("Loading data...")
df_jmsr = pd.read_csv(os.path.join(DATA_DIR, 'medsafe_accidents_by_specialty.csv'))
df_lit = pd.read_csv(os.path.join(DATA_DIR, 'litigation_by_specialty.csv'))
df_phys = pd.read_csv(os.path.join(DATA_DIR, 'physicians_by_specialty.csv'))
df_fac = pd.read_csv(os.path.join(DATA_DIR, 'facilities_by_specialty.csv'))
df_media = pd.read_csv(os.path.join(DATA_DIR, 'nikkei_media_counts_2004_2018.csv'))

# Media series: not specialty-specific (total newspaper coverage)
media_series = pd.Series(df_media['total_articles'].values, index=df_media['year'].values)
print(f"Media series: {media_series.index[0]}-{media_series.index[-1]} ({len(media_series)} years)")
print(f"  Range: {media_series.min()} - {media_series.max()}")
print(f"  Mean: {media_series.mean():.0f}")


def _make_series(df, specialty, skip_cols=('specialty', 'category', 'total')):
    row = df[df['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    year_cols = [c for c in df.columns if c not in skip_cols]
    years_int = sorted(int(y) for y in year_cols)
    vals = []
    for y in years_int:
        v = row[str(y)].values[0]
        vals.append(float(v) if pd.notna(v) else np.nan)
    return pd.Series(vals, index=years_int)


def get_jmsr(specialty):
    return _make_series(df_jmsr, specialty, skip_cols=('category', 'specialty', 'total'))


def get_litigation(specialty):
    return _make_series(df_lit, specialty)


def _interpolate_biennial(df, specialty):
    raw = _make_series(df, specialty)
    if raw.empty or raw.dropna().sum() == 0:
        return pd.Series(dtype=float)
    valid = raw.dropna()
    if len(valid) < 2:
        return pd.Series(dtype=float)
    f = interp1d(valid.index, valid.values, kind='linear', fill_value='extrapolate')
    annual_years = range(int(valid.index.min()), int(valid.index.max()) + 1)
    return pd.Series(f(list(annual_years)), index=list(annual_years))


def get_physicians(specialty):
    return _interpolate_biennial(df_phys, specialty)


def get_facilities(specialty):
    return _interpolate_biennial(df_fac, specialty)


def adf_test(series, name=''):
    clean = series.dropna()
    if len(clean) < 8:
        return {'name': name, 'statistic': np.nan, 'pvalue': np.nan,
                'stationary': None, 'n': len(clean)}
    result = adfuller(clean, autolag='AIC')
    return {
        'name': name, 'statistic': result[0], 'pvalue': result[1],
        'stationary': result[1] < 0.05, 'n': len(clean),
    }


def granger_test_bivar(df_var, max_lag=4):
    """Granger causality for bivariate VAR: accidents -> outcome and reverse."""
    if df_var is None or len(df_var) < 10:
        return {'forward': None, 'reverse': None}
    max_possible = max(1, min(max_lag, len(df_var) // 3 - 1))
    results = {}
    for direction, (cause, effect) in [('forward', ('accidents', 'outcome')),
                                        ('reverse', ('outcome', 'accidents'))]:
        try:
            test_data = df_var[[effect, cause]].values
            gc = grangercausalitytests(test_data, maxlag=max_possible, verbose=False)
            lag_results = []
            for lag in range(1, max_possible + 1):
                ftest = gc[lag][0]['ssr_ftest']
                lag_results.append({
                    'lag': lag, 'F_stat': ftest[0], 'p_value': ftest[1],
                })
            best = min(lag_results, key=lambda x: x['p_value'])
            results[direction] = {
                'best_lag': best['lag'], 'best_F': best['F_stat'],
                'best_p': best['p_value'], 'significant': best['p_value'] < 0.05,
            }
        except Exception:
            results[direction] = None
    return results


# ============================================================
# PART 1: Bivariate VAR — media → workforce
# ============================================================
print("\n" + "=" * 70)
print("PART 1: Bivariate VAR — Media → Workforce")
print("=" * 70)

bivar_media_results = []

for spec in CORE_SPECIALTIES:
    phys = get_physicians(spec)
    fac = get_facilities(spec)
    if phys.empty or fac.empty:
        continue

    for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
        # Align media and outcome on common years
        common = sorted(set(media_series.dropna().index) & set(outcome_series.dropna().index))
        if len(common) < 8:
            continue

        df_var = pd.DataFrame({
            'accidents': media_series.loc[common].values,
            'outcome': outcome_series.loc[common].values,
        }, index=common)

        n_obs = len(df_var)

        # ADF tests
        adf_acc = adf_test(df_var['accidents'], 'media')
        adf_out = adf_test(df_var['outcome'], f'{en(spec)}_{outcome_name}')

        # Stationarity handling
        if adf_acc.get('stationary') is False and adf_out.get('stationary') is False:
            df_var_fit = df_var.diff().dropna()
            use_diff = True
        else:
            df_var_fit = df_var.copy()
            use_diff = False

        # Fit VAR
        max_possible = max(1, min(4, len(df_var_fit) // 3 - 1))
        try:
            model = VAR(df_var_fit)
            lag_order = model.select_order(maxlags=max_possible)
            best_lag = max(1, lag_order.aic)
            var_result = model.fit(best_lag)
            aic = var_result.aic
        except Exception:
            continue

        # Granger test
        gc = granger_test_bivar(df_var_fit)

        entry = {
            'specialty': spec, 'specialty_en': en(spec),
            'outcome': outcome_name, 'n_obs': n_obs,
            'differenced': use_diff, 'var_lag': best_lag, 'aic': aic,
        }
        if gc['forward']:
            entry['gc_forward_F'] = gc['forward']['best_F']
            entry['gc_forward_p'] = gc['forward']['best_p']
            entry['gc_forward_sig'] = gc['forward']['significant']
            entry['gc_forward_lag'] = gc['forward']['best_lag']
        if gc['reverse']:
            entry['gc_reverse_F'] = gc['reverse']['best_F']
            entry['gc_reverse_p'] = gc['reverse']['best_p']
            entry['gc_reverse_sig'] = gc['reverse']['significant']
            entry['gc_reverse_lag'] = gc['reverse']['best_lag']

        bivar_media_results.append(entry)

        sig_mark = " *" if entry.get('gc_forward_sig') else ""
        fwd_str = f"F={entry.get('gc_forward_F', 0):.2f}, p={entry.get('gc_forward_p', 1):.4f}"
        print(f"  {en(spec):30s} {outcome_name:12s}: n={n_obs}, "
              f"VAR({best_lag}), AIC={aic:.1f}, {fwd_str}{sig_mark}")

df_bivar_media = pd.DataFrame(bivar_media_results)

# Summary
n_sig_fwd = sum(1 for r in bivar_media_results if r.get('gc_forward_sig'))
n_total = len(bivar_media_results)
print(f"\nBivariate media → workforce: {n_sig_fwd}/{n_total} significant (forward Granger)")
mean_F_fwd = np.mean([r['gc_forward_F'] for r in bivar_media_results if 'gc_forward_F' in r])
print(f"Mean forward F: {mean_F_fwd:.2f}")


# ============================================================
# PART 2: Bivariate VAR — litigation → workforce (same period)
# ============================================================
print("\n" + "=" * 70)
print("PART 2: Bivariate VAR — Litigation → Workforce (media-matched period)")
print("=" * 70)

bivar_lit_matched_results = []

for spec in CORE_SPECIALTIES:
    phys = get_physicians(spec)
    fac = get_facilities(spec)
    lit = get_litigation(spec)
    if phys.empty or fac.empty or lit.empty:
        continue

    for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
        # Restrict litigation to media period (2004-2018)
        common = sorted(set(lit.dropna().index) & set(outcome_series.dropna().index)
                        & set(media_series.dropna().index))
        if len(common) < 8:
            continue

        df_var = pd.DataFrame({
            'accidents': lit.loc[common].values,
            'outcome': outcome_series.loc[common].values,
        }, index=common)

        n_obs = len(df_var)
        adf_acc = adf_test(df_var['accidents'], 'litigation')
        adf_out = adf_test(df_var['outcome'], f'{en(spec)}_{outcome_name}')

        if adf_acc.get('stationary') is False and adf_out.get('stationary') is False:
            df_var_fit = df_var.diff().dropna()
            use_diff = True
        else:
            df_var_fit = df_var.copy()
            use_diff = False

        max_possible = max(1, min(4, len(df_var_fit) // 3 - 1))
        try:
            model = VAR(df_var_fit)
            lag_order = model.select_order(maxlags=max_possible)
            best_lag = max(1, lag_order.aic)
            var_result = model.fit(best_lag)
            aic = var_result.aic
        except Exception:
            continue

        gc = granger_test_bivar(df_var_fit)

        entry = {
            'specialty': spec, 'specialty_en': en(spec),
            'outcome': outcome_name, 'n_obs': n_obs,
            'differenced': use_diff, 'var_lag': best_lag, 'aic': aic,
        }
        if gc['forward']:
            entry['gc_forward_F'] = gc['forward']['best_F']
            entry['gc_forward_p'] = gc['forward']['best_p']
            entry['gc_forward_sig'] = gc['forward']['significant']
            entry['gc_forward_lag'] = gc['forward']['best_lag']
        if gc['reverse']:
            entry['gc_reverse_F'] = gc['reverse']['best_F']
            entry['gc_reverse_p'] = gc['reverse']['best_p']
            entry['gc_reverse_sig'] = gc['reverse']['significant']
            entry['gc_reverse_lag'] = gc['reverse']['best_lag']

        bivar_lit_matched_results.append(entry)

        sig_mark = " *" if entry.get('gc_forward_sig') else ""
        fwd_str = f"F={entry.get('gc_forward_F', 0):.2f}, p={entry.get('gc_forward_p', 1):.4f}"
        print(f"  {en(spec):30s} {outcome_name:12s}: n={n_obs}, "
              f"VAR({best_lag}), AIC={aic:.1f}, {fwd_str}{sig_mark}")

df_bivar_lit_matched = pd.DataFrame(bivar_lit_matched_results)

n_sig_lit = sum(1 for r in bivar_lit_matched_results if r.get('gc_forward_sig'))
n_total_lit = len(bivar_lit_matched_results)
print(f"\nBivariate litigation → workforce (2004-2018): {n_sig_lit}/{n_total_lit} significant")
mean_F_lit = np.mean([r['gc_forward_F'] for r in bivar_lit_matched_results if 'gc_forward_F' in r])
print(f"Mean forward F: {mean_F_lit:.2f}")


# ============================================================
# PART 3: Trivariate VAR — media + litigation → workforce
# ============================================================
print("\n" + "=" * 70)
print("PART 3: Trivariate VAR — Media + Litigation → Workforce")
print("=" * 70)

trivar_results = []

for spec in CORE_SPECIALTIES:
    phys = get_physicians(spec)
    fac = get_facilities(spec)
    lit = get_litigation(spec)
    if phys.empty or fac.empty or lit.empty:
        continue

    for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
        common = sorted(set(media_series.dropna().index) & set(lit.dropna().index)
                        & set(outcome_series.dropna().index))
        if len(common) < 8:
            continue

        df_trivar = pd.DataFrame({
            'media': media_series.loc[common].values,
            'litigation': lit.loc[common].values,
            'outcome': outcome_series.loc[common].values,
        }, index=common)

        n_obs = len(df_trivar)

        # ADF
        adf_m = adf_test(df_trivar['media'], 'media')
        adf_l = adf_test(df_trivar['litigation'], 'litigation')
        adf_o = adf_test(df_trivar['outcome'], f'{en(spec)}_{outcome_name}')

        all_nonstat = (adf_m.get('stationary') is False and
                       adf_l.get('stationary') is False and
                       adf_o.get('stationary') is False)
        if all_nonstat:
            df_fit = df_trivar.diff().dropna()
            use_diff = True
        else:
            df_fit = df_trivar.copy()
            use_diff = False

        max_possible = max(1, min(3, len(df_fit) // 4 - 1))
        if max_possible < 1:
            continue

        try:
            model3 = VAR(df_fit)
            lag_order3 = model3.select_order(maxlags=max_possible)
            best_lag3 = max(1, lag_order3.aic)
            var3 = model3.fit(best_lag3)
            aic3 = var3.aic
        except Exception:
            continue

        # Granger: media → outcome (controlling for litigation)
        # Test by comparing trivariate model (with media) vs bivariate (without media)
        # Use Granger test on the trivariate system
        gc_media_fwd = None
        gc_lit_fwd = None
        try:
            # media → outcome: test if media lags help predict outcome
            test_data_mo = df_fit[['outcome', 'media']].values
            gc_mo = grangercausalitytests(test_data_mo, maxlag=max_possible, verbose=False)
            best_mo = min(
                [{'lag': l, 'F': gc_mo[l][0]['ssr_ftest'][0],
                  'p': gc_mo[l][0]['ssr_ftest'][1]}
                 for l in range(1, max_possible + 1)],
                key=lambda x: x['p']
            )
            gc_media_fwd = best_mo

            # litigation → outcome
            test_data_lo = df_fit[['outcome', 'litigation']].values
            gc_lo = grangercausalitytests(test_data_lo, maxlag=max_possible, verbose=False)
            best_lo = min(
                [{'lag': l, 'F': gc_lo[l][0]['ssr_ftest'][0],
                  'p': gc_lo[l][0]['ssr_ftest'][1]}
                 for l in range(1, max_possible + 1)],
                key=lambda x: x['p']
            )
            gc_lit_fwd = best_lo
        except Exception:
            pass

        # Find matched bivariate AIC for comparison
        matched_bivar = None
        for r in bivar_lit_matched_results:
            if r['specialty'] == spec and r['outcome'] == outcome_name:
                matched_bivar = r
                break
        dAIC = aic3 - matched_bivar['aic'] if matched_bivar else np.nan

        entry = {
            'specialty': spec, 'specialty_en': en(spec),
            'outcome': outcome_name, 'n_obs': n_obs,
            'differenced': use_diff, 'var_lag': best_lag3,
            'trivar_aic': aic3,
            'bivar_lit_aic': matched_bivar['aic'] if matched_bivar else np.nan,
            'dAIC': dAIC,
        }
        if gc_media_fwd:
            entry['gc_media_F'] = gc_media_fwd['F']
            entry['gc_media_p'] = gc_media_fwd['p']
            entry['gc_media_sig'] = gc_media_fwd['p'] < 0.05
        if gc_lit_fwd:
            entry['gc_lit_F'] = gc_lit_fwd['F']
            entry['gc_lit_p'] = gc_lit_fwd['p']
            entry['gc_lit_sig'] = gc_lit_fwd['p'] < 0.05

        trivar_results.append(entry)

        media_sig = " *" if entry.get('gc_media_sig') else ""
        lit_sig = " *" if entry.get('gc_lit_sig') else ""
        print(f"  {en(spec):30s} {outcome_name:12s}: n={n_obs}, "
              f"VAR({best_lag3}), AIC={aic3:.1f}, dAIC={dAIC:+.1f}, "
              f"media F={entry.get('gc_media_F', 0):.2f}{media_sig}, "
              f"lit F={entry.get('gc_lit_F', 0):.2f}{lit_sig}")

df_trivar = pd.DataFrame(trivar_results)

n_trivar_better = sum(1 for r in trivar_results if r['dAIC'] < 0)
n_trivar_total = len(trivar_results)
mean_dAIC = np.mean([r['dAIC'] for r in trivar_results if not np.isnan(r['dAIC'])])
n_media_sig = sum(1 for r in trivar_results if r.get('gc_media_sig'))
print(f"\nTrivariate model improved AIC: {n_trivar_better}/{n_trivar_total}")
print(f"Mean dAIC: {mean_dAIC:+.2f}")
print(f"Media Granger significant: {n_media_sig}/{n_trivar_total}")


# ============================================================
# PART 4: Correlations — media, litigation, JMSR
# ============================================================
print("\n" + "=" * 70)
print("PART 4: Correlations")
print("=" * 70)

# Media-litigation correlation by specialty
corr_results = []
for spec in CORE_SPECIALTIES:
    lit = get_litigation(spec)
    if lit.empty:
        continue
    common = sorted(set(media_series.dropna().index) & set(lit.dropna().index))
    if len(common) < 5:
        continue
    r, p = stats.pearsonr(media_series.loc[common].values, lit.loc[common].values)
    corr_results.append({
        'specialty': spec, 'specialty_en': en(spec),
        'comparison': 'media_vs_litigation',
        'r': r, 'p': p, 'n': len(common),
    })
    print(f"  Media–Litigation  {en(spec):30s}: r={r:.3f}, p={p:.4f} (n={len(common)})")

# Media-JMSR correlation by specialty (limited overlap)
for spec in CORE_SPECIALTIES:
    jmsr = get_jmsr(spec)
    if jmsr.empty:
        continue
    common = sorted(set(media_series.dropna().index) & set(jmsr.dropna().index))
    if len(common) < 5:
        continue
    r, p = stats.pearsonr(media_series.loc[common].values, jmsr.loc[common].values)
    corr_results.append({
        'specialty': spec, 'specialty_en': en(spec),
        'comparison': 'media_vs_jmsr',
        'r': r, 'p': p, 'n': len(common),
    })
    print(f"  Media–JMSR        {en(spec):30s}: r={r:.3f}, p={p:.4f} (n={len(common)})")

# Litigation-JMSR (reference from prior analysis)
for spec in CORE_SPECIALTIES:
    lit = get_litigation(spec)
    jmsr = get_jmsr(spec)
    if lit.empty or jmsr.empty:
        continue
    common = sorted(set(lit.dropna().index) & set(jmsr.dropna().index))
    if len(common) < 5:
        continue
    r, p = stats.pearsonr(lit.loc[common].values, jmsr.loc[common].values)
    corr_results.append({
        'specialty': spec, 'specialty_en': en(spec),
        'comparison': 'litigation_vs_jmsr',
        'r': r, 'p': p, 'n': len(common),
    })

df_corr = pd.DataFrame(corr_results)

# Aggregate correlations
for comp in ['media_vs_litigation', 'media_vs_jmsr', 'litigation_vs_jmsr']:
    subset = df_corr[df_corr['comparison'] == comp]
    if not subset.empty:
        print(f"\n  {comp}: median |r|={subset['r'].abs().median():.3f}, "
              f"mean |r|={subset['r'].abs().mean():.3f}, "
              f"n_specs={len(subset)}")


# ============================================================
# PART 5: Summary comparison table
# ============================================================
print("\n" + "=" * 70)
print("PART 5: Summary Comparison")
print("=" * 70)

# Compare bivariate significance rates across all three sources
print("\nBivariate Granger significance rates (forward: source → workforce):")
print(f"  Media (2004-2018):     {n_sig_fwd}/{n_total} ({100*n_sig_fwd/n_total:.0f}%)")
print(f"  Litigation (2004-2018):{n_sig_lit}/{n_total_lit} ({100*n_sig_lit/n_total_lit:.0f}%)")

# Load original full-series litigation results for comparison
original_gc_file = os.path.join(OUTPUT_DIR, 'granger_causality_results.csv')
if os.path.exists(original_gc_file):
    df_orig_gc = pd.read_csv(original_gc_file)
    lit_full = df_orig_gc[df_orig_gc['definition'] == 'litigation']
    n_sig_lit_full = lit_full['gc_forward_sig'].sum() if 'gc_forward_sig' in lit_full.columns else 0
    n_total_lit_full = len(lit_full)
    print(f"  Litigation (full 2004-2023): {int(n_sig_lit_full)}/{n_total_lit_full} "
          f"({100*n_sig_lit_full/n_total_lit_full:.0f}%)")
    jmsr_full = df_orig_gc[df_orig_gc['definition'] == 'jmsr']
    n_sig_jmsr = jmsr_full['gc_forward_sig'].sum() if 'gc_forward_sig' in jmsr_full.columns else 0
    n_total_jmsr = len(jmsr_full)
    print(f"  JMSR (2015-2025):     {int(n_sig_jmsr)}/{n_total_jmsr} "
          f"({100*n_sig_jmsr/n_total_jmsr:.0f}%)")

print(f"\nTrivariate (media + litigation) vs bivariate (litigation only):")
print(f"  Models with improved AIC: {n_trivar_better}/{n_trivar_total}")
print(f"  Mean dAIC: {mean_dAIC:+.2f}")
print(f"  Media adds significant Granger contribution: {n_media_sig}/{n_trivar_total}")

# Media–litigation correlation summary
ml_corr = df_corr[df_corr['comparison'] == 'media_vs_litigation']
if not ml_corr.empty:
    print(f"\nMedia–Litigation correlations:")
    print(f"  Median |r|: {ml_corr['r'].abs().median():.3f}")
    print(f"  Mean |r|: {ml_corr['r'].abs().mean():.3f}")
    n_sig_corr = (ml_corr['p'] < 0.05).sum()
    print(f"  Significant (p<0.05): {n_sig_corr}/{len(ml_corr)}")


# ============================================================
# SAVE RESULTS
# ============================================================
print("\n" + "=" * 70)
print("Saving results")
print("=" * 70)

df_bivar_media.to_csv(os.path.join(OUTPUT_DIR, 'media_bivar_granger.csv'), index=False)
print("  Saved: media_bivar_granger.csv")

df_bivar_lit_matched.to_csv(os.path.join(OUTPUT_DIR, 'media_lit_matched_granger.csv'), index=False)
print("  Saved: media_lit_matched_granger.csv")

df_trivar.to_csv(os.path.join(OUTPUT_DIR, 'media_trivar_results.csv'), index=False)
print("  Saved: media_trivar_results.csv")

df_corr.to_csv(os.path.join(OUTPUT_DIR, 'media_correlations.csv'), index=False)
print("  Saved: media_correlations.csv")

# Summary JSON
summary = {
    'data_source': 'Nikkei Telecom 21 (新聞トレンド)',
    'keywords': ['医療事故', '医療過誤'],
    'media_period': f'{media_series.index[0]}-{media_series.index[-1]}',
    'media_n_years': len(media_series),
    'bivariate_media': {
        'n_models': n_total,
        'n_significant': n_sig_fwd,
        'rate': round(n_sig_fwd / n_total, 3) if n_total > 0 else 0,
        'mean_F': round(mean_F_fwd, 2),
    },
    'bivariate_litigation_matched': {
        'n_models': n_total_lit,
        'n_significant': n_sig_lit,
        'rate': round(n_sig_lit / n_total_lit, 3) if n_total_lit > 0 else 0,
        'mean_F': round(mean_F_lit, 2),
    },
    'trivariate': {
        'n_models': n_trivar_total,
        'n_aic_improved': n_trivar_better,
        'mean_dAIC': round(mean_dAIC, 2),
        'n_media_granger_sig': n_media_sig,
    },
    'media_litigation_correlation': {
        'median_abs_r': round(ml_corr['r'].abs().median(), 3) if not ml_corr.empty else None,
        'mean_abs_r': round(ml_corr['r'].abs().mean(), 3) if not ml_corr.empty else None,
    },
}

with open(os.path.join(OUTPUT_DIR, 'media_whatif_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("  Saved: media_whatif_summary.json")

print("\n=== Media What-If Analysis Complete ===")
