#!/usr/bin/env python3
"""
Interrupted Time Series (ITS) Analysis for Medical Accidents
- Definition 1: JMSR
- Definition 2: Supreme Court Litigation
- Definition 3: Mixed (normalized combination)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import rcParams
import warnings
warnings.filterwarnings('ignore')
import os
from scipy import stats
from scipy.interpolate import interp1d
import statsmodels.api as sm

# Japanese font setup
import subprocess
result = subprocess.run(['fc-list', ':lang=ja'], capture_output=True, text=True)
if result.stdout:
    font_path = result.stdout.split(':')[0].strip()
else:
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'fonts-noto-cjk'],
                   capture_output=True, timeout=120)
    result = subprocess.run(['fc-list', ':lang=ja'], capture_output=True, text=True)
    font_path = result.stdout.split(':')[0].strip() if result.stdout else None

if font_path:
    try:
        fp = fm.FontProperties(fname=font_path)
        rcParams['font.family'] = fp.get_name()
    except Exception:
        pass
rcParams['axes.unicode_minus'] = False

DATA_DIR = '/home/ubuntu/medical_analysis/data'
OUTPUT_DIR = '/home/ubuntu/medical_analysis/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# LOAD ALL DATA
# ============================================================
print("Loading data...")
df_jmsr = pd.read_csv(f'{DATA_DIR}/medsafe_accidents_by_specialty.csv')
df_lit = pd.read_csv(f'{DATA_DIR}/litigation_by_specialty.csv')
df_phys = pd.read_csv(f'{DATA_DIR}/physicians_by_specialty.csv')
df_fac = pd.read_csv(f'{DATA_DIR}/facilities_by_specialty.csv')
df_train = pd.read_csv(f'{DATA_DIR}/specialist_trainees_by_specialty.csv')

core_specialties = [
    '\u5185\u79d1', '\u5916\u79d1', '\u6574\u5f62\u5916\u79d1', '\u5f62\u6210\u5916\u79d1',
    '\u7523\u5a66\u4eba\u79d1', '\u5c0f\u5150\u79d1', '\u7cbe\u795e\u79d1', '\u773c\u79d1',
    '\u8033\u9f3b\u54bd\u5589\u79d1', '\u6ccc\u5c3f\u5668\u79d1', '\u76ae\u819a\u79d1',
    '\u9ebb\u9154\u79d1'
]

trainee_specialties = [
    '\u5185\u79d1', '\u5916\u79d1', '\u6574\u5f62\u5916\u79d1', '\u7523\u5a66\u4eba\u79d1',
    '\u5c0f\u5150\u79d1', '\u7cbe\u795e\u79d1', '\u773c\u79d1', '\u8033\u9f3b\u54bd\u5589\u79d1',
    '\u6ccc\u5c3f\u5668\u79d1', '\u76ae\u819a\u79d1', '\u9ebb\u9154\u79d1',
    '\u8133\u795e\u7d4c\u5916\u79d1', '\u653e\u5c04\u7dda\u79d1', '\u6551\u6025\u79d1',
    '\u5f62\u6210\u5916\u79d1', '\u30ea\u30cf\u30d3\u30ea\u30c6\u30fc\u30b7\u30e7\u30f3\u79d1',
    '\u7dcf\u5408\u8a3a\u7642'
]

print(f"Core specialties: {len(core_specialties)}")

# ============================================================
# DATA RESHAPING FUNCTIONS
# ============================================================

def get_jmsr_series(specialty):
    row = df_jmsr[df_jmsr['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    years = [str(y) for y in range(2015, 2026)]
    vals = row[years].values.flatten().astype(float)
    return pd.Series(vals, index=range(2015, 2026), name='jmsr_accidents')

def get_litigation_series(specialty):
    row = df_lit[df_lit['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    years = [str(y) for y in range(2004, 2024)]
    vals = []
    for y in years:
        v = row[y].values[0]
        vals.append(float(v) if pd.notna(v) else np.nan)
    return pd.Series(vals, index=range(2004, 2024), name='litigation_cases')

def get_physician_series(specialty):
    row = df_phys[df_phys['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    year_cols = [c for c in df_phys.columns if c != 'specialty']
    years_int = sorted([int(y) for y in year_cols])
    vals = [float(row[str(y)].values[0]) if pd.notna(row[str(y)].values[0]) else np.nan for y in years_int]
    valid = [(y, v) for y, v in zip(years_int, vals) if not np.isnan(v)]
    if len(valid) < 2:
        return pd.Series(dtype=float)
    y_arr, v_arr = zip(*valid)
    f_interp = interp1d(y_arr, v_arr, kind='linear', fill_value='extrapolate')
    all_years = range(min(y_arr), max(y_arr) + 1)
    interp_vals = f_interp(list(all_years))
    return pd.Series(interp_vals, index=all_years, name='physician_count')

def get_facility_series(specialty):
    row = df_fac[df_fac['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    year_cols = [c for c in df_fac.columns if c != 'specialty']
    years_int = sorted([int(y) for y in year_cols])
    vals = [float(row[str(y)].values[0]) if pd.notna(row[str(y)].values[0]) else np.nan for y in years_int]
    valid = [(y, v) for y, v in zip(years_int, vals) if not np.isnan(v)]
    if len(valid) < 2:
        return pd.Series(dtype=float)
    y_arr, v_arr = zip(*valid)
    f_interp = interp1d(y_arr, v_arr, kind='linear', fill_value='extrapolate')
    all_years = range(min(y_arr), max(y_arr) + 1)
    interp_vals = f_interp(list(all_years))
    return pd.Series(interp_vals, index=all_years, name='facility_count')

def get_trainee_series(specialty):
    row = df_train[df_train['specialty'] == specialty]
    if row.empty:
        return pd.Series(dtype=float)
    year_cols = [c for c in df_train.columns if c != 'specialty']
    years_int = sorted([int(y) for y in year_cols])
    vals = [float(row[str(y)].values[0]) if pd.notna(row[str(y)].values[0]) else np.nan for y in years_int]
    return pd.Series(vals, index=years_int, name='trainee_count')

# ============================================================
# ITS ANALYSIS FUNCTIONS
# ============================================================

def compute_cross_correlation(accident_series, outcome_series, max_lag=8):
    common_idx = accident_series.index.intersection(outcome_series.index)
    if len(common_idx) < 5:
        return {'best_lag': None, 'best_corr': None, 'lags': [], 'corrs': []}
    x = accident_series.loc[common_idx].values.astype(float)
    y = outcome_series.loc[common_idx].values.astype(float)
    t = np.arange(len(x))
    x_detrend = x - np.polyval(np.polyfit(t, x, 1), t)
    y_detrend = y - np.polyval(np.polyfit(t, y, 1), t)
    if np.std(x_detrend) == 0 or np.std(y_detrend) == 0:
        return {'best_lag': None, 'best_corr': None, 'lags': [], 'corrs': []}
    x_norm = (x_detrend - np.mean(x_detrend)) / np.std(x_detrend)
    y_norm = (y_detrend - np.mean(y_detrend)) / np.std(y_detrend)
    lags = []
    corrs = []
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            xx = x_norm[:len(x_norm)-lag] if lag > 0 else x_norm
            yy = y_norm[lag:] if lag > 0 else y_norm
        else:
            xx = x_norm[-lag:]
            yy = y_norm[:len(y_norm)+lag]
        if len(xx) < 4:
            continue
        r, _ = stats.pearsonr(xx, yy)
        lags.append(lag)
        corrs.append(r)
    if not corrs:
        return {'best_lag': None, 'best_corr': None, 'lags': [], 'corrs': []}
    best_idx = np.argmin(corrs)
    return {'best_lag': lags[best_idx], 'best_corr': corrs[best_idx], 'lags': lags, 'corrs': corrs}

def its_segmented_regression(accident_series, outcome_series, intervention_year=None):
    common_idx = sorted(accident_series.index.intersection(outcome_series.index))
    if len(common_idx) < 6:
        return None
    accidents = accident_series.loc[common_idx].values.astype(float)
    outcome = outcome_series.loc[common_idx].values.astype(float)
    if intervention_year is None:
        intervention_year = common_idx[np.argmax(accidents)]
    time = np.arange(len(common_idx))
    intervention = np.array([1 if y >= intervention_year else 0 for y in common_idx])
    time_after = np.array([y - intervention_year if y >= intervention_year else 0 for y in common_idx])
    X = np.column_stack([time, intervention, time_after, accidents])
    X = sm.add_constant(X)
    try:
        model = sm.OLS(outcome, X).fit()
        return {
            'model': model,
            'intervention_year': intervention_year,
            'years': common_idx,
            'outcome': outcome,
            'accidents': accidents,
            'params': {
                'intercept': model.params[0],
                'trend': model.params[1],
                'level_change': model.params[2],
                'slope_change': model.params[3],
                'accident_effect': model.params[4],
            },
            'pvalues': {
                'intercept': model.pvalues[0],
                'trend': model.pvalues[1],
                'level_change': model.pvalues[2],
                'slope_change': model.pvalues[3],
                'accident_effect': model.pvalues[4],
            },
            'r_squared': model.rsquared,
            'fitted': model.fittedvalues,
            'conf_int': model.conf_int(),
        }
    except Exception as e:
        print(f"  ITS regression error: {e}")
        return None

def estimate_window_period(accident_series, outcome_series, max_window=10):
    common_idx = sorted(accident_series.index.intersection(outcome_series.index))
    if len(common_idx) < 6:
        return None
    accidents = accident_series.loc[common_idx].values.astype(float)
    outcome = outcome_series.loc[common_idx].values.astype(float)
    best_aic = np.inf
    best_window = None
    results = []
    peak_year_idx = np.argmax(accidents)
    for window in range(1, min(max_window + 1, len(common_idx) - peak_year_idx)):
        intervention = np.zeros(len(common_idx))
        intervention[peak_year_idx:peak_year_idx + window] = 1
        time = np.arange(len(common_idx))
        X = np.column_stack([time, intervention, accidents])
        X = sm.add_constant(X)
        try:
            model = sm.OLS(outcome, X).fit()
            results.append({'window': window, 'aic': model.aic, 'r2': model.rsquared})
            if model.aic < best_aic:
                best_aic = model.aic
                best_window = window
        except Exception:
            continue
    return {'best_window': best_window, 'results': results}

# ============================================================
# MAIN ANALYSIS
# ============================================================
all_results = {}
lead_time_results = {}
window_results = {}

accident_defs = {
    'def1_jmsr': ('JMSR', get_jmsr_series),
    'def2_litigation': ('Litigation', get_litigation_series),
}

for spec in core_specialties:
    print(f"\n{'='*60}\nSpecialty: {spec}\n{'='*60}")
    phys = get_physician_series(spec)
    fac = get_facility_series(spec)
    if phys.empty or fac.empty:
        print(f"  Skipping {spec}: insufficient data")
        continue
    for def_name, (def_label, get_acc_fn) in accident_defs.items():
        acc = get_acc_fn(spec)
        if acc.empty or acc.sum() == 0:
            print(f"  {def_label}: No accident data for {spec}")
            continue
        print(f"\n  --- {def_label} ---")
        for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
            cc = compute_cross_correlation(acc, outcome_series)
            key = f"{spec}_{def_name}_{outcome_name}"
            lead_time_results[key] = {
                'specialty': spec, 'definition': def_label, 'outcome': outcome_name, **cc
            }
            if cc['best_lag'] is not None:
                print(f"    {outcome_name}: best_lag={cc['best_lag']}y, r={cc['best_corr']:.3f}")
        for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
            its = its_segmented_regression(acc, outcome_series)
            key = f"{spec}_{def_name}_{outcome_name}"
            all_results[key] = {
                'specialty': spec, 'definition': def_label, 'outcome': outcome_name, 'its': its,
            }
            if its:
                print(f"    ITS {outcome_name}: R2={its['r_squared']:.3f}, "
                      f"acc_eff={its['params']['accident_effect']:.1f} "
                      f"(p={its['pvalues']['accident_effect']:.4f})")
        for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
            wp = estimate_window_period(acc, outcome_series)
            key = f"{spec}_{def_name}_{outcome_name}"
            window_results[key] = {
                'specialty': spec, 'definition': def_label, 'outcome': outcome_name, 'window': wp
            }
            if wp and wp['best_window']:
                print(f"    Window {outcome_name}: {wp['best_window']}y")

# ============================================================
# Definition 3: Mixed
# ============================================================
print(f"\n{'='*60}\nDefinition 3: Mixed\n{'='*60}")
for spec in core_specialties:
    jmsr = get_jmsr_series(spec)
    lit = get_litigation_series(spec)
    phys = get_physician_series(spec)
    fac = get_facility_series(spec)
    if jmsr.empty or lit.empty or phys.empty or fac.empty:
        continue
    common_years = jmsr.index.intersection(lit.index)
    if len(common_years) < 3:
        continue
    j_vals = jmsr.loc[common_years].values.astype(float)
    l_vals = lit.loc[common_years].values.astype(float)
    j_range = j_vals.max() - j_vals.min()
    l_range = l_vals.max() - l_vals.min()
    if j_range == 0 or l_range == 0:
        continue
    j_norm = (j_vals - j_vals.min()) / j_range
    l_norm = (l_vals - l_vals.min()) / l_range
    mixed = pd.Series((j_norm + l_norm) / 2, index=common_years, name='mixed_accidents')
    print(f"\n  {spec}:")
    for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
        cc = compute_cross_correlation(mixed, outcome_series)
        key = f"{spec}_def3_mixed_{outcome_name}"
        lead_time_results[key] = {'specialty': spec, 'definition': 'Mixed', 'outcome': outcome_name, **cc}
        its = its_segmented_regression(mixed, outcome_series)
        all_results[key] = {'specialty': spec, 'definition': 'Mixed', 'outcome': outcome_name, 'its': its}
        wp = estimate_window_period(mixed, outcome_series)
        window_results[key] = {'specialty': spec, 'definition': 'Mixed', 'outcome': outcome_name, 'window': wp}
        parts = []
        if cc['best_lag'] is not None:
            parts.append(f"lag={cc['best_lag']}y, r={cc['best_corr']:.3f}")
        if its:
            parts.append(f"R2={its['r_squared']:.3f}")
        if wp and wp['best_window']:
            parts.append(f"window={wp['best_window']}y")
        if parts:
            print(f"    {outcome_name}: {', '.join(parts)}")

# ============================================================
# TRAINEE ANALYSIS
# ============================================================
print(f"\n{'='*60}\nTrainee Analysis\n{'='*60}")
trainee_results = {}
for spec in trainee_specialties:
    train = get_trainee_series(spec)
    if train.empty or train.dropna().empty:
        continue
    jmsr = get_jmsr_series(spec)
    if not jmsr.empty:
        cc = compute_cross_correlation(jmsr, train, max_lag=4)
        trainee_results[f"{spec}_jmsr"] = {'specialty': spec, 'definition': 'JMSR', **cc}
        if cc['best_lag'] is not None:
            print(f"  {spec} (JMSR): lag={cc['best_lag']}y, r={cc['best_corr']:.3f}")

# ============================================================
# LEAD TIME & WINDOW PERIOD SUMMARY
# ============================================================
print(f"\n{'='*60}\nLEAD TIME & WINDOW PERIOD SUMMARY\n{'='*60}")

lt_summary = []
for key, result in lead_time_results.items():
    if result['best_lag'] is not None:
        lt_summary.append({
            'specialty': result['specialty'], 'definition': result['definition'],
            'outcome': result['outcome'], 'lead_time_years': result['best_lag'],
            'correlation': result['best_corr'],
        })
df_lt = pd.DataFrame(lt_summary)
if not df_lt.empty:
    print("\nLead Time Estimates:")
    print(df_lt.to_string(index=False))
    df_lt.to_csv(f'{DATA_DIR}/lead_time_estimates.csv', index=False)

wp_summary = []
for key, result in window_results.items():
    if result['window'] and result['window']['best_window']:
        wp_summary.append({
            'specialty': result['specialty'], 'definition': result['definition'],
            'outcome': result['outcome'], 'window_years': result['window']['best_window'],
        })
df_wp = pd.DataFrame(wp_summary)
if not df_wp.empty:
    print("\nWindow Period Estimates:")
    print(df_wp.to_string(index=False))
    df_wp.to_csv(f'{DATA_DIR}/window_period_estimates.csv', index=False)

print("\n--- Aggregate Estimates ---")
if not df_lt.empty:
    for outcome in ['physicians', 'facilities']:
        subset = df_lt[df_lt['outcome'] == outcome]
        if not subset.empty:
            weights = subset['correlation'].abs()
            weighted_lag = np.average(subset['lead_time_years'], weights=weights)
            print(f"\n  {outcome}: mean={subset['lead_time_years'].mean():.1f}y, "
                  f"median={subset['lead_time_years'].median():.1f}y, weighted={weighted_lag:.1f}y")
if not df_wp.empty:
    for outcome in ['physicians', 'facilities']:
        subset = df_wp[df_wp['outcome'] == outcome]
        if not subset.empty:
            print(f"  {outcome} window: mean={subset['window_years'].mean():.1f}y, "
                  f"median={subset['window_years'].median():.1f}y")

# ============================================================
# FORECASTING
# ============================================================
print(f"\n{'='*60}\nFORECASTING\n{'='*60}")

forecast_results = {}
forecast_years = list(range(2025, 2035))

for spec in core_specialties:
    phys = get_physician_series(spec)
    fac = get_facility_series(spec)
    if phys.empty or fac.empty:
        continue
    for outcome_name, outcome_series in [('physicians', phys), ('facilities', fac)]:
        recent_years = [y for y in outcome_series.index if y >= 2014]
        if len(recent_years) < 3:
            continue
        t = np.array(recent_years)
        v = outcome_series.loc[recent_years].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(t, v)
        forecast_vals = intercept + slope * np.array(forecast_years)
        residuals = v - (intercept + slope * t)
        sigma = np.std(residuals)
        forecast_results[f"{spec}_{outcome_name}"] = {
            'specialty': spec, 'outcome': outcome_name, 'trend_slope': slope,
            'trend_intercept': intercept,
            'forecast_years': forecast_years,
            'forecast_values': forecast_vals.tolist(),
            'forecast_upper': (forecast_vals + 2 * sigma).tolist(),
            'forecast_lower': (forecast_vals - 2 * sigma).tolist(),
            'historical_years': list(outcome_series.index),
            'historical_values': outcome_series.values.tolist(),
        }
        print(f"  {spec} {outcome_name}: slope={slope:.1f}/yr, "
              f"2025={forecast_vals[0]:.0f}, 2030={forecast_vals[5]:.0f}, 2034={forecast_vals[-1]:.0f}")

for spec in trainee_specialties:
    train = get_trainee_series(spec)
    if train.empty or train.dropna().empty:
        continue
    clean_train = train.dropna()
    if len(clean_train) < 3:
        continue
    t = np.array(list(clean_train.index))
    v = clean_train.values
    slope, intercept, r_value, p_value, std_err = stats.linregress(t, v)
    forecast_vals = intercept + slope * np.array(forecast_years)
    residuals = v - (intercept + slope * t)
    sigma = np.std(residuals)
    forecast_results[f"{spec}_trainees"] = {
        'specialty': spec, 'outcome': 'trainees', 'trend_slope': slope,
        'forecast_years': forecast_years,
        'forecast_values': forecast_vals.tolist(),
        'forecast_upper': (forecast_vals + 2 * sigma).tolist(),
        'forecast_lower': (forecast_vals - 2 * sigma).tolist(),
        'historical_years': list(clean_train.index),
        'historical_values': clean_train.values.tolist(),
    }

# ============================================================
# VISUALIZATIONS
# ============================================================
print(f"\n{'='*60}\nCreating Visualizations\n{'='*60}")

# Plot 1: ITS Physicians - Def1 JMSR
fig, axes = plt.subplots(4, 3, figsize=(20, 24))
fig.suptitle('ITS Analysis: Physician Count vs Medical Accidents\n(Definition 1: JMSR)', fontsize=16)
for i, spec in enumerate(core_specialties):
    ax = axes[i // 3, i % 3]
    key = f"{spec}_def1_jmsr_physicians"
    if key in all_results and all_results[key]['its']:
        its = all_results[key]['its']
        ax.plot(its['years'], its['outcome'], 'bo-', label='Observed', markersize=4)
        ax.plot(its['years'], its['fitted'], 'r-', label='ITS Fitted', linewidth=2)
        ax.axvline(x=its['intervention_year'], color='gray', linestyle='--', alpha=0.7,
                   label=f"Peak ({its['intervention_year']})")
        ax.set_title(f"{spec}\nR2={its['r_squared']:.3f}")
    else:
        phys = get_physician_series(spec)
        if not phys.empty:
            ax.plot(phys.index, phys.values, 'bo-', markersize=4)
        ax.set_title(f'{spec}\n(Insufficient overlap)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Physician Count')
    if i == 0:
        ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/its_physicians_def1.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: its_physicians_def1.png")

# Plot 2: ITS Facilities - Def1 JMSR
fig, axes = plt.subplots(4, 3, figsize=(20, 24))
fig.suptitle('ITS Analysis: Facility Count vs Medical Accidents\n(Definition 1: JMSR)', fontsize=16)
for i, spec in enumerate(core_specialties):
    ax = axes[i // 3, i % 3]
    key = f"{spec}_def1_jmsr_facilities"
    if key in all_results and all_results[key]['its']:
        its = all_results[key]['its']
        ax.plot(its['years'], its['outcome'], 'go-', label='Observed', markersize=4)
        ax.plot(its['years'], its['fitted'], 'r-', label='ITS Fitted', linewidth=2)
        ax.axvline(x=its['intervention_year'], color='gray', linestyle='--', alpha=0.7)
        ax.set_title(f"{spec}\nR2={its['r_squared']:.3f}")
    else:
        fac = get_facility_series(spec)
        if not fac.empty:
            ax.plot(fac.index, fac.values, 'go-', markersize=4)
        ax.set_title(f'{spec}\n(Insufficient overlap)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Facility Count')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/its_facilities_def1.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: its_facilities_def1.png")

# Plot 3: Lead Time Heatmap
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
for ax_idx, outcome_name in enumerate(['physicians', 'facilities']):
    ax = axes[ax_idx]
    lag_matrix = np.full((len(core_specialties), 3), np.nan)
    defs = ['def1_jmsr', 'def2_litigation', 'def3_mixed']
    def_labels = ['JMSR', 'Litigation', 'Mixed']
    for i, spec in enumerate(core_specialties):
        for j, def_name in enumerate(defs):
            key = f"{spec}_{def_name}_{outcome_name}"
            if key in lead_time_results and lead_time_results[key]['best_lag'] is not None:
                lag_matrix[i, j] = lead_time_results[key]['best_lag']
    im = ax.imshow(lag_matrix, aspect='auto', cmap='RdYlBu_r', vmin=-5, vmax=5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(def_labels)
    ax.set_yticks(range(len(core_specialties)))
    ax.set_yticklabels(core_specialties)
    ax.set_title(f'Lead Time (years)\n{outcome_name}')
    for i in range(len(core_specialties)):
        for j in range(3):
            if not np.isnan(lag_matrix[i, j]):
                ax.text(j, i, f'{lag_matrix[i, j]:.0f}', ha='center', va='center', fontsize=10)
    plt.colorbar(im, ax=ax, label='Lead time (years)')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/lead_time_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: lead_time_heatmap.png")

# Plot 4: Physician Forecasts
key_specs = ['\u5185\u79d1', '\u5916\u79d1', '\u6574\u5f62\u5916\u79d1',
             '\u7523\u5a66\u4eba\u79d1', '\u5c0f\u5150\u79d1', '\u7cbe\u795e\u79d1']
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
fig.suptitle('Physician Count Forecast (2025-2034)', fontsize=16)
for i, spec in enumerate(key_specs):
    ax = axes[i // 2, i % 2]
    key = f"{spec}_physicians"
    if key in forecast_results:
        fr = forecast_results[key]
        ax.plot(fr['historical_years'], fr['historical_values'], 'bo-', label='Historical', markersize=4)
        ax.plot(fr['forecast_years'], fr['forecast_values'], 'r--', label='Forecast', linewidth=2)
        ax.fill_between(fr['forecast_years'], fr['forecast_lower'], fr['forecast_upper'],
                        alpha=0.2, color='red', label='95% CI')
        ax.axvline(x=2024, color='gray', linestyle=':', alpha=0.5)
    ax.set_title(spec)
    ax.set_xlabel('Year')
    ax.set_ylabel('Physician Count')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/forecast_physicians.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: forecast_physicians.png")

# Plot 5: Facility Forecasts
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
fig.suptitle('Facility Count Forecast (2025-2034)', fontsize=16)
for i, spec in enumerate(key_specs):
    ax = axes[i // 2, i % 2]
    key = f"{spec}_facilities"
    if key in forecast_results:
        fr = forecast_results[key]
        ax.plot(fr['historical_years'], fr['historical_values'], 'go-', label='Historical', markersize=4)
        ax.plot(fr['forecast_years'], fr['forecast_values'], 'r--', label='Forecast', linewidth=2)
        ax.fill_between(fr['forecast_years'], fr['forecast_lower'], fr['forecast_upper'],
                        alpha=0.2, color='red', label='95% CI')
        ax.axvline(x=2024, color='gray', linestyle=':', alpha=0.5)
    ax.set_title(spec)
    ax.set_xlabel('Year')
    ax.set_ylabel('Facility Count')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/forecast_facilities.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: forecast_facilities.png")

# Plot 6: Trainee Forecasts
train_specs = ['\u5185\u79d1', '\u5916\u79d1', '\u6574\u5f62\u5916\u79d1',
               '\u7523\u5a66\u4eba\u79d1', '\u5c0f\u5150\u79d1', '\u6551\u6025\u79d1',
               '\u9ebb\u9154\u79d1', '\u7cbe\u795e\u79d1', '\u8133\u795e\u7d4c\u5916\u79d1']
fig, axes = plt.subplots(3, 3, figsize=(18, 15))
fig.suptitle('Specialist Trainee Count Forecast (2025-2034)', fontsize=16)
for i, spec in enumerate(train_specs):
    ax = axes[i // 3, i % 3]
    key = f"{spec}_trainees"
    if key in forecast_results:
        fr = forecast_results[key]
        ax.plot(fr['historical_years'], fr['historical_values'], 'ms-', label='Historical', markersize=5)
        ax.plot(fr['forecast_years'], fr['forecast_values'], 'r--', label='Forecast', linewidth=2)
        ax.fill_between(fr['forecast_years'], fr['forecast_lower'], fr['forecast_upper'],
                        alpha=0.2, color='red', label='95% CI')
        ax.axvline(x=2024, color='gray', linestyle=':', alpha=0.5)
    ax.set_title(spec)
    ax.set_xlabel('Year')
    ax.set_ylabel('Trainee Count')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/forecast_trainees.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: forecast_trainees.png")

# Plot 7: Accident Trends Comparison
fig, axes = plt.subplots(4, 3, figsize=(20, 20))
fig.suptitle('Medical Accident Trends by Specialty\n(JMSR vs Litigation)', fontsize=16)
for i, spec in enumerate(core_specialties):
    ax = axes[i // 3, i % 3]
    jmsr = get_jmsr_series(spec)
    lit = get_litigation_series(spec)
    ax2 = ax.twinx()
    if not jmsr.empty:
        ax.plot(jmsr.index, jmsr.values, 'b.-', label='JMSR', markersize=4)
    if not lit.empty:
        ax2.plot(lit.index, lit.values, 'r.-', label='Litigation', markersize=4)
    ax.set_title(spec)
    ax.set_xlabel('Year')
    ax.set_ylabel('JMSR Cases', color='blue')
    ax2.set_ylabel('Litigation Cases', color='red')
    if i == 0:
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=7)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/accident_trends.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: accident_trends.png")

# Plot 8: ITS Physicians - Def2 Litigation
fig, axes = plt.subplots(4, 3, figsize=(20, 24))
fig.suptitle('ITS Analysis: Physician Count vs Litigation\n(Definition 2)', fontsize=16)
for i, spec in enumerate(core_specialties):
    ax = axes[i // 3, i % 3]
    key = f"{spec}_def2_litigation_physicians"
    if key in all_results and all_results[key]['its']:
        its = all_results[key]['its']
        ax.plot(its['years'], its['outcome'], 'bo-', label='Observed', markersize=4)
        ax.plot(its['years'], its['fitted'], 'r-', label='ITS Fitted', linewidth=2)
        ax.axvline(x=its['intervention_year'], color='gray', linestyle='--', alpha=0.7)
        ax.set_title(f"{spec}\nR2={its['r_squared']:.3f}, acc_eff={its['params']['accident_effect']:.1f}")
    else:
        ax.set_title(f'{spec}\n(No result)')
    ax.set_xlabel('Year')
    ax.set_ylabel('Physician Count')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/its_physicians_def2.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: its_physicians_def2.png")

# ============================================================
# SAVE RESULTS SUMMARY
# ============================================================
its_summary = []
for key, result in all_results.items():
    if result['its']:
        its = result['its']
        its_summary.append({
            'specialty': result['specialty'], 'definition': result['definition'],
            'outcome': result['outcome'], 'R_squared': its['r_squared'],
            'intervention_year': its['intervention_year'],
            'trend_coef': its['params']['trend'], 'trend_pval': its['pvalues']['trend'],
            'level_change_coef': its['params']['level_change'],
            'level_change_pval': its['pvalues']['level_change'],
            'slope_change_coef': its['params']['slope_change'],
            'slope_change_pval': its['pvalues']['slope_change'],
            'accident_effect_coef': its['params']['accident_effect'],
            'accident_effect_pval': its['pvalues']['accident_effect'],
        })
df_its_summary = pd.DataFrame(its_summary)
df_its_summary.to_csv(f'{DATA_DIR}/its_results_summary.csv', index=False)
print(f"\nITS Results: {len(df_its_summary)} models saved")

forecast_summary = []
for key, fr in forecast_results.items():
    forecast_summary.append({
        'specialty': fr['specialty'], 'outcome': fr['outcome'],
        'trend_slope_per_year': fr['trend_slope'],
        'forecast_2025': fr['forecast_values'][0],
        'forecast_2030': fr['forecast_values'][5],
        'forecast_2034': fr['forecast_values'][-1],
        'forecast_2030_upper': fr['forecast_upper'][5],
        'forecast_2030_lower': fr['forecast_lower'][5],
    })
df_forecast = pd.DataFrame(forecast_summary)
df_forecast.to_csv(f'{DATA_DIR}/forecast_summary.csv', index=False)
print(f"Forecast: {len(df_forecast)} forecasts saved")

print("\n=== Analysis Complete ===")
