#!/usr/bin/env python3
"""
Proof of concept: Three-body scattering as a pharmacokinetic compartment model.

This script:
1. Runs an ensemble of three-body scattering simulations
2. Extracts transition counts and dwell times (= PK observables)
3. Fits a 3-compartment PK model to the data
4. Compares the PK-predicted lifetime distribution to the numerical data
5. Tests whether a nonlinear (MM) model better captures the power-law tail
6. Generates publication-quality figures

Output: figures/ directory with PNG files + summary statistics to stdout.
"""

from __future__ import annotations

import sys
import os
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import expon, kstest

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulations.threebody_scattering import (
    run_scattering_ensemble,
    ThreeBodyState,
)
from analysis.pk_compartment_model import (
    outcomes_to_transition_counts,
    estimate_pk_params_from_counts,
    fit_pk_params_to_lifetime_distribution,
    linear_pk_survival,
    linear_pk_escape_pdf,
    nonlinear_pk_survival,
    NonlinearPKParams,
    pk_summary,
    phase_space_flux_rates,
    PAIR_TO_COMPARTMENT,
)


FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIGDIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Run scattering ensemble
# ---------------------------------------------------------------------------

def run_ensemble(n_runs: int = 2000, seed: int = 42):
    """Run scattering simulations for equal-mass and unequal-mass cases."""
    print("=" * 60)
    print("PHASE 1: Three-body scattering simulations")
    print("=" * 60)

    configs = {
        "equal_mass": {
            "masses": (1.0, 1.0, 1.0),
            "mode": "binary_single",
            "kwargs": {"v_inf": 0.8, "b_max": 4.0},
        },
        "unequal_mass": {
            "masses": (1.0, 2.0, 0.5),
            "mode": "binary_single",
            "kwargs": {"v_inf": 0.8, "b_max": 4.0},
        },
        "democratic": {
            "masses": (1.0, 1.0, 1.0),
            "mode": "democratic",
            "kwargs": {},
        },
    }

    all_results = {}
    for name, cfg in configs.items():
        print(f"\n--- {name} ({n_runs} runs) ---")
        t0 = time.time()
        results = run_scattering_ensemble(
            n_runs,
            masses=cfg["masses"],
            mode=cfg["mode"],
            seed=seed,
            **cfg["kwargs"],
        )
        elapsed = time.time() - t0

        n_esc = sum(1 for r in results if r.status == "escape")
        n_col = sum(1 for r in results if r.status == "collision")
        n_to = sum(1 for r in results if r.status == "timeout")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Results: {n_esc} escapes, {n_col} collisions, {n_to} timeouts")

        if n_esc > 0:
            lifetimes = [r.lifetime for r in results if r.status == "escape"]
            print(f"  Lifetime: median={np.median(lifetimes):.2f}, "
                  f"mean={np.mean(lifetimes):.2f}")
            excursions = [r.n_excursions for r in results if r.status == "escape"]
            print(f"  Excursions: median={np.median(excursions):.0f}, "
                  f"mean={np.mean(excursions):.1f}")

            # Energy conservation check
            dE = [abs((r.final_energy - r.initial_energy) /
                      (abs(r.initial_energy) + 1e-30))
                  for r in results if r.status == "escape"]
            print(f"  Energy conservation: max|dE/E|={max(dE):.2e}")

        all_results[name] = results

    return all_results


# ---------------------------------------------------------------------------
# 2. PK analysis
# ---------------------------------------------------------------------------

