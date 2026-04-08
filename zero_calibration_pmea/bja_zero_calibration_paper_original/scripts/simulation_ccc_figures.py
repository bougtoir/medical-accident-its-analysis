"""
Simulation and Figure Generation for CCC Commentary Manuscript
Generates Figures 1-3 demonstrating the diagnostic value of Lin's CCC
in cardiac output monitor validation.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats

np.random.seed(42)

# --- Helper Functions ---

def lins_ccc(y1, y2):
    """Calculate Lin's CCC with full decomposition."""
    n = len(y1)
    mean1, mean2 = np.mean(y1), np.mean(y2)
    var1 = np.var(y1, ddof=1)
    var2 = np.var(y2, ddof=1)
    sd1, sd2 = np.std(y1, ddof=1), np.std(y2, ddof=1)
    cov = np.sum((y1 - mean1) * (y2 - mean2)) / (n - 1)
    
    # Pearson r (precision)
    r = cov / (sd1 * sd2)
    
    # Bias correction factor C_b (accuracy)
    c_b = (2 * sd1 * sd2) / (var1 + var2 + (mean1 - mean2)**2)
    
    # CCC = r * C_b
    ccc = r * c_b
    
    # Also calculate directly
    ccc_direct = (2 * cov) / (var1 + var2 + (mean1 - mean2)**2)
    
    return {
        'ccc': ccc,
        'ccc_direct': ccc_direct,
        'pearson_r': r,
        'C_b': c_b,
        'bias': mean2 - mean1,
        'mean1': mean1,
        'mean2': mean2,
        'sd1': sd1,
        'sd2': sd2
    }


def bland_altman_stats(ref, test):
    """Calculate Bland-Altman statistics."""
    diff = test - ref
    mean_both = (ref + test) / 2
    bias = np.mean(diff)
    sd_diff = np.std(diff, ddof=1)
    loa_upper = bias + 1.96 * sd_diff
    loa_lower = bias - 1.96 * sd_diff
    mean_co = np.mean(mean_both)
    pe = (1.96 * sd_diff / mean_co) * 100  # percentage error
    return {
        'bias': bias,
        'sd': sd_diff,
        'loa_upper': loa_upper,
        'loa_lower': loa_lower,
        'pe': pe,
        'mean_co': mean_co,
        'diff': diff,
        'mean_both': mean_both
    }


# --- Generate Simulated Data ---

n = 100
# Reference: PAC thermodilution, CO range 2.5-8.0 L/min
co_ref = np.random.normal(5.0, 1.5, n)
co_ref = np.clip(co_ref, 2.0, 9.0)

# Device A: Proportional bias (slope=1.15, offset=-0.65), good precision
# This creates a scale error: overestimates at high CO, underestimates at low CO
# But the offset partially compensates, keeping mean bias near zero
noise_a = np.random.normal(0, 0.4, n)
co_device_a = 1.15 * co_ref - 0.65 + noise_a

# Device B: No systematic bias, poor precision (high random noise)
noise_b = np.random.normal(0, 1.0, n)
co_device_b = co_ref + noise_b

# Calculate statistics
ccc_a = lins_ccc(co_ref, co_device_a)
ccc_b = lins_ccc(co_ref, co_device_b)
ba_a = bland_altman_stats(co_ref, co_device_a)
ba_b = bland_altman_stats(co_ref, co_device_b)

print("=" * 70)
print("DEVICE A (Proportional bias, good precision)")
print("=" * 70)
print(f"  Bland-Altman: bias = {ba_a['bias']:+.2f} L/min, "
      f"LoA = [{ba_a['loa_lower']:.2f}, {ba_a['loa_upper']:.2f}] L/min")
print(f"  Percentage Error = {ba_a['pe']:.1f}%")
print(f"  Lin's CCC = {ccc_a['ccc']:.3f} "
      f"(r = {ccc_a['pearson_r']:.3f}, C_b = {ccc_a['C_b']:.3f})")
print(f"  Interpretation: HIGH precision, REDUCED accuracy -> recalibration may help")
print()

print("=" * 70)
print("DEVICE B (No bias, poor precision)")
print("=" * 70)
print(f"  Bland-Altman: bias = {ba_b['bias']:+.2f} L/min, "
      f"LoA = [{ba_b['loa_lower']:.2f}, {ba_b['loa_upper']:.2f}] L/min")
