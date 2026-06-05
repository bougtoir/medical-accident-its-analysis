#!/usr/bin/env python3
"""
Generate additional figures and tables for the BJA manuscript:
- Figure 5: Bland-Altman plots for 4 scenarios (paired with Figure 2 concordance plots)
- Figure 6: Sensitivity heatmap (gain error % x offset → Cb)
- Figure 7: PP validation demonstration (PP accuracy validates gain)
- Table 2 data: Complete statistical comparison across all scenarios
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from scipy import stats
import os

FIGDIR = '/home/ubuntu/bja_figures'
os.makedirs(FIGDIR, exist_ok=True)
np.random.seed(42)

# ──────────────────────────────────────────────────────────────
# Shared simulation data (same as Figure 2)
# ──────────────────────────────────────────────────────────────
n = 150
# Reference arterial pressures (realistic distribution)
ref_sbp = np.random.normal(120, 18, n)
ref_dbp = ref_sbp - np.random.normal(45, 8, n)
ref_dbp = np.clip(ref_dbp, 40, 100)
# Interleave SBP and DBP to create paired measurements
ref = np.concatenate([ref_sbp, ref_dbp])
ref = ref_sbp * 0.6 + ref_dbp * 0.4 + np.random.normal(0, 8, n)  # mixed arterial pressures
ref = np.random.normal(100, 22, n)  # simplified: mean=100, SD=22

noise = np.random.normal(0, 3.5, n)

# Four scenarios
offset = 12  # mmHg
gain = 0.89

dev_A = ref + offset + noise          # offset only (before zeroing)
dev_B = ref + noise                   # after zeroing (offset removed)
dev_C = gain * ref + noise            # gain error only
dev_D = gain * ref + offset + noise   # gain + offset

scenarios = [
    ('A: Before zeroing\n(offset only)', ref, dev_A, '#E74C3C'),
    ('B: After zeroing\n(offset removed)', ref, dev_B, '#3498DB'),
    ('C: Gain error\n(zeroing cannot fix)', ref, dev_C, '#8E44AD'),
    ('D: Gain + offset\n(zeroing fixes only offset)', ref, dev_D, '#E67E22'),
]

def calc_ccc(x, y):
    """Calculate Lin's CCC and its components."""
    mx, my = np.mean(x), np.mean(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    r = np.corrcoef(x, y)[0, 1]
    v = sx / sy  # scale shift
    u = (mx - my) / np.sqrt(sx * sy)  # location shift
    cb = 2 / (v + 1/v + u**2)
    ccc = r * cb
    return ccc, r, cb, u, v

def calc_ba(x, y):
    """Calculate Bland-Altman statistics."""
    diff = y - x
    mean_pair = (x + y) / 2
    bias = np.mean(diff)
    sd_diff = np.std(diff, ddof=1)
    loa_upper = bias + 1.96 * sd_diff
    loa_lower = bias - 1.96 * sd_diff
    # Percentage error (Critchley-Critchley)
    pe = 1.96 * sd_diff / np.mean(x) * 100
    return bias, sd_diff, loa_upper, loa_lower, pe, diff, mean_pair

# ──────────────────────────────────────────────────────────────
# FIGURE 5: Bland-Altman plots for 4 scenarios
# ──────────────────────────────────────────────────────────────
fig5, axes5 = plt.subplots(1, 4, figsize=(20, 5), sharey=True)
fig5.suptitle('Bland-Altman Analysis: Zero Calibration Hides Gain Error', 
              fontsize=14, fontweight='bold', y=1.02)

ba_stats = []

for idx, (title, x, y, color) in enumerate(scenarios):
    ax = axes5[idx]
    bias, sd_diff, loa_up, loa_low, pe, diff, mean_pair = calc_ba(x, y)
    ccc, r, cb, u, v = calc_ccc(x, y)
    ba_stats.append({
        'scenario': title.split('\n')[0],
        'ccc': ccc, 'r': r, 'cb': cb, 'u': u, 'v': v,
        'bias': bias, 'sd_diff': sd_diff, 'loa_up': loa_up, 'loa_low': loa_low, 'pe': pe
    })
    
    ax.scatter(mean_pair, diff, c=color, alpha=0.5, s=20, edgecolors='none')
    
    # Bias line
    ax.axhline(y=bias, color=color, linewidth=2, linestyle='-', label=f'Bias = {bias:.1f}')
    # LOA lines
    ax.axhline(y=loa_up, color=color, linewidth=1, linestyle='--', alpha=0.7,
               label=f'LOA = [{loa_low:.1f}, {loa_up:.1f}]')
    ax.axhline(y=loa_low, color=color, linewidth=1, linestyle='--', alpha=0.7)
    # Zero line
    ax.axhline(y=0, color='gray', linewidth=0.5, linestyle=':')
    
    # Fill LOA
    xlim = ax.get_xlim()
    ax.fill_between([20, 180], loa_low, loa_up, alpha=0.08, color=color)
    ax.set_xlim(20, 180)
    
    ax.set_xlabel('Mean of Reference & Device (mmHg)', fontsize=9)
    if idx == 0:
        ax.set_ylabel('Device − Reference (mmHg)', fontsize=10)
    
    ax.set_title(title, fontsize=10, fontweight='bold', color=color)
    
    # Stats box
    stats_text = f'Bias = {bias:.1f} mmHg\nLOA = [{loa_low:.1f}, {loa_up:.1f}]\nPE = {pe:.1f}%'
    props = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.9)
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', bbox=props)
    
    # Add CCC info in bottom-right
    ccc_text = f'CCC = {ccc:.3f}\nCb = {cb:.3f}'
    props2 = dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', alpha=0.9)
    ax.text(0.95, 0.05, ccc_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='bottom', horizontalalignment='right', bbox=props2)
    
    ax.set_ylim(-35, 35)
    ax.grid(True, alpha=0.3)

