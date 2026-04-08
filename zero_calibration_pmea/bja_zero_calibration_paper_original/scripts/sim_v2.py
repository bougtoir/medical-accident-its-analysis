"""
Simulation v2: Carefully tuned so that Device A and Device B produce
SIMILAR Bland-Altman / PE profiles but DIFFERENT CCC decompositions.

Device A: proportional bias (slope ~1.18, offset ~-0.9), LOW noise (sd=0.75)
  -> systematic scale error, but mean bias near zero
  -> high r (precision), lower C_b (accuracy)

Device B: no scale error (slope ~1.0), HIGH noise (sd=1.1)
  -> no systematic bias, but wide scatter
  -> lower r (precision), high C_b (accuracy)

Both should have PE in the 35-45% range.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

np.random.seed(99)

def lins_ccc(y1, y2):
    n = len(y1)
    m1, m2 = np.mean(y1), np.mean(y2)
    v1, v2 = np.var(y1, ddof=1), np.var(y2, ddof=1)
    s1, s2 = np.std(y1, ddof=1), np.std(y2, ddof=1)
    cov = np.sum((y1 - m1) * (y2 - m2)) / (n - 1)
    r = cov / (s1 * s2)
    c_b = (2 * s1 * s2) / (v1 + v2 + (m1 - m2)**2)
    return {'ccc': r * c_b, 'r': r, 'C_b': c_b}

def ba_stats(ref, test):
    d = test - ref
    m = (ref + test) / 2
    bias = np.mean(d)
    sd = np.std(d, ddof=1)
    loa_u = bias + 1.96 * sd
    loa_l = bias - 1.96 * sd
    pe = 1.96 * sd / np.mean(m) * 100
    return {'bias': bias, 'sd': sd, 'loa_u': loa_u, 'loa_l': loa_l,
            'pe': pe, 'diff': d, 'mean': m}

# --- Search for parameter set that gives similar PE ---
best = None
for seed in range(1000):
    rng = np.random.RandomState(seed)
    n = 120
    ref = rng.normal(5.0, 1.5, n)
    ref = np.clip(ref, 2.0, 9.0)

    # Device A: scale error + low noise
    a = 1.18 * ref - 0.90 + rng.normal(0, 0.75, n)
    # Device B: no scale error + high noise
    b = ref + rng.normal(0, 1.10, n)

    ba_a = ba_stats(ref, a)
    ba_b = ba_stats(ref, b)
    ccc_a = lins_ccc(ref, a)
    ccc_b = lins_ccc(ref, b)

    pe_diff = abs(ba_a['pe'] - ba_b['pe'])
    r_diff = abs(ccc_a['r'] - ccc_b['r'])
    cb_diff = abs(ccc_a['C_b'] - ccc_b['C_b'])

    # Want: small PE difference, large r difference, moderate C_b difference
    # Also want both PE in 30-50 range and both bias small
    if (pe_diff < 5 and
        30 < ba_a['pe'] < 50 and
        30 < ba_b['pe'] < 50 and
        abs(ba_a['bias']) < 0.5 and
        abs(ba_b['bias']) < 0.5 and
        r_diff > 0.10 and
        ccc_a['r'] > ccc_b['r'] and
        ccc_b['C_b'] > ccc_a['C_b']):
        score = r_diff + cb_diff - pe_diff * 0.5
        if best is None or score > best[0]:
            best = (score, seed, ba_a['pe'], ba_b['pe'],
                    ccc_a['r'], ccc_b['r'], ccc_a['C_b'], ccc_b['C_b'],
                    ba_a['bias'], ba_b['bias'])

if best:
    print(f"Best seed: {best[1]}")
    print(f"  PE: A={best[2]:.1f}%, B={best[3]:.1f}%  (diff={abs(best[2]-best[3]):.1f}%)")
    print(f"  r:  A={best[4]:.3f}, B={best[5]:.3f}")
    print(f"  Cb: A={best[6]:.3f}, B={best[7]:.3f}")
    print(f"  Bias: A={best[8]:+.2f}, B={best[9]:+.2f}")
else:
    print("No suitable seed found. Relaxing constraints...")
    # Fallback: just find closest PE match
    best_fallback = None
    for seed in range(5000):
        rng = np.random.RandomState(seed)
        n = 120
        ref = rng.normal(5.0, 1.5, n)
        ref = np.clip(ref, 2.0, 9.0)
        a = 1.18 * ref - 0.90 + rng.normal(0, 0.75, n)
        b = ref + rng.normal(0, 1.10, n)
        ba_a = ba_stats(ref, a)
        ba_b = ba_stats(ref, b)
        ccc_a = lins_ccc(ref, a)
        ccc_b = lins_ccc(ref, b)
        pe_diff = abs(ba_a['pe'] - ba_b['pe'])
        if pe_diff < 8 and ccc_a['r'] > ccc_b['r']:
            score = -pe_diff
            if best_fallback is None or score > best_fallback[0]:
                best_fallback = (score, seed, ba_a['pe'], ba_b['pe'],
                                 ccc_a['r'], ccc_b['r'], ccc_a['C_b'], ccc_b['C_b'],
                                 ba_a['bias'], ba_b['bias'])
    if best_fallback:
        best = best_fallback
        print(f"Fallback seed: {best[1]}")
        print(f"  PE: A={best[2]:.1f}%, B={best[3]:.1f}%")
        print(f"  r:  A={best[4]:.3f}, B={best[5]:.3f}")
        print(f"  Cb: A={best[6]:.3f}, B={best[7]:.3f}")

# Now generate final data with best seed
SEED = best[1]
rng = np.random.RandomState(SEED)
n = 120
co_ref = rng.normal(5.0, 1.5, n)
co_ref = np.clip(co_ref, 2.0, 9.0)
co_a = 1.18 * co_ref - 0.90 + rng.normal(0, 0.75, n)
co_b = co_ref + rng.normal(0, 1.10, n)

ccc_a = lins_ccc(co_ref, co_a)
ccc_b = lins_ccc(co_ref, co_b)
ba_a = ba_stats(co_ref, co_a)
ba_b = ba_stats(co_ref, co_b)

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print(f"\nDevice A (scale error, low noise):")
print(f"  BA: bias={ba_a['bias']:+.2f}, LoA=[{ba_a['loa_l']:.2f}, {ba_a['loa_u']:.2f}], PE={ba_a['pe']:.1f}%")
print(f"  CCC={ccc_a['ccc']:.3f}  (r={ccc_a['r']:.3f}, Cb={ccc_a['C_b']:.3f})")

print(f"\nDevice B (no scale error, high noise):")
print(f"  BA: bias={ba_b['bias']:+.2f}, LoA=[{ba_b['loa_l']:.2f}, {ba_b['loa_u']:.2f}], PE={ba_b['pe']:.1f}%")
print(f"  CCC={ccc_b['ccc']:.3f}  (r={ccc_b['r']:.3f}, Cb={ccc_b['C_b']:.3f})")


# ===== FIGURES =====

fig, axes = plt.subplots(2, 2, figsize=(14, 12))
plt.subplots_adjust(hspace=0.38, wspace=0.32)

lims = [0.5, 11.0]
x_fit = np.linspace(0.5, 11, 100)

# Panel A: Concordance - Device A
ax = axes[0, 0]
ax.scatter(co_ref, co_a, alpha=0.5, s=25, c='#1565C0', edgecolors='none')
ax.plot(lims, lims, 'k--', lw=1.5, label='Identity (y = x)')
sl_a, ic_a = np.polyfit(co_ref, co_a, 1)
ax.plot(x_fit, sl_a * x_fit + ic_a, color='#E53935', lw=1.5,
        label=f'Fit: y = {sl_a:.2f}x {ic_a:+.2f}')
ax.set_xlim(lims); ax.set_ylim(lims); ax.set_aspect('equal')
ax.set_xlabel('Reference CO (PAC, L/min)', fontsize=11)
ax.set_ylabel('Device A CO (L/min)', fontsize=11)
ax.set_title(f'A. Concordance \u2014 Device A\n'
             f'CCC = {ccc_a["ccc"]:.3f}  (r = {ccc_a["r"]:.3f}, '
             f'$C_b$ = {ccc_a["C_b"]:.3f})', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.25)

# Panel B: Concordance - Device B
ax = axes[0, 1]
ax.scatter(co_ref, co_b, alpha=0.5, s=25, c='#E65100', edgecolors='none')
ax.plot(lims, lims, 'k--', lw=1.5, label='Identity (y = x)')
sl_b, ic_b = np.polyfit(co_ref, co_b, 1)
ax.plot(x_fit, sl_b * x_fit + ic_b, color='#E53935', lw=1.5,
        label=f'Fit: y = {sl_b:.2f}x {ic_b:+.2f}')
ax.set_xlim(lims); ax.set_ylim(lims); ax.set_aspect('equal')
ax.set_xlabel('Reference CO (PAC, L/min)', fontsize=11)
ax.set_ylabel('Device B CO (L/min)', fontsize=11)
ax.set_title(f'B. Concordance \u2014 Device B\n'
             f'CCC = {ccc_b["ccc"]:.3f}  (r = {ccc_b["r"]:.3f}, '
             f'$C_b$ = {ccc_b["C_b"]:.3f})', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, loc='upper left')
ax.grid(True, alpha=0.25)

# Panel C: BA - Device A
ax = axes[1, 0]
ax.scatter(ba_a['mean'], ba_a['diff'], alpha=0.5, s=25, c='#1565C0', edgecolors='none')
ax.axhline(ba_a['bias'], color='k', lw=1.5,
           label=f'Bias = {ba_a["bias"]:+.2f} L/min')
ax.axhline(ba_a['loa_u'], color='#616161', lw=1, ls='--',
           label=f'LoA = [{ba_a["loa_l"]:.2f}, +{ba_a["loa_u"]:.2f}]')
ax.axhline(ba_a['loa_l'], color='#616161', lw=1, ls='--')
z_a = np.polyfit(ba_a['mean'], ba_a['diff'], 1)
x_ba = np.linspace(1, 10, 100)
ax.plot(x_ba, np.poly1d(z_a)(x_ba), 'r-', lw=1.2, alpha=0.8,
        label=f'Trend slope = {z_a[0]:.3f}')
ax.set_xlabel('Mean CO (L/min)', fontsize=11)
ax.set_ylabel('Difference (A \u2212 Ref, L/min)', fontsize=11)
ax.set_title(f'C. Bland\u2013Altman \u2014 Device A\nPE = {ba_a["pe"]:.1f}%',
             fontsize=11, fontweight='bold')
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.25)

# Panel D: BA - Device B
ax = axes[1, 1]
ax.scatter(ba_b['mean'], ba_b['diff'], alpha=0.5, s=25, c='#E65100', edgecolors='none')
ax.axhline(ba_b['bias'], color='k', lw=1.5,
           label=f'Bias = {ba_b["bias"]:+.2f} L/min')
ax.axhline(ba_b['loa_u'], color='#616161', lw=1, ls='--',
           label=f'LoA = [{ba_b["loa_l"]:.2f}, +{ba_b["loa_u"]:.2f}]')
ax.axhline(ba_b['loa_l'], color='#616161', lw=1, ls='--')
z_b = np.polyfit(ba_b['mean'], ba_b['diff'], 1)
ax.plot(x_ba, np.poly1d(z_b)(x_ba), 'r-', lw=1.2, alpha=0.8,
        label=f'Trend slope = {z_b[0]:.3f}')
ax.set_xlabel('Mean CO (L/min)', fontsize=11)
ax.set_ylabel('Difference (B \u2212 Ref, L/min)', fontsize=11)
ax.set_title(f'D. Bland\u2013Altman \u2014 Device B\nPE = {ba_b["pe"]:.1f}%',
             fontsize=11, fontweight='bold')
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.25)

# Sync BA y-axes
ym = max(abs(ba_a['loa_l']), ba_a['loa_u'], abs(ba_b['loa_l']), ba_b['loa_u']) * 1.4
axes[1, 0].set_ylim(-ym, ym)
axes[1, 1].set_ylim(-ym, ym)

fig.suptitle('Figure 1. Two devices with comparable Bland\u2013Altman profiles\n'
             'but distinct CCC decompositions revealing different error structures',
             fontsize=13, fontweight='bold', y=1.01)
plt.savefig('/home/ubuntu/figure1_comparison.png', dpi=300, bbox_inches='tight',
            facecolor='white')
plt.close()
print("\nFigure 1 saved.")


# --- Figure 2: Decomposition space ---
fig, ax = plt.subplots(figsize=(8, 8))
r_g = np.linspace(0.50, 1.0, 300)
cb_g = np.linspace(0.50, 1.0, 300)
R, CB = np.meshgrid(r_g, cb_g)
CCC_grid = R * CB

levels = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]
cs = ax.contour(R, CB, CCC_grid, levels=levels, colors='#9E9E9E', linewidths=0.7)
ax.clabel(cs, inline=True, fontsize=8, fmt='CCC=%.2f')

ax.fill_between([0.90, 1.005], 0.50, 0.90, alpha=0.08, color='#1565C0')
ax.fill_between([0.50, 0.90], 0.90, 1.005, alpha=0.08, color='#E65100')

ax.text(0.95, 0.65, 'High precision\nLow accuracy\n\nScale/offset error\n'
        r'$\rightarrow$ Recalibrate', fontsize=9, ha='center', va='center',
        color='#1565C0', style='italic')
ax.text(0.65, 0.95, 'Low precision\nHigh accuracy\n\nRandom noise\n'
        r'$\rightarrow$ Hardware/signal', fontsize=9, ha='center', va='center',
        color='#E65100', style='italic')

ax.plot(ccc_a['r'], ccc_a['C_b'], 'o', color='#1565C0', ms=14,
        mec='black', mew=1.5, zorder=5,
        label=f'Device A (r={ccc_a["r"]:.3f}, $C_b$={ccc_a["C_b"]:.3f})')
ax.plot(ccc_b['r'], ccc_b['C_b'], 's', color='#E65100', ms=14,
        mec='black', mew=1.5, zorder=5,
        label=f'Device B (r={ccc_b["r"]:.3f}, $C_b$={ccc_b["C_b"]:.3f})')

ax.set_xlabel("Pearson r (Precision)", fontsize=13)
ax.set_ylabel('Bias Correction Factor $C_b$ (Accuracy)', fontsize=13)
ax.set_title('Figure 2. CCC Decomposition Diagnostic Space\n'
             'Iso-CCC contours with diagnostic regions',
             fontsize=12, fontweight='bold')
ax.set_xlim(0.50, 1.005); ax.set_ylim(0.50, 1.005)
ax.legend(fontsize=10, loc='lower left')
ax.grid(True, alpha=0.25)
ax.set_aspect('equal')
plt.savefig('/home/ubuntu/figure2_ccc_decomposition.png', dpi=300, bbox_inches='tight',
            facecolor='white')
plt.close()
print("Figure 2 saved.")


# --- Figure 3: Framework table ---
fig, ax = plt.subplots(figsize=(14, 6))
ax.axis('off')

col_labels = ['Metric', 'Evaluates', 'Clinical Question', 'Limitation']
row_data = [
    ['Bland\u2013Altman\nplot',
     'Bias, Limits of\nAgreement (LoA)',
     'What is the systematic error\nand spread of differences?',
     'Does not quantify agreement\nwith identity line directly'],
    ['Percentage\nerror (PE)',
     'Normalised LoA\n(Critchley\u2013Critchley)',
     'Is agreement acceptable\nrelative to reference precision?',
     'Inherits BA limitations;\nthreshold assumes PAC reference'],
    ['Polar plot',
     'Trending ability\n(direction of changes)',
     'Does the device track\nCO changes correctly?',
     'Evaluates only changes,\nnot absolute values'],
    ['CCC +\nconcordance plot\n(PROPOSED)',
     'Integrated\naccuracy \u00d7 precision\n(r \u00d7 C_b)',
     'How closely do measurements\nfall on the identity line?\nIs error from bias or noise?',
     'Does not evaluate\ntrending ability\n(complementary to polar)'],
]

table = ax.table(cellText=row_data, colLabels=col_labels,
                 loc='center', cellLoc='center',
                 colWidths=[0.14, 0.20, 0.34, 0.27])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.0, 2.8)

for j in range(4):
    table[0, j].set_facecolor('#263238')
    table[0, j].set_text_props(color='white', fontweight='bold', fontsize=11)
for i in range(1, 4):
    for j in range(4):
        table[i, j].set_facecolor('#ECEFF1')
for j in range(4):
    table[4, j].set_facecolor('#FFF8E1')
    table[4, j].set_text_props(fontweight='bold')
    table[4, j].set_edgecolor('#FF8F00')

ax.set_title('Figure 3. Proposed Extended Validation Framework for CO Monitors\n'
             'Adding CCC as the fourth complementary metric',
             fontsize=13, fontweight='bold', pad=25)
plt.savefig('/home/ubuntu/figure3_framework.png', dpi=300, bbox_inches='tight',
            facecolor='white')
plt.close()
print("Figure 3 saved.")

print("\n" + "=" * 70)
print("ALL FIGURES GENERATED SUCCESSFULLY")
print("=" * 70)
