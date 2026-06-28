#!/usr/bin/env python3
"""
Phase 2: Advanced PK analysis.

1. Nonlinear PK (hybrid MM) model for sticky chaos tails
2. Population PK (mass-ratio dependence)
3. TMDD reverse application

Requires: data/ from Julia simulations (threebody_scattering.jl + mass_scan.jl)
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.linalg import expm
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.advanced_pk_analysis import (
    compare_linear_vs_nonlinear,
    load_mass_scan,
    population_pk_analysis,
    fit_population_model,
    tmdd_three_body_analogy,
    tmdd_dose_response_bifurcation,
    tmdd_steady_states,
    tmdd_stability_analysis,
    nonlinear_pk_survival,
)

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")
FIGDIR = os.path.join(BASEDIR, "figures")
os.makedirs(FIGDIR, exist_ok=True)

PAIR_TO_COMP = {(1, 2): 0, (1, 3): 1, (2, 3): 2}


def load_results(name):
    with open(os.path.join(DATADIR, f"{name}.json")) as f:
        return json.load(f)


def extract_for_nonlinear(results):
    """Extract lifetimes, initial distribution, and linear rates."""
    lifetimes = []
    first_comp = np.zeros(3)
    trans = np.zeros((3, 3))
    esc_counts = np.zeros(3)
    dwell_times = {0: [], 1: [], 2: []}

    for r in results:
        if r["status"] != "escape" or not r["config_sequence"]:
            continue
        lifetimes.append(r["lifetime"])
        seq = r["config_sequence"]

        p0 = tuple(seq[0]["pair"])
        c0 = PAIR_TO_COMP.get(p0)
        if c0 is not None:
            first_comp[c0] += 1

        for k in range(len(seq) - 1):
            cf = PAIR_TO_COMP.get(tuple(seq[k]["pair"]))
            ct = PAIR_TO_COMP.get(tuple(seq[k+1]["pair"]))
            if cf is not None and ct is not None and cf != ct:
                trans[cf, ct] += 1

        for k in range(len(seq)):
            c = PAIR_TO_COMP.get(tuple(seq[k]["pair"]))
            if c is None:
                continue
            t_s = seq[k]["t"]
            t_e = seq[k+1]["t"] if k+1 < len(seq) else r["lifetime"]
            if t_e > t_s:
                dwell_times[c].append(t_e - t_s)

        lc = PAIR_TO_COMP.get(tuple(seq[-1]["pair"]))
        if lc is not None:
            esc_counts[lc] += 1

    P0 = first_comp / max(np.sum(first_comp), 1)
    T = np.array([sum(dwell_times[i]) if dwell_times[i] else 1e-10 for i in range(3)])

    rates = {}
    rate_names = ["k12", "k13", "k21", "k23", "k31", "k32"]
    rate_idx = [(0,1), (0,2), (1,0), (1,2), (2,0), (2,1)]
    for name_r, (i, j) in zip(rate_names, rate_idx):
        rates[name_r] = trans[i, j] / T[i]
    rates["ke1"] = esc_counts[0] / T[0]
    rates["ke2"] = esc_counts[1] / T[1]
    rates["ke3"] = esc_counts[2] / T[2]

    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                A[i, j] = trans[i, j] / T[i]
        ke_i = esc_counts[i] / T[i]
        A[i, i] = -(sum(trans[i, j] / T[i] for j in range(3) if j != i) + ke_i)

    return np.array(lifetimes), P0, A, rates


# ===================================================================
# FIGURE GENERATION
# ===================================================================

def fig6_nonlinear_comparison(results_dict):
    """Fig 6: Linear vs nonlinear PK model — sticky chaos tail."""
    configs = [
        ("equal_mass", "Equal mass (1:1:1)"),
        ("unequal_mass", "Unequal mass (1:2:0.5)"),
        ("democratic", "Democratic IC (1:1:1)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    fig.suptitle("Linear vs Nonlinear PK: Sticky Chaos Tail",
                 fontsize=14, fontweight="bold")

    for idx, (name, label) in enumerate(configs):
        if name not in results_dict:
            continue
        r = results_dict[name]
        ax = axes[idx]

        # Empirical
        ax.loglog(r["lt_sorted"], r["S_empirical"], "b.", ms=1, alpha=0.3,
                  label="N-body simulation")

        # Linear
        ax.loglog(r["t_grid"], np.maximum(r["S_linear"], 1e-15), "r-", lw=2,
                  label=f"Linear PK (RMSE={r['rmse_linear_tail']:.3f})")

        # Nonlinear
        ax.loglog(r["t_grid"], np.maximum(r["S_nonlinear"], 1e-15), "g--", lw=2,
                  label=f"Hybrid MM (RMSE={r['rmse_nonlinear_tail']:.3f})")

        # Power law reference
        if np.isfinite(r["alpha_power_law"]):
            t_ref = r["t_grid"]
            t_mid = np.percentile(r["lt_sorted"], 80)
            S_ref = 0.2 * (t_ref / t_mid) ** (-r["alpha_power_law"])
            ax.loglog(t_ref, S_ref, "k:", lw=1, alpha=0.5,
                      label=f"Power law (α={r['alpha_power_law']:.1f})")

        ax.set_xlabel("Lifetime (dynamical times)")
        ax.set_ylabel("Survival S(t)")
        ax.set_title(label)
        ax.legend(fontsize=7, loc="lower left")
        ax.set_ylim(1e-4, 1.5)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig6_nonlinear_comparison.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig6_nonlinear_comparison.png")
    plt.close()


def fig7_population_pk(pop_results):
    """Fig 7: Population PK — mass-ratio dependence of PK parameters."""
    if pop_results is None:
        print("  Skipping fig7 — no population data")
        return

    records = pop_results["records"]
    beta = pop_results["beta"]

    fig = plt.figure(figsize=(16, 12))
    fig.suptitle("Population PK: Mass-Ratio Dependence",
                 fontsize=14, fontweight="bold")

    # (a) MRT vs mu_out (reduced mass of third body)
    ax = fig.add_subplot(2, 3, 1)
    mu_out = [r["mu_out"] for r in records]
    mrt = [r["mrt"] for r in records]
    valid = [(m, rt) for m, rt in zip(mu_out, mrt) if rt > 0 and np.isfinite(rt)]
    if valid:
        mu_v, mrt_v = zip(*valid)
        ax.scatter(mu_v, mrt_v, s=20, c="steelblue", alpha=0.7)
        ax.set_xlabel("μ_out (reduced mass)")
        ax.set_ylabel("MRT (dynamical times)")
        ax.set_title("(a) MRT vs μ_out")
        ax.set_xscale("log")
        ax.set_yscale("log")

    # (b) Median lifetime vs m3 (mass of incoming body)
    ax = fig.add_subplot(2, 3, 2)
    m3_vals = [r["m3"] for r in records]
    lt_med = [r["lifetimes_median"] for r in records]
    ax.scatter(m3_vals, lt_med, s=20, c="coral", alpha=0.7)
    ax.set_xlabel("m₃ (incoming body mass)")
    ax.set_ylabel("Median lifetime")
    ax.set_title("(b) Median lifetime vs m₃")
    ax.set_xscale("log")
    ax.set_yscale("log")

    # (c) Mean excursions vs mass ratio
    ax = fig.add_subplot(2, 3, 3)
    q_min = [min(r["m1"], r["m2"], r["m3"]) / r["M"] for r in records]
    exc = [r["mean_excursions"] for r in records]
    ax.scatter(q_min, exc, s=20, c="forestgreen", alpha=0.7)
    ax.set_xlabel("q_min (lightest mass fraction)")
    ax.set_ylabel("Mean excursions")
    ax.set_title("(c) Excursions vs mass ratio")

    # (d) Escape probability of lightest body
    ax = fig.add_subplot(2, 3, 4)
    p_esc = pop_results["p_esc_lightest"]
    ax.scatter(q_min, p_esc, s=20, c="purple", alpha=0.7)
    ax.set_xlabel("q_min (lightest mass fraction)")
    ax.set_ylabel("P(lightest escapes)")
    ax.set_title("(d) Lightest body escape probability")
    ax.axhline(1/3, color="gray", ls="--", alpha=0.5, label="Equal probability")
    ax.legend(fontsize=8)

    # (e) Population PK model: predicted vs observed MRT
    ax = fig.add_subplot(2, 3, 5)
    valid_r = [r for r in records if r["mrt"] > 0 and np.isfinite(r["mrt"])]
    if valid_r and beta is not None:
        X = np.column_stack([
            np.ones(len(valid_r)),
            np.log([r["mu12"] for r in valid_r]),
            np.log([r["mu_out"] for r in valid_r]),
            np.log([r["M"] for r in valid_r]),
        ])
        y_obs = np.array([r["mrt"] for r in valid_r])
        y_pred = np.exp(X @ np.array(beta))

        ax.scatter(y_pred, y_obs, s=20, c="steelblue", alpha=0.7)
        lim = [min(min(y_pred), min(y_obs)) * 0.5,
               max(max(y_pred), max(y_obs)) * 2]
        ax.plot(lim, lim, "k--", alpha=0.4)
        ax.set_xlabel("Predicted MRT (population model)")
        ax.set_ylabel("Observed MRT")
        ax.set_title(f"(e) Pop PK fit (R²={pop_results['r_squared']:.3f})")
        ax.set_xscale("log")
        ax.set_yscale("log")

    # (f) Half-life heatmap: t½(γ) as function of m2, m3
    ax = fig.add_subplot(2, 3, 6)
    m2_unique = sorted(set(r["m2"] for r in records))
    m3_unique = sorted(set(r["m3"] for r in records))
    hl_matrix = np.full((len(m2_unique), len(m3_unique)), np.nan)
    for r in records:
        i = m2_unique.index(r["m2"])
        j = m3_unique.index(r["m3"])
        hl = sorted(r["half_lives"])
        if len(hl) >= 3 and np.isfinite(hl[2]) and hl[2] > 0:
            hl_matrix[i, j] = np.log10(hl[2])

    im = ax.imshow(hl_matrix, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(m3_unique)))
    ax.set_xticklabels([f"{m:.1f}" for m in m3_unique], fontsize=7)
    ax.set_yticks(range(len(m2_unique)))
    ax.set_yticklabels([f"{m:.1f}" for m in m2_unique], fontsize=7)
    ax.set_xlabel("m₃")
    ax.set_ylabel("m₂")
    ax.set_title("(f) log₁₀(t½(γ)) — slowest half-life")
    plt.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig7_population_pk.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig7_population_pk.png")
    plt.close()


def fig8_tmdd_analogy(bifurcation_data, base_params):
    """Fig 8: TMDD reverse application — bifurcation diagram."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("TMDD Reverse Application: Three-Body → Pharmacokinetics",
                 fontsize=14, fontweight="bold")

    doses = [d["dose"] for d in bifurcation_data]
    C_ss = [d["C_ss"] for d in bifurcation_data]
    R_ss = [d["R_ss"] for d in bifurcation_data]
    stable = [d["is_stable"] for d in bifurcation_data]

    # (a) Dose-response: C_ss vs dose
    ax = axes[0]
    for i, s in enumerate(stable):
        color = "steelblue" if s else "red"
        marker = "o" if s else "x"
        ax.scatter(doses[i], C_ss[i], c=color, s=10, marker=marker, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Dose rate (Input)")
    ax.set_ylabel("Steady-state drug conc. (C_ss)")
    ax.set_title("(a) Dose-response curve")
    ax.scatter([], [], c="steelblue", s=30, label="Stable")
    ax.scatter([], [], c="red", s=30, marker="x", label="Unstable")
    ax.legend(fontsize=8)

    # (b) Receptor occupancy: CR_ss / (R_ss + CR_ss) vs dose
    ax = axes[1]
    CR_ss = [d["CR_ss"] for d in bifurcation_data]
    occupancy = [cr / (r + cr + 1e-15) for r, cr in zip(R_ss, CR_ss)]
    for i, s in enumerate(stable):
        color = "steelblue" if s else "red"
        ax.scatter(doses[i], occupancy[i], c=color, s=10, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("Dose rate")
    ax.set_ylabel("Receptor occupancy")
    ax.set_title("(b) Receptor occupancy vs dose")

    # (c) Eigenvalue spectrum: slowest eigenvalue vs dose
    ax = axes[2]
    for d in bifurcation_data:
        eigs = d["eigenvalues_real"]
        slowest = max(eigs)  # least negative = slowest
        color = "steelblue" if d["is_stable"] else "red"
        ax.scatter(d["dose"], slowest, c=color, s=10, alpha=0.7)
    ax.set_xscale("log")
    ax.axhline(0, color="black", ls="-", lw=0.5)
    ax.set_xlabel("Dose rate")
    ax.set_ylabel("Slowest eigenvalue (real part)")
    ax.set_title("(c) Stability boundary\n(= Lagrange point analogy)")
    ax.fill_between([min(doses), max(doses)], 0, max(0.1, ax.get_ylim()[1]),
                    alpha=0.1, color="red", label="Unstable region")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig8_tmdd_analogy.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig8_tmdd_analogy.png")
    plt.close()


def fig9_synthesis_table(nl_results, pop_results):
    """Fig 9: Synthesis table — three-body ↔ PK dictionary."""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")

    rows = [
        ["Compartment i", "Binary configuration (pair i bound)",
         "Drug/receptor/complex state"],
        ["Transfer rate k_ij", "Config i→j transition rate\n(phase-space flux)",
         "Drug-receptor association/\ndissociation rate"],
        ["Elimination k_ei", "Escape rate (system dissolution)",
         "Drug elimination / receptor\ninternalisation"],
        ["Half-life t½(α,β,γ)", "Three timescales of resonant\ninteraction",
         "Distribution, redistribution,\nelimination half-lives"],
        ["MRT", "Mean lifetime of 3-body\nencounter",
         "Mean residence time of drug\nin body"],
        ["AUC", "Cumulative time in resonant\nstate",
         "Total drug exposure"],
        ["Population PK\n(mixed effects)", "Mass-ratio dependence:\nMRT ∝ μ^a₁·M^a₃ ± η",
         "Allometric scaling:\nCL = CL_ref·(BW/70)^α ± η"],
        ["Nonlinear PK\n(Michaelis-Menten)", "Sticky chaos: saturated escape\nrate → power-law tail",
         "Saturable elimination:\nV_max·C/(K_m+C)"],
        ["Bifurcation\nanalysis", "Stability boundary\n(Mardling-Aarseth criterion)",
         "Dose-response bifurcation\n(therapeutic window)"],
        ["Jacobian eigenvalues", "Lagrange point stability",
         "Steady-state stability\n(therapeutic vs toxic)"],
    ]

    cols = ["PK concept", "Three-body interpretation", "TMDD interpretation"]

    table = ax.table(cellText=rows, colLabels=cols, loc="center",
                     cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 2.2)

    for j in range(len(cols)):
        table[(0, j)].set_facecolor("#2E4057")
        table[(0, j)].set_text_props(color="white", fontweight="bold", fontsize=10)

    # Alternate row colors
    for i in range(1, len(rows) + 1):
        color = "#f0f4f8" if i % 2 == 0 else "white"
        for j in range(len(cols)):
            table[(i, j)].set_facecolor(color)

    ax.set_title("Three-body ↔ Pharmacokinetics: Complete Dictionary",
                 fontsize=15, fontweight="bold", pad=30)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig9_synthesis_table.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig9_synthesis_table.png")
    plt.close()


# ===================================================================
# MAIN
# ===================================================================

def main():
    print("=" * 60)
    print("  Phase 2: Advanced PK Analysis")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Nonlinear PK model for sticky chaos
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  MODULE 1: Nonlinear PK (Michaelis-Menten) for sticky chaos")
    print(f"{'=' * 60}")

    nl_results = {}
    for name, label in [("equal_mass", "Equal mass"),
                         ("unequal_mass", "Unequal mass"),
                         ("democratic", "Democratic")]:
        print(f"\n  --- {label} ---")
        try:
            results = load_results(name)
            lifetimes, P0, A, rates = extract_for_nonlinear(results)
            if len(lifetimes) < 50:
                print(f"    Too few escapes ({len(lifetimes)}). Skipping.")
                continue
            nl = compare_linear_vs_nonlinear(lifetimes, P0, A, rates)
            nl_results[name] = nl
        except Exception as e:
            print(f"    Error: {e}")

    if nl_results:
        fig6_nonlinear_comparison(nl_results)

    # ------------------------------------------------------------------
    # 2. Population PK (mass-ratio scan)
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  MODULE 2: Population PK (mass-ratio dependence)")
    print(f"{'=' * 60}")

    pop_results = None
    mass_scan_path = os.path.join(DATADIR, "mass_scan.json")
    if os.path.exists(mass_scan_path):
        scan_data = load_mass_scan(DATADIR)
        print(f"  Loaded {len(scan_data)} mass configurations")

        records = population_pk_analysis(scan_data)
        print(f"  Analysed {len(records)} configurations")

        print("\n  Fitting population model...")
        pop_results = fit_population_model(records)

        fig7_population_pk(pop_results)
    else:
        print(f"  Mass scan data not found at {mass_scan_path}")
        print("  Run: julia simulations/mass_scan.jl")

    # ------------------------------------------------------------------
    # 3. TMDD reverse application
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  MODULE 3: TMDD Reverse Application")
    print(f"{'=' * 60}")

    base_params, bifurcation = tmdd_three_body_analogy()
    fig8_tmdd_analogy(bifurcation, base_params)

    # ------------------------------------------------------------------
    # 4. Synthesis
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  MODULE 4: Synthesis Table")
    print(f"{'=' * 60}")

    fig9_synthesis_table(nl_results, pop_results)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")

    if nl_results:
        print("\n  Nonlinear PK results:")
        for name, nl in nl_results.items():
            print(f"    {name}:")
            print(f"      Linear tail RMSE:    {nl['rmse_linear_tail']:.4f}")
            print(f"      Nonlinear tail RMSE: {nl['rmse_nonlinear_tail']:.4f}")
            improvement = (nl["rmse_linear_tail"] - nl["rmse_nonlinear_tail"]) / nl["rmse_linear_tail"] * 100
            print(f"      Improvement:         {improvement:.1f}%")
            print(f"      Power-law exponent:  α = {nl['alpha_power_law']:.2f}")

    if pop_results:
        print(f"\n  Population PK model:")
        print(f"    R² = {pop_results['r_squared']:.4f}")
        print(f"    ω (inter-individual variability) = {pop_results['omega']:.4f}")
        b = pop_results["beta"]
        print(f"    MRT ∝ μ12^{b[1]:.2f} · μ_out^{b[2]:.2f} · M^{b[3]:.2f}")

    print(f"\n  All figures saved to: {FIGDIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