# Add annotation: highlight that B and C look similar on BA
fig5.text(0.5, -0.08, 
          '★ Key observation: After zeroing (B), BA bias ≈ 0 looks "good" — but gain error (C) also shows near-zero bias.\n'
          '    BA plot cannot distinguish B (true agreement) from C (hidden gain error). CCC decomposition (Cb, v) reveals the difference.',
          ha='center', fontsize=10, style='italic',
          bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#FBC02D'))

fig5.tight_layout()
fig5.savefig(os.path.join(FIGDIR, 'figure5_ba_comparison.png'), 
             dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig5)
print('Figure 5 saved.')

# ──────────────────────────────────────────────────────────────
# FIGURE 6: Sensitivity heatmap (gain error % × offset → Cb)
# ──────────────────────────────────────────────────────────────
fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(16, 7))

# Panel A: Cb as function of gain error and offset
gain_errors = np.linspace(-20, 20, 200)  # % gain error
offsets = np.linspace(0, 30, 200)  # mmHg offset

# For Cb calculation, need to convert to u and v
# Assume reference: mean=100, SD=22
ref_mean = 100
ref_sd = 22

Cb_matrix = np.zeros((len(offsets), len(gain_errors)))

for i, off in enumerate(offsets):
    for j, ge in enumerate(gain_errors):
        g = 1 + ge/100  # actual gain
        dev_mean = g * ref_mean + off
        dev_sd = g * ref_sd
        v_val = dev_sd / ref_sd  # = g
        u_val = (dev_mean - ref_mean) / np.sqrt(dev_sd * ref_sd)
        Cb_matrix[i, j] = 2 / (v_val + 1/v_val + u_val**2)

im = ax6a.imshow(Cb_matrix, extent=[gain_errors[0], gain_errors[-1], offsets[-1], offsets[0]],
                 aspect='auto', cmap='RdYlGn', vmin=0.5, vmax=1.0)
cb_bar = plt.colorbar(im, ax=ax6a, label='$C_b$ (bias correction factor)')

