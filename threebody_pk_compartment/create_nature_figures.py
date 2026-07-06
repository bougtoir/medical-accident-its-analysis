#!/usr/bin/env python3
"""
Generate publication-quality figures for Nature submission.

Nature requirements:
- Single column: 89 mm (3.5 in); double column: 183 mm (7.2 in)
- Minimum 300 DPI
- Font: 5-7 pt (axis labels), 8 pt (panel labels)
- Colours: colour-blind safe palette
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
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.patheffects as pe
from scipy.linalg import expm
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")
FIGDIR = os.path.join(BASEDIR, "figures_nature")
os.makedirs(FIGDIR, exist_ok=True)

# Nature colour-blind safe palette
CB_BLUE = "#0072B2"
CB_ORANGE = "#E69F00"
CB_GREEN = "#009E73"
CB_RED = "#D55E00"
CB_PURPLE = "#CC79A7"
CB_CYAN = "#56B4E9"
CB_YELLOW = "#F0E442"
CB_BLACK = "#000000"

# Global matplotlib settings for Nature
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.titlesize": 8,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "legend.fontsize": 6,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "lines.linewidth": 1.0,
})

PAIR_TO_COMP = {(1, 2): 0, (1, 3): 1, (2, 3): 2}


def load_results(name):
    with open(os.path.join(DATADIR, f"{name}.json")) as f:
        return json.load(f)


def extract_lifetimes_and_rates(results):
    """Extract lifetimes and MLE rates from simulation results."""
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
                # A[j,i] = rate from i to j (column-vector convention: dp/dt = A@p)
                A[j, i] = trans[i, j] / T[i]
        ke_i = esc_counts[i] / T[i]
        A[i, i] = -(sum(trans[i, j] / T[i] for j in range(3) if j != i) + ke_i)

    return np.array(lifetimes), P0, A, rates


# ===========================================================================
# FIGURE 1: Conceptual mapping (schematic)
# ===========================================================================

def fig1_conceptual():
    """Figure 1: Conceptual mapping between three-body and PK."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.0))

    # Left: Three-body schematic
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.2, 1.4)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("a", fontweight="bold", fontsize=9, loc="left", x=-0.05)

    # Three configurations as triangles
    configs = [
        {"pos": (-0.8, 0.5), "label": "Config 1\n(1,2) + 3",
         "color": CB_BLUE, "binary": [(-.95, 0.6), (-.65, 0.6)], "single": (-.8, 0.3)},
        {"pos": (0.8, 0.5), "label": "Config 2\n(1,3) + 2",
         "color": CB_ORANGE, "binary": [(.65, 0.6), (.95, 0.6)], "single": (.8, 0.3)},
        {"pos": (0.0, -0.5), "label": "Config 3\n(2,3) + 1",
         "color": CB_GREEN, "binary": [(-.15, -0.4), (.15, -0.4)], "single": (0.0, -0.7)},
    ]

    for cfg in configs:
        rect = FancyBboxPatch(
            (cfg["pos"][0] - 0.45, cfg["pos"][1] - 0.35), 0.9, 0.7,
            boxstyle="round,pad=0.05", facecolor=cfg["color"], alpha=0.15,
            edgecolor=cfg["color"], linewidth=1.0
        )
        ax1.add_patch(rect)
        ax1.text(cfg["pos"][0], cfg["pos"][1] + 0.1, cfg["label"],
                 ha="center", va="center", fontsize=6, fontweight="bold")

    # Arrows between configs
    arrow_style = "Simple,tail_width=0.3,head_width=3,head_length=2"
    for (i, j), label in [((0, 1), "$k_{12}$"), ((1, 0), "$k_{21}$"),
                           ((0, 2), "$k_{13}$"), ((2, 0), "$k_{31}$"),
                           ((1, 2), "$k_{23}$"), ((2, 1), "$k_{32}$")]:
        start = np.array(configs[i]["pos"])
        end = np.array(configs[j]["pos"])
        mid = (start + end) / 2
        direction = end - start
        direction = direction / np.linalg.norm(direction)
        offset = np.array([-direction[1], direction[0]]) * 0.08

        ax1.annotate("", xy=end - direction * 0.4,
                     xytext=start + direction * 0.4,
                     arrowprops=dict(arrowstyle="->", color="gray",
                                     lw=0.8, connectionstyle="arc3,rad=0.15"))

    # Escape arrows
    for idx, cfg in enumerate(configs):
        ax1.annotate("", xy=(cfg["pos"][0], cfg["pos"][1] - 0.6),
                     xytext=(cfg["pos"][0], cfg["pos"][1] - 0.35),
                     arrowprops=dict(arrowstyle="->", color=CB_RED, lw=1.0))
    ax1.text(0.0, -1.1, "Escape (elimination)", ha="center", fontsize=6,
             color=CB_RED, fontstyle="italic")

    ax1.text(0.0, 1.3, "Three-body scattering", ha="center",
             fontsize=8, fontweight="bold")

    # Right: PK compartment diagram
    ax2.set_xlim(-1.5, 1.5)
    ax2.set_ylim(-1.2, 1.4)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("b", fontweight="bold", fontsize=9, loc="left", x=-0.05)

    comps = [
        {"pos": (-0.8, 0.5), "label": "Compartment 1\n(Central)",
         "color": CB_BLUE},
        {"pos": (0.8, 0.5), "label": "Compartment 2\n(Peripheral 1)",
         "color": CB_ORANGE},
        {"pos": (0.0, -0.5), "label": "Compartment 3\n(Peripheral 2)",
         "color": CB_GREEN},
    ]

    for comp in comps:
        rect = FancyBboxPatch(
            (comp["pos"][0] - 0.45, comp["pos"][1] - 0.35), 0.9, 0.7,
            boxstyle="round,pad=0.05", facecolor=comp["color"], alpha=0.15,
            edgecolor=comp["color"], linewidth=1.0
        )
        ax2.add_patch(rect)
        ax2.text(comp["pos"][0], comp["pos"][1] + 0.1, comp["label"],
                 ha="center", va="center", fontsize=6, fontweight="bold")

    # Transfer arrows
    for (i, j) in [(0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1)]:
        start = np.array(comps[i]["pos"])
        end = np.array(comps[j]["pos"])
        direction = end - start
        direction = direction / np.linalg.norm(direction)
        ax2.annotate("", xy=end - direction * 0.4,
                     xytext=start + direction * 0.4,
                     arrowprops=dict(arrowstyle="->", color="gray",
                                     lw=0.8, connectionstyle="arc3,rad=0.15"))

    # Elimination arrows
    for comp in comps:
        ax2.annotate("", xy=(comp["pos"][0], comp["pos"][1] - 0.6),
                     xytext=(comp["pos"][0], comp["pos"][1] - 0.35),
                     arrowprops=dict(arrowstyle="->", color=CB_RED, lw=1.0))
    ax2.text(0.0, -1.1, "Elimination ($k_{e}$)", ha="center", fontsize=6,
             color=CB_RED, fontstyle="italic")

    ax2.text(0.0, 1.3, "Pharmacokinetic model", ha="center",
             fontsize=8, fontweight="bold")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_conceptual.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig1_conceptual.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig1_conceptual")


