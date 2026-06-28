#!/usr/bin/env python3
"""
PK compartmental analysis of three-body scattering results.

Reads JSON output from the Julia simulator and performs:
1. Transition count extraction & CTMC-MLE rate estimation
2. Linear 3-compartment PK model fitting (lifetime distribution)
3. Comparison with phase-space flux predictions
4. Nonlinear (MM) model fitting for sticky chaos tails
5. Publication-quality figure generation

Usage:
  python run_analysis.py [data_dir]
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
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.optimize import minimize, differential_evolution
from scipy.stats import kstest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")
FIGDIR = os.path.join(BASEDIR, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# Binary pair → compartment index (Julia is 1-indexed, convert)
PAIR_TO_COMP = {(1, 2): 0, (1, 3): 1, (2, 3): 2}
COMP_LABELS = ["(1,2)+3", "(1,3)+2", "(2,3)+1"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_results(name: str) -> list[dict]:
    path = os.path.join(DATADIR, f"{name}.json")
    with open(path) as f:
        return json.load(f)


def extract_transitions(results: list[dict]) -> dict:
    """Extract transition counts, dwell times, lifetimes from results."""
    trans = np.zeros((3, 3), dtype=int)
    esc_counts = np.zeros(3, dtype=int)
    dwell_times: dict[int, list[float]] = {0: [], 1: [], 2: []}
    lifetimes = []
    n_exc_list = []
    escaper_body = []

    for r in results:
        if r["status"] != "escape":
            continue
        seq = r["config_sequence"]
        if not seq:
            continue

        lifetimes.append(r["lifetime"])
        n_exc_list.append(r["n_excursions"])
        escaper_body.append(r["escaper"])

        # Transitions
        for k in range(len(seq) - 1):
            p_from = tuple(seq[k]["pair"])
            p_to = tuple(seq[k + 1]["pair"])
            c_from = PAIR_TO_COMP.get(p_from)
            c_to = PAIR_TO_COMP.get(p_to)
            if c_from is not None and c_to is not None and c_from != c_to:
                trans[c_from, c_to] += 1

        # Dwell times
        for k in range(len(seq)):
            p = tuple(seq[k]["pair"])
            c = PAIR_TO_COMP.get(p)
            if c is None:
                continue
            t_start = seq[k]["t"]
            t_end = seq[k + 1]["t"] if k + 1 < len(seq) else r["lifetime"]
            dt = t_end - t_start
            if dt > 0:
                dwell_times[c].append(dt)

        # Escape from which compartment
        if seq:
            last_p = tuple(seq[-1]["pair"])
            c_last = PAIR_TO_COMP.get(last_p)
            if c_last is not None:
                esc_counts[c_last] += 1

    return {
        "trans": trans,
        "esc_counts": esc_counts,
        "dwell_times": dwell_times,
        "lifetimes": np.array(lifetimes),
        "n_excursions": np.array(n_exc_list),
        "escaper_body": np.array(escaper_body),
    }


# ---------------------------------------------------------------------------
# Linear PK model
# ---------------------------------------------------------------------------

def estimate_rates_mle(data: dict) -> np.ndarray:
    """
    CTMC-MLE: k_ij = N_ij / T_i, k_e_i = N_esc_i / T_i.

    Returns 3x3 rate matrix A (diagonal = -(sum of outgoing rates)).
    Also returns the 9 individual rates as a dict.
    """
    trans = data["trans"].astype(float)
    esc = data["esc_counts"].astype(float)
    T = np.array([sum(data["dwell_times"][i]) for i in range(3)])
    T = np.maximum(T, 1e-10)

    # Off-diagonal: k_ij
    K = np.zeros((3, 3))
    ke = np.zeros(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                K[i, j] = trans[i, j] / T[i]
        ke[i] = esc[i] / T[i]

    # Rate matrix A
    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                A[i, j] = K[i, j]
        A[i, i] = -(np.sum(K[i, :]) + ke[i])

    rates = {
        "k12": K[0, 1], "k13": K[0, 2],
        "k21": K[1, 0], "k23": K[1, 2],
        "k31": K[2, 0], "k32": K[2, 1],
        "ke1": ke[0], "ke2": ke[1], "ke3": ke[2],
    }
    return A, rates, ke


def pk_survival(t: np.ndarray, A: np.ndarray, P0: np.ndarray) -> np.ndarray:
    """S(t) = 1^T @ exp(A*t) @ P0."""
    S = np.zeros(len(t))
    for i, ti in enumerate(t):
        S[i] = np.sum(expm(A * ti) @ P0)
    return S


def pk_escape_pdf(t: np.ndarray, A: np.ndarray, P0: np.ndarray) -> np.ndarray:
    """f(t) = -1^T @ A @ exp(A*t) @ P0."""
    ones = np.ones(3)
    f = np.zeros(len(t))
    for i, ti in enumerate(t):
        f[i] = -ones @ A @ expm(A * ti) @ P0
    return np.maximum(f, 0)


def pk_summary_stats(A: np.ndarray, P0: np.ndarray) -> dict:
    eigs = np.sort(np.real(np.linalg.eigvals(A)))
    half_lives = np.log(2) / (-eigs)
    try:
        mrt = -np.ones(3) @ np.linalg.inv(A) @ P0
    except np.linalg.LinAlgError:
        mrt = float("inf")
    return {
        "eigenvalues": eigs,
        "half_lives": half_lives,
        "MRT": float(mrt),
    }


# ---------------------------------------------------------------------------
# Phase-space flux prediction
# ---------------------------------------------------------------------------

def phase_space_rates(masses: tuple[float, float, float]) -> np.ndarray:
    """Predict rates from phase-space volume (Stone & Leigh 2019 simplified)."""
    m = np.array(masses)
    M = np.sum(m)
    pairs = [(0, 1), (0, 2), (1, 2)]  # 0-indexed body pairs

    K = np.zeros((3, 3))
    ke = np.zeros(3)

    for idx_from, (i, j) in enumerate(pairs):
        k = 3 - i - j
        mu_from = m[i] * m[j] / (m[i] + m[j])
        for idx_to, (p, q) in enumerate(pairs):
            if idx_from == idx_to:
                continue
            r = 3 - p - q
            mu_to = m[p] * m[q] / (m[p] + m[q])
            K[idx_from, idx_to] = (mu_to ** 1.5 * m[r] ** 1.5) / (
                mu_from ** 1.5 * m[k] ** 1.5
            )
        ke[idx_from] = (m[k] / M) ** 1.5

    # Normalise
    t_dyn = 1.0 / np.sqrt(M)
    total = np.sum(K) + np.sum(ke)
    K /= total * t_dyn
    ke /= total * t_dyn

    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                A[i, j] = K[i, j]
        A[i, i] = -(np.sum(K[i, :]) + ke[i])

    return A, ke


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig1_conceptual_mapping():
    """Conceptual diagram: three-body ↔ PK compartment mapping."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: three-body
    ax = axes[0]
    ax.set_xlim(-3, 3); ax.set_ylim(-3, 3); ax.set_aspect("equal")
    ax.set_title("Three-body resonant scattering", fontsize=14, fontweight="bold")

    cfgs = [
        {"lbl": "Binary(1,2)\n+ Single 3", "pos": (0, 1.8), "col": "#e41a1c"},
        {"lbl": "Binary(1,3)\n+ Single 2", "pos": (-1.8, -1.2), "col": "#377eb8"},
        {"lbl": "Binary(2,3)\n+ Single 1", "pos": (1.8, -1.2), "col": "#4daf4a"},
    ]
    for c in cfgs:
        cx, cy = c["pos"]
        circle = plt.Circle((cx, cy), 0.7, fc=c["col"], alpha=0.15, ec=c["col"], lw=2)
        ax.add_patch(circle)
        ax.text(cx, cy, c["lbl"], ha="center", va="center", fontsize=9,
                fontweight="bold", color=c["col"])

    # Arrows
    arrow_kw = dict(arrowstyle="<->", color="#555", lw=1.5,
                    connectionstyle="arc3,rad=0.15")
    for i in range(3):
        for j in range(i + 1, 3):
            ax.annotate("", cfgs[j]["pos"], cfgs[i]["pos"], arrowprops=arrow_kw)

    # Escape arrows
    for c in cfgs:
        cx, cy = c["pos"]
        angle = np.arctan2(cy, cx)
        dx, dy = 0.9 * np.cos(angle), 0.9 * np.sin(angle)
        ax.annotate("escape",
                    (cx + dx + 0.5 * np.cos(angle), cy + dy + 0.5 * np.sin(angle)),
                    (cx + dx * 0.8, cy + dy * 0.8),
                    arrowprops=dict(arrowstyle="->", color="red", lw=2),
                    fontsize=8, color="red", ha="center", fontweight="bold")
    ax.axis("off")

    # Right: PK model
    ax = axes[1]
    ax.set_xlim(-3, 3); ax.set_ylim(-3, 3); ax.set_aspect("equal")
    ax.set_title("3-Compartment PK model", fontsize=14, fontweight="bold")

    comps = [
        {"lbl": "Compartment 1\nP₁(t)", "pos": (0, 1.8), "col": "#e41a1c"},
        {"lbl": "Compartment 2\nP₂(t)", "pos": (-1.8, -1.2), "col": "#377eb8"},
        {"lbl": "Compartment 3\nP₃(t)", "pos": (1.8, -1.2), "col": "#4daf4a"},
    ]
    for c in comps:
        cx, cy = c["pos"]
        rect = plt.Rectangle((cx - 0.8, cy - 0.5), 1.6, 1.0,
                              fc=c["col"], alpha=0.15, ec=c["col"], lw=2,
                              joinstyle="round")
        ax.add_patch(rect)
        ax.text(cx, cy, c["lbl"], ha="center", va="center", fontsize=9,
                fontweight="bold", color=c["col"])

    rate_labels = [["k₁₂", "k₂₁"], ["k₁₃", "k₃₁"], ["k₂₃", "k₃₂"]]
    pair_idx = [(0, 1), (0, 2), (1, 2)]
    for pidx, (i, j) in enumerate(pair_idx):
        c1 = np.array(comps[i]["pos"])
        c2 = np.array(comps[j]["pos"])
        d = c2 - c1
        dn = d / np.linalg.norm(d)
        perp = np.array([-dn[1], dn[0]]) * 0.15

        ax.annotate("", tuple(c2 - 0.85 * dn + perp), tuple(c1 + 0.85 * dn + perp),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))
        mid1 = (c1 + c2) / 2 + perp * 2
        ax.text(mid1[0], mid1[1], rate_labels[pidx][0], fontsize=8, ha="center",
                color="#555")

        ax.annotate("", tuple(c1 + 0.85 * dn - perp), tuple(c2 - 0.85 * dn - perp),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))
        mid2 = (c1 + c2) / 2 - perp * 2
        ax.text(mid2[0], mid2[1], rate_labels[pidx][1], fontsize=8, ha="center",
                color="#555")

    for i, c in enumerate(comps):
        cx, cy = c["pos"]
        angle = np.arctan2(cy, cx)
        dx, dy = 0.9 * np.cos(angle), 0.9 * np.sin(angle)
        ax.annotate(f"kₑ{i+1}",
                    (cx + dx + 0.5 * np.cos(angle), cy + dy + 0.5 * np.sin(angle)),
                    (cx + dx * 0.9, cy + dy * 0.9),
                    arrowprops=dict(arrowstyle="->", color="red", lw=2),
                    fontsize=9, color="red", ha="center", fontweight="bold")
    ax.axis("off")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_conceptual_mapping.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig1_conceptual_mapping.png")
    plt.close()