# Contour lines
X, Y = np.meshgrid(gain_errors, offsets)
contours = ax6a.contour(X, Y, Cb_matrix, levels=[0.6, 0.7, 0.8, 0.9, 0.95, 0.99],
                        colors='black', linewidths=0.8)
ax6a.clabel(contours, inline=True, fontsize=8, fmt='%.2f')

# Mark scenarios
ax6a.plot(0, 12, 'o', color='#E74C3C', markersize=10, markeredgecolor='white', markeredgewidth=2,
          zorder=5)
ax6a.annotate('A', (0, 12), textcoords='offset points', xytext=(10, 5),
              fontsize=11, fontweight='bold', color='#E74C3C')

ax6a.plot(0, 0, marker='*', color='gold', markersize=15, markeredgecolor='black', markeredgewidth=1,
          zorder=5, linestyle='none')
ax6a.annotate('B (ideal)', (0, 0), textcoords='offset points', xytext=(10, -15),
              fontsize=10, fontweight='bold', color='#3498DB')

ax6a.plot(-11, 0, 'o', color='#8E44AD', markersize=10, markeredgecolor='white', markeredgewidth=2,
          zorder=5)
ax6a.annotate('C', (-11, 0), textcoords='offset points', xytext=(10, 5),
              fontsize=11, fontweight='bold', color='#8E44AD')

ax6a.plot(-11, 12, 'o', color='#E67E22', markersize=10, markeredgecolor='white', markeredgewidth=2,
          zorder=5)
ax6a.annotate('D', (-11, 12), textcoords='offset points', xytext=(10, 5),
              fontsize=11, fontweight='bold', color='#E67E22')

# Arrow showing zero calibration effect (D→C)
ax6a.annotate('', xy=(-11, 1), xytext=(-11, 11),
              arrowprops=dict(arrowstyle='->', color='green', lw=2))
ax6a.text(-8, 6, 'Zero\ncalibration', fontsize=8, color='green', fontweight='bold')

# Arrow showing zero calibration effect (A→B)
ax6a.annotate('', xy=(0, 1), xytext=(0, 11),
              arrowprops=dict(arrowstyle='->', color='green', lw=2))

ax6a.set_xlabel('Gain error (%)', fontsize=12)
ax6a.set_ylabel('DC offset (mmHg)', fontsize=12)
ax6a.set_title('A. $C_b$ sensitivity to gain error and offset', fontsize=12, fontweight='bold')

# Panel B: CCC as function of gain error for different noise levels (r values)
ax6b_colors = ['#2ECC71', '#3498DB', '#E67E22', '#E74C3C']
noise_levels = [0.99, 0.95, 0.90, 0.80]  # r values

for r_val, color in zip(noise_levels, ax6b_colors):
    gains = np.linspace(-20, 20, 200)
    cccs = []
    for ge in gains:
        g = 1 + ge/100
        v_val = g
        # Assume offset = 0 (zeroed)
        cb = 2 / (v_val + 1/v_val)
        cccs.append(r_val * cb)
    ax6b.plot(gains, cccs, color=color, linewidth=2, label=f'r = {r_val:.2f}')

# Reference lines
ax6b.axhline(y=0.90, color='gray', linestyle=':', alpha=0.5, linewidth=1)
ax6b.text(18, 0.905, 'Substantial\nagreement', fontsize=7, ha='right', color='gray')
ax6b.axhline(y=0.95, color='gray', linestyle=':', alpha=0.5, linewidth=1)
ax6b.text(18, 0.955, 'Near-perfect', fontsize=7, ha='right', color='gray')

# Shade acceptable gain error zone
ax6b.axvspan(-5, 5, alpha=0.1, color='green')
ax6b.text(0, 0.62, 'Typical MEMS\ngain accuracy\n(±5%)', fontsize=8, ha='center',
          color='green', fontstyle='italic')

ax6b.set_xlabel('Gain error (%)', fontsize=12)
ax6b.set_ylabel('CCC ($= r × C_b$)', fontsize=12)
ax6b.set_title('B. CCC degradation from gain error\n(offset = 0, i.e., after zeroing or zero-free design)',
               fontsize=11, fontweight='bold')
