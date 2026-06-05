#!/usr/bin/env python3
"""
Stochastic Resonance + Covariate-Adjusted Denoising Simulation

Generates all figures for the PRE manuscript:
  Fig. 1 — Conceptual schematic: threshold detector + SR + ANCOVA analogy
  Fig. 2 — Classic SR curve (SNR vs noise) + covariate-adjusted shift
  Fig. 3 — Optimal rho* vs input noise: "too much adjustment kills SR"
  Fig. 4 — Detection probability P_D at fixed P_FA for different rho
  Fig. 5 — ROC curves: raw vs covariate-adjusted
  Fig. 6 — Mutual information vs noise level
  Fig. 7 — DVS application: EBSSA results in SR framework

Key insight: covariate adjustment (ANCOVA) reduces effective noise
  sigma_eff = sigma * sqrt(1 - rho^2).
  - If sigma >> sigma* (too much noise): adjustment helps (moves toward SR peak)
  - If sigma = sigma* (at optimum): any adjustment HURTS
  - Therefore exists an optimal rho*(sigma) for each input noise level
  This "optimal noise model accuracy" is the novel theoretical result.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.special import erfc
from scipy.optimize import minimize_scalar

OUT_DIR = Path(__file__).resolve().parent.parent / 'pre_submission'
OUT_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'font.family': 'serif',
})

# ===================================================================
# Analytical SR theory for threshold detector
# ===================================================================

def sr_snr_analytic(sigma, A, theta):
    """
    Analytical output SNR for a threshold detector with
    subthreshold periodic signal A*sin(2*pi*f0*t) + Gaussian noise N(0,sigma).

    Based on the two-state (McNamara-Wiesenfeld) theory adapted for
    symmetric threshold |x| > theta:
      SNR_out = pi * A^2 / (2 * sigma^4) * exp(-2*theta^2/sigma^2)
              * 1 / r_K(0)
    where r_K(0) is the Kramers rate.

    For our purposes (relative comparisons), we use:
      SNR(sigma) proportional to (A/sigma^2)^2 * exp(-2*theta^2 / sigma^2)
    """
    if sigma < 1e-12:
        return 0.0
    return (A / sigma**2)**2 * np.exp(-2 * theta**2 / sigma**2)


def sr_snr_analytic_vec(sigma_arr, A, theta):
    """Vectorised version."""
    sigma_arr = np.asarray(sigma_arr, dtype=float)
    result = np.zeros_like(sigma_arr)
    mask = sigma_arr > 1e-12
    s = sigma_arr[mask]
    result[mask] = (A / s**2)**2 * np.exp(-2 * theta**2 / s**2)
    return result


def optimal_sigma(theta):
    """
    Optimal noise level for SR in this model.
    d/dsigma [ (A/sigma^2)^2 exp(-2 theta^2/sigma^2) ] = 0
    => sigma* = theta  (independent of A)
    """
    return theta


def sr_snr_effective(sigma_input, rho, A, theta):
    """
    SNR after covariate adjustment with noise model correlation rho.
    Effective noise: sigma_eff = sigma_input * sqrt(1 - rho^2)
    """
    sigma_eff = sigma_input * np.sqrt(max(1 - rho**2, 1e-12))
    return sr_snr_analytic(sigma_eff, A, theta)


def optimal_rho(sigma_input, A, theta):
    """
    Find the optimal rho* that maximises SNR for given input sigma.
    If sigma_input <= theta, rho*=0 (any adjustment hurts).
    If sigma_input > theta, rho* sets sigma_eff = theta.
      rho* = sqrt(1 - (theta/sigma_input)^2)
    """
    if sigma_input <= theta:
        return 0.0
    return np.sqrt(1 - (theta / sigma_input)**2)


# ===================================================================
# Monte Carlo validation
# ===================================================================

def mc_sr_curve(sigma_range, A, f0, theta, N=200000, dt=0.001, n_trials=20):
    """
    Monte Carlo SR curve via cross-correlation at signal frequency.
    Uses time-domain correlation instead of spectral estimation for stability.
    """
    snr_mean = np.zeros(len(sigma_range))
    snr_std = np.zeros(len(sigma_range))
    for i, sigma in enumerate(sigma_range):
        snrs = []
        for _ in range(n_trials):
            t = np.arange(N) * dt
            s = A * np.sin(2 * np.pi * f0 * t)
            n = np.random.normal(0, sigma, N)
            events = (np.abs(s + n) > theta).astype(float)
            # Cross-correlation with reference sinusoid at f0
            ref_sin = np.sin(2 * np.pi * f0 * t)
            ref_cos = np.cos(2 * np.pi * f0 * t)
            # Signal component in event stream
            c_sin = np.mean(events * ref_sin)
            c_cos = np.mean(events * ref_cos)
            signal_power = c_sin**2 + c_cos**2
            # Noise power: variance of event stream minus signal power
            event_var = np.var(events)
            noise_power = max(event_var - signal_power, 1e-20)
            snr = signal_power / noise_power
            snrs.append(snr)
        snr_mean[i] = np.mean(snrs)
        snr_std[i] = np.std(snrs) / np.sqrt(n_trials)
    return snr_mean, snr_std


# ===================================================================
# Figure generation
# ===================================================================

def fig1_schematic():
    """Fig. 1: Three-panel conceptual schematic."""
    print("Generating Fig. 1: Conceptual schematic...")
    fig, axes = plt.subplots(1, 3, figsize=(10, 3))

    # (a) Threshold detector
    ax = axes[0]
    np.random.seed(42)
    t = np.linspace(0, 2, 500)
    s = 0.3 * np.sin(2 * np.pi * 2 * t)
    n = np.random.normal(0, 0.6, len(t))
    x = s + n
    theta_val = 0.8
    events = np.abs(x) > theta_val
    ax.plot(t, x, color='0.5', ls='-', lw=0.5, alpha=0.7, label=r'$x(t) = s(t) + n(t)$')
    ax.plot(t, s, 'k-', lw=1.8, label=r'$s(t)$')
    ax.axhline(y=theta_val, color='k', ls='--', lw=1, label=r'$\theta$')
    ax.axhline(y=-theta_val, color='k', ls='--', lw=1)
    event_times = t[events]
    ax.plot(event_times, np.ones_like(event_times) * 1.3, 'k|', ms=5, mew=0.5)
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    ax.set_title('(a) Threshold detector')
    ax.set_ylim(-2.2, 1.7)
    ax.legend(fontsize=7, loc='lower left')

    # (b) SR: event rate modulation at different noise levels
    ax = axes[1]
    np.random.seed(123)
    sigmas = [0.2, 0.7, 1.8]
    labels_sr = [r'$\sigma/\theta=0.25$', r'$\sigma/\theta=0.88$ (near opt.)',
                 r'$\sigma/\theta=2.25$']
    styles_sr = [('#d62728', '-', 1.4), ('#2ca02c', '--', 1.4), ('#1f77b4', '-.', 1.4)]
    for sigma, lab, (col, ls, lw) in zip(sigmas, labels_sr, styles_sr):
        n_trial = np.random.normal(0, sigma, len(t))
        x_trial = s + n_trial
        events_trial = np.abs(x_trial) > theta_val
        # Smooth event rate
        kernel = np.ones(30) / 30
        rate = np.convolve(events_trial.astype(float), kernel, mode='same')
        ax.plot(t, rate, color=col, ls=ls, lw=lw, label=lab)
    ax.set_xlabel('Time')
    ax.set_ylabel('Event rate (smoothed)')
    ax.set_title('(b) Stochastic resonance')
    ax.legend(fontsize=7, loc='upper right')
    ax.set_ylim(bottom=-0.02)

    # (c) ANCOVA: residual noise distributions
    ax = axes[2]
    sigma_base = 0.8
    x_range = np.linspace(-3, 3, 300)
    rho_vals = [0, 0.5, 0.8, 0.95]
    styles_c = [('k', '-', 1.5), ('#1f77b4', '--', 1.3), ('#2ca02c', '-.', 1.3), ('#d62728', ':', 1.5)]
    for rho, (col, ls, lw) in zip(rho_vals, styles_c):
        sigma_eff = sigma_base * np.sqrt(max(1 - rho**2, 0.005))
        pdf = np.exp(-x_range**2 / (2 * sigma_eff**2)) / (sigma_eff * np.sqrt(2 * np.pi))
        label = r'$\rho=%.2f$' % rho if rho > 0 else r'Raw ($\rho=0$)'
        ax.plot(x_range, pdf, color=col, ls=ls, lw=lw, label=label)
    ax.axvline(x=theta_val, color='k', ls='--', lw=1)
    ax.axvline(x=-theta_val, color='k', ls='--', lw=1)
    ax.set_xlabel(r'Residual noise $\varepsilon$')
    ax.set_ylabel('Probability density')
    ax.set_title(r'(c) Covariate adjustment ($\sigma=\theta$)')
    ax.legend(fontsize=7, loc='upper right')

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig1_schematic.png')
    plt.close(fig)
    print("  -> fig1_schematic.png")

    # Also export individual panels for editable PPTX
    for idx, ax_label in enumerate(['a', 'b', 'c']):
        fig_single, ax_single = plt.subplots(1, 1, figsize=(4, 3))
        # Re-draw each panel individually
        if idx == 0:
            np.random.seed(42)
            t2 = np.linspace(0, 2, 500)
            s2 = 0.3 * np.sin(2 * np.pi * 2 * t2)
            n2 = np.random.normal(0, 0.6, len(t2))
            x2 = s2 + n2
            th = 0.8
            ev = np.abs(x2) > th
            ax_single.plot(t2, x2, color='0.5', ls='-', lw=0.5, alpha=0.7, label=r'$x(t) = s(t) + n(t)$')
            ax_single.plot(t2, s2, 'k-', lw=1.8, label=r'$s(t)$')
            ax_single.axhline(y=th, color='k', ls='--', lw=1, label=r'$\theta$')
            ax_single.axhline(y=-th, color='k', ls='--', lw=1)
            et = t2[ev]
            ax_single.plot(et, np.ones_like(et) * 1.3, 'k|', ms=5, mew=0.5)
            ax_single.set_xlabel('Time')
            ax_single.set_ylabel('Amplitude')
            ax_single.set_ylim(-2.2, 1.7)
            ax_single.legend(fontsize=8, loc='lower left')
        elif idx == 1:
            np.random.seed(123)
            t2 = np.linspace(0, 2, 500)
            s2 = 0.3 * np.sin(2 * np.pi * 2 * t2)
            th = 0.8
            sigmas2 = [0.2, 0.7, 1.8]
            labels2 = [r'$\sigma/\theta=0.25$', r'$\sigma/\theta=0.88$ (opt.)',
                       r'$\sigma/\theta=2.25$']
            styles2 = [('#d62728', '-', 1.4), ('#2ca02c', '--', 1.4), ('#1f77b4', '-.', 1.4)]
            for sigma, lab, (col, ls, lw) in zip(sigmas2, labels2, styles2):
                n2 = np.random.normal(0, sigma, len(t2))
                x2 = s2 + n2
                ev2 = np.abs(x2) > th
                kernel = np.ones(30) / 30
                rate = np.convolve(ev2.astype(float), kernel, mode='same')
                ax_single.plot(t2, rate, color=col, ls=ls, lw=lw, label=lab)
            ax_single.set_xlabel('Time')
            ax_single.set_ylabel('Event rate (smoothed)')
            ax_single.legend(fontsize=8, loc='upper right')
            ax_single.set_ylim(bottom=-0.02)
        else:
            sigma_base = 0.8
            x_range = np.linspace(-3, 3, 300)
            rho_vals2 = [0, 0.5, 0.8, 0.95]
            styles2 = [('k', '-', 1.5), ('#1f77b4', '--', 1.3), ('#2ca02c', '-.', 1.3), ('#d62728', ':', 1.5)]
            th = 0.8
            for rho, (col, ls, lw) in zip(rho_vals2, styles2):
                sigma_eff = sigma_base * np.sqrt(max(1 - rho**2, 0.005))
                pdf = np.exp(-x_range**2 / (2 * sigma_eff**2)) / (sigma_eff * np.sqrt(2 * np.pi))
                label = r'$\rho=%.2f$' % rho if rho > 0 else r'Raw ($\rho=0$)'
                ax_single.plot(x_range, pdf, color=col, ls=ls, lw=lw, label=label)
            ax_single.axvline(x=th, color='k', ls='--', lw=1)
            ax_single.axvline(x=-th, color='k', ls='--', lw=1)
            ax_single.set_xlabel(r'Residual noise $\varepsilon$')
            ax_single.set_ylabel('Probability density')
            ax_single.legend(fontsize=8, loc='upper right')

        fig_single.tight_layout()
        fig_single.savefig(OUT_DIR / f'fig1{ax_label}.png', dpi=200)
        plt.close(fig_single)
    print("  -> fig1a.png, fig1b.png, fig1c.png (individual panels)")


def fig2_sr_curve():
    """
    Fig. 2: SR curve — analytical + MC validation.
    Shows how covariate adjustment shifts the effective SR curve.
    """
    print("Generating Fig. 2: SR curves...")
    A = 0.3
    theta = 1.0
    sigma_range = np.linspace(0.05, 3.5, 200)

    # Analytical curves
    snr_raw = sr_snr_analytic_vec(sigma_range, A, theta)
    rho_vals = [0.5, 0.8, 0.95]
    snr_adj = {}
    for rho in rho_vals:
        sigma_eff = sigma_range * np.sqrt(1 - rho**2)
        snr_adj[rho] = sr_snr_analytic_vec(sigma_eff, A, theta)

    # Normalise to peak of raw
    peak = snr_raw.max()
    snr_raw_n = snr_raw / peak
    snr_adj_n = {rho: s / peak for rho, s in snr_adj.items()}

    # MC validation (sparse points for raw curve)
    sigma_mc = np.array([0.3, 0.5, 0.7, 1.0, 1.3, 1.5, 1.8, 2.0, 2.5, 3.0])
    print("  Running MC validation (this may take ~30s)...")
    mc_snr, mc_se = mc_sr_curve(sigma_mc, A, 5.0, theta, N=100000, dt=0.001, n_trials=15)
    mc_peak = mc_snr.max() if mc_snr.max() > 0 else 1.0
    mc_snr_n = mc_snr / mc_peak

    fig, ax = plt.subplots(1, 1, figsize=(5, 3.8))
    ax.plot(sigma_range / theta, snr_raw_n, 'k-', lw=2,
            label=r'No adjustment ($\rho=0$)')
    styles_fig2 = [('#1f77b4', '--', 1.5), ('#2ca02c', '-.', 1.5), ('#d62728', ':', 1.8)]
    for rho, (col, ls, lw) in zip(rho_vals, styles_fig2):
        ax.plot(sigma_range / theta, snr_adj_n[rho], color=col, ls=ls, lw=lw,
                label=r'$\rho=%.2f$' % rho)
    # MC points
    ax.errorbar(sigma_mc / theta, mc_snr_n, yerr=mc_se / mc_peak,
                fmt='ks', ms=4, capsize=2, lw=0.8, zorder=5,
                label='MC validation')

    # Mark optima
    idx_opt_raw = np.argmax(snr_raw_n)
    ax.axvline(x=sigma_range[idx_opt_raw] / theta, color='gray',
               ls=':', lw=0.8, alpha=0.6)
    ax.annotate(r'$\sigma^*/\theta$', xy=(sigma_range[idx_opt_raw]/theta, 1.02),
                fontsize=9, ha='center')

    ax.set_xlabel(r'Input noise level $\sigma_n / \theta$')
    ax.set_ylabel(r'Normalized output SNR')
    ax.legend(loc='upper right', framealpha=0.9, fontsize=8)
    ax.set_xlim(0, 3.5)
    ax.set_ylim(-0.02, 1.15)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig2_sr_curves.png')
    plt.close(fig)
    print("  -> fig2_sr_curves.png")


def fig4_detection_probability():
    """
    Fig. 4: Detection probability improvement through covariate adjustment.
    At fixed P_FA, how does P_D change with noise and rho?
    """
    print("Generating Fig. 4: Detection probability...")
    A = 0.4
    theta = 1.0
    sigma_range = np.linspace(0.1, 3.0, 60)
    rho_values = [0.0, 0.5, 0.8, 0.95]
    styles_fig4 = [('k', '-', 1.5), ('#1f77b4', '--', 1.5), ('#2ca02c', '-.', 1.5), ('#d62728', ':', 1.8)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

    for rho, (col, ls, lw) in zip(rho_values, styles_fig4):
        pds = []
        pfas = []
        for sigma in sigma_range:
            sigma_eff = sigma * np.sqrt(max(1 - rho**2, 1e-12))
            # Analytical: P_FA = erfc(theta / (sqrt(2) * sigma_eff))
            # P_D = 0.5 * erfc((theta - A)/(sqrt(2)*sigma_eff))
            #      + 0.5 * erfc((theta + A)/(sqrt(2)*sigma_eff))  [two-sided]
            if sigma_eff < 1e-10:
                pfa = 0.0
                pd = 1.0 if A > theta else 0.0
            else:
                pfa = erfc(theta / (np.sqrt(2) * sigma_eff))
                pd = (0.5 * erfc((theta - A) / (np.sqrt(2) * sigma_eff))
                     + 0.5 * erfc((theta + A) / (np.sqrt(2) * sigma_eff)))
            pfas.append(pfa)
            pds.append(pd)

        label = r'$\rho=%.2f$' % rho if rho > 0 else r'No adjustment ($\rho=0$)'
        ax1.plot(sigma_range / theta, pds, color=col, ls=ls, lw=lw, label=label)
        ax2.plot(sigma_range / theta, pfas, color=col, ls=ls, lw=lw, label=label)

    ax1.set_xlabel(r'Input noise $\sigma_n / \theta$')
    ax1.set_ylabel(r'Detection probability $P_D$')
    ax1.legend(loc='lower right', fontsize=8, framealpha=0.9)
    ax1.set_xlim(0, 3)
    ax1.set_ylim(0, 1.02)
    ax1.grid(True, alpha=0.3)
    ax1.set_title(r'(a) $P_D$ ($A/\theta = 0.4$)')

    ax2.set_xlabel(r'Input noise $\sigma_n / \theta$')
    ax2.set_ylabel(r'False alarm probability $P_{FA}$')
    ax2.legend(loc='upper left', fontsize=8, framealpha=0.9)
    ax2.set_xlim(0, 3)
    ax2.set_ylim(0, 1.02)
    ax2.grid(True, alpha=0.3)
    ax2.set_title('(b) $P_{FA}$')

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig4_detection_probability.png')
    plt.close(fig)
    print("  -> fig4_detection_probability.png")


def fig5_roc_comparison():
    """Fig. 5: ROC curves for different rho at a fixed high-noise regime."""
    print("Generating Fig. 5: ROC comparison...")
    A = 0.4
    sigma_n = 1.5  # well above theta=1 (noisy regime)
    theta_range = np.linspace(0.001, 5.0, 500)

    rho_values = [0.0, 0.5, 0.8, 0.95]
    styles_fig5 = [('k', '-', 1.5), ('#1f77b4', '--', 1.5), ('#2ca02c', '-.', 1.5), ('#d62728', ':', 1.8)]
    labels = [r'Raw ($\rho=0$)', r'$\rho=0.50$', r'$\rho=0.80$', r'$\rho=0.95$']

    fig, ax = plt.subplots(1, 1, figsize=(4.5, 4))

    for rho, (col, ls, lw), label in zip(rho_values, styles_fig5, labels):
        sigma_eff = sigma_n * np.sqrt(max(1 - rho**2, 1e-12))
        if sigma_eff < 1e-10:
            ax.plot([0, 0, 1], [0, 1, 1], color=col, ls=ls, lw=lw, label=label)
            continue
        pfa = erfc(theta_range / (np.sqrt(2) * sigma_eff))
        pd = (0.5 * erfc((theta_range - A) / (np.sqrt(2) * sigma_eff))
             + 0.5 * erfc((theta_range + A) / (np.sqrt(2) * sigma_eff)))
        # Sort by P_FA
        sort_idx = np.argsort(pfa)
        ax.plot(pfa[sort_idx], pd[sort_idx], color=col, ls=ls, lw=lw, label=label)

    ax.plot([0, 1], [0, 1], 'k--', lw=0.5, alpha=0.5)
    ax.set_xlabel(r'False alarm probability $P_{FA}$')
    ax.set_ylabel(r'Detection probability $P_D$')
    ax.set_title(r'$A/\theta=0.4$, $\sigma_n/\theta=1.5$')
    ax.legend(loc='lower right', framealpha=0.9, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig5_roc_comparison.png')
    plt.close(fig)
    print("  -> fig5_roc_comparison.png")


def fig3_optimal_rho():
    """
    Fig. 3: THE KEY RESULT — optimal rho* as a function of input noise.
    Shows that there exists an optimal noise model accuracy:
    - sigma < theta: rho* = 0 (don't adjust — you need the noise for SR)
    - sigma > theta: rho* = sqrt(1 - theta^2/sigma^2) (adjust to SR peak)
    """
    print("Generating Fig. 3: Optimal rho*...")
    theta = 1.0
    A_values = [0.2, 0.3, 0.5]
    styles_fig3 = [('#1f77b4', '-', 1.5), ('#ff7f0e', '--', 1.5), ('#2ca02c', '-.', 1.5)]

    sigma_range = np.linspace(0.3, 4.0, 100)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

    for A, (col, ls, lw) in zip(A_values, styles_fig3):
        rho_opt = []
        snr_improvement = []
        for sigma in sigma_range:
            # Find optimal rho by grid search
            rho_grid = np.linspace(0, 0.999, 500)
            snr_vals = np.array([sr_snr_effective(sigma, r, A, theta) for r in rho_grid])
            best_idx = np.argmax(snr_vals)
            rho_opt.append(rho_grid[best_idx])
            # SNR improvement vs no adjustment
            snr_raw = sr_snr_analytic(sigma, A, theta)
            if snr_raw > 1e-30:
                snr_improvement.append(snr_vals[best_idx] / snr_raw)
            else:
                snr_improvement.append(1.0)

        ax1.plot(sigma_range / theta, rho_opt, color=col, ls=ls, lw=lw,
                 label=r'$A/\theta=%.1f$' % (A / theta))
        ax2.plot(sigma_range / theta, snr_improvement, color=col, ls=ls, lw=lw,
                 label=r'$A/\theta=%.1f$' % (A / theta))

    # Analytical rho* curve (independent of A)
    rho_theory = np.zeros_like(sigma_range)
    for i, sigma in enumerate(sigma_range):
        if sigma > theta:
            rho_theory[i] = np.sqrt(1 - (theta / sigma)**2)
    ax1.plot(sigma_range / theta, rho_theory, 'k:', lw=1.2,
             label=r'$\rho^* = \sqrt{1 - (\theta/\sigma)^2}$')

    ax1.axvline(x=1.0, color='0.5', ls=':', lw=0.8)
    ax1.annotate(r'$\sigma = \theta$', xy=(1.02, 0.9), fontsize=8, color='0.4')
    ax1.fill_betweenx([0, 1], 0, 1, color='0.92', alpha=0.6, zorder=0)
    ax1.fill_betweenx([0, 1], 1, 4, color='0.82', alpha=0.4, zorder=0)
    ax1.text(0.5, 0.05, 'SR\nregime', ha='center', fontsize=7, color='0.4')
    ax1.text(2.5, 0.05, 'Excess noise\nregime', ha='center', fontsize=7, color='0.4')
    ax1.set_xlabel(r'Input noise level $\sigma_n / \theta$')
    ax1.set_ylabel(r'Optimal $\rho^*$')
    ax1.legend(loc='upper left', fontsize=7, framealpha=0.9)
    ax1.set_xlim(0.3, 4)
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('(a) Optimal noise model accuracy')

    ax2.axvline(x=1.0, color='0.5', ls=':', lw=0.8)
    ax2.axhline(y=1.0, color='0.5', ls='--', lw=0.8)
    ax2.set_xlabel(r'Input noise level $\sigma_n / \theta$')
    ax2.set_ylabel(r'Peak SNR gain at $\rho^*$')
    ax2.legend(loc='upper left', fontsize=7, framealpha=0.9)
    ax2.set_xlim(0.3, 4)
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('(b) SNR improvement at optimal $\\rho^*$')

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig3_optimal_rho.png')
    plt.close(fig)
    print("  -> fig3_optimal_rho.png")


def fig7_dvs_application():
    """Fig. 7: DVS EBSSA results reinterpreted in SR+ANCOVA framework."""
    print("Generating Fig. 7: DVS application...")
    methods = ['Temporal\nFilter', 'Fano Filter\n(Covariate Adj.)', 'PI-DC-DVS\n(Neural)']
    auc_means = [0.534, 0.866, 0.546]
    auc_stds = [0.083, 0.107, 0.218]
    nrr_means = [0.852, 0.713, 0.171]
    spr_means = [0.216, 0.939, 0.841]
    colors_bar = ['#636363', '#e6550d', '#3182bd']
    hatches_bar = ['///', '', '\\\\']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5))

    x = np.arange(len(methods))
    bars = ax1.bar(x, auc_means, yerr=auc_stds, color=colors_bar,
                   edgecolor='black', lw=0.8, capsize=3, width=0.6)
    for bar, hatch in zip(bars, hatches_bar):
        bar.set_hatch(hatch)
    ax1.set_xticks(x)
    ax1.set_xticklabels(methods, fontsize=8)
    ax1.set_ylabel('ROC-AUC')
    ax1.set_ylim(0, 1.15)
    ax1.axhline(y=0.5, color='0.5', ls='--', lw=0.8, label='Chance')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_title('(a) Noise classification performance')
    for bar, val in zip(bars, auc_means):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=8)

    markers_scatter = ['o', 's', '^']
    for i, (nrr, spr, method) in enumerate(zip(nrr_means, spr_means, methods)):
        ax2.scatter(nrr, spr, s=100, c=colors_bar[i], edgecolors='black',
                    marker=markers_scatter[i],
                    lw=0.8, zorder=3, label=method.replace('\n', ' '))
    ax2.set_xlabel('Noise Removal Rate (NRR)')
    ax2.set_ylabel('Signal Preservation Rate (SPR)')
    ax2.set_xlim(0, 1.05)
    ax2.set_ylim(0, 1.05)
    ax2.legend(fontsize=7, loc='lower left')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('(b) NRR vs SPR trade-off')
    ax2.annotate('Ideal', xy=(1, 1), fontsize=8, ha='center',
                 xytext=(0.82, 0.88),
                 arrowprops=dict(arrowstyle='->', lw=0.8, color='0.4'),
                 color='0.4')

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig7_dvs_application.png')
    plt.close(fig)
    print("  -> fig7_dvs_application.png")


def fig6_mutual_information():
    """
    Fig. 6: Mutual information I(S;E) vs noise level.
    Analytical approximation based on event probability modulation.
    """
    print("Generating Fig. 6: Mutual information...")
    A = 0.3
    theta = 1.0
    sigma_range = np.linspace(0.1, 4.0, 200)
    rho_values = [0.0, 0.8]
    styles_fig6 = [('k', '-', 1.5), ('#d62728', '--', 1.5)]

    fig, ax = plt.subplots(1, 1, figsize=(5, 3.5))

    n_phase = 40  # phase bins for numerical integration
    phase_bins = np.linspace(0, 2 * np.pi, n_phase, endpoint=False)

    for rho, (col, ls, lw) in zip(rho_values, styles_fig6):
        mi_vals = []
        for sigma in sigma_range:
            sigma_eff = sigma * np.sqrt(max(1 - rho**2, 1e-12))
            if sigma_eff < 1e-10:
                mi_vals.append(0.0)
                continue
            # Two-sided event probability P(|s+n|>θ) for each phase
            s_vals = A * np.sin(phase_bins)
            sqrt2_sig = np.sqrt(2) * sigma_eff
            p_cond = (0.5 * erfc((theta - s_vals) / sqrt2_sig)
                      + 0.5 * erfc((theta + s_vals) / sqrt2_sig))
            # Marginal event probability (average over phases)
            p0 = np.mean(p_cond)
            if p0 < 1e-15 or p0 > 1 - 1e-15:
                mi_vals.append(0.0)
                continue
            # MI via KL divergence averaged over phase bins
            p_cond = np.clip(p_cond, 1e-15, 1 - 1e-15)
            mi = np.mean(
                p_cond * np.log2(p_cond / p0)
                + (1 - p_cond) * np.log2((1 - p_cond) / (1 - p0))
            )
            mi_vals.append(max(0, mi))

        label = r'$\rho=%.1f$' % rho if rho > 0 else r'No adjustment ($\rho=0$)'
        ax.plot(sigma_range / theta, mi_vals, color=col, ls=ls, lw=lw, label=label)

    ax.set_xlabel(r'Input noise level $\sigma_n / \theta$')
    ax.set_ylabel(r'Mutual information $I(S; E)$ [bits]')
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_xlim(0, 4)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / 'fig6_mutual_information.png')
    plt.close(fig)
    print("  -> fig6_mutual_information.png")


# ===================================================================

if __name__ == '__main__':
    print(f"Output directory: {OUT_DIR}")
    np.random.seed(2025)
    fig1_schematic()
    fig2_sr_curve()
    fig3_optimal_rho()
    fig4_detection_probability()
    fig5_roc_comparison()
    fig6_mutual_information()
    fig7_dvs_application()
    print("\nAll figures generated successfully.")