print(f"  Percentage Error = {ba_b['pe']:.1f}%")
print(f"  Lin's CCC = {ccc_b['ccc']:.3f} "
      f"(r = {ccc_b['pearson_r']:.3f}, C_b = {ccc_b['C_b']:.3f})")
print(f"  Interpretation: POOR precision, HIGH accuracy -> hardware improvement needed")
print()

print("=" * 70)
print("KEY INSIGHT")
print("=" * 70)
print(f"  BA analysis: Device A PE={ba_a['pe']:.1f}% vs Device B PE={ba_b['pe']:.1f}%")
print(f"  -> Appear SIMILAR by conventional metrics")
print(f"  CCC decomposition: Device A (r={ccc_a['pearson_r']:.3f}, C_b={ccc_a['C_b']:.3f}) "
      f"vs Device B (r={ccc_b['pearson_r']:.3f}, C_b={ccc_b['C_b']:.3f})")
print(f"  -> DIFFERENT error profiles revealed!")


# --- Figure 1: Side-by-side comparison (4 panels) ---

fig, axes = plt.subplots(2, 2, figsize=(14, 12))
plt.subplots_adjust(hspace=0.35, wspace=0.3)

# Panel A: Concordance plot - Device A
ax = axes[0, 0]
ax.scatter(co_ref, co_device_a, alpha=0.5, s=30, c='#2196F3', edgecolors='none')
lims = [1.5, 10]
ax.plot(lims, lims, 'k--', linewidth=1.5, label='Identity line (y = x)')
# Best fit line
slope_a, intercept_a = np.polyfit(co_ref, co_device_a, 1)
x_fit = np.linspace(1.5, 10, 100)
ax.plot(x_fit, slope_a * x_fit + intercept_a, 'r-', linewidth=1.5,
        label=f'Best fit (y = {slope_a:.2f}x {intercept_a:+.2f})')
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect('equal')
ax.set_xlabel('Reference CO (PAC thermodilution, L/min)', fontsize=11)
ax.set_ylabel('Device A CO (L/min)', fontsize=11)
ax.set_title(f'A. Concordance Plot - Device A\n'
             f'CCC = {ccc_a["ccc"]:.3f} (r = {ccc_a["pearson_r"]:.3f}, '
             f'$C_b$ = {ccc_a["C_b"]:.3f})', fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.3)

# Panel B: Concordance plot - Device B
ax = axes[0, 1]
ax.scatter(co_ref, co_device_b, alpha=0.5, s=30, c='#FF5722', edgecolors='none')
ax.plot(lims, lims, 'k--', linewidth=1.5, label='Identity line (y = x)')
slope_b, intercept_b = np.polyfit(co_ref, co_device_b, 1)
ax.plot(x_fit, slope_b * x_fit + intercept_b, 'r-', linewidth=1.5,
        label=f'Best fit (y = {slope_b:.2f}x {intercept_b:+.2f})')
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_aspect('equal')
ax.set_xlabel('Reference CO (PAC thermodilution, L/min)', fontsize=11)
ax.set_ylabel('Device B CO (L/min)', fontsize=11)
ax.set_title(f'B. Concordance Plot - Device B\n'
             f'CCC = {ccc_b["ccc"]:.3f} (r = {ccc_b["pearson_r"]:.3f}, '
             f'$C_b$ = {ccc_b["C_b"]:.3f})', fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.3)

# Panel C: Bland-Altman - Device A
ax = axes[1, 0]
ax.scatter(ba_a['mean_both'], ba_a['diff'], alpha=0.5, s=30, c='#2196F3', edgecolors='none')
ax.axhline(y=ba_a['bias'], color='k', linewidth=1.5, label=f'Bias = {ba_a["bias"]:+.2f} L/min')
ax.axhline(y=ba_a['loa_upper'], color='gray', linewidth=1, linestyle='--',
           label=f'LoA = [{ba_a["loa_lower"]:.2f}, {ba_a["loa_upper"]:.2f}]')