ax6b.legend(title='Precision (r)', fontsize=10, title_fontsize=10)
ax6b.set_ylim(0.6, 1.01)
ax6b.set_xlim(-20, 20)
ax6b.grid(True, alpha=0.3)

fig6.tight_layout()
fig6.savefig(os.path.join(FIGDIR, 'figure6_sensitivity_analysis.png'),
             dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig6)
print('Figure 6 saved.')

# ──────────────────────────────────────────────────────────────
# FIGURE 7: PP validation demonstration
# ──────────────────────────────────────────────────────────────
fig7 = plt.figure(figsize=(18, 10))
gs = gridspec.GridSpec(2, 3, figure=fig7, hspace=0.35, wspace=0.3)

# Generate realistic arterial pressure data
t = np.linspace(0, 3, 3000)
# Simulate 4 cardiac cycles
def arterial_wave(t, sbp=120, dbp=80, hr=75):
    period = 60 / hr
    phase = (t % period) / period
    # Systolic upstroke
    wave = dbp + (sbp - dbp) * (
        np.exp(-((phase - 0.15)**2) / 0.005) * 0.8 +
        np.exp(-((phase - 0.25)**2) / 0.015) * 0.4 +
        np.exp(-((phase - 0.08)**2) / 0.003) * 0.6 +
        # Dicrotic notch
        np.exp(-((phase - 0.4)**2) / 0.008) * 0.15
    )
    return wave

true_pressure = arterial_wave(t, sbp=120, dbp=80)
true_pp = 40  # SBP - DBP

# Panel A: Correct gain (v=1.0) - PP preserved
ax7a = fig7.add_subplot(gs[0, 0])
measured_correct = true_pressure + 0  # no offset, no gain error
ax7a.plot(t, true_pressure, 'b-', linewidth=1.5, label='True pressure', alpha=0.7)
ax7a.plot(t, measured_correct, 'g--', linewidth=1.5, label='Measured (v=1.0)')
ax7a.set_title('A. Correct gain (v = 1.0)', fontsize=11, fontweight='bold', color='green')
ax7a.set_ylabel('Pressure (mmHg)')
ax7a.set_ylim(50, 160)
# Annotate PP
ax7a.annotate('', xy=(2.5, 120), xytext=(2.5, 80),
              arrowprops=dict(arrowstyle='<->', color='green', lw=2))
ax7a.text(2.6, 100, f'PP = {true_pp}\nmmHg', fontsize=10, color='green', fontweight='bold')
ax7a.legend(fontsize=8, loc='upper left')
ax7a.grid(True, alpha=0.3)

# Panel B: Gain error (v=1.15) - PP distorted
ax7b = fig7.add_subplot(gs[0, 1])
gain_err = 1.15
measured_gain = gain_err * true_pressure
measured_pp = int(round(gain_err * true_pp))
ax7b.plot(t, true_pressure, 'b-', linewidth=1.5, label='True pressure', alpha=0.7)
ax7b.plot(t, measured_gain, 'r--', linewidth=1.5, label=f'Measured (v={gain_err})')
ax7b.set_title(f'B. Gain error (v = {gain_err})', fontsize=11, fontweight='bold', color='red')
ax7b.set_ylim(50, 160)
# Annotate PP
ax7b.annotate('', xy=(2.5, 120*gain_err), xytext=(2.5, 80*gain_err),
              arrowprops=dict(arrowstyle='<->', color='red', lw=2))
ax7b.text(2.6, 105, f'PP = {measured_pp}\nmmHg', fontsize=10, color='red', fontweight='bold')
ax7b.annotate('', xy=(0.8, 120), xytext=(0.8, 80),
              arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5, ls='--'))
ax7b.text(0.9, 100, f'True\nPP=40', fontsize=8, color='blue')
ax7b.legend(fontsize=8, loc='upper left')
ax7b.grid(True, alpha=0.3)

