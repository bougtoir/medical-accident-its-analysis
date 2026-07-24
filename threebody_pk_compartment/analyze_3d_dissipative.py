#!/usr/bin/env python3
"""
Analyze 3D + dissipative simulations and compare with 2D conservative results.
Fits PK models and generates comparison figures.
"""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.stats import ks_2samp
from scipy.optimize import minimize_scalar

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")
FIGDIR = os.path.join(BASEDIR, "figures_nature")
os.makedirs(FIGDIR, exist_ok=True)

# Colour-blind safe palette
CB_BLUE = "#0072B2"
CB_ORANGE = "#E69F00"
CB_GREEN = "#009E73"
CB_RED = "#D55E00"
CB_PURPLE = "#CC79A7"
CB_CYAN = "#56B4E9"

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
    fpath = os.path.join(DATADIR, f"{name}.json")
    if not os.path.exists(fpath):
        return None
    with open(fpath) as f:
        return json.load(f)


def extract_lifetimes_and_rates(results):
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

    # Rate matrix (column-vector convention: dp/dt = A@p)
    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i != j:
                A[j, i] = trans[i, j] / T[i]
        ke_i = esc_counts[i] / T[i]
        A[i, i] = -(sum(trans[i, j] / T[i] for j in range(3) if j != i) + ke_i)

    return np.array(lifetimes), P0, A


def pk_survival(t_grid, A, P0):
    return np.array([np.sum(expm(A * t) @ P0) for t in t_grid])


def compute_ks_statistic(lifetimes, A, P0):
    """KS test: empirical CDF vs PK model CDF."""
    lt_sorted = np.sort(lifetimes)
    S_emp = 1 - np.arange(1, len(lt_sorted) + 1) / len(lt_sorted)
    t_grid = lt_sorted
    S_pk = pk_survival(t_grid, A, P0)
    return np.max(np.abs(S_emp - S_pk))


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_dataset(name, label):
    results = load_results(name)
    if results is None:
        return None
    lifetimes, P0, A = extract_lifetimes_and_rates(results)
    if len(lifetimes) < 50:
        return None

    # Eigenvalues and half-lives
    eigs = np.sort(-np.real(np.linalg.eigvals(A)))
    half_lives = np.log(2) / eigs[eigs > 0] if np.any(eigs > 0) else []

    # KS statistic
    ks_stat = compute_ks_statistic(lifetimes, A, P0)

    # Energy dissipation
    dE_list = []
    for r in results:
        if r["status"] == "escape":
            E0 = r["E_initial"]
            Ef = r["E_final"]
            if abs(E0) > 1e-10:
                dE_list.append(abs((Ef - E0) / abs(E0)))

    return {
        "name": name,
        "label": label,
        "lifetimes": lifetimes,
        "P0": P0,
        "A": A,
        "eigs": eigs,
        "half_lives": half_lives,
        "ks_stat": ks_stat,
        "median_lt": np.median(lifetimes),
        "mean_lt": np.mean(lifetimes),
        "n_escaped": len(lifetimes),
        "median_dE": np.median(dE_list) if dE_list else 0,
    }


