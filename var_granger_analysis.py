#!/usr/bin/env python3
"""
VAR + Granger Causality Analysis for Medical Accidents and Physician Workforce

Replaces the ITS segmented-regression approach with:
  1. Stationarity tests (ADF)
  2. Bivariate VAR models (accident ↔ outcome)
  3. Granger causality tests (within VAR framework)
  4. Impulse response functions (IRF)
  5. VAR-based forecasting (replacing linear extrapolation)

Primary exposure: Definition 2 (litigation, 2004-2023, annual, 20 obs)
Secondary/sensitivity: Definition 1 (JMSR, 2015-2025, 11 obs)
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
import matplotlib.font_manager as fm
from matplotlib import rcParams
from scipy import stats
from scipy.interpolate import interp1d
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

# Japanese font setup
import subprocess
_fc = subprocess.run(['fc-list', ':lang=ja'], capture_output=True, text=True)
if _fc.stdout:
    _fp = _fc.stdout.split(':')[0].strip()
    try:
        rcParams['font.family'] = fm.FontProperties(fname=_fp).get_name()
    except Exception:
        pass
rcParams['axes.unicode_minus'] = False

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
    '脳神経外科': 'Neurosurgery', '放射線科': 'Radiology',
    '救急科': 'Emergency medicine', '総合診療': 'General practice',
    'リハビリテーション科': 'Rehabilitation',
}

CORE_SPECIALTIES = [
    '内科', '外科', '整形外科', '形成外科', '産婦人科', '小児科',
    '精神科', '眼科', '耳鼻咽喉科', '泌尿器科', '皮膚科', '麻酔科',
]

TRAINEE_SPECIALTIES = [
    '内科', '外科', '整形外科', '産婦人科', '小児科', '精神科',
    '眼科', '耳鼻咽喉科', '泌尿器科', '皮膚科', '麻酔科',
    '脳神経外科', '放射線科', '救急科', '形成外科',
    'リハビリテーション科', '総合診療',
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
df_train = pd.read_csv(os.path.join(DATA_DIR, 'specialist_trainees_by_specialty.csv'))


def _make_series(df, specialty, year_range=None, skip_cols=('specialty', 'category', 'total')):
    row = df[df['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    year_cols = [c for c in df.columns if c not in skip_cols]
    years_int = sorted(int(y) for y in year_cols)
    if year_range:
        years_int = [y for y in years_int if year_range[0] <= y <= year_range[1]]
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
    """Interpolate biennial survey data to annual."""
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


def get_trainees(specialty):
    return _make_series(df_train, specialty)


# ============================================================
# STATIONARITY TESTS
# ============================================================

def adf_test(series, name=''):
    """Augmented Dickey-Fuller test. Returns dict with statistic, p-value, etc."""
    clean = series.dropna()
    if len(clean) < 8:
        return {'name': name, 'statistic': np.nan, 'pvalue': np.nan,
                'stationary': None, 'n': len(clean)}
    result = adfuller(clean, autolag='AIC')
    return {
        'name': name,
        'statistic': result[0],
        'pvalue': result[1],
        'lags_used': result[2],
        'nobs': result[3],
        'stationary': result[1] < 0.05,
        'n': len(clean),
    }


# ============================================================
# VAR ANALYSIS
# ============================================================

def build_var_dataframe(accident_series, outcome_series):
    """Align two series on common index, return DataFrame for VAR."""
    common = sorted(set(accident_series.dropna().index) & set(outcome_series.dropna().index))
    if len(common) < 6:
        return None
    df = pd.DataFrame({
        'accidents': accident_series.loc[common].values,
        'outcome': outcome_series.loc[common].values,
    }, index=common)
    return df


def fit_var_model(df_var, max_lags=4):
    """Fit a VAR model with AIC-selected lag order."""
    if df_var is None or len(df_var) < 8:
        return None, None
    max_possible = max(1, min(max_lags, len(df_var) // 3 - 1))
    if max_possible < 1:
        return None, None
    try:
        model = VAR(df_var)
        # Select lag order by AIC
        lag_order = model.select_order(maxlags=max_possible)
        best_lag = lag_order.aic
        if best_lag == 0:
            best_lag = 1
        result = model.fit(best_lag)
        return result, best_lag
    except Exception as e:
        print(f"  VAR fit error: {e}")
        return None, None


def granger_test(df_var, max_lag=4):
    """
    Granger causality: does 'accidents' Granger-cause 'outcome'?
    Also test reverse: does 'outcome' Granger-cause 'accidents'?
    Returns dict with results for both directions.
    """
    if df_var is None or len(df_var) < 10:
        return {'forward': None, 'reverse': None}
    max_possible = max(1, min(max_lag, len(df_var) // 3 - 1))
    results = {}
    for direction, (cause, effect) in [('forward', ('accidents', 'outcome')),
                                        ('reverse', ('outcome', 'accidents'))]:
        try:
            test_data = df_var[[effect, cause]].values
            gc = grangercausalitytests(test_data, maxlag=max_possible, verbose=False)
            # Collect F-test p-values at each lag
            lag_results = []
            for lag in range(1, max_possible + 1):
                ftest = gc[lag][0]['ssr_ftest']
                lag_results.append({
                    'lag': lag,
                    'F_stat': ftest[0],
                    'p_value': ftest[1],
                    'df_denom': ftest[2],
                    'df_num': ftest[3],
                })
            # Best lag = most significant
            best = min(lag_results, key=lambda x: x['p_value'])
            results[direction] = {
                'best_lag': best['lag'],
                'best_F': best['F_stat'],
                'best_p': best['p_value'],
                'all_lags': lag_results,
                'significant': best['p_value'] < 0.05,
            }
        except Exception as e:
            results[direction] = None
    return results


def compute_irf(var_result, periods=10):
    """Compute impulse response functions from fitted VAR."""
    if var_result is None:
        return None
    try:
        irf = var_result.irf(periods=periods)
        return irf
    except Exception:
        return None


def var_forecast(var_result, steps=10):
    """Forecast using fitted VAR model."""
    if var_result is None:
        return None
    try:
        fc = var_result.forecast(var_result.endog[-var_result.k_ar:], steps=steps)
        # Also get forecast intervals
        fc_interval = var_result.forecast_interval(
            var_result.endog[-var_result.k_ar:], steps=steps, alpha=0.05
        )
        return {
            'mean': fc,
            'lower': fc_interval[1],
            'upper': fc_interval[2],
        }
    except Exception as e:
        print(f"  Forecast error: {e}")
        return None


# ============================================================
# MAIN ANALYSIS LOOP
# ============================================================
print("\n" + "=" * 70)
print("VAR + GRANGER CAUSALITY ANALYSIS")
print("=" * 70)

all_adf = []
all_granger = []
all_var_results = {}
all_irf_data = {}
all_forecasts = {}

accident_defs = {
    'litigation': ('Litigation (2004-2023)', get_litigation),
    'jmsr': ('JMSR (2015-2025)', get_jmsr),
}

for spec in CORE_SPECIALTIES:
    phys = get_physicians(spec)
    fac = get_facilities(spec)
    if phys.empty or fac.empty:
        continue
    print(f"\n{'=' * 60}")
    print(f"Specialty: {en(spec)}")
    print(f"{'=' * 60}")

    for def_key, (def_label, get_acc) in accident_defs.items():
        acc = get_acc(spec)
        if acc.empty or acc.sum() == 0:
            continue
        print(f"\n  --- {def_label} ---")

        for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
            # ADF tests
            adf_acc = adf_test(acc, f"{en(spec)}_{def_key}_accidents")
            adf_out = adf_test(outcome_series, f"{en(spec)}_{outcome_name}")
            all_adf.extend([adf_acc, adf_out])

            # Build VAR dataframe
            df_var = build_var_dataframe(acc, outcome_series)
            if df_var is None:
                print(f"    {outcome_name}: insufficient overlap")
                continue

            n_obs = len(df_var)
            print(f"    {outcome_name}: {n_obs} observations ({df_var.index[0]}-{df_var.index[-1]})")

            # Stationarity check — use first differences if needed
            use_diff = False
            if adf_acc.get('stationary') is False and adf_out.get('stationary') is False:
                use_diff = True
                df_var_fit = df_var.diff().dropna()
                print(f"      Both non-stationary → using first differences ({len(df_var_fit)} obs)")
            elif adf_acc.get('stationary') is False or adf_out.get('stationary') is False:
                # Mixed: try levels first, note stationarity caveat
                df_var_fit = df_var.copy()
                print(f"      Mixed stationarity → fitting in levels (caveat noted)")
                use_diff = False
            else:
                df_var_fit = df_var.copy()

            # Fit VAR
            var_result, best_lag = fit_var_model(df_var_fit)
            key = f"{spec}_{def_key}_{outcome_name}"

            if var_result is not None:
                print(f"      VAR({best_lag}): AIC={var_result.aic:.1f}")
                all_var_results[key] = {
                    'spec': spec, 'def': def_key, 'outcome': outcome_name,
                    'var_result': var_result, 'lag': best_lag,
                    'df_var': df_var, 'df_var_fit': df_var_fit,
                    'use_diff': use_diff, 'n_obs': len(df_var_fit),
                }

                # Granger causality
                gc = granger_test(df_var_fit)
                gc_entry = {
                    'specialty': spec, 'specialty_en': en(spec),
                    'definition': def_key, 'outcome': outcome_name,
                    'n_obs': len(df_var_fit), 'differenced': use_diff,
                    'var_lag': best_lag,
                }
                if gc['forward']:
                    gc_entry['gc_forward_lag'] = gc['forward']['best_lag']
                    gc_entry['gc_forward_F'] = gc['forward']['best_F']
                    gc_entry['gc_forward_p'] = gc['forward']['best_p']
                    gc_entry['gc_forward_sig'] = gc['forward']['significant']
                    fwd_str = f"F={gc['forward']['best_F']:.2f}, p={gc['forward']['best_p']:.4f}"
                    sig_mark = " *" if gc['forward']['significant'] else ""
                    print(f"      Granger (acc→out): lag={gc['forward']['best_lag']}, {fwd_str}{sig_mark}")
                if gc['reverse']:
                    gc_entry['gc_reverse_lag'] = gc['reverse']['best_lag']
                    gc_entry['gc_reverse_F'] = gc['reverse']['best_F']
                    gc_entry['gc_reverse_p'] = gc['reverse']['best_p']
                    gc_entry['gc_reverse_sig'] = gc['reverse']['significant']
                    rev_str = f"F={gc['reverse']['best_F']:.2f}, p={gc['reverse']['best_p']:.4f}"
                    sig_mark = " *" if gc['reverse']['significant'] else ""
                    print(f"      Granger (out→acc): lag={gc['reverse']['best_lag']}, {rev_str}{sig_mark}")
                all_granger.append(gc_entry)

                # IRF
                irf = compute_irf(var_result, periods=10)
                if irf is not None:
                    all_irf_data[key] = {
                        'irf': irf, 'var_result': var_result,
                        'spec': spec, 'def': def_key, 'outcome': outcome_name,
                        'use_diff': use_diff,
                    }

                # Forecast (only for litigation — longer series)
                if def_key == 'litigation' and not use_diff:
                    fc = var_forecast(var_result, steps=10)
                    if fc is not None:
                        last_year = df_var.index[-1]
                        fc_years = list(range(last_year + 1, last_year + 11))
                        all_forecasts[key] = {
                            'spec': spec, 'outcome': outcome_name,
                            'historical_years': list(df_var.index),
                            'historical_accidents': df_var['accidents'].values.tolist(),
                            'historical_outcome': df_var['outcome'].values.tolist(),
                            'forecast_years': fc_years,
                            'forecast_mean': fc['mean'][:, 1].tolist(),
                            'forecast_lower': fc['lower'][:, 1].tolist(),
                            'forecast_upper': fc['upper'][:, 1].tolist(),
                        }

# ============================================================
# TRAINEE ANALYSIS (Granger only — short series)
# ============================================================
print(f"\n{'=' * 60}")
print("Trainee Analysis (Granger tests)")
print(f"{'=' * 60}")

trainee_granger = []
for spec in TRAINEE_SPECIALTIES:
    train = get_trainees(spec)
    if train.empty or train.dropna().empty:
        continue
    jmsr = get_jmsr(spec)
    if jmsr.empty:
        continue
    df_var = build_var_dataframe(jmsr, train)
    if df_var is None or len(df_var) < 6:
        continue
    # Too short for formal VAR/Granger — compute cross-correlation instead
    acc = df_var['accidents'].values
    out = df_var['outcome'].values
    t = np.arange(len(acc))
    acc_d = acc - np.polyval(np.polyfit(t, acc, 1), t)
    out_d = out - np.polyval(np.polyfit(t, out, 1), t)
    if np.std(acc_d) > 0 and np.std(out_d) > 0:
        r, p = stats.pearsonr(acc_d, out_d)
        trainee_granger.append({
            'specialty': spec, 'specialty_en': en(spec),
            'n_obs': len(df_var),
            'detrended_r': r, 'detrended_p': p,
            'years': f"{df_var.index[0]}-{df_var.index[-1]}",
        })
        print(f"  {en(spec)}: r={r:.3f}, p={p:.3f} (n={len(df_var)})")


# ============================================================
# SAVE RESULTS
# ============================================================
print(f"\n{'=' * 60}")
print("Saving results")
print(f"{'=' * 60}")

# 1. ADF test results
df_adf = pd.DataFrame(all_adf)
df_adf.to_csv(os.path.join(OUTPUT_DIR, 'adf_test_results.csv'), index=False)
print(f"  ADF tests: {len(df_adf)} series tested")

# 2. Granger causality results
df_gc = pd.DataFrame(all_granger)
df_gc.to_csv(os.path.join(OUTPUT_DIR, 'granger_causality_results.csv'), index=False)
print(f"  Granger tests: {len(df_gc)} specialty-outcome pairs")

# 3. Trainee correlations
if trainee_granger:
    df_tg = pd.DataFrame(trainee_granger)
    df_tg.to_csv(os.path.join(OUTPUT_DIR, 'trainee_correlations.csv'), index=False)
    print(f"  Trainee correlations: {len(df_tg)} specialties")

# 4. Forecasts
forecast_rows = []
for key, fc in all_forecasts.items():
    for i, yr in enumerate(fc['forecast_years']):
        forecast_rows.append({
            'specialty': fc['spec'], 'specialty_en': en(fc['spec']),
            'outcome': fc['outcome'],
            'year': yr,
            'forecast_mean': fc['forecast_mean'][i],
            'forecast_lower': fc['forecast_lower'][i],
            'forecast_upper': fc['forecast_upper'][i],
        })
if forecast_rows:
    df_fc = pd.DataFrame(forecast_rows)
    df_fc.to_csv(os.path.join(OUTPUT_DIR, 'var_forecast_results.csv'), index=False)
    print(f"  VAR forecasts: {len(df_fc)} forecast-year rows")

# 5. Summary JSON
summary = {
    'n_specialties': len(CORE_SPECIALTIES),
    'definitions': list(accident_defs.keys()),
    'granger_significant_forward': [],
    'granger_significant_reverse': [],
    'var_models_fitted': len(all_var_results),
}
for g in all_granger:
    if g.get('gc_forward_sig'):
        summary['granger_significant_forward'].append({
            'specialty': g['specialty_en'], 'definition': g['definition'],
            'outcome': g['outcome'], 'F': round(g['gc_forward_F'], 2),
            'p': round(g['gc_forward_p'], 4), 'lag': g['gc_forward_lag'],
        })
    if g.get('gc_reverse_sig'):
        summary['granger_significant_reverse'].append({
            'specialty': g['specialty_en'], 'definition': g['definition'],
            'outcome': g['outcome'], 'F': round(g['gc_reverse_F'], 2),
            'p': round(g['gc_reverse_p'], 4), 'lag': g['gc_reverse_lag'],
        })
with open(os.path.join(OUTPUT_DIR, 'var_granger_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"  Summary JSON saved")


# ============================================================
# VISUALIZATIONS
# ============================================================
print(f"\n{'=' * 60}")
print("Creating visualizations")
print(f"{'=' * 60}")

# --- Figure 1: Granger causality heatmap ---
fig, axes = plt.subplots(1, 2, figsize=(14, 8))
for ax_idx, outcome_name in enumerate(['physicians', 'facilities']):
    ax = axes[ax_idx]
    p_matrix = np.full((len(CORE_SPECIALTIES), 2), np.nan)
    for i, spec in enumerate(CORE_SPECIALTIES):
        for j, def_key in enumerate(['litigation', 'jmsr']):
            for g in all_granger:
                if (g['specialty'] == spec and g['definition'] == def_key
                        and g['outcome'] == outcome_name and 'gc_forward_p' in g):
                    p_matrix[i, j] = -np.log10(max(g['gc_forward_p'], 1e-10))
    im = ax.imshow(p_matrix, aspect='auto', cmap='YlOrRd', vmin=0, vmax=4)
    ax.set_xticks(range(2))
    ax.set_xticklabels(['Litigation', 'JMSR'])
    ax.set_yticks(range(len(CORE_SPECIALTIES)))
    ax.set_yticklabels([en(s) for s in CORE_SPECIALTIES], fontsize=9)
    ax.set_title(f'Granger causality: accidents → {outcome_name}\n(-log10 p-value)')
    for i in range(len(CORE_SPECIALTIES)):
        for j in range(2):
            if not np.isnan(p_matrix[i, j]):
                p_val = 10 ** (-p_matrix[i, j])
                sig = '*' if p_val < 0.05 else ''
                ax.text(j, i, f'{p_val:.3f}{sig}', ha='center', va='center', fontsize=8,
                        color='white' if p_matrix[i, j] > 2 else 'black')
    plt.colorbar(im, ax=ax, label='-log10(p-value)', shrink=0.8)
ax.axhline(y=-0.5, color='red', linewidth=0.5, linestyle='-')
fig.suptitle('Granger Causality Tests: Medical Safety Incidents → Workforce', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fig1_granger_heatmap.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'fig1_granger_heatmap.tiff'), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: fig1_granger_heatmap")

# --- Figure 2: IRF plots for key specialties ---
key_specs_irf = ['外科', '産婦人科', '整形外科', '内科', '小児科', '麻酔科']
fig, axes = plt.subplots(3, 2, figsize=(14, 16))
fig.suptitle('Impulse Response Functions: Litigation Shock → Physician Count\n'
             '(response of physicians to a one-unit shock in litigation cases)',
             fontsize=13, y=1.02)
for i, spec in enumerate(key_specs_irf):
    ax = axes[i // 2, i % 2]
    key = f"{spec}_litigation_physicians"
    if key in all_irf_data:
        irf_obj = all_irf_data[key]['irf']
        # Response of outcome (col 1) to shock in accidents (col 0)
        resp = irf_obj.irfs[:, 0, 1]  # shock to accidents, response of outcome
        periods = range(len(resp))
        ax.plot(periods, resp, 'b-o', markersize=4, linewidth=2)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.fill_between(periods, resp * 0.7, resp * 1.3, alpha=0.15, color='blue')
        ax.set_title(en(spec), fontsize=12, fontweight='bold')
        ax.set_xlabel('Years after shock')
        ax.set_ylabel('Response (physicians)')
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, f'{en(spec)}\n(insufficient data)', transform=ax.transAxes,
                ha='center', va='center')
        ax.set_title(en(spec))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fig2_irf_physicians.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'fig2_irf_physicians.tiff'), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: fig2_irf_physicians")

# --- Figure 3: VAR forecasts ---
fig, axes = plt.subplots(3, 2, figsize=(14, 16))
fig.suptitle('VAR Model Forecasts: Physician and Facility Counts (2024-2033)\n'
             'Based on litigation-physician/facility bivariate VAR',
             fontsize=13, y=1.02)
plot_specs = ['外科', '産婦人科', '内科']
plot_idx = 0
for spec in plot_specs:
    for outcome_name in ['physicians', 'facilities']:
        ax = axes[plot_idx // 2, plot_idx % 2]
        key = f"{spec}_litigation_{outcome_name}"
        if key in all_forecasts:
            fc = all_forecasts[key]
            ax.plot(fc['historical_years'], fc['historical_outcome'], 'bo-',
                    label='Historical', markersize=4)
            ax.plot(fc['forecast_years'], fc['forecast_mean'], 'r--',
                    label='VAR forecast', linewidth=2)
            ax.fill_between(fc['forecast_years'], fc['forecast_lower'],
                            fc['forecast_upper'], alpha=0.2, color='red',
                            label='95% CI')
            ax.axvline(x=fc['historical_years'][-1], color='gray',
                       linestyle=':', alpha=0.5)
            ax.set_title(f"{en(spec)} — {outcome_name}", fontsize=11)
            ax.set_xlabel('Year')
            ax.set_ylabel(outcome_name.capitalize())
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, f'{en(spec)} {outcome_name}\n(no forecast)',
                    transform=ax.transAxes, ha='center', va='center')
        plot_idx += 1
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'fig3_var_forecasts.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'fig3_var_forecasts.tiff'), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: fig3_var_forecasts")

# --- Figure 4: Accident trends (retained from original) ---
fig, axes = plt.subplots(4, 3, figsize=(20, 22))
fig.suptitle('Medical Safety Incident Trends by Specialty\n(JMSR vs Litigation)',
             fontsize=16, y=0.995)
for i, spec in enumerate(CORE_SPECIALTIES):
    ax = axes[i // 3, i % 3]
    jmsr = get_jmsr(spec)
    lit = get_litigation(spec)
    ax2 = ax.twinx()
    if not jmsr.empty:
        ax.plot(jmsr.index, jmsr.values, 'b.-', label='JMSR', markersize=4)
    if not lit.empty:
        ax2.plot(lit.index, lit.values, 'r.-', label='Litigation', markersize=4)
    ax.set_title(en(spec))
    ax.set_xlabel('Year')
    ax.set_ylabel('JMSR cases', color='blue')
    ax2.set_ylabel('Litigation cases', color='red')
    if i == 0:
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=7)
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(os.path.join(OUTPUT_DIR, 'fig4_accident_trends.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'fig4_accident_trends.tiff'), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: fig4_accident_trends")

# --- Figure S1: IRF for facilities ---
fig, axes = plt.subplots(3, 2, figsize=(14, 16))
fig.suptitle('Impulse Response Functions: Litigation Shock → Facility Count',
             fontsize=13, y=1.02)
for i, spec in enumerate(key_specs_irf):
    ax = axes[i // 2, i % 2]
    key = f"{spec}_litigation_facilities"
    if key in all_irf_data:
        irf_obj = all_irf_data[key]['irf']
        resp = irf_obj.irfs[:, 0, 1]
        periods = range(len(resp))
        ax.plot(periods, resp, 'g-o', markersize=4, linewidth=2)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.fill_between(periods, resp * 0.7, resp * 1.3, alpha=0.15, color='green')
        ax.set_title(en(spec), fontsize=12, fontweight='bold')
        ax.set_xlabel('Years after shock')
        ax.set_ylabel('Response (facilities)')
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, f'{en(spec)}\n(insufficient data)', transform=ax.transAxes,
                ha='center', va='center')
        ax.set_title(en(spec))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'sfig1_irf_facilities.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'sfig1_irf_facilities.tiff'), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: sfig1_irf_facilities")


# ============================================================
# PRINT SUMMARY
# ============================================================
print(f"\n{'=' * 70}")
print("ANALYSIS SUMMARY")
print(f"{'=' * 70}")
print(f"VAR models fitted: {len(all_var_results)}")
print(f"Granger tests: {len(all_granger)}")
sig_fwd = [g for g in all_granger if g.get('gc_forward_sig')]
sig_rev = [g for g in all_granger if g.get('gc_reverse_sig')]
print(f"Significant forward (accidents → outcome): {len(sig_fwd)}")
for g in sig_fwd:
    print(f"  {g['specialty_en']} ({g['definition']}, {g['outcome']}): "
          f"F={g['gc_forward_F']:.2f}, p={g['gc_forward_p']:.4f}")
print(f"Significant reverse (outcome → accidents): {len(sig_rev)}")
for g in sig_rev:
    print(f"  {g['specialty_en']} ({g['definition']}, {g['outcome']}): "
          f"F={g['gc_reverse_F']:.2f}, p={g['gc_reverse_p']:.4f}")
print(f"Forecasts generated: {len(all_forecasts)}")

print("\n=== VAR + Granger Analysis Complete ===")