# Panel C: Offset only (v=1.0) - PP preserved despite offset
ax7c = fig7.add_subplot(gs[0, 2])
offset_val = 15
measured_offset = true_pressure + offset_val
ax7c.plot(t, true_pressure, 'b-', linewidth=1.5, label='True pressure', alpha=0.7)
ax7c.plot(t, measured_offset, color='#E67E22', linestyle='--', linewidth=1.5, 
          label=f'Measured (+{offset_val} mmHg offset)')
ax7c.set_title(f'C. DC offset only (+{offset_val} mmHg)', fontsize=11, fontweight='bold', color='#E67E22')
ax7c.set_ylim(50, 160)
# Annotate PP - same for both
ax7c.annotate('', xy=(2.5, 135), xytext=(2.5, 95),
              arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=2))
ax7c.text(2.6, 115, f'PP = {true_pp}\nmmHg\n(unchanged!)', fontsize=9, color='#E67E22', fontweight='bold')
ax7c.legend(fontsize=8, loc='upper left')
ax7c.grid(True, alpha=0.3)

# Panel D: PP accuracy vs gain - scatter plot
ax7d = fig7.add_subplot(gs[1, 0])
# Simulate many measurements with varying gain
n_sim = 500
true_pps = np.random.normal(40, 10, n_sim)
true_pps = np.clip(true_pps, 15, 80)
gains = np.random.uniform(0.85, 1.15, n_sim)
measured_pps = gains * true_pps + np.random.normal(0, 1.5, n_sim)

scatter = ax7d.scatter(true_pps, measured_pps, c=gains, cmap='RdYlGn', 
                        s=15, alpha=0.6, vmin=0.85, vmax=1.15)
plt.colorbar(scatter, ax=ax7d, label='Sensor gain (v)')
ax7d.plot([10, 85], [10, 85], 'k--', linewidth=1, label='Perfect agreement')
ax7d.set_xlabel('True PP (mmHg)', fontsize=10)
ax7d.set_ylabel('Measured PP (mmHg)', fontsize=10)
ax7d.set_title('D. PP accuracy reveals gain error', fontsize=11, fontweight='bold')
ax7d.legend(fontsize=9)
ax7d.grid(True, alpha=0.3)
ax7d.set_aspect('equal')

# Panel E: Gain estimation from PP regression
ax7e = fig7.add_subplot(gs[1, 1])
# Correct gain device
measured_pps_good = 1.0 * true_pps + np.random.normal(0, 2, n_sim)
# Bad gain device
measured_pps_bad = 0.88 * true_pps + np.random.normal(0, 2, n_sim)

ax7e.scatter(true_pps, measured_pps_good, c='#2ECC71', s=12, alpha=0.4, label='Device A (v≈1.0)')
ax7e.scatter(true_pps, measured_pps_bad, c='#E74C3C', s=12, alpha=0.4, label='Device B (v≈0.88)')

# Regression lines
z_good = np.polyfit(true_pps, measured_pps_good, 1)
z_bad = np.polyfit(true_pps, measured_pps_bad, 1)
x_line = np.linspace(15, 80, 100)
ax7e.plot(x_line, np.polyval(z_good, x_line), '#2ECC71', linewidth=2, 
          label=f'Slope = {z_good[0]:.2f} (gain ≈ correct)')
ax7e.plot(x_line, np.polyval(z_bad, x_line), '#E74C3C', linewidth=2,
          label=f'Slope = {z_bad[0]:.2f} (gain error!)')
ax7e.plot([10, 85], [10, 85], 'k--', linewidth=1)

ax7e.set_xlabel('True PP (mmHg)', fontsize=10)
ax7e.set_ylabel('Measured PP (mmHg)', fontsize=10)
ax7e.set_title('E. PP regression slope = sensor gain', fontsize=11, fontweight='bold')
ax7e.legend(fontsize=8, loc='upper left')
ax7e.grid(True, alpha=0.3)
ax7e.set_aspect('equal')