def main():
    print("=" * 60)
    print("  3D + Dissipative PK Analysis")
    print("=" * 60)

    # Analyze all datasets
    datasets_2d = [
        ("equal_mass", "2D Equal (1:1:1)"),
        ("unequal_mass", "2D Unequal (1:2:0.5)"),
        ("democratic", "2D Democratic (1:1:1)"),
    ]

    datasets_3d_cons = [
        ("3d_equal_mass_conservative", "3D Equal (conservative)"),
        ("3d_unequal_mass_conservative", "3D Unequal (conservative)"),
        ("3d_democratic_conservative", "3D Democratic (conservative)"),
    ]

    datasets_3d_diss = [
        ("3d_equal_mass_dissipative", "3D Equal (dissipative, c=100)"),
        ("3d_unequal_mass_dissipative", "3D Unequal (dissipative, c=100)"),
        ("3d_democratic_dissipative", "3D Democratic (dissipative, c=100)"),
    ]

    results_2d = [analyze_dataset(n, l) for n, l in datasets_2d]
    results_3d_cons = [analyze_dataset(n, l) for n, l in datasets_3d_cons]
    results_3d_diss = [analyze_dataset(n, l) for n, l in datasets_3d_diss]

    # Print summary table
    print("\n  {:40s} {:>8s} {:>8s} {:>8s} {:>8s}".format(
        "Dataset", "N_esc", "Med(τ)", "KS stat", "|ΔE/E|"))
    print("  " + "-" * 76)

    for group, group_name in [(results_2d, "2D Conservative"),
                               (results_3d_cons, "3D Conservative"),
                               (results_3d_diss, "3D Dissipative")]:
        print(f"\n  [{group_name}]")
        for r in group:
            if r is None:
                continue
            print("  {:40s} {:>8d} {:>8.1f} {:>8.4f} {:>8.4f}".format(
                r["label"], r["n_escaped"], r["median_lt"],
                r["ks_stat"], r["median_dE"]))

    # ---------------------------------------------------------------------------
    # Figure 6: Comparison plot (3 rows × 3 columns)
    # ---------------------------------------------------------------------------

    fig, axes = plt.subplots(3, 3, figsize=(7.2, 6.5))

    mass_labels = ["Equal (1:1:1)", "Unequal (1:2:0.5)", "Democratic"]
    row_labels = ["2D Conservative", "3D Conservative", "3D Dissipative (c=100)"]
    row_data = [results_2d, results_3d_cons, results_3d_diss]

    for row_idx, (row_results, row_label) in enumerate(zip(row_data, row_labels)):
        for col_idx, r in enumerate(row_results):
            ax = axes[row_idx, col_idx]
            if r is None:
                ax.text(0.5, 0.5, "No data", ha="center", va="center",
                        transform=ax.transAxes)
                continue

            lt = np.sort(r["lifetimes"])
            S_emp = 1 - np.arange(1, len(lt) + 1) / len(lt)

            t_grid = np.logspace(np.log10(max(lt[0], 0.1)), np.log10(lt[-1]), 200)
            S_pk = pk_survival(t_grid, r["A"], r["P0"])

            ax.loglog(lt, S_emp, ".", color=CB_BLUE, ms=1, alpha=0.3,
                      rasterized=True)
            ax.loglog(t_grid, np.maximum(S_pk, 1e-15), "-", color=CB_RED, lw=1.0)

            ax.set_ylim(1e-4, 1.5)
            if row_idx == 2:
                ax.set_xlabel("Lifetime ($t/t_{\\rm dyn}$)")
            if col_idx == 0:
                ax.set_ylabel("$S(t)$")

            # Annotations
            ax.text(0.95, 0.95, f"KS={r['ks_stat']:.3f}",
                    transform=ax.transAxes, fontsize=5, ha="right", va="top")
            if r["median_dE"] > 0.0001:
                ax.text(0.95, 0.82, f"|ΔE/E|={r['median_dE']:.4f}",
                        transform=ax.transAxes, fontsize=5, ha="right", va="top",
                        color=CB_GREEN)

            if row_idx == 0:
                ax.set_title(mass_labels[col_idx], fontsize=7)

    # Row labels
    for row_idx, label in enumerate(row_labels):
        axes[row_idx, 0].text(-0.4, 0.5, label, transform=axes[row_idx, 0].transAxes,
                              fontsize=6, ha="center", va="center", rotation=90,
                              fontweight="bold")

    plt.tight_layout(rect=[0.05, 0, 1, 1])
    fig.savefig(os.path.join(FIGDIR, "fig6_3d_dissipative_comparison.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig6_3d_dissipative_comparison.pdf"),
                bbox_inches="tight")
    plt.close()
    print("\n  Saved fig6_3d_dissipative_comparison")

    # ---------------------------------------------------------------------------
    # Figure 7: Dissipation effect on lifetime distribution
    # ---------------------------------------------------------------------------

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5))

    for col_idx in range(3):
        ax = axes[col_idx]
        r_cons = results_3d_cons[col_idx]
        r_diss = results_3d_diss[col_idx]

        if r_cons is None or r_diss is None:
            continue

        # CDFs
        lt_c = np.sort(r_cons["lifetimes"])
        lt_d = np.sort(r_diss["lifetimes"])
        S_c = 1 - np.arange(1, len(lt_c) + 1) / len(lt_c)
        S_d = 1 - np.arange(1, len(lt_d) + 1) / len(lt_d)

        ax.loglog(lt_c, S_c, "-", color=CB_BLUE, lw=1.0, label="Conservative")
        ax.loglog(lt_d, S_d, "-", color=CB_RED, lw=1.0, label="Dissipative")

        # PK fits
        t_grid = np.logspace(np.log10(max(min(lt_c[0], lt_d[0]), 0.1)),
                             np.log10(max(lt_c[-1], lt_d[-1])), 200)
        S_pk_c = pk_survival(t_grid, r_cons["A"], r_cons["P0"])
        S_pk_d = pk_survival(t_grid, r_diss["A"], r_diss["P0"])

        ax.loglog(t_grid, np.maximum(S_pk_c, 1e-15), "--", color=CB_BLUE,
                  lw=0.7, alpha=0.7)
        ax.loglog(t_grid, np.maximum(S_pk_d, 1e-15), "--", color=CB_RED,
                  lw=0.7, alpha=0.7)

        # KS between conservative and dissipative
        ks_stat, ks_p = ks_2samp(r_cons["lifetimes"], r_diss["lifetimes"])

        ax.set_xlabel("Lifetime ($t/t_{\\rm dyn}$)")
        if col_idx == 0:
            ax.set_ylabel("$S(t)$")
        ax.set_title(f"{'abc'[col_idx]}", fontweight="bold", fontsize=9,
                     loc="left", x=-0.15)
        ax.text(0.95, 0.95, mass_labels[col_idx], transform=ax.transAxes,
                fontsize=5.5, ha="right", va="top")
        ax.text(0.95, 0.80, f"KS={ks_stat:.3f}\np={ks_p:.2e}",
                transform=ax.transAxes, fontsize=5, ha="right", va="top",
                color=CB_PURPLE)

        # Median lifetime ratio
        ratio = np.median(r_diss["lifetimes"]) / np.median(r_cons["lifetimes"])
        ax.text(0.95, 0.60, f"τ_diss/τ_cons={ratio:.2f}",
                transform=ax.transAxes, fontsize=5, ha="right", va="top",
                color=CB_GREEN)

        ax.set_ylim(1e-4, 1.5)

    axes[0].legend(loc="lower left", fontsize=5.5, framealpha=0.8)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig7_dissipation_effect.png"),
                dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, "fig7_dissipation_effect.pdf"),
                bbox_inches="tight")
    plt.close()
    print("  Saved fig7_dissipation_effect")

    # ---------------------------------------------------------------------------
    # Summary statistics for manuscript
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Summary for manuscript")
    print("=" * 60)

    print("\n  PK model fit quality (KS statistic, lower = better fit):")
    for group, gname in [(results_2d, "2D"), (results_3d_cons, "3D cons"),
                          (results_3d_diss, "3D diss")]:
        ks_vals = [r["ks_stat"] for r in group if r is not None]
        print(f"    {gname}: mean KS = {np.mean(ks_vals):.4f} ± {np.std(ks_vals):.4f}")

    print("\n  Lifetime shift (dissipative vs conservative):")
    for i, mass_label in enumerate(mass_labels):
        if results_3d_cons[i] is None or results_3d_diss[i] is None:
            continue
        ratio = (np.median(results_3d_diss[i]["lifetimes"]) /
                 np.median(results_3d_cons[i]["lifetimes"]))
        print(f"    {mass_label}: τ_diss/τ_cons = {ratio:.3f}")

    print("\n  Energy dissipated (median |ΔE/E|):")
    for r in results_3d_diss:
        if r is not None:
            print(f"    {r['label']}: {r['median_dE']:.4f}")

    print("\n  Half-lives comparison:")
    for i, mass_label in enumerate(mass_labels):
        r2d = results_2d[i]
        r3d = results_3d_cons[i]
        r3dd = results_3d_diss[i]
        if r2d is None or r3d is None or r3dd is None:
            continue
        hl_2d = r2d["half_lives"][:3] if len(r2d["half_lives"]) >= 3 else r2d["half_lives"]
        hl_3d = r3d["half_lives"][:3] if len(r3d["half_lives"]) >= 3 else r3d["half_lives"]
        hl_3dd = r3dd["half_lives"][:3] if len(r3dd["half_lives"]) >= 3 else r3dd["half_lives"]
        print(f"    {mass_label}:")
        print(f"      2D:   {[f'{h:.1f}' for h in hl_2d]}")
        print(f"      3D:   {[f'{h:.1f}' for h in hl_3d]}")
        print(f"      3D+GW:{[f'{h:.1f}' for h in hl_3dd]}")

    print("\n" + "=" * 60)
    print("  Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