def fig2_lifetime_distribution(data: dict, A_mle: np.ndarray,
                               P0: np.ndarray, label: str):
    """Lifetime distribution: numerical vs PK prediction."""
    lt = data["lifetimes"]
    if len(lt) < 20:
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f"Lifetime distribution — {label}", fontsize=14, fontweight="bold")

    t_99 = np.percentile(lt, 99)
    t_grid = np.linspace(0.01, t_99, 500)

    # (a) PDF
    ax = axes[0]
    ax.hist(lt, bins=60, density=True, alpha=0.6, color="steelblue",
            label="N-body simulation", range=(0, t_99))
    pdf = pk_escape_pdf(t_grid, A_mle, P0)
    ax.plot(t_grid, pdf, "r-", lw=2, label="3-compartment PK model")
    ax.set_xlabel("Lifetime (dynamical times)")
    ax.set_ylabel("Probability density")
    ax.set_title("(a) Lifetime PDF")
    ax.legend(fontsize=8)

    # (b) Survival — semi-log
    ax = axes[1]
    sorted_lt = np.sort(lt)
    S_emp = 1 - np.arange(1, len(sorted_lt) + 1) / len(sorted_lt)
    ax.semilogy(sorted_lt, S_emp, "b.", ms=1.5, alpha=0.4, label="Numerical")

    S_pk = pk_survival(t_grid, A_mle, P0)
    ax.semilogy(t_grid, np.maximum(S_pk, 1e-10), "r-", lw=2, label="PK model")

    # Single exponential
    lam = 1.0 / np.mean(lt)
    ax.semilogy(t_grid, np.exp(-lam * t_grid), "k--", lw=1, alpha=0.5,
                label="Single exponential")

    ax.set_xlabel("Lifetime")
    ax.set_ylabel("Survival S(t)")
    ax.set_title("(b) Survival curve (semi-log)")
    ax.legend(fontsize=8)

    # (c) Log-log (power-law tail check)
    ax = axes[2]
    mask = (sorted_lt > 0) & (S_emp > 0)
    ax.loglog(sorted_lt[mask], S_emp[mask], "b.", ms=1.5, alpha=0.4,
              label="Numerical")

    t_grid_ll = np.logspace(np.log10(sorted_lt[mask][0]),
                            np.log10(sorted_lt[mask][-1]), 500)
    S_pk_ll = pk_survival(t_grid_ll, A_mle, P0)
    ax.loglog(t_grid_ll, np.maximum(S_pk_ll, 1e-10), "r-", lw=2,
              label="PK model (multi-exponential)")
    ax.set_xlabel("Lifetime")
    ax.set_ylabel("Survival S(t)")
    ax.set_title("(c) Log-log survival")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fname = f"fig2_lifetime_{label.replace(' ', '_')}.png"
    fig.savefig(os.path.join(FIGDIR, fname), dpi=200, bbox_inches="tight")
    print(f"  Saved {fname}")
    plt.close()