# ===========================================================================
# FIGURE 2: Lifetime distributions + linear PK fit
# ===========================================================================

def fig2_lifetime_distributions():
    """Figure 2: Survival curves with PK model fits."""
    configs = [
        ("equal_mass", "Equal mass (1:1:1)", [1.0, 1.0, 1.0]),
        ("unequal_mass", "Unequal mass (1:2:0.5)", [1.0, 2.0, 0.5]),
        ("democratic", "Democratic IC (1:1:1)", [1.0, 1.0, 1.0]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

    for idx, (name, label, masses) in enumerate(configs):
        ax = axes[idx]
        results = load_results(name)
        lifetimes, P0, A, rates = extract_lifetimes_and_rates(results)

        lt = np.sort(lifetimes)
        S_emp = 1 - np.arange(1, len(lt) + 1) / len(lt)

        # Linear PK prediction
        t_grid = np.logspace(np.log10(max(lt[0], 0.1)), np.log10(lt[-1]), 300)
        S_pk = np.array([np.sum(expm(A * t) @ P0) for t in t_grid])

        # Plot
        ax.loglog(lt, S_emp, ".", color=CB_BLUE, ms=1, alpha=0.3,
                  rasterized=True)
        ax.loglog(t_grid, np.maximum(S_pk, 1e-15), "-", color=CB_RED, lw=1.2)

        ax.set_xlabel("Lifetime ($t / t_{\\rm dyn}$)")
        if idx == 0:
            ax.set_ylabel("Survival $S(t)$")
        ax.set_title(f"{'abc'[idx]}", fontweight="bold", fontsize=9,
                     loc="left", x=-0.15)
        ax.text(0.95, 0.95, label, transform=ax.transAxes, fontsize=5.5,
                ha="right", va="top")
        ax.set_ylim(1e-4, 1.5)

        # Eigenvalues annotation
        eigs = np.sort(-np.real(np.linalg.eigvals(A)))
        hl = np.log(2) / eigs
        ax.text(0.95, 0.75,
                f"$t_{{1/2}}^{{(\\alpha)}}={hl[2]:.0f}$\n"
                f"$t_{{1/2}}^{{(\\beta)}}={hl[1]:.0f}$\n"
                f"$t_{{1/2}}^{{(\\gamma)}}={hl[0]:.0f}$",
                transform=ax.transAxes, fontsize=5, ha="right", va="top",
                fontfamily="monospace")

    # Legend
    axes[0].plot([], [], ".", color=CB_BLUE, ms=4, label="N-body")
    axes[0].plot([], [], "-", color=CB_RED, lw=1.2, label="3-comp PK")
    axes[0].legend(loc="lower left", fontsize=5.5, framealpha=0.8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig2_survival.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig2_survival.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig2_survival")


# ===========================================================================
# FIGURE 3: Nonlinear PK — sticky chaos tail
# ===========================================================================

def fig3_nonlinear():
    """Figure 3: Linear vs nonlinear PK for sticky chaos."""
    from analysis.advanced_pk_analysis import (
        compare_linear_vs_nonlinear, stretched_exp_survival
    )

    configs = [
        ("equal_mass", "Equal (1:1:1)"),
        ("unequal_mass", "Unequal (1:2:0.5)"),
        ("democratic", "Democratic"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

    for idx, (name, label) in enumerate(configs):
        ax = axes[idx]
        results = load_results(name)
        lifetimes, P0, A, rates = extract_lifetimes_and_rates(results)

        if len(lifetimes) < 50:
            continue

        nl = compare_linear_vs_nonlinear(lifetimes, P0, A, rates)

        # Empirical
        ax.loglog(nl["lt_sorted"], nl["S_empirical"], ".", color=CB_BLUE,
                  ms=1, alpha=0.3, rasterized=True)

        # Linear PK
        ax.loglog(nl["t_grid"], np.maximum(nl["S_linear"], 1e-15), "-",
                  color=CB_RED, lw=1.0, label="Linear PK")

        # Nonlinear
        ax.loglog(nl["t_grid"], np.maximum(nl["S_nonlinear"], 1e-15), "--",
                  color=CB_GREEN, lw=1.2, label="Hybrid MM")

        # Power-law reference
        if np.isfinite(nl["alpha_power_law"]):
            t_ref = nl["t_grid"]
            t_mid = np.percentile(nl["lt_sorted"], 80)
            S_ref = 0.15 * (t_ref / t_mid) ** (-nl["alpha_power_law"])
            ax.loglog(t_ref, S_ref, ":", color="gray", lw=0.8, alpha=0.6)
            ax.text(0.05, 0.15, f"$\\alpha={nl['alpha_power_law']:.1f}$",
                    transform=ax.transAxes, fontsize=5.5, color="gray")

        ax.set_xlabel("Lifetime ($t / t_{\\rm dyn}$)")
        if idx == 0:
            ax.set_ylabel("Survival $S(t)$")
        ax.set_title(f"{'abc'[idx]}", fontweight="bold", fontsize=9,
                     loc="left", x=-0.15)
        ax.text(0.95, 0.95, label, transform=ax.transAxes, fontsize=5.5,
                ha="right", va="top")
        ax.set_ylim(1e-4, 1.5)

        # RMSE annotation
        improv = ((nl["rmse_linear_tail"] - nl["rmse_nonlinear_tail"])
                  / nl["rmse_linear_tail"] * 100)
        if improv > 0:
            ax.text(0.95, 0.65, f"Tail improvement:\n{improv:.0f}%",
                    transform=ax.transAxes, fontsize=5, ha="right", va="top",
                    color=CB_GREEN)

    axes[1].legend(loc="lower left", fontsize=5.5, framealpha=0.8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig3_nonlinear.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig3_nonlinear.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig3_nonlinear")


# ===========================================================================
# FIGURE 4: Population PK
# ===========================================================================

def fig4_population_pk():
    """Figure 4: Population PK analysis."""
    from analysis.advanced_pk_analysis import (
        load_mass_scan, population_pk_analysis, fit_population_model
    )

    scan_data = load_mass_scan(DATADIR)
    records = population_pk_analysis(scan_data)
    # B1: report the allometric law on the (tail-robust) median lifetime.
    pop_results = fit_population_model(records, response="median")

    if pop_results is None:
        print("  Skipping fig4 — no population data")
        return

    valid = pop_results["records"]
    beta = pop_results["beta"]

    fig = plt.figure(figsize=(7.2, 5.0))
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.4)

    # (a) MRT vs mu_out
    ax = fig.add_subplot(gs[0, 0])
    mu_out = [r["mu_out"] for r in valid]
    mrt = [r["mrt"] for r in valid]
    v = [(m, rt) for m, rt in zip(mu_out, mrt) if rt > 0 and np.isfinite(rt)]
    if v:
        mu_v, mrt_v = zip(*v)
        ax.scatter(mu_v, mrt_v, s=8, c=CB_BLUE, alpha=0.7, edgecolors="none")
        ax.set_xlabel("$\\mu_{\\rm out}$")
        ax.set_ylabel("MRT")
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_title("a", fontweight="bold", fontsize=9, loc="left", x=-0.2)

    # (b) Median lifetime vs m3
    ax = fig.add_subplot(gs[0, 1])
    m3_vals = [r["m3"] for r in valid]
    lt_med = [r["lifetimes_median"] for r in valid]
    ax.scatter(m3_vals, lt_med, s=8, c=CB_ORANGE, alpha=0.7, edgecolors="none")
    ax.set_xlabel("$m_3$")
    ax.set_ylabel("Median lifetime")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("b", fontweight="bold", fontsize=9, loc="left", x=-0.2)

    # (c) Excursions vs mass ratio
    ax = fig.add_subplot(gs[0, 2])
    q_min = [min(r["m1"], r["m2"], r["m3"]) / r["M"] for r in valid]
    exc = [r["mean_excursions"] for r in valid]
    ax.scatter(q_min, exc, s=8, c=CB_GREEN, alpha=0.7, edgecolors="none")
    ax.set_xlabel("$q_{\\rm min}$")
    ax.set_ylabel("Mean excursions")
    ax.set_title("c", fontweight="bold", fontsize=9, loc="left", x=-0.2)

    # (d) Escape probability of lightest
    ax = fig.add_subplot(gs[1, 0])
    p_esc = pop_results["p_esc_lightest"]
    ax.scatter(q_min, p_esc, s=8, c=CB_PURPLE, alpha=0.7, edgecolors="none")
    ax.axhline(1/3, color="gray", ls="--", lw=0.5, alpha=0.5)
    ax.set_xlabel("$q_{\\rm min}$")
    ax.set_ylabel("$P$(lightest escapes)")
    ax.set_title("d", fontweight="bold", fontsize=9, loc="left", x=-0.2)

    # (e) Predicted vs observed median lifetime, with collinearity diagnostics
    ax = fig.add_subplot(gs[1, 1])
    X = np.column_stack([
        np.ones(len(valid)),
        np.log([r["mu12"] for r in valid]),
        np.log([r["mu_out"] for r in valid]),
        np.log([r["M"] for r in valid]),
    ])
    y_obs = np.array([r["lifetimes_median"] for r in valid])
    y_pred = np.exp(X @ np.array(beta))

    ax.scatter(y_pred, y_obs, s=8, c=CB_BLUE, alpha=0.7, edgecolors="none")
    lim = [min(min(y_pred), min(y_obs)) * 0.5,
           max(max(y_pred), max(y_obs)) * 2]
    ax.plot(lim, lim, "k--", lw=0.5, alpha=0.4)
    ax.set_xlabel("Predicted median lifetime")
    ax.set_ylabel("Observed median lifetime")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("e", fontweight="bold", fontsize=9, loc="left", x=-0.2)
    sh = pop_results["shapley_r2"]
    vf = pop_results["vif"]
    ax.text(0.05, 0.94,
            f"$R^2={pop_results['r_squared']:.2f}$\n"
            f"LMG: {sh[0]:.02f}/{sh[1]:.02f}/{sh[2]:.02f}\n"
            f"VIF: {vf[0]:.1f}/{vf[1]:.1f}/{vf[2]:.1f}",
            transform=ax.transAxes, fontsize=4.5, va="top")

    # (f) Half-life heatmap
    ax = fig.add_subplot(gs[1, 2])
    m2_unique = sorted(set(r["m2"] for r in valid))
    m3_unique = sorted(set(r["m3"] for r in valid))
    hl_matrix = np.full((len(m2_unique), len(m3_unique)), np.nan)
    for r in valid:
        i = m2_unique.index(r["m2"])
        j = m3_unique.index(r["m3"])
        hl = sorted(r["half_lives"])
        if len(hl) >= 3 and np.isfinite(hl[2]) and hl[2] > 0:
            hl_matrix[i, j] = np.log10(hl[2])

    im = ax.imshow(hl_matrix, origin="lower", aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(m3_unique)))
    ax.set_xticklabels([f"{m:.1f}" for m in m3_unique], fontsize=5)
    ax.set_yticks(range(len(m2_unique)))
    ax.set_yticklabels([f"{m:.1f}" for m in m2_unique], fontsize=5)
    ax.set_xlabel("$m_3$")
    ax.set_ylabel("$m_2$")
    ax.set_title("f", fontweight="bold", fontsize=9, loc="left", x=-0.2)
    cb = plt.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("$\\log_{10}(t_{1/2}^{(\\gamma)})$", fontsize=6)

    fig.savefig(os.path.join(FIGDIR, "fig4_population_pk.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig4_population_pk.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig4_population_pk")


# ===========================================================================
# FIGURE 5: TMDD reverse application
# ===========================================================================

def fig5_tmdd():
    """Figure 5: TMDD bifurcation and stability analysis."""
    from analysis.advanced_pk_analysis import tmdd_three_body_analogy

    base_params, bifurcation = tmdd_three_body_analogy()

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

    doses = [d["dose"] for d in bifurcation]
    C_ss = [d["C_ss"] for d in bifurcation]
    R_ss = [d["R_ss"] for d in bifurcation]
    CR_ss = [d["CR_ss"] for d in bifurcation]
    stable = [d["is_stable"] for d in bifurcation]

    # (a) Dose-response
    ax = axes[0]
    for i, s in enumerate(stable):
        color = CB_BLUE if s else CB_RED
        marker = "o" if s else "x"
        ax.scatter(doses[i], C_ss[i], c=color, s=5, marker=marker, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Dose rate")
    ax.set_ylabel("$C_{ss}$")
    ax.set_title("a", fontweight="bold", fontsize=9, loc="left", x=-0.15)
    ax.scatter([], [], c=CB_BLUE, s=15, label="Stable")
    ax.scatter([], [], c=CB_RED, s=15, marker="x", label="Unstable")
    ax.legend(fontsize=5.5, loc="lower right")

    # (b) Receptor occupancy
    ax = axes[1]
    occupancy = [cr / (r + cr + 1e-15) for r, cr in zip(R_ss, CR_ss)]
    for i, s in enumerate(stable):
        color = CB_BLUE if s else CB_RED
        ax.scatter(doses[i], occupancy[i], c=color, s=5, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("Dose rate")
    ax.set_ylabel("Receptor occupancy")
    ax.set_title("b", fontweight="bold", fontsize=9, loc="left", x=-0.15)

    # (c) Eigenvalue spectrum
    ax = axes[2]
    for d in bifurcation:
        eigs = d["eigenvalues_real"]
        slowest = max(eigs)
        color = CB_BLUE if d["is_stable"] else CB_RED
        ax.scatter(d["dose"], slowest, c=color, s=5, alpha=0.7)
    ax.set_xscale("log")
    ax.axhline(0, color="black", ls="-", lw=0.3)
    ax.set_xlabel("Dose rate")
    ax.set_ylabel("Slowest eigenvalue")
    ax.set_title("c", fontweight="bold", fontsize=9, loc="left", x=-0.15)

    # Shade unstable region
    ylim = ax.get_ylim()
    ax.fill_between([min(doses), max(doses)], 0,
                    max(0.05, ylim[1]), alpha=0.05, color=CB_RED)
    ax.set_ylim(ylim)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig5_tmdd.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig5_tmdd.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig5_tmdd")


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Generating Nature-quality figures")
    print("=" * 60)

    print("\nFigure 1: Conceptual mapping")
    fig1_conceptual()

    print("\nFigure 2: Lifetime distributions")
    fig2_lifetime_distributions()

    print("\nFigure 3: Nonlinear PK (sticky chaos)")
    fig3_nonlinear()

    print("\nFigure 4: Population PK")
    fig4_population_pk()

    print("\nFigure 5: TMDD reverse application")
    fig5_tmdd()

    print(f"\nAll figures saved to: {FIGDIR}")
    print("=" * 60)
