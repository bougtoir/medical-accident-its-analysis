#!/usr/bin/env python3
"""Generate Figure S3: Cross-correlation function plots for all specialties."""

import sys
sys.path.insert(0, '/home/ubuntu/medical_analysis')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from its_analysis import (
    core_specialties, get_jmsr_series, get_litigation_series,
    get_physician_series, get_facility_series, compute_cross_correlation
)

SPEC_EN = {
    '内科': 'Internal medicine', '外科': 'General surgery',
    '整形外科': 'Orthopaedic surgery', '形成外科': 'Plastic surgery',
    '産婦人科': 'Obstetrics & gynaecology', '小児科': 'Paediatrics',
    '精神科': 'Psychiatry', '眼科': 'Ophthalmology',
    '耳鼻咽喉科': 'Otolaryngology', '泌尿器科': 'Urology',
    '皮膚科': 'Dermatology', '麻酔科': 'Anaesthesiology',
}

fig, axes = plt.subplots(4, 3, figsize=(16, 18))
axes = axes.flatten()

for i, spec in enumerate(core_specialties):
    ax = axes[i]
    phys = get_physician_series(spec)
    
    # JMSR vs physicians
    jmsr = get_jmsr_series(spec)
    if not jmsr.empty:
        cc = compute_cross_correlation(jmsr, phys)
        if cc['lags']:
            ax.plot(cc['lags'], cc['corrs'], 'o-', color='#2196F3', label='JMSR', linewidth=1.5, markersize=4)
            best_idx = cc['lags'].index(cc['best_lag'])
            ax.plot(cc['best_lag'], cc['best_corr'], 's', color='#2196F3', markersize=10, zorder=5)
    
    # Litigation vs physicians
    lit = get_litigation_series(spec)
    if not lit.empty:
        cc2 = compute_cross_correlation(lit, phys)
        if cc2['lags']:
            ax.plot(cc2['lags'], cc2['corrs'], 'o-', color='#F44336', label='Litigation', linewidth=1.5, markersize=4)
            ax.plot(cc2['best_lag'], cc2['best_corr'], 's', color='#F44336', markersize=10, zorder=5)
    
    # Mixed vs physicians
    if not jmsr.empty and not lit.empty:
        common_years = jmsr.index.intersection(lit.index)
        if len(common_years) >= 3:
            j_vals = jmsr.loc[common_years].values.astype(float)
            l_vals = lit.loc[common_years].values.astype(float)
            j_range = j_vals.max() - j_vals.min()
            l_range = l_vals.max() - l_vals.min()
            if j_range > 0 and l_range > 0:
                j_norm = (j_vals - j_vals.min()) / j_range
                l_norm = (l_vals - l_vals.min()) / l_range
                mixed = pd.Series((j_norm + l_norm) / 2, index=common_years)
                cc3 = compute_cross_correlation(mixed, phys)
                if cc3['lags']:
                    ax.plot(cc3['lags'], cc3['corrs'], 'o-', color='#4CAF50', label='Composite', linewidth=1.5, markersize=4)
                    ax.plot(cc3['best_lag'], cc3['best_corr'], 's', color='#4CAF50', markersize=10, zorder=5)
    
    ax.axhline(y=0, color='grey', linestyle='--', linewidth=0.5)
    ax.axvline(x=0, color='grey', linestyle='--', linewidth=0.5)
    ax.set_xlim(-9, 9)
    ax.set_ylim(-1.1, 1.1)
    ax.set_title(SPEC_EN.get(spec, spec), fontsize=11, fontweight='bold')
    ax.set_xlabel('Lag (years)')
    ax.set_ylabel('Correlation (r)')
    if i == 0:
        ax.legend(fontsize=8, loc='upper right')

plt.suptitle(
    'Cross-correlation functions between incident counts and physician numbers\n'
    '(detrended) at lags \u22128 to +8 years. Squares indicate the lag with the most negative correlation.',
    fontsize=12, y=1.02
)
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig('/home/ubuntu/medical_analysis/output/ccf_plots.png', dpi=200, bbox_inches='tight')
print("Saved ccf_plots.png")
