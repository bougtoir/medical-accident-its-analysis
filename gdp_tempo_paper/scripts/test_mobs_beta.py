"""
Test M_obs+β combination model.

M_obs uses observable μ(t) from asset composition (0 free parameters for tempo).
M_obs+β adds intangible capital share β (1 free parameter, fitted in-sample).

Question: Does adding β to M_obs improve OOS prediction?

Models compared:
  M0:      K_tang = PIM_instant(I),               β=0      (0 params)
  M_obs:   K_tang = PIM_obs_tempo(I, μ_obs(t)),   β=0      (0 params)
  M3:      K_tang = PIM_instant(I),               β=est    (1 param)
  M_obs+β: K_tang = PIM_obs_tempo(I, μ_obs(t)),   β=est    (1 param)
  M2:      K_tang = PIM_drift(I, μ0, μ1),         β=0      (2 params)
  M4:      K_tang = PIM_lagged(I, μ_j),           β=est    (3+ params)
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_full_analysis_mobs import (
    prepare_countries, load_oecd_gfcf, compute_observable_mu,
    pim_instant, pim_lagged, pim_lagged_tempo, pim_observable_tempo,
    build_intan_stock, fit_mu_const, fit_tempo, fit_beta_given_K, fit_joint,
    test_B_growth, test_B_growth_intan, test_A_levels,
    DELTA_I, OOS_TEST_YEARS,
)

ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")


def fit_beta_given_K_obs(K_tang, K_intan, logY, logL, alpha):
    """Fit β given observable-tempo K_tang."""
    logK_tang = np.log(np.where(K_tang > 0, K_tang, 1e-6))
    logK_intan = np.log(np.where(K_intan > 0, K_intan, 1e-6))
    best = (np.inf, 0.0)
    for beta in np.linspace(0.0, 0.40, 41):
        if alpha + beta >= 0.95:
            continue
        r = test_B_growth_intan(logY, logK_tang, logK_intan, logL, alpha, beta)
        if r < best[0]:
            best = (r, beta)
    return best[1]


def run_comparison(countries):
    fair_rows = []
    oos_rows = []

    for c in countries:
        alpha = 1 - float(np.clip(np.mean(c.labsh), 0.40, 0.75))
        L = c.emp * c.avh; LH = L * c.hc
        logY = np.log(c.Y); logLH = np.log(LH); logL = np.log(L)
        K_intan = build_intan_stock(c.Y, c.rnd_share)
        if K_intan is None:
            continue
        logK_intan = np.log(np.where(K_intan > 0, K_intan, 1e-6))

        # Build capital stocks
        K_M0 = pim_instant(c.I, c.delta, c.K0)
        K_Mobs = pim_observable_tempo(c.I, c.delta, c.K0, c.mu_obs)
        mu0, mu1d = fit_tempo(c.I, c.delta, c.K0, logY, logLH, alpha, c.years)
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1d, c.years)

        # Fit β for M3 (instant K) and M_obs+β (observable tempo K)
        beta_M3 = fit_beta_given_K(K_M0, K_intan, logY, logL, alpha)
        beta_Mobs = fit_beta_given_K_obs(K_Mobs, K_intan, logY, logL, alpha)

        # Fit M4 (joint)
        idx_map = {int(y): ii for ii, y in enumerate(c.years)}
        ki = [idx_map.get(int(y), None) for y in c.cwon_years]
        mu_j, beta_j, _, _ = fit_joint(
            c.I, c.delta, c.K0, K_intan, logY, logL, alpha, ki, c.pca)
        K_M4 = pim_lagged(c.I, c.delta, c.K0, float(mu_j)) \
            if np.isfinite(mu_j) else K_M0

        # ── In-sample fair eval ───────────────────────────────────────
        models = {
            "M0":      (K_M0,   0.0),
            "Mobs":    (K_Mobs, 0.0),
            "M3":      (K_M0,   beta_M3),
            "Mobs_b":  (K_Mobs, beta_Mobs),
            "M2":      (K_M2,   0.0),
            "M4":      (K_M4,   beta_j if np.isfinite(beta_j) else 0.0),
        }
        rec = {"country": c.country, "iso3": c.iso, "alpha": alpha,
               "beta_M3": beta_M3, "beta_Mobs": beta_Mobs,
               "beta_M4": beta_j if np.isfinite(beta_j) else 0.0,
               "mu_obs_mean": float(np.mean(c.mu_obs))}
        for name, (K, beta) in models.items():
            if K is None:
                rec[f"{name}_B"] = np.nan; continue
            logK = np.log(np.where(K > 0, K, 1e-6))
            if beta > 0:
                rec[f"{name}_B"] = test_B_growth_intan(
                    logY, logK, logK_intan, logL, alpha, beta)
            else:
                rec[f"{name}_B"] = test_B_growth(logY, logK, logLH, alpha)
        fair_rows.append(rec)

        # ── OOS ───────────────────────────────────────────────────────
        mask_train = c.years <= 2014
        mask_test = np.isin(c.years, OOS_TEST_YEARS)
        if mask_test.sum() < 3 or mask_train.sum() < 20:
            continue

        I_tr = c.I[mask_train]; d_tr = c.delta[mask_train]
        yr_tr = c.years[mask_train]; Y_tr = c.Y[mask_train]
        emp_t = c.emp[mask_train]; avh_t = c.avh[mask_train]; hc_t = c.hc[mask_train]
        logY_tr = np.log(Y_tr); logLH_tr = np.log(emp_t * avh_t * hc_t)
        logL_tr = np.log(emp_t * avh_t)
        K_intan_tr = K_intan[mask_train]
        K_intan_full = K_intan
        L_full = c.emp * c.avh * c.hc
        K0 = c.K0

        # Train-set fits
        mu0_tr, mu1_tr = fit_tempo(I_tr, d_tr, K0, logY_tr, logLH_tr, alpha, yr_tr)
        K_M0_tr = pim_instant(I_tr, d_tr, K0)
        mu_obs_tr = c.mu_obs[mask_train]
        K_Mobs_tr = pim_observable_tempo(I_tr, d_tr, K0, mu_obs_tr)
        beta3_tr = fit_beta_given_K(K_M0_tr, K_intan_tr, logY_tr, logL_tr, alpha)
        beta_obs_tr = fit_beta_given_K_obs(K_Mobs_tr, K_intan_tr, logY_tr, logL_tr, alpha)

        ki_tr = [idx_map.get(int(y), None) if int(y) <= 2014 else None
                 for y in c.cwon_years]
        mu4_tr, beta4_tr, _, _ = fit_joint(
            I_tr, d_tr, K0, K_intan_tr, logY_tr, logL_tr, alpha,
            ki_tr[:len(np.arange(1995, 2015))], c.pca[c.cwon_years <= 2014])

        # Full-period capital stocks (using train-set parameters)
        K_full = {
            "M0":     (pim_instant(c.I, c.delta, K0), 0.0),
            "Mobs":   (pim_observable_tempo(c.I, c.delta, K0, c.mu_obs), 0.0),
            "M3":     (pim_instant(c.I, c.delta, K0), beta3_tr),
            "Mobs_b": (pim_observable_tempo(c.I, c.delta, K0, c.mu_obs), beta_obs_tr),
            "M2":     (pim_lagged_tempo(c.I, c.delta, K0, mu0_tr, mu1_tr, c.years), 0.0),
            "M4":     (pim_lagged(c.I, c.delta, K0, mu4_tr) if np.isfinite(mu4_tr)
                       else pim_instant(c.I, c.delta, K0),
                       beta4_tr if np.isfinite(beta4_tr) else 0.0),
        }

        orec = {"country": c.country, "iso3": c.iso,
                "beta3_tr": beta3_tr, "beta_obs_tr": beta_obs_tr,
                "beta4_tr": beta4_tr if np.isfinite(beta4_tr) else 0.0}

        for name, (K, beta) in K_full.items():
            if K is None:
                orec[f"{name}_oos"] = np.nan; continue
            logK = np.log(np.where(K > 0, K, 1e-6))
            if beta > 0:
                logI = np.log(np.where(K_intan_full > 0, K_intan_full, 1e-6))
                logLf = np.log(c.emp * c.avh)
                w_L = 1 - alpha - beta
                raw_tfp = logY - alpha * logK - beta * logI - w_L * logLf
            else:
                logLf = np.log(L_full)
                raw_tfp = logY - alpha * logK - (1 - alpha) * logLf
            tdm = (c.years >= 2005) & (c.years <= 2014)
            if tdm.sum() == 0:
                orec[f"{name}_oos"] = np.nan; continue
            tfp_proj = float(np.mean(raw_tfp[tdm]))
            if beta > 0:
                pred = alpha * logK + beta * logI + w_L * np.log(c.emp * c.avh) + tfp_proj
            else:
                pred = alpha * logK + (1 - alpha) * np.log(L_full) + tfp_proj
            resid = np.log(c.Y)[mask_test] - pred[mask_test]
            orec[f"{name}_oos"] = float(np.mean(np.abs(np.expm1(resid))) * 100)
        oos_rows.append(orec)

        print(f"  {c.country:22s}  "
              f"M0={orec['M0_oos']:.2f}  Mobs={orec['Mobs_oos']:.2f}  "
              f"M3={orec['M3_oos']:.2f}  Mobs+β={orec['Mobs_b_oos']:.2f}  "
              f"M2={orec['M2_oos']:.2f}  M4={orec.get('M4_oos','nan')}  "
              f"(β_obs={beta_obs_tr:.3f})", flush=True)

    return pd.DataFrame(fair_rows), pd.DataFrame(oos_rows)


def make_figure(oos):
    cols = ["M0_oos", "Mobs_oos", "M3_oos", "Mobs_b_oos", "M2_oos", "M4_oos"]
    labels = ["M0\n(instant)\n0 params", "$M_{obs}$\n(asset comp.)\n0 params",
              "M3\n(+intan.)\n1 param", "$M_{obs}+\\beta$\n(asset+intan.)\n1 param",
              "M2\n(est. drift)\n2 params", "M4\n(joint)\n3+ params"]
    colors = ["#888888", "#9467bd", "#55a868", "#e377c2", "#dd8452", "#c44e52"]

    fig, ax = plt.subplots(figsize=(11, 5))
    data = [oos[c].dropna().values for c in cols]
    bp = ax.boxplot(data, tick_labels=labels, showmeans=True, widths=0.5,
                    patch_artist=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color); patch.set_alpha(0.4)
    for i, col in enumerate(cols):
        med = float(oos[col].dropna().median())
        ax.text(i+1, med+0.3, f"{med:.2f}%", ha="center", fontsize=9,
                fontweight="bold")
    ax.set_ylabel("Out-of-sample MAPE 2015–19 (%)")
    ax.set_title("OOS forecast: Does adding intangible $\\beta$ improve $M_{obs}$?")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, "fig_mobs_beta_comparison.png")
    plt.savefig(out, dpi=180); plt.close()
    print(f"  wrote {out}")


def main():
    print("Loading data...", flush=True)
    gfcf = load_oecd_gfcf()
    mu_df = compute_observable_mu(gfcf)
    countries = prepare_countries(mu_df)
    print(f"  {len(countries)} countries\n", flush=True)

    print("--- OOS comparison: M_obs vs M_obs+β ---", flush=True)
    fair, oos = run_comparison(countries)
    fair.to_csv(os.path.join(DATA, "mobs_beta_fair.csv"), index=False)
    oos.to_csv(os.path.join(DATA, "mobs_beta_oos.csv"), index=False)

    print("\n" + "=" * 60)
    print("RESULTS: M_obs+β COMBINATION MODEL")
    print("=" * 60)

    print("\nIn-sample (Test B RMSE, median pp):")
    for name in ("M0", "Mobs", "M3", "Mobs_b", "M2", "M4"):
        col = f"{name}_B"
        if col in fair.columns:
            print(f"  {name:8s}: {fair[col].median():.4f}")

    print("\nOut-of-sample (MAPE 2015-19, median %):")
    for name in ("M0", "Mobs", "M3", "Mobs_b", "M2", "M4"):
        col = f"{name}_oos"
        if col in oos.columns:
            v = oos[col].median()
            print(f"  {name:8s}: {v:.3f} %")

    m0 = oos["M0_oos"].median()
    mobs = oos["Mobs_oos"].median()
    mobs_b = oos["Mobs_b_oos"].median()
    m3 = oos["M3_oos"].median()
    m2 = oos["M2_oos"].median()

    print(f"\nKey comparisons:")
    print(f"  M_obs    vs M0:     {(m0-mobs)/m0*100:+.1f}%  (tempo only, 0 params)")
    print(f"  M_obs+β  vs M0:     {(m0-mobs_b)/m0*100:+.1f}%  (tempo+intan, 1 param)")
    print(f"  M_obs+β  vs M_obs:  {(mobs-mobs_b)/mobs*100:+.1f}%  (marginal β contribution)")
    print(f"  M3       vs M0:     {(m0-m3)/m0*100:+.1f}%  (intan only, 1 param)")
    print(f"  M2       vs M0:     {(m0-m2)/m0*100:+.1f}%  (est. drift, 2 params)")

    # Country-level: how often does M_obs+β beat M_obs?
    wins = (oos["Mobs_b_oos"] < oos["Mobs_oos"]).sum()
    total = oos[["Mobs_oos", "Mobs_b_oos"]].dropna().shape[0]
    print(f"\n  M_obs+β beats M_obs: {wins}/{total} countries ({wins/total*100:.0f}%)")

    # β distribution
    print(f"\nEstimated β (train-set):")
    print(f"  M3 β:      mean={oos['beta3_tr'].mean():.3f}  "
          f"median={oos['beta3_tr'].median():.3f}")
    print(f"  M_obs+β β: mean={oos['beta_obs_tr'].mean():.3f}  "
          f"median={oos['beta_obs_tr'].median():.3f}")

    make_figure(oos)

    # Save summary
    summary = {
        "n_countries": len(oos),
        "oos_median": {name: float(oos[f"{name}_oos"].median())
                       for name in ("M0", "Mobs", "M3", "Mobs_b", "M2", "M4")},
        "mobs_b_beats_mobs": f"{wins}/{total}",
        "beta_obs_median": float(oos["beta_obs_tr"].median()),
        "beta_obs_mean": float(oos["beta_obs_tr"].mean()),
    }
    with open(os.path.join(DATA, "mobs_beta_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
