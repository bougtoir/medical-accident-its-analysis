#!/usr/bin/env python3
"""Fix Figure 4 label overlap."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

fig, ax = plt.subplots(1, 1, figsize=(8, 7))

u_range = np.linspace(-2.5, 2.5, 500)
v_range = np.linspace(0.5, 2.0, 500)
U, V = np.meshgrid(u_range, v_range)
Cb = 2.0 / (V + 1.0/V + U**2)

levels = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 0.99]
cs = ax.contourf(U, V, Cb, levels=np.linspace(0.3, 1.0, 50), cmap='RdYlGn', alpha=0.8)
contour_lines = ax.contour(U, V, Cb, levels=levels, colors='black', linewidths=0.5, alpha=0.6)
ax.clabel(contour_lines, levels, fmt='%.2f', fontsize=7, inline=True)
cbar = plt.colorbar(cs, ax=ax, label='$C_b$ (bias correction factor)', shrink=0.85)

np.random.seed(42)
n = 150
p_ref = np.random.normal(100, 20, n)
p_ref = np.clip(p_ref, 40, 180)
noise = np.random.normal(0, 3, n)

def get_uv(x, y):
    mx, my = np.mean(x), np.mean(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    v = sx / sy
    u = (mx - my) / np.sqrt(sx * sy)
    return u, v

p_a = p_ref + 12 + noise
ua, va = get_uv(p_ref, p_a)
p_b = p_ref + noise
ub, vb = get_uv(p_ref, p_b)
p_c = 1.12 * p_ref + noise
uc, vc = get_uv(p_ref, p_c)
p_d = 1.12 * p_ref + 12 + noise
ud, vd = get_uv(p_ref, p_d)

# Plot points with better label positioning
markers = [
    (ua, va, 'A', '#D6604D', 'A: Before zeroing (offset only)', (0.2, 0.12)),
    (ub, vb, 'B', '#4393C3', 'B: After zeroing (ideal)', (0.2, 0.1)),
    (uc, vc, 'C', '#762A83', 'C: Gain error (zeroing cannot fix)', (0.2, -0.15)),
    (ud, vd, 'D', '#B2182B', 'D: Gain + offset', (-0.15, 0.12)),
]

for u_val, v_val, label, color, desc, (dx, dy) in markers:
    ax.plot(u_val, v_val, 'o', color=color, markersize=13, markeredgecolor='white', 
            markeredgewidth=2, zorder=10)
    ax.text(u_val, v_val, label, ha='center', va='center', fontsize=8, 
            fontweight='bold', color='white', zorder=11)
    ax.annotate(desc, xy=(u_val, v_val), 
                xytext=(u_val + dx, v_val + dy),
                fontsize=8, color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=color, alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2))

# Arrow A → B (zero calibration)
ax.annotate('', xy=(ub + 0.03, vb), xytext=(ua - 0.03, va),
            arrowprops=dict(arrowstyle='->', color='#006600', lw=2.5, 
                           connectionstyle='arc3,rad=0.3'))
ax.text((ua + ub)/2, (va + vb)/2 + 0.15, 'Zero calibration\n(moves u \u2192 0)', 
        fontsize=8, color='#006600', fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E0FFE0', edgecolor='#006600', alpha=0.95))

# Arrow D → C (zero calibration)
ax.annotate('', xy=(uc + 0.03, vc), xytext=(ud - 0.03, vd),
            arrowprops=dict(arrowstyle='->', color='#006600', lw=2.5,
                           connectionstyle='arc3,rad=-0.3'))
ax.text((ud + uc)/2, (vd + vc)/2 - 0.18, 'Zero calibration\n(v unchanged!)', 
        fontsize=8, color='#006600', fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E0FFE0', edgecolor='#006600', alpha=0.95))

# Ideal star
ax.plot(0, 1, '*', color='gold', markersize=22, markeredgecolor='black', 
        markeredgewidth=1, zorder=11)
ax.text(0.25, 1.08, 'Ideal (u=0, v=1)\n$C_b$ = 1.0', fontsize=9, fontweight='bold', color='#333333',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFFFCC', edgecolor='#999900', alpha=0.95))

ax.set_xlabel('Location shift (u)', fontsize=12)
ax.set_ylabel('Scale shift (v = $\\sigma_1 / \\sigma_2$)', fontsize=12)
ax.set_title('$C_b$ diagnostic space: what zero calibration can and cannot correct', 
             fontweight='bold', fontsize=12)
ax.axhline(y=1, color='black', linewidth=0.5, alpha=0.3, linestyle=':')
ax.axvline(x=0, color='black', linewidth=0.5, alpha=0.3, linestyle=':')

plt.tight_layout()
fig.savefig('/home/ubuntu/bja_figures/figure4_cb_diagnostic_space.png')
plt.close(fig)
print('Figure 4 fixed.')