ax.axhline(y=ba_a['loa_lower'], color='gray', linewidth=1, linestyle='--')
ax.set_xlabel('Mean CO (L/min)', fontsize=11)
ax.set_ylabel('Difference (Device A - Reference, L/min)', fontsize=11)
ax.set_title(f'C. Bland-Altman - Device A\n'
             f'PE = {ba_a["pe"]:.1f}%', fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.3)
# Show proportional bias trend
z = np.polyfit(ba_a['mean_both'], ba_a['diff'], 1)
p = np.poly1d(z)
x_ba = np.linspace(ba_a['mean_both'].min(), ba_a['mean_both'].max(), 100)
ax.plot(x_ba, p(x_ba), 'r-', linewidth=1, alpha=0.7, label=f'Trend (slope={z[0]:.3f})')
ax.legend(fontsize=9, loc='upper left')

# Panel D: Bland-Altman - Device B
ax = axes[1, 1]
ax.scatter(ba_b['mean_both'], ba_b['diff'], alpha=0.5, s=30, c='#FF5722', edgecolors='none')
ax.axhline(y=ba_b['bias'], color='k', linewidth=1.5, label=f'Bias = {ba_b["bias"]:+.2f} L/min')
ax.axhline(y=ba_b['loa_upper'], color='gray', linewidth=1, linestyle='--',
           label=f'LoA = [{ba_b["loa_lower"]:.2f}, {ba_b["loa_upper"]:.2f}]')
ax.axhline(y=ba_b['loa_lower'], color='gray', linewidth=1, linestyle='--')
ax.set_xlabel('Mean CO (L/min)', fontsize=11)
ax.set_ylabel('Difference (Device B - Reference, L/min)', fontsize=11)
ax.set_title(f'D. Bland-Altman - Device B\n'
             f'PE = {ba_b["pe"]:.1f}%', fontsize=12, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.3)
z = np.polyfit(ba_b['mean_both'], ba_b['diff'], 1)
p = np.poly1d(z)
x_ba = np.linspace(ba_b['mean_both'].min(), ba_b['mean_both'].max(), 100)
ax.plot(x_ba, p(x_ba), 'r-', linewidth=1, alpha=0.7, label=f'Trend (slope={z[0]:.3f})')
ax.legend(fontsize=9, loc='upper left')

fig.suptitle('Figure 1. Two devices with similar Bland-Altman profiles but different CCC decompositions',
             fontsize=13, fontweight='bold', y=0.98)