def analyse_pk(results: list, label: str, masses: tuple):
    """Fit PK model and generate comparison plots."""
    print(f"\n{'=' * 60}")
    print(f"PHASE 2: PK compartmental analysis — {label}")
    print(f"{'=' * 60}")

    escaped = [r for r in results if r.status == "escape" and r.n_excursions > 0]
    if len(escaped) < 10:
        print(f"  Too few escaped systems with excursions ({len(escaped)}). Skipping.")
        return None

    # Extract transition data
    data = outcomes_to_transition_counts(escaped)
    print(f"\n  Transition matrix (counts):")
    labels = ["(0,1)+2", "(0,2)+1", "(1,2)+0"]
    print(f"  {'':>10s}  {'→(0,1)+2':>10s}  {'→(0,2)+1':>10s}  {'→(1,2)+0':>10s}")
    for i in range(3):
        print(f"  {labels[i]:>10s}  {data['transition_matrix'][i,0]:>10d}  "
              f"{data['transition_matrix'][i,1]:>10d}  "
              f"{data['transition_matrix'][i,2]:>10d}")

    print(f"\n  Escape counts: {data['escape_counts']}")
    print(f"  Total excursions: {sum(data['n_excursions'])}")

    # 2a. Estimate rates from counts (CTMC MLE)
    params_mle = estimate_pk_params_from_counts(data)
    print(f"\n  MLE rate estimates:")
    print(f"    k12={params_mle.k12:.4f}  k13={params_mle.k13:.4f}")
    print(f"    k21={params_mle.k21:.4f}  k23={params_mle.k23:.4f}")
    print(f"    k31={params_mle.k31:.4f}  k32={params_mle.k32:.4f}")
    print(f"    ke1={params_mle.ke1:.4f}  ke2={params_mle.ke2:.4f}  ke3={params_mle.ke3:.4f}")

    summary_mle = pk_summary(params_mle)
    print(f"\n  PK summary (MLE):")
    print(f"    Half-lives: {summary_mle['half_lives']}")
    print(f"    Mean lifetime (MRT): {summary_mle['mean_lifetime']:.2f}")

    # 2b. Phase-space flux prediction
    params_flux = phase_space_flux_rates(masses, E_total=-0.5)
    summary_flux = pk_summary(params_flux)
    print(f"\n  PK summary (phase-space flux):")
    print(f"    Half-lives: {summary_flux['half_lives']}")
    print(f"    Mean lifetime (MRT): {summary_flux['mean_lifetime']:.2f}")

    # 2c. Numerical lifetime data
    lifetimes = np.array(data["lifetimes"])

    # 2d. Fit PK params to lifetime distribution (if we have enough data)
    params_fit = None
    if len(lifetimes) > 50:
        print(f"\n  Fitting PK model to lifetime distribution ({len(lifetimes)} samples)...")
        try:
            params_fit, nll = fit_pk_params_to_lifetime_distribution(
                lifetimes, method="differential_evolution"
            )
            print(f"    Neg-log-likelihood: {nll:.2f}")
            print(f"    k12={params_fit.k12:.4f}  k13={params_fit.k13:.4f}")
            print(f"    ke1={params_fit.ke1:.4f}  ke2={params_fit.ke2:.4f}  ke3={params_fit.ke3:.4f}")
            summary_fit = pk_summary(params_fit)
            print(f"    Half-lives: {summary_fit['half_lives']}")
            print(f"    Mean lifetime (MRT): {summary_fit['mean_lifetime']:.2f}")
        except Exception as e:
            print(f"    Fitting failed: {e}")

    return {
        "data": data,
        "lifetimes": lifetimes,
        "params_mle": params_mle,
        "params_flux": params_flux,
        "params_fit": params_fit,
        "summary_mle": summary_mle,
        "summary_flux": summary_flux,
        "label": label,
        "masses": masses,
    }


# ---------------------------------------------------------------------------
# 3. Figures
# ---------------------------------------------------------------------------

