#!/usr/bin/env python3
"""
Generate BJA Special Article manuscript with color figures in .docx format.
English and Japanese versions.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec
from scipy import stats
import os

# ── Global style ──
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

OUTDIR = '/home/ubuntu/bja_figures'
os.makedirs(OUTDIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════
# FIGURE 1 – Arterial pressure signal decomposition (AC vs DC)
# ════════════════════════════════════════════════════════════════
def make_figure1():
    """Arterial waveform decomposition into AC (pulse pressure) and DC (offset) components."""
    t = np.linspace(0, 3, 1000)  # 3 seconds
    hr = 72  # bpm
    period = 60 / hr
    
    # Simulate arterial pressure waveform
    def arterial_wave(t, sbp=120, dbp=80):
        phase = (t % period) / period
        # Systolic upstroke
        sys_component = np.exp(-((phase - 0.15)**2) / (2 * 0.03**2))
        # Dicrotic notch
        dicrotic = 0.15 * np.exp(-((phase - 0.45)**2) / (2 * 0.02**2))
        # Diastolic decay
        dias_decay = 0.3 * np.exp(-phase / 0.3)
        
        waveform = sys_component + dicrotic + dias_decay
        waveform = (waveform - waveform.min()) / (waveform.max() - waveform.min())
        return dbp + (sbp - dbp) * waveform
    
    true_sbp, true_dbp = 120, 80
    true_pp = true_sbp - true_dbp  # 40 mmHg
    true_map = true_dbp + true_pp / 3  # ~93.3 mmHg
    
    p_true = arterial_wave(t, true_sbp, true_dbp)
    
    # With offset (uncalibrated) - e.g., 15 mmHg hydrostatic offset
    offset = 15
    p_offset = p_true + offset
    
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    
    # Panel A: True waveform with AC/DC decomposition
    ax = axes[0]
    ax.plot(t, p_true, color='#2166AC', linewidth=1.5)
    ax.axhline(y=true_map, color='#B2182B', linestyle='--', linewidth=1, alpha=0.8)
    ax.axhline(y=true_dbp, color='#777777', linestyle=':', linewidth=0.8)
    ax.axhline(y=true_sbp, color='#777777', linestyle=':', linewidth=0.8)
    
    # DC component shading
    ax.fill_between(t, 0, true_dbp, alpha=0.08, color='#B2182B')
    ax.annotate('DC component\n(offset-dependent)', xy=(1.5, true_dbp/2), 
                fontsize=8, ha='center', va='center', color='#B2182B',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#B2182B', alpha=0.8))
    
    # AC component annotation
    ax.annotate('', xy=(2.65, true_sbp), xytext=(2.65, true_dbp),
                arrowprops=dict(arrowstyle='<->', color='#2166AC', lw=1.5))
    ax.text(2.75, (true_sbp + true_dbp)/2, f'PP = {true_pp}\nmmHg\n(AC)', 
            fontsize=8, color='#2166AC', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#2166AC', alpha=0.8))
    
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 160)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Pressure (mmHg)')
    ax.set_title('A. True arterial pressure', fontweight='bold')
    
    # Panel B: Offset waveform (uncalibrated)
    ax = axes[1]
    ax.plot(t, p_offset, color='#D6604D', linewidth=1.5)
    ax.plot(t, p_true, color='#2166AC', linewidth=1, alpha=0.4, linestyle='--')
    ax.axhline(y=true_map + offset, color='#D6604D', linestyle='--', linewidth=1, alpha=0.8)
    
    # Show offset
    ax.annotate('', xy=(0.3, true_map + offset), xytext=(0.3, true_map),
                arrowprops=dict(arrowstyle='<->', color='#B2182B', lw=1.5))
    ax.text(0.55, true_map + offset/2, f'Offset\n= {offset} mmHg\n(location shift u)', 
            fontsize=8, color='#B2182B', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#B2182B', alpha=0.8))
    
    # PP is unchanged
    pp_offset_sbp = true_sbp + offset
    pp_offset_dbp = true_dbp + offset
    ax.annotate('', xy=(2.65, pp_offset_sbp), xytext=(2.65, pp_offset_dbp),
                arrowprops=dict(arrowstyle='<->', color='#2166AC', lw=1.5))
    ax.text(2.75, (pp_offset_sbp + pp_offset_dbp)/2, f'PP = {true_pp}\nmmHg\n(unchanged)', 
            fontsize=8, color='#2166AC', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#2166AC', alpha=0.8))
    
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 160)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Pressure (mmHg)')
    ax.set_title('B. With DC offset (before zeroing)', fontweight='bold')
    
    # Panel C: Gain error
    ax = axes[2]
    gain = 1.15
    p_gain = arterial_wave(t, true_sbp * gain, true_dbp * gain)
    ax.plot(t, p_gain, color='#762A83', linewidth=1.5)
    ax.plot(t, p_true, color='#2166AC', linewidth=1, alpha=0.4, linestyle='--')
    
    pp_gain = int(true_pp * gain)
    sbp_gain = true_sbp * gain
    dbp_gain = true_dbp * gain
    
    ax.annotate('', xy=(2.65, sbp_gain), xytext=(2.65, dbp_gain),
                arrowprops=dict(arrowstyle='<->', color='#762A83', lw=1.5))
    ax.text(2.75, (sbp_gain + dbp_gain)/2, f'PP = {pp_gain}\nmmHg\n(scale shift v)', 
            fontsize=8, color='#762A83', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#762A83', alpha=0.8))
    
    ax.text(1.5, 10, f'Gain error: v = {gain:.2f}  (PP distorted: {true_pp} \u2192 {pp_gain} mmHg)',
            fontsize=8, ha='center', color='#762A83',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F2E6FA', edgecolor='#762A83', alpha=0.9))
    
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 160)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Pressure (mmHg)')
    ax.set_title('C. With gain error (PP distorted)', fontweight='bold')
    
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'figure1_signal_decomposition.png')
    fig.savefig(path)
    plt.close(fig)
    print(f'Saved {path}')
    return path


# ════════════════════════════════════════════════════════════════
# FIGURE 2 – CCC decomposition: zero calibration corrects u only
# ════════════════════════════════════════════════════════════════
def make_figure2():
    """Simulation showing zero calibration corrects location shift but not scale shift."""
    np.random.seed(42)
    n = 150
    
    # True arterial pressures (reference)
    p_ref = np.random.normal(loc=100, scale=20, size=n)
    p_ref = np.clip(p_ref, 40, 180)
    
    noise = np.random.normal(0, 3, size=n)
    
    # Scenario A: Offset only (u != 0, v = 1) — before zeroing
    offset_a = 12  # mmHg
    p_a = p_ref + offset_a + noise
    
    # Scenario B: Offset removed by zeroing (u = 0, v = 1)
    p_b = p_ref + noise
    
    # Scenario C: Gain error (u = 0, v != 1) — zeroing done, but gain wrong
    gain_c = 1.12
    p_c = gain_c * p_ref + noise
    
    # Scenario D: Gain error + offset (u != 0, v != 1) — worst case
    p_d = gain_c * p_ref + offset_a + noise
    
    def calc_ccc(x, y):
        mx, my = np.mean(x), np.mean(y)
        sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
        sxy = np.mean((x - mx) * (y - my))
        r = np.corrcoef(x, y)[0, 1]
        v = sx / sy
        u = (mx - my) / np.sqrt(sx * sy)
        cb = 2 / (v + 1/v + u**2)
        ccc = r * cb
        return ccc, r, cb, u, v
    
    scenarios = [
        ('A. Before zeroing\n(offset only)', p_ref, p_a, '#D6604D'),
        ('B. After zeroing\n(offset removed)', p_ref, p_b, '#4393C3'),
        ('C. Gain error\n(zeroing cannot fix)', p_ref, p_c, '#762A83'),
        ('D. Gain + offset\n(zeroing fixes only offset)', p_ref, p_d, '#B2182B'),
    ]
    
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
    
    for ax, (title, x, y, color) in zip(axes, scenarios):
        ccc, r, cb, u, v = calc_ccc(x, y)
        
        ax.scatter(x, y, s=12, alpha=0.5, color=color, edgecolors='none')
        
        # Identity line
        lims = [30, 200]
        ax.plot(lims, lims, 'k--', linewidth=0.8, alpha=0.5, label='Identity (y=x)')
        
        # Best fit line
        slope, intercept = np.polyfit(x, y, 1)
        xfit = np.array(lims)
        ax.plot(xfit, slope * xfit + intercept, color=color, linewidth=1.5, 
                label=f'Fit: y={slope:.2f}x{intercept:+.1f}')
        
        ax.set_xlim(30, 200)
        ax.set_ylim(30, 200)
        ax.set_aspect('equal')
        ax.set_xlabel('Reference (mmHg)')
        ax.set_ylabel('Device (mmHg)')
        ax.set_title(title, fontweight='bold', fontsize=9)
        
        # Stats box
        stats_text = (f'CCC = {ccc:.3f}\n'
                      f'r = {r:.3f}\n'
                      f'$C_b$ = {cb:.3f}\n'
                      f'u = {u:.2f}, v = {v:.2f}')
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                fontsize=7.5, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                         edgecolor=color, alpha=0.9))
        
        ax.legend(fontsize=6.5, loc='lower right')
    
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'figure2_ccc_zeroing_scenarios.png')
    fig.savefig(path)
    plt.close(fig)
    print(f'Saved {path}')
    return path


# ════════════════════════════════════════════════════════════════
# FIGURE 3 – Engineering pathway: from offset sources to zero-free
# ════════════════════════════════════════════════════════════════
def make_figure3():
    """Conceptual diagram: conventional vs zero-free measurement system."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    
    # ── Panel A: Conventional system ──
    ax = axes[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('A. Conventional fluid-filled system', fontweight='bold', fontsize=11, pad=15)
    
    # Artery
    ax.add_patch(FancyBboxPatch((0.3, 6.5), 2.2, 1.2, boxstyle="round,pad=0.15",
                                facecolor='#FFCCCC', edgecolor='#CC0000', linewidth=1.5))
    ax.text(1.4, 7.1, 'Artery\n(catheter tip)', ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Tubing
    ax.annotate('', xy=(4.0, 7.1), xytext=(2.5, 7.1),
                arrowprops=dict(arrowstyle='->', color='#0066CC', lw=2))
    ax.text(3.25, 7.6, 'Fluid-filled\ntubing', ha='center', va='bottom', fontsize=7, color='#0066CC')
    
    # External transducer
    ax.add_patch(FancyBboxPatch((4.0, 6.2), 2.5, 1.8, boxstyle="round,pad=0.15",
                                facecolor='#CCE5FF', edgecolor='#0066CC', linewidth=1.5))
    ax.text(5.25, 7.1, 'External\ntransducer', ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Monitor
    ax.add_patch(FancyBboxPatch((7.2, 6.2), 2.3, 1.8, boxstyle="round,pad=0.15",
                                facecolor='#E8E8E8', edgecolor='#333333', linewidth=1.5))
    ax.text(8.35, 7.1, 'Monitor', ha='center', va='center', fontsize=8, fontweight='bold')
    
    ax.annotate('', xy=(7.2, 7.1), xytext=(6.5, 7.1),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    # Offset sources (red warning boxes)
    sources = [
        (1.4, 4.5, 'Hydrostatic\ncolumn\n(\u0394P = \u03C1gh)', '#FF6666'),
        (4.2, 4.5, 'Atmospheric\npressure\nreference', '#FF9966'),
        (7.0, 4.5, 'Transducer\ndrift', '#FFCC66'),
    ]
    for x, y, text, color in sources:
        ax.add_patch(FancyBboxPatch((x-0.9, y-0.7), 1.8, 1.4, boxstyle="round,pad=0.1",
                                    facecolor=color, edgecolor='#CC0000', linewidth=1, alpha=0.7))
        ax.text(x, y, text, ha='center', va='center', fontsize=7, color='#660000')
    
    # Arrow to zeroing
    ax.add_patch(FancyBboxPatch((2.5, 1.5), 5.0, 1.5, boxstyle="round,pad=0.2",
                                facecolor='#FFE0E0', edgecolor='#CC0000', linewidth=2))
    ax.text(5.0, 2.25, 'Manual zero calibration required\n(corrects offset/u only; gain/v unchanged)',
            ha='center', va='center', fontsize=8, fontweight='bold', color='#CC0000')
    
    ax.annotate('', xy=(5.0, 3.0), xytext=(5.0, 3.8),
                arrowprops=dict(arrowstyle='->', color='#CC0000', lw=2))
    
    # ── Panel B: Proposed zero-free system ──
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('B. Proposed zero-free system', fontweight='bold', fontsize=11, pad=15)
    
    # Catheter-tip sensor
    ax.add_patch(FancyBboxPatch((0.3, 6.5), 3.0, 1.8, boxstyle="round,pad=0.15",
                                facecolor='#CCFFCC', edgecolor='#006600', linewidth=1.5))
    ax.text(1.8, 7.6, 'Catheter-tip\nMEMS sensor', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(1.8, 6.9, '(absolute pressure)', ha='center', va='center', fontsize=7, color='#006600')
    
    # Monitor with barometric sensor
    ax.add_patch(FancyBboxPatch((4.5, 6.0), 3.2, 2.8, boxstyle="round,pad=0.15",
                                facecolor='#E8FFE8', edgecolor='#006600', linewidth=1.5))
    ax.text(6.1, 8.1, 'Smart Monitor', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.text(6.1, 7.5, 'Built-in barometer\n+ auto-compensation', ha='center', va='center', fontsize=7, color='#006600')
    ax.text(6.1, 6.6, 'Self-calibrating\nMEMS reference', ha='center', va='center', fontsize=7, color='#006600')
    
    ax.annotate('', xy=(4.5, 7.4), xytext=(3.3, 7.4),
                arrowprops=dict(arrowstyle='->', color='#006600', lw=2))
    
    # Eliminated sources (green checkmarks)
    solutions = [
        (1.4, 4.5, 'Tip sensor\n\u2192 \u0394h = 0\n\u2713 Eliminated', '#66CC66'),
        (4.2, 4.5, 'Barometric\ncompensation\n\u2713 Eliminated', '#99CC66'),
        (7.0, 4.5, 'Self-calibrating\nMEMS\n\u2713 Eliminated', '#CCCC66'),
    ]
    for x, y, text, color in solutions:
        ax.add_patch(FancyBboxPatch((x-0.9, y-0.7), 1.8, 1.4, boxstyle="round,pad=0.1",
                                    facecolor=color, edgecolor='#006600', linewidth=1, alpha=0.7))
        ax.text(x, y, text, ha='center', va='center', fontsize=7, color='#003300')
    
    # Result
    ax.add_patch(FancyBboxPatch((2.5, 1.5), 5.0, 1.5, boxstyle="round,pad=0.2",
                                facecolor='#E0FFE0', edgecolor='#006600', linewidth=2))
    ax.text(5.0, 2.25, 'Zero calibration unnecessary by design\n(u = 0 by design; PP accuracy validates v = 1)',
            ha='center', va='center', fontsize=8, fontweight='bold', color='#006600')
    
    ax.annotate('', xy=(5.0, 3.0), xytext=(5.0, 3.8),
                arrowprops=dict(arrowstyle='->', color='#006600', lw=2))
    
    # Output box
    ax.add_patch(FancyBboxPatch((7.8, 6.2), 1.8, 1.5, boxstyle="round,pad=0.15",
                                facecolor='#E8E8E8', edgecolor='#333333', linewidth=1.5))
    ax.text(8.7, 6.95, 'Display', ha='center', va='center', fontsize=8, fontweight='bold')
    ax.annotate('', xy=(7.8, 6.95), xytext=(7.7, 7.4),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=2))
    
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'figure3_system_comparison.png')
    fig.savefig(path)
    plt.close(fig)
    print(f'Saved {path}')
    return path


# ════════════════════════════════════════════════════════════════
# FIGURE 4 – CCC diagnostic space (u-v plane with Cb contours)
# ════════════════════════════════════════════════════════════════
def make_figure4():
    """CCC Cb decomposition diagnostic space showing effect of zero calibration."""
    fig, ax = plt.subplots(1, 1, figsize=(7, 6))
    
    # Create u-v grid
    u_range = np.linspace(-2, 2, 500)
    v_range = np.linspace(0.5, 2.0, 500)
    U, V = np.meshgrid(u_range, v_range)
    
    Cb = 2.0 / (V + 1.0/V + U**2)
    
    # Contour plot
    levels = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 0.99]
    cs = ax.contourf(U, V, Cb, levels=np.linspace(0.3, 1.0, 50), cmap='RdYlGn', alpha=0.8)
    contour_lines = ax.contour(U, V, Cb, levels=levels, colors='black', linewidths=0.5, alpha=0.6)
    ax.clabel(contour_lines, levels, fmt='%.2f', fontsize=7, inline=True)
    
    cbar = plt.colorbar(cs, ax=ax, label='$C_b$ (bias correction factor)', shrink=0.85)
    
    # Mark scenarios
    # Before zeroing: offset present
    np.random.seed(42)
    n = 150
    p_ref = np.random.normal(100, 20, n)
    p_ref = np.clip(p_ref, 40, 180)
    noise = np.random.normal(0, 3, n)
    
    # Calculate actual u, v for scenarios
    def get_uv(x, y):
        mx, my = np.mean(x), np.mean(y)
        sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
        v = sx / sy
        u = (mx - my) / np.sqrt(sx * sy)
        return u, v
    
    # A: offset only
    p_a = p_ref + 12 + noise
    ua, va = get_uv(p_ref, p_a)
    
    # B: zeroed (offset removed)
    p_b = p_ref + noise
    ub, vb = get_uv(p_ref, p_b)
    
    # C: gain error
    p_c = 1.12 * p_ref + noise
    uc, vc = get_uv(p_ref, p_c)
    
    # D: gain + offset
    p_d = 1.12 * p_ref + 12 + noise
    ud, vd = get_uv(p_ref, p_d)
    
    markers = [
        (ua, va, 'A', '#D6604D', 'Before zeroing\n(offset only)'),
        (ub, vb, 'B', '#4393C3', 'After zeroing\n(ideal)'),
        (uc, vc, 'C', '#762A83', 'Gain error\n(zeroing cannot fix)'),
        (ud, vd, 'D', '#B2182B', 'Gain + offset'),
    ]
    
    for u_val, v_val, label, color, desc in markers:
        ax.plot(u_val, v_val, 'o', color=color, markersize=12, markeredgecolor='white', 
                markeredgewidth=2, zorder=10)
        ax.annotate(f'{label}: {desc}', xy=(u_val, v_val), 
                    xytext=(u_val + 0.15, v_val + 0.06),
                    fontsize=7.5, fontweight='bold', color=color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.9))
    
    # Arrow showing zero calibration effect (A → B)
    ax.annotate('', xy=(ub, vb), xytext=(ua, va),
                arrowprops=dict(arrowstyle='->', color='#006600', lw=2.5, 
                               connectionstyle='arc3,rad=0.2'))
    ax.text((ua + ub)/2 - 0.3, (va + vb)/2 + 0.08, 'Zero\ncalibration', 
            fontsize=8, color='#006600', fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#E0FFE0', edgecolor='#006600'))
    
    # Arrow showing zero calibration effect (D → C)  
    ax.annotate('', xy=(uc, vc), xytext=(ud, vd),
                arrowprops=dict(arrowstyle='->', color='#006600', lw=2.5,
                               connectionstyle='arc3,rad=-0.2'))
    ax.text((ud + uc)/2 + 0.2, (vd + vc)/2 - 0.08, 'Zero\ncalibration', 
            fontsize=8, color='#006600', fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#E0FFE0', edgecolor='#006600'))
    
    # Ideal point
    ax.plot(0, 1, '*', color='gold', markersize=20, markeredgecolor='black', 
            markeredgewidth=1, zorder=11)
    ax.text(0.15, 1.04, 'Ideal\n(u=0, v=1)', fontsize=8, fontweight='bold', color='#333333')
    
    ax.set_xlabel('Location shift (u)', fontsize=11)
    ax.set_ylabel('Scale shift (v = $\\sigma_1 / \\sigma_2$)', fontsize=11)
    ax.set_title('$C_b$ diagnostic space: what zero calibration can and cannot correct', 
                 fontweight='bold', fontsize=11)
    ax.axhline(y=1, color='black', linewidth=0.5, alpha=0.3, linestyle=':')
    ax.axvline(x=0, color='black', linewidth=0.5, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    path = os.path.join(OUTDIR, 'figure4_cb_diagnostic_space.png')
    fig.savefig(path)
    plt.close(fig)
    print(f'Saved {path}')
    return path


# ════════════════════════════════════════════════════════════════
# GENERATE ALL FIGURES
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    fig1 = make_figure1()
    fig2 = make_figure2()
    fig3 = make_figure3()
    fig4 = make_figure4()
    print('\nAll figures generated successfully.')
    print(f'Figure 1: {fig1}')
    print(f'Figure 2: {fig2}')
    print(f'Figure 3: {fig3}')
    print(f'Figure 4: {fig4}')