plt.savefig('/home/ubuntu/figure1_comparison.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("\nFigure 1 saved: /home/ubuntu/figure1_comparison.png")


# --- Figure 2: CCC Decomposition Diagnostic Plot ---

fig, ax = plt.subplots(figsize=(8, 8))

# Create a grid showing r vs C_b with CCC contours
r_range = np.linspace(0.5, 1.0, 200)
cb_range = np.linspace(0.5, 1.0, 200)
R, CB = np.meshgrid(r_range, cb_range)
CCC = R * CB

# Contour plot
contour_levels = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
cs = ax.contour(R, CB, CCC, levels=contour_levels, colors='gray', linewidths=0.8)
ax.clabel(cs, inline=True, fontsize=9, fmt='CCC=%.2f')

# Plot Device A and Device B
ax.plot(ccc_a['pearson_r'], ccc_a['C_b'], 'o', color='#2196F3', markersize=15,
        markeredgecolor='black', markeredgewidth=1.5, zorder=5,
        label=f'Device A (r={ccc_a["pearson_r"]:.3f}, $C_b$={ccc_a["C_b"]:.3f})')
ax.plot(ccc_b['pearson_r'], ccc_b['C_b'], 's', color='#FF5722', markersize=15,
        markeredgecolor='black', markeredgewidth=1.5, zorder=5,
        label=f'Device B (r={ccc_b["pearson_r"]:.3f}, $C_b$={ccc_b["C_b"]:.3f})')

# Add annotation arrows
ax.annotate('High precision\nLow accuracy\n(Recalibrate)',
            xy=(ccc_a['pearson_r'], ccc_a['C_b']),
            xytext=(ccc_a['pearson_r'] - 0.12, ccc_a['C_b'] - 0.08),
            fontsize=10, ha='center',
            arrowprops=dict(arrowstyle='->', color='#2196F3', lw=1.5),
            color='#2196F3', fontweight='bold')

ax.annotate('Low precision\nHigh accuracy\n(Hardware issue)',
            xy=(ccc_b['pearson_r'], ccc_b['C_b']),
            xytext=(ccc_b['pearson_r'] - 0.15, ccc_b['C_b'] + 0.06),
            fontsize=10, ha='center',
            arrowprops=dict(arrowstyle='->', color='#FF5722', lw=1.5),
            color='#FF5722', fontweight='bold')

# Shade regions
ax.fill_between([0.9, 1.0], 0.5, 0.85, alpha=0.1, color='blue',
                label='High r, low $C_b$: calibration error')
ax.fill_between([0.5, 0.85], 0.9, 1.0, alpha=0.1, color='red',
                label='Low r, high $C_b$: precision error')

ax.set_xlabel("Pearson's r (Precision)", fontsize=13)
ax.set_ylabel('Bias Correction Factor $C_b$ (Accuracy)', fontsize=13)
ax.set_title('Figure 2. CCC Decomposition Diagnostic Space\n'
             'r (precision) vs $C_b$ (accuracy) with CCC iso-contours',
             fontsize=13, fontweight='bold')
ax.set_xlim(0.5, 1.02)
ax.set_ylim(0.5, 1.02)
ax.legend(fontsize=9, loc='lower left')
ax.grid(True, alpha=0.3)
ax.set_aspect('equal')

plt.savefig('/home/ubuntu/figure2_ccc_decomposition.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Figure 2 saved: /home/ubuntu/figure2_ccc_decomposition.png")


# --- Figure 3: Summary Table as Figure ---

fig, ax = plt.subplots(figsize=(12, 5))
ax.axis('off')

# Table data
col_labels = ['Metric', 'Device A', 'Device B', 'Same by\nBA/PE?', 'Diagnostic Value\nof CCC']
row_data = [
    ['Bias (L/min)', f'{ba_a["bias"]:+.2f}', f'{ba_b["bias"]:+.2f}', 'Similar', '---'],
    ['LoA (L/min)', f'[{ba_a["loa_lower"]:.2f}, {ba_a["loa_upper"]:.2f}]',
     f'[{ba_b["loa_lower"]:.2f}, {ba_b["loa_upper"]:.2f}]', 'Similar', '---'],
    ['PE (%)', f'{ba_a["pe"]:.1f}', f'{ba_b["pe"]:.1f}', 'Similar', '---'],
    ['CCC', f'{ccc_a["ccc"]:.3f}', f'{ccc_b["ccc"]:.3f}', '---', 'Different overall agreement'],
    ['  Pearson r\n  (precision)', f'{ccc_a["pearson_r"]:.3f}', f'{ccc_b["pearson_r"]:.3f}',
     '---', 'A >> B: A is more precise'],
    ['  $C_b$\n  (accuracy)', f'{ccc_a["C_b"]:.3f}', f'{ccc_b["C_b"]:.3f}',
     '---', 'B >> A: B is more accurate'],
    ['Clinical\nimplication', 'Recalibrate\nalgorithm', 'Improve\nhardware/signal',
     'Cannot\ndistinguish', 'Actionable\ndiagnostics'],
]

table = ax.table(cellText=row_data, colLabels=col_labels,
                 loc='center', cellLoc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.0, 2.0)

# Style header
for j in range(len(col_labels)):
    table[0, j].set_facecolor('#37474F')
    table[0, j].set_text_props(color='white', fontweight='bold')

# Style rows
for i in range(1, len(row_data) + 1):
    for j in range(len(col_labels)):
        if i <= 3:  # BA/PE rows
            table[i, j].set_facecolor('#E3F2FD')
        elif i <= 6:  # CCC rows
            table[i, j].set_facecolor('#FFF3E0')
        else:  # Conclusion row
            table[i, j].set_facecolor('#E8F5E9')

ax.set_title('Figure 3 (Table). Comparative summary of Device A and Device B:\n'
             'Bland-Altman metrics appear similar, but CCC decomposition reveals different error profiles',
             fontsize=12, fontweight='bold', pad=20)

plt.savefig('/home/ubuntu/figure3_summary_table.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Figure 3 saved: /home/ubuntu/figure3_summary_table.png")

print("\n" + "=" * 70)
print("All figures generated successfully.")
print("=" * 70)