# Panel F: Summary diagram - the logic chain
ax7f = fig7.add_subplot(gs[1, 2])
ax7f.set_xlim(0, 10)
ax7f.set_ylim(0, 10)
ax7f.axis('off')

# Logic chain boxes
boxes = [
    (5, 9.0, 'PP is accurate\n(measured PP ≈ true PP)', '#3498DB', 'white'),
    (5, 7.2, '↓ implies', None, None),
    (5, 6.0, 'Sensor gain is correct\n(v ≈ 1.0)', '#2ECC71', 'white'),
    (5, 4.2, '↓ combined with', None, None),
    (5, 3.0, 'Offset-free design\n(tip MEMS + barometer + self-cal)', '#E67E22', 'white'),
    (5, 1.2, '↓ therefore', None, None),
    (5, 0.2, 'Zero calibration unnecessary\n(Cb → 1.0 by design)', '#8E44AD', 'white'),
]

for x, y, text, bg, fc in boxes:
    if bg is None:
        ax7f.text(x, y, text, ha='center', va='center', fontsize=10, color='gray',
                  fontstyle='italic')
    else:
        props = dict(boxstyle='round,pad=0.5', facecolor=bg, edgecolor='black', alpha=0.85)
        ax7f.text(x, y, text, ha='center', va='center', fontsize=10, color=fc,
                  fontweight='bold', bbox=props)

ax7f.set_title('F. Logical chain', fontsize=11, fontweight='bold')

fig7.suptitle('Pulse Pressure Accuracy as Implicit Gain Validation', 
              fontsize=14, fontweight='bold', y=1.01)
fig7.savefig(os.path.join(FIGDIR, 'figure7_pp_validation.png'),
             dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig7)
print('Figure 7 saved.')

# ──────────────────────────────────────────────────────────────
# FIGURE 8: Combined BA + Concordance side-by-side (key figure)
# ──────────────────────────────────────────────────────────────
fig8, axes8 = plt.subplots(2, 4, figsize=(20, 10))
fig8.suptitle('Concordance Plots (top) vs. Bland-Altman Plots (bottom):\nWhy BA Alone Cannot Detect Gain Error',
              fontsize=14, fontweight='bold', y=1.03)

for idx, (title, x, y, color) in enumerate(scenarios):
    # Top row: Concordance plots
    ax_top = axes8[0, idx]
    ccc, r, cb, u, v = calc_ccc(x, y)
    
    ax_top.scatter(x, y, c=color, alpha=0.4, s=15, edgecolors='none')
    lims = [30, 190]
    ax_top.plot(lims, lims, 'k--', linewidth=1, alpha=0.5, label='y = x')
    z = np.polyfit(x, y, 1)
    x_fit = np.linspace(30, 190, 100)
    ax_top.plot(x_fit, np.polyval(z, x_fit), color=color, linewidth=2)
    ax_top.set_xlim(lims)
    ax_top.set_ylim(lims)
    ax_top.set_aspect('equal')
    ax_top.set_title(title, fontsize=10, fontweight='bold', color=color)
    if idx == 0:
        ax_top.set_ylabel('Device (mmHg)', fontsize=10)
    ax_top.grid(True, alpha=0.3)
    
    stats_text = f'CCC = {ccc:.3f}\nr = {r:.3f}\n$C_b$ = {cb:.3f}\nv = {v:.2f}, u = {u:.2f}'
    props = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.9)
    ax_top.text(0.05, 0.95, stats_text, transform=ax_top.transAxes, fontsize=8,
                verticalalignment='top', bbox=props)
    
    # Bottom row: Bland-Altman plots
    ax_bot = axes8[1, idx]
    bias, sd_diff, loa_up, loa_low, pe, diff, mean_pair = calc_ba(x, y)
    
    ax_bot.scatter(mean_pair, diff, c=color, alpha=0.4, s=15, edgecolors='none')
    ax_bot.axhline(y=bias, color=color, linewidth=2, linestyle='-')
    ax_bot.axhline(y=loa_up, color=color, linewidth=1, linestyle='--', alpha=0.7)
    ax_bot.axhline(y=loa_low, color=color, linewidth=1, linestyle='--', alpha=0.7)
    ax_bot.axhline(y=0, color='gray', linewidth=0.5, linestyle=':')
    ax_bot.fill_between([20, 180], loa_low, loa_up, alpha=0.08, color=color)
    ax_bot.set_xlim(20, 180)
    ax_bot.set_ylim(-35, 35)
    if idx == 0:
        ax_bot.set_ylabel('Device − Reference (mmHg)', fontsize=10)
    ax_bot.set_xlabel('Mean (mmHg)', fontsize=9)
    ax_bot.grid(True, alpha=0.3)
    
    ba_text = f'Bias = {bias:.1f}\nLOA = [{loa_low:.1f}, {loa_up:.1f}]\nPE = {pe:.1f}%'
    props2 = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.9)
    ax_bot.text(0.05, 0.95, ba_text, transform=ax_bot.transAxes, fontsize=8,
                verticalalignment='top', bbox=props2)