def plot_conceptual_mapping(save: bool = True):
    """Fig 1: Conceptual diagram of the three-body ↔ PK mapping."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: three-body configurations
    ax = axes[0]
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_aspect("equal")
    ax.set_title("Three-body scattering\n(resonant encounter)", fontsize=13)

    # Draw three configurations
    configs = [
        {"pair": (0, 1), "single": 2, "color": "#e41a1c", "pos": (0, 1.5)},
        {"pair": (0, 2), "single": 1, "color": "#377eb8", "pos": (-1.5, -1)},
        {"pair": (1, 2), "single": 0, "color": "#4daf4a", "pos": (1.5, -1)},
    ]

    for cfg in configs:
        cx, cy = cfg["pos"]
        # Binary as two dots close together
        ax.plot([cx - 0.2, cx + 0.2], [cy, cy], "o-", color=cfg["color"],
                markersize=10, linewidth=2)
        # Single dot far away
        angle = np.arctan2(cy, cx) + np.pi
        sx = cx + 0.8 * np.cos(angle)
        sy = cy + 0.8 * np.sin(angle)
        ax.plot(sx, sy, "o", color=cfg["color"], markersize=8, alpha=0.5)
        ax.annotate(f"({cfg['pair'][0]},{cfg['pair'][1]})+{cfg['single']}",
                    (cx, cy - 0.4), ha="center", fontsize=9, color=cfg["color"])

    # Arrows between configurations
    arrow_style = dict(arrowstyle="<->", color="gray", lw=1.5)
    for i in range(3):
        for j in range(i + 1, 3):
            c1 = configs[i]["pos"]
            c2 = configs[j]["pos"]
            mid = ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2)
            ax.annotate("", c2, c1, arrowprops=arrow_style)
            ax.text(mid[0], mid[1], f"k{i+1}{j+1}", fontsize=8,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))

    # Escape arrows
    for i, cfg in enumerate(configs):
        cx, cy = cfg["pos"]
        angle = np.arctan2(cy, cx)
        ax.annotate("", (cx + 1.2 * np.cos(angle), cy + 1.2 * np.sin(angle)),
                    (cx + 0.5 * np.cos(angle), cy + 0.5 * np.sin(angle)),
                    arrowprops=dict(arrowstyle="->", color="red", lw=1.5))
        ax.text(cx + 1.4 * np.cos(angle), cy + 1.4 * np.sin(angle),
                f"ke{i+1}", fontsize=8, color="red", ha="center")

    ax.axis("off")

    # Right: PK compartment diagram
    ax = axes[1]
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_aspect("equal")
    ax.set_title("Pharmacokinetic compartment model\n(3-compartment + elimination)",
                 fontsize=13)

    compartments = [
        {"label": "C₁\n(0,1)+2", "pos": (0, 1.5), "color": "#e41a1c"},
        {"label": "C₂\n(0,2)+1", "pos": (-1.5, -1), "color": "#377eb8"},
        {"label": "C₃\n(1,2)+0", "pos": (1.5, -1), "color": "#4daf4a"},
    ]

    for comp in compartments:
        cx, cy = comp["pos"]
        circle = plt.Circle((cx, cy), 0.6, fill=True, fc=comp["color"],
                             alpha=0.2, ec=comp["color"], lw=2)
        ax.add_patch(circle)
        ax.text(cx, cy, comp["label"], ha="center", va="center",
                fontsize=10, fontweight="bold")

    # Transfer arrows
    for i in range(3):
        for j in range(i + 1, 3):
            c1 = np.array(compartments[i]["pos"])
            c2 = np.array(compartments[j]["pos"])
            d = c2 - c1
            d_norm = d / np.linalg.norm(d)
            perp = np.array([-d_norm[1], d_norm[0]]) * 0.1

            start = c1 + 0.65 * d_norm + perp
            end = c2 - 0.65 * d_norm + perp
            ax.annotate("", end, start,
                        arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))

            start2 = c2 - 0.65 * d_norm - perp
            end2 = c1 + 0.65 * d_norm - perp
            ax.annotate("", end2, start2,
                        arrowprops=dict(arrowstyle="->", color="gray", lw=1.5))

    # Elimination arrows
    for i, comp in enumerate(compartments):
        cx, cy = comp["pos"]
        angle = np.arctan2(cy, cx)
        ax.annotate("escape", (cx + 1.5 * np.cos(angle), cy + 1.5 * np.sin(angle)),
                    (cx + 0.65 * np.cos(angle), cy + 0.65 * np.sin(angle)),
                    arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
                    fontsize=8, color="red", ha="center")

    ax.axis("off")

    plt.tight_layout()
    if save:
        path = os.path.join(FIGDIR, "fig1_conceptual_mapping.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print(f"  Saved: {path}")
    plt.close()


def plot_lifetime_distribution(analysis: dict, save: bool = True):
    """Fig 2: Lifetime distribution — numerical vs PK prediction."""
    lifetimes = analysis["lifetimes"]
    params_mle = analysis["params_mle"]
    label = analysis["label"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 2a: Histogram + PK PDF (linear scale)
    ax = axes[0]
    t_max = np.percentile(lifetimes, 99)
    t_grid = np.linspace(0.01, t_max, 300)

    ax.hist(lifetimes, bins=50, density=True, alpha=0.6, color="steelblue",
            label="Numerical (N-body)", range=(0, t_max))

    pdf_mle = linear_pk_escape_pdf(t_grid, params_mle)
    ax.plot(t_grid, pdf_mle, "r-", lw=2, label="Linear PK model (MLE)")

    if analysis["params_fit"] is not None:
        pdf_fit = linear_pk_escape_pdf(t_grid, analysis["params_fit"])
        ax.plot(t_grid, pdf_fit, "g--", lw=2, label="Linear PK model (MLE-lifetime)")

    ax.set_xlabel("Lifetime (dynamical times)")
    ax.set_ylabel("Probability density")
    ax.set_title(f"Lifetime distribution — {label}")
    ax.legend(fontsize=8)

    # 2b: Survival curve (semi-log)
    ax = axes[1]
    sorted_lt = np.sort(lifetimes)
    S_empirical = 1 - np.arange(1, len(sorted_lt) + 1) / len(sorted_lt)

    ax.semilogy(sorted_lt, S_empirical, "b.", markersize=2, alpha=0.5,
                label="Numerical")

    S_pk = linear_pk_survival(t_grid, params_mle)
    ax.semilogy(t_grid, S_pk, "r-", lw=2, label="Linear PK model")

    # Pure exponential for comparison
    rate_exp = 1.0 / np.mean(lifetimes)
    ax.semilogy(t_grid, np.exp(-rate_exp * t_grid), "k--", lw=1,
                label="Single exponential", alpha=0.5)

    ax.set_xlabel("Lifetime")
    ax.set_ylabel("Survival probability S(t)")
    ax.set_title("Survival curve (semi-log)")
    ax.legend(fontsize=8)

    # 2c: Log-log survival (to check power-law tails)
    ax = axes[2]
    mask = S_empirical > 0
    ax.loglog(sorted_lt[mask], S_empirical[mask], "b.", markersize=2, alpha=0.5,
              label="Numerical")
    ax.loglog(t_grid, np.maximum(S_pk, 1e-10), "r-", lw=2,
              label="Linear PK (exponential)")

    ax.set_xlabel("Lifetime")
    ax.set_ylabel("Survival probability S(t)")
    ax.set_title("Log-log survival (power-law tail?)")
    ax.legend(fontsize=8)

    plt.tight_layout()
    if save:
        path = os.path.join(FIGDIR, f"fig2_lifetime_{label.replace(' ', '_')}.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print(f"  Saved: {path}")
    plt.close()


def plot_transition_matrix_comparison(analysis: dict, save: bool = True):
    """Fig 3: Transition rates — MLE vs phase-space flux prediction."""
    label = analysis["label"]
    params_mle = analysis["params_mle"]
    params_flux = analysis["params_flux"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Rate comparison
    rate_names = ["k12", "k13", "k21", "k23", "k31", "k32", "ke1", "ke2", "ke3"]
    mle_vals = params_mle.to_vector()
    flux_vals = params_flux.to_vector()

    # Normalise flux rates to have same total rate as MLE
    flux_vals_norm = flux_vals * (np.sum(mle_vals) / np.sum(flux_vals))

    ax = axes[0]
    x = np.arange(len(rate_names))
    width = 0.35
    ax.bar(x - width / 2, mle_vals, width, label="MLE (from simulation)",
           color="steelblue", alpha=0.8)
    ax.bar(x + width / 2, flux_vals_norm, width, label="Phase-space flux (theory)",
           color="coral", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(rate_names, rotation=45)
    ax.set_ylabel("Rate constant")
    ax.set_title(f"Rate comparison — {label}")
    ax.legend()

    # Scatter plot: MLE vs theory
    ax = axes[1]
    ax.scatter(flux_vals_norm, mle_vals, s=60, c="steelblue", edgecolors="navy")
    for i, name in enumerate(rate_names):
        ax.annotate(name, (flux_vals_norm[i], mle_vals[i]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)

    lims = [0, max(max(mle_vals), max(flux_vals_norm)) * 1.2]
    ax.plot(lims, lims, "k--", alpha=0.5, label="y = x")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Phase-space flux prediction")
    ax.set_ylabel("MLE from simulation")
    ax.set_title("Theory vs simulation")
    ax.legend()
    ax.set_aspect("equal")

    plt.tight_layout()
    if save:
        path = os.path.join(FIGDIR, f"fig3_rates_{label.replace(' ', '_')}.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print(f"  Saved: {path}")
    plt.close()


def plot_pk_summary_table(analyses: list[dict], save: bool = True):
    """Fig 4: Summary table of PK parameters across mass configurations."""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")

    col_labels = ["Configuration", "t₁/₂(α)", "t₁/₂(β)", "t₁/₂(γ)",
                  "MRT", "CL", "Escaper\nprobability"]
    rows = []
    for a in analyses:
        if a is None:
            continue
        s = a["summary_mle"]
        hl = sorted(s["half_lives"])
        esc = a["data"]["escape_counts"]
        esc_prob = esc / max(np.sum(esc), 1)
        rows.append([
            a["label"],
            f"{hl[0]:.3f}",
            f"{hl[1]:.3f}" if len(hl) > 1 else "—",
            f"{hl[2]:.3f}" if len(hl) > 2 else "—",
            f"{s['mean_lifetime']:.2f}",
            f"{s['clearance']:.3f}",
            f"[{esc_prob[0]:.2f}, {esc_prob[1]:.2f}, {esc_prob[2]:.2f}]",
        ])

    table = ax.table(cellText=rows, colLabels=col_labels,
                     loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.5)

    # Header style
    for j in range(len(col_labels)):
        table[(0, j)].set_facecolor("#4472C4")
        table[(0, j)].set_text_props(color="white", fontweight="bold")

    ax.set_title("PK-style summary of three-body scattering", fontsize=14,
                 fontweight="bold", pad=20)

    plt.tight_layout()
    if save:
        path = os.path.join(FIGDIR, "fig4_pk_summary_table.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print(f"  Saved: {path}")
    plt.close()


def plot_excursion_distribution(analyses: list[dict], save: bool = True):
    """Supplementary: Distribution of number of excursions."""
    fig, axes = plt.subplots(1, len([a for a in analyses if a]),
                             figsize=(5 * len([a for a in analyses if a]), 4))
    if not hasattr(axes, "__len__"):
        axes = [axes]

    idx = 0
    for a in analyses:
        if a is None:
            continue
        ax = axes[idx]
        exc = a["data"]["n_excursions"]
        ax.hist(exc, bins=range(0, max(exc) + 2), density=True,
                alpha=0.7, color="steelblue", edgecolor="navy")
        ax.set_xlabel("Number of excursions")
        ax.set_ylabel("Probability")
        ax.set_title(f"{a['label']}")

        # Geometric distribution fit (expected for Markov chain)
        p_esc = 1.0 / (np.mean(exc) + 1) if np.mean(exc) > 0 else 1.0
        k_range = np.arange(0, max(exc) + 1)
        geom_pmf = (1 - p_esc) ** k_range * p_esc
        ax.plot(k_range, geom_pmf, "r-o", markersize=4, lw=1.5,
                label=f"Geometric(p={p_esc:.3f})")
        ax.legend(fontsize=8)
        idx += 1

    plt.tight_layout()
    if save:
        path = os.path.join(FIGDIR, "fig_supp_excursion_dist.png")
        fig.savefig(path, dpi=200, bbox_inches="tight")
        print(f"  Saved: {path}")
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Three-body scattering as a PK compartment model")
    print("Proof of concept")
    print("=" * 60)

    # Run simulations
    n_runs = 2000
    all_results = run_ensemble(n_runs=n_runs, seed=42)

    # PK analysis
    analyses = []
    for name, cfg in [
        ("equal_mass", (1.0, 1.0, 1.0)),
        ("unequal_mass", (1.0, 2.0, 0.5)),
        ("democratic", (1.0, 1.0, 1.0)),
    ]:
        if name in all_results:
            a = analyse_pk(all_results[name], name, cfg)
            analyses.append(a)

    # Generate figures
    print(f"\n{'=' * 60}")
    print("PHASE 3: Generating figures")
    print("=" * 60)

    plot_conceptual_mapping()
    for a in analyses:
        if a is not None:
            plot_lifetime_distribution(a)
            plot_transition_matrix_comparison(a)
    plot_pk_summary_table(analyses)
    plot_excursion_distribution(analyses)

    # Goodness-of-fit tests
    print(f"\n{'=' * 60}")
    print("PHASE 4: Goodness-of-fit tests")
    print("=" * 60)

    for a in analyses:
        if a is None:
            continue
        lt = a["lifetimes"]
        if len(lt) < 10:
            continue

        # KS test: exponential fit
        scale = np.mean(lt)
        ks_stat, ks_p = kstest(lt, "expon", args=(0, scale))
        print(f"\n  {a['label']}:")
        print(f"    KS test (single exponential): D={ks_stat:.4f}, p={ks_p:.4f}")
        if ks_p < 0.05:
            print(f"    → REJECT single exponential (multi-exponential / power-law needed)")
        else:
            print(f"    → Cannot reject single exponential")

    print(f"\n{'=' * 60}")
    print("DONE. Figures saved to:", FIGDIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