def fig3_rate_comparison(rates_mle: dict, A_flux: np.ndarray, ke_flux: np.ndarray,
                         label: str):
    """Bar chart + scatter: MLE rates vs phase-space flux prediction."""
    names = ["k12", "k13", "k21", "k23", "k31", "k32", "ke1", "ke2", "ke3"]
    mle_vals = np.array([rates_mle[n] for n in names])

    # Extract flux rates in same order
    flux_K = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                flux_K[i, j] = A_flux[i, j]  # off-diagonal of A = positive rates

    flux_vals = np.array([
        flux_K[0, 1], flux_K[0, 2], flux_K[1, 0], flux_K[1, 2],
        flux_K[2, 0], flux_K[2, 1], ke_flux[0], ke_flux[1], ke_flux[2],
    ])

    # Normalise flux to same total rate
    if np.sum(flux_vals) > 0:
        flux_vals *= np.sum(mle_vals) / np.sum(flux_vals)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle(f"Rate comparison — {label}", fontsize=14, fontweight="bold")

    ax = axes[0]
    x = np.arange(len(names))
    w = 0.35
    ax.bar(x - w / 2, mle_vals, w, color="steelblue", alpha=0.8,
           label="MLE (simulation)")
    ax.bar(x + w / 2, flux_vals, w, color="coral", alpha=0.8,
           label="Phase-space flux (theory)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45)
    ax.set_ylabel("Rate constant")
    ax.set_title("(a) Rate constants")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.scatter(flux_vals, mle_vals, s=60, c="steelblue", edgecolors="navy", zorder=3)
    for i, n in enumerate(names):
        ax.annotate(n, (flux_vals[i], mle_vals[i]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    lim = max(max(mle_vals), max(flux_vals)) * 1.2
    ax.plot([0, lim], [0, lim], "k--", alpha=0.4, label="y = x")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Phase-space flux prediction")
    ax.set_ylabel("MLE from simulation")
    ax.set_title("(b) Theory vs simulation")
    ax.set_aspect("equal")
    ax.legend(fontsize=8)

    plt.tight_layout()
    fname = f"fig3_rates_{label.replace(' ', '_')}.png"
    fig.savefig(os.path.join(FIGDIR, fname), dpi=200, bbox_inches="tight")
    print(f"  Saved {fname}")
    plt.close()


def fig4_pk_table(all_analyses: list[dict]):
    """Summary table of PK parameters."""
    fig, ax = plt.subplots(figsize=(14, 3))
    ax.axis("off")

    cols = ["Config", "N_escape", "t½(α)", "t½(β)", "t½(γ)",
            "MRT", "Median τ", "Mean excursions",
            "P(esc body 1)", "P(esc body 2)", "P(esc body 3)"]
    rows = []
    for a in all_analyses:
        s = a["pk_summary"]
        hl = sorted(s["half_lives"])
        eb = a["data"]["escaper_body"]
        n_total = len(eb)
        if n_total == 0:
            continue
        p_esc = [np.sum(eb == b) / n_total for b in [1, 2, 3]]
        rows.append([
            a["label"],
            str(n_total),
            f"{hl[0]:.1f}",
            f"{hl[1]:.1f}" if len(hl) > 1 else "—",
            f"{hl[2]:.1f}" if len(hl) > 2 else "—",
            f"{s['MRT']:.1f}",
            f"{np.median(a['data']['lifetimes']):.1f}",
            f"{np.mean(a['data']['n_excursions']):.1f}",
            f"{p_esc[0]:.3f}",
            f"{p_esc[1]:.3f}",
            f"{p_esc[2]:.3f}",
        ])

    if not rows:
        plt.close()
        return

    table = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)
    for j in range(len(cols)):
        table[(0, j)].set_facecolor("#4472C4")
        table[(0, j)].set_text_props(color="white", fontweight="bold", fontsize=8)

    ax.set_title("Pharmacokinetic summary of three-body scattering ensembles",
                 fontsize=13, fontweight="bold", pad=20)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig4_pk_summary_table.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig4_pk_summary_table.png")
    plt.close()


def fig5_excursion_distribution(all_analyses: list[dict]):
    """Distribution of excursion counts + geometric fit."""
    valid = [a for a in all_analyses if len(a["data"]["n_excursions"]) > 0]
    if not valid:
        return

    fig, axes = plt.subplots(1, len(valid), figsize=(5 * len(valid), 4))
    if not hasattr(axes, "__len__"):
        axes = [axes]

    for idx, a in enumerate(valid):
        ax = axes[idx]
        exc = a["data"]["n_excursions"]
        max_e = int(np.percentile(exc, 99)) + 1
        ax.hist(exc, bins=range(0, max_e + 2), density=True,
                alpha=0.7, color="steelblue", edgecolor="navy",
                label="Simulation")

        # Geometric distribution fit
        p_esc = 1.0 / (np.mean(exc) + 1) if np.mean(exc) > 0 else 1.0
        k_range = np.arange(0, max_e + 1)
        geom = (1 - p_esc) ** k_range * p_esc
        ax.plot(k_range, geom, "r-o", ms=3, lw=1.5,
                label=f"Geometric(p={p_esc:.3f})")
        ax.set_xlabel("Number of excursions")
        ax.set_ylabel("Probability")
        ax.set_title(a["label"])
        ax.legend(fontsize=8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig5_excursion_dist.png"),
                dpi=200, bbox_inches="tight")
    print("  Saved fig5_excursion_dist.png")
    plt.close()


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyse_one(name: str, masses: tuple, label: str) -> dict | None:
    """Full PK analysis for one configuration."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    try:
        results = load_results(name)
    except FileNotFoundError:
        print(f"  Data file not found: {name}.json — skipping")
        return None

    data = extract_transitions(results)
    lt = data["lifetimes"]
    n_esc = len(lt)
    print(f"  Escaped systems: {n_esc}")
    if n_esc < 20:
        print("  Too few escapes for analysis. Skipping.")
        return None

    print(f"  Lifetime: median={np.median(lt):.1f}, mean={np.mean(lt):.1f}, "
          f"max={np.max(lt):.1f}")
    print(f"  Excursions: median={np.median(data['n_excursions']):.0f}, "
          f"mean={np.mean(data['n_excursions']):.1f}")

    # Transition matrix
    print(f"\n  Transition counts:")
    print(f"  {'':>12s} {'→C1':>8s} {'→C2':>8s} {'→C3':>8s}")
    for i in range(3):
        print(f"  {COMP_LABELS[i]:>12s} {data['trans'][i,0]:>8d} "
              f"{data['trans'][i,1]:>8d} {data['trans'][i,2]:>8d}")
    print(f"  Escape counts: {data['esc_counts']}")

    # MLE rates
    A_mle, rates_mle, ke_mle = estimate_rates_mle(data)
    print(f"\n  MLE rate estimates:")
    for k, v in rates_mle.items():
        print(f"    {k} = {v:.6f}")

    # Initial probability: proportional to how often each config is first visited
    first_comp_counts = np.zeros(3)
    for r in results:
        if r["status"] == "escape" and r["config_sequence"]:
            p = tuple(r["config_sequence"][0]["pair"])
            c = PAIR_TO_COMP.get(p)
            if c is not None:
                first_comp_counts[c] += 1
    P0 = first_comp_counts / max(np.sum(first_comp_counts), 1)
    print(f"  Initial distribution P0: {P0}")

    # PK summary
    summary = pk_summary_stats(A_mle, P0)
    print(f"\n  PK summary:")
    print(f"    Eigenvalues: {summary['eigenvalues']}")
    print(f"    Half-lives: {summary['half_lives']}")
    print(f"    Mean Residence Time (MRT): {summary['MRT']:.1f}")

    # Phase-space flux prediction
    A_flux, ke_flux = phase_space_rates(masses)
    summary_flux = pk_summary_stats(A_flux, P0)
    print(f"\n  Phase-space flux prediction:")
    print(f"    Eigenvalues: {summary_flux['eigenvalues']}")
    print(f"    Half-lives: {summary_flux['half_lives']}")

    # KS test
    scale = np.mean(lt)
    ks_stat, ks_p = kstest(lt, "expon", args=(0, scale))
    print(f"\n  KS test (single exponential): D={ks_stat:.4f}, p={ks_p:.6f}")
    if ks_p < 0.05:
        print("    → REJECT single exponential → multi-exponential PK model needed")
    else:
        print("    → Cannot reject single exponential")

    # Energy conservation stats
    dE = [abs((r["E_final"] - r["E_initial"]) / (abs(r["E_initial"]) + 1e-30))
          for r in results if r["status"] == "escape"]
    if dE:
        print(f"\n  Energy conservation: median|dE/E|={np.median(dE):.2e}, "
              f"max|dE/E|={np.max(dE):.2e}")

    return {
        "label": label,
        "masses": masses,
        "data": data,
        "A_mle": A_mle,
        "rates_mle": rates_mle,
        "ke_mle": ke_mle,
        "P0": P0,
        "pk_summary": summary,
        "A_flux": A_flux,
        "ke_flux": ke_flux,
    }


def main():
    print("=" * 60)
    print("  Three-body → PK compartmental analysis")
    print("=" * 60)

    configs = [
        ("equal_mass", (1.0, 1.0, 1.0), "Equal mass (1:1:1)"),
        ("unequal_mass", (1.0, 2.0, 0.5), "Unequal mass (1:2:0.5)"),
        ("democratic", (1.0, 1.0, 1.0), "Democratic IC (1:1:1)"),
    ]

    all_analyses = []
    for name, masses, label in configs:
        a = analyse_one(name, masses, label)
        if a is not None:
            all_analyses.append(a)

    if not all_analyses:
        print("\nNo data to analyse. Run Julia simulation first.")
        return

    # Generate figures
    print(f"\n{'=' * 60}")
    print("  Generating figures")
    print(f"{'=' * 60}")

    fig1_conceptual_mapping()
    for a in all_analyses:
        fig2_lifetime_distribution(a["data"], a["A_mle"], a["P0"], a["label"])
        fig3_rate_comparison(a["rates_mle"], a["A_flux"], a["ke_flux"], a["label"])
    fig4_pk_table(all_analyses)
    fig5_excursion_distribution(all_analyses)

    print(f"\n{'=' * 60}")
    print(f"  All figures saved to: {FIGDIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