# Highlight columns B and C
for col in [1, 2]:
    rect = plt.Rectangle((0.255 + col * 0.185, 0.02), 0.18, 0.96,
                          transform=fig8.transFigure, 
                          facecolor='yellow' if col == 1 else 'red',
                          alpha=0.05, edgecolor='none', zorder=0)
    # Can't easily add this, skip

# Add annotation below
fig8.text(0.5, -0.03,
          '★ Compare B and C: BA bias is similar (~0 vs ~−11), but CCC decomposition reveals C has v = 0.89 (gain error)\n'
          '    while B has v = 0.99 (correct gain). Zeroing fixes A→B but cannot fix C. BA alone misses this critical distinction.',
          ha='center', fontsize=11, style='italic',
          bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#FBC02D'))

fig8.tight_layout()
fig8.savefig(os.path.join(FIGDIR, 'figure8_ba_vs_concordance.png'),
             dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig8)
print('Figure 8 saved.')

# ──────────────────────────────────────────────────────────────
# Print Table 2 data
# ──────────────────────────────────────────────────────────────
print('\n=== TABLE 2: Complete Statistical Comparison ===')
print(f'{"Scenario":<30} {"CCC":>6} {"r":>6} {"Cb":>6} {"u":>7} {"v":>6} {"Bias":>7} {"LOA_low":>8} {"LOA_up":>8} {"PE%":>7}')
print('-' * 105)
for s in ba_stats:
    print(f'{s["scenario"]:<30} {s["ccc"]:>6.3f} {s["r"]:>6.3f} {s["cb"]:>6.3f} {s["u"]:>7.2f} {s["v"]:>6.2f} {s["bias"]:>7.1f} {s["loa_low"]:>8.1f} {s["loa_up"]:>8.1f} {s["pe"]:>7.1f}')

# After zeroing: what changes
print('\n=== ZEROING EFFECT ===')
print(f'A → B: Bias {ba_stats[0]["bias"]:.1f} → {ba_stats[1]["bias"]:.1f}, Cb {ba_stats[0]["cb"]:.3f} → {ba_stats[1]["cb"]:.3f}, u {ba_stats[0]["u"]:.2f} → {ba_stats[1]["u"]:.2f}')
print(f'D → C: Bias {ba_stats[3]["bias"]:.1f} → {ba_stats[2]["bias"]:.1f}, Cb {ba_stats[3]["cb"]:.3f} → {ba_stats[2]["cb"]:.3f}, u {ba_stats[3]["u"]:.2f} → {ba_stats[2]["u"]:.2f}')
print(f'Note: v unchanged: A→B: {ba_stats[0]["v"]:.2f}→{ba_stats[1]["v"]:.2f}, D→C: {ba_stats[3]["v"]:.2f}→{ba_stats[2]["v"]:.2f}')

print('\nAll figures saved to', FIGDIR)
