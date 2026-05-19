"""Solow-residual historical decomposition and counterfactual wealth simulation.

Produces:
  - Fig 10: TFP decomposition — M0 raw Solow residual vs post-tempo residual
            for 6 representative countries (time-series panel).
  - Fig 11: Counterfactual national wealth — CWON official vs β-adjusted
            for 12 countries (bar chart).
  - Table 5: Summary of tempo-artifact share of TFP (all 39 countries).
  - solow_decomposition.csv  — per-country per-year TFP under M0 vs M2/M4.
  - counterfactual_wealth.csv — per-country CWON vs β-adjusted wealth.

These analyses answer Economica's "so what?" question:
  (a) What fraction of measured TFP is a timing artefact?
  (b) How much does official wealth understate true productive capital?
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Register a Japanese font so that JA figures render correctly.
from matplotlib import font_manager
for path in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
             "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
    if os.path.exists(path):
        font_manager.fontManager.addfont(path)
        plt.rcParams["font.sans-serif"] = ["IPAGothic", "DejaVu Sans"]
        break

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
TAB = os.path.join(ROOT, "tables")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

# Import helpers from the main analysis script
import sys
sys.path.insert(0, HERE)
from run_paper_analyses import (
    prepare_countries, Country,
    pim_instant, pim_lagged, pim_lagged_tempo, build_intan_stock,
    geom_weights, load_cwon,
    fit_mu_const, fit_tempo, fit_beta_given_K, fit_joint,
    DELTA_I, CWON_DIR,
)


def compute_tfp_series(logY, logK, logLH, alpha):
    """Raw TFP = log Y - alpha * log K - (1-alpha) * log L*H."""
    return logY - alpha * logK - (1 - alpha) * logLH


def compute_tfp_intan(logY, logK_tang, logK_intan, logL, alpha, beta):
    """TFP with intangibles."""
    w_L = 1 - alpha - beta
    return logY - alpha * logK_tang - beta * logK_intan - w_L * logL


def run_solow_decomposition(countries: list[Country]) -> pd.DataFrame:
    """For each country, compute TFP under M0, M2, and M4."""
    all_rows = []
    for c in countries:
        alpha = 1 - float(np.clip(np.mean(c.labsh), 0.40, 0.75))
        L = c.emp * c.avh
        LH = L * c.hc
        logY = np.log(c.Y)
        logLH = np.log(LH)
        logL = np.log(L)

        K_intan = build_intan_stock(c.Y, c.rnd_share)
        if K_intan is None:
            continue

        # M0 (instant PIM, beta=0)
        K_M0 = pim_instant(c.I, c.delta, c.K0)
        logK_M0 = np.log(np.where(K_M0 > 0, K_M0, 1e-6))
        tfp_M0 = compute_tfp_series(logY, logK_M0, logLH, alpha)

        # M2 (time-varying lag, beta=0)
        mu0, mu1 = fit_tempo(c.I, c.delta, c.K0, logY, logLH, alpha, c.years)
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1, c.years)
        logK_M2 = np.log(np.where(K_M2 > 0, K_M2, 1e-6))
        tfp_M2 = compute_tfp_series(logY, logK_M2, logLH, alpha)

        # M4 (joint, mu + beta)
        idx_map = {int(y): ii for ii, y in enumerate(c.years)}
        ki = [idx_map.get(int(y), None) for y in c.cwon_years]
        mu_j, beta_j, _, _ = fit_joint(c.I, c.delta, c.K0, K_intan,
                                       logY, logL, alpha, ki, c.pca)
        if np.isfinite(mu_j):
            K_M4 = pim_lagged(c.I, c.delta, c.K0, float(mu_j))
        else:
            K_M4 = K_M0.copy()
            mu_j = 0.0
            beta_j = 0.0
        logK_M4 = np.log(np.where(K_M4 > 0, K_M4, 1e-6))
        logK_intan = np.log(np.where(K_intan > 0, K_intan, 1e-6))
        if beta_j > 0:
            tfp_M4 = compute_tfp_intan(logY, logK_M4, logK_intan, logL,
                                       alpha, beta_j)
        else:
            tfp_M4 = compute_tfp_series(logY, logK_M4, logLH, alpha)

        for t_idx, yr in enumerate(c.years):
            all_rows.append({
                "country": c.country,
                "iso3": c.iso,
                "year": int(yr),
                "tfp_M0": float(tfp_M0[t_idx]),
                "tfp_M2": float(tfp_M2[t_idx]),
                "tfp_M4": float(tfp_M4[t_idx]),
                "mu0": float(mu0),
                "mu1": float(mu1),
                "mu_j": float(mu_j),
                "beta_j": float(beta_j),
                "alpha": float(alpha),
            })
    return pd.DataFrame(all_rows)


def summarise_tempo_artifact(df: pd.DataFrame) -> pd.DataFrame:
    """Table 5: per-country summary of tempo artifact share."""
    rows = []
    for country, grp in df.groupby("country"):
        # Growth-rate variance decomposition
        dtfp_M0 = np.diff(grp["tfp_M0"].values)
        dtfp_M2 = np.diff(grp["tfp_M2"].values)
        dtfp_M4 = np.diff(grp["tfp_M4"].values)

        var_M0 = float(np.var(dtfp_M0)) if len(dtfp_M0) > 1 else np.nan
        var_M2 = float(np.var(dtfp_M2)) if len(dtfp_M2) > 1 else np.nan
        var_M4 = float(np.var(dtfp_M4)) if len(dtfp_M4) > 1 else np.nan

        # Tempo artifact share = (var_M0 - var_M2) / var_M0
        artifact_tempo = (var_M0 - var_M2) / var_M0 if var_M0 > 0 else np.nan
        artifact_joint = (var_M0 - var_M4) / var_M0 if var_M0 > 0 else np.nan

        # Cumulative TFP drift
        cum_M0 = float(grp["tfp_M0"].iloc[-1] - grp["tfp_M0"].iloc[0])
        cum_M2 = float(grp["tfp_M2"].iloc[-1] - grp["tfp_M2"].iloc[0])
        cum_M4 = float(grp["tfp_M4"].iloc[-1] - grp["tfp_M4"].iloc[0])

        rows.append({
            "Country": country,
            "ISO3": grp["iso3"].iloc[0],
            "mu1": float(grp["mu1"].iloc[0]),
            "beta_j": float(grp["beta_j"].iloc[0]),
            "Var(dTFP) M0": round(var_M0 * 1e4, 2),
            "Var(dTFP) M2": round(var_M2 * 1e4, 2),
            "Tempo share %": round(artifact_tempo * 100, 1) if np.isfinite(artifact_tempo) else "",
            "Joint share %": round(artifact_joint * 100, 1) if np.isfinite(artifact_joint) else "",
            "Cum TFP M0": round(cum_M0, 3),
            "Cum TFP M4": round(cum_M4, 3),
        })
    return pd.DataFrame(rows).sort_values("Country")


def run_counterfactual_wealth(countries: list[Country],
                              fair_df: pd.DataFrame) -> pd.DataFrame:
    """Counterfactual: CWON official vs beta-adjusted wealth.

    The intangible capital stock from build_intan_stock is in PWT constant
    national-currency units (rgdpna). To express the beta-correction in CWON
    USD terms, we compute the ratio K_intan / K_tang (PIM) at 2019 and apply
    that ratio to CWON produced capital.  This avoids cross-currency scaling.
    """
    cwon_pca = load_cwon("NW.PCA.TO")
    cwon_tow = load_cwon("NW.TOW.TO")
    rows = []
    for c in countries:
        frow = fair_df[fair_df["country"] == c.country]
        if frow.empty:
            continue
        beta_j = float(frow["beta_M4"].iloc[0])
        mu_j = float(frow["mu_M4"].iloc[0])
        if beta_j <= 0:
            continue

        latest_yr = 2019
        pca_val = cwon_pca.get((c.iso, latest_yr))
        tow_val = cwon_tow.get((c.iso, latest_yr))
        if pca_val is None or tow_val is None:
            continue

        K_intan = build_intan_stock(c.Y, c.rnd_share)
        if K_intan is None:
            continue

        # Tangible capital stock under M4 parameters
        if np.isfinite(mu_j) and mu_j > 0.02:
            K_tang = pim_lagged(c.I, c.delta, c.K0, float(mu_j))
        else:
            K_tang = pim_instant(c.I, c.delta, c.K0)

        idx_map = {int(y): ii for ii, y in enumerate(c.years)}
        yr_idx = idx_map.get(latest_yr)
        if yr_idx is None:
            continue

        k_tang_val = float(K_tang[yr_idx])
        k_intan_val = float(K_intan[yr_idx])
        if k_tang_val <= 0:
            continue

        # The beta-correction adds beta * K_intan to the production function.
        # In CWON terms, this is equivalent to scaling CWON_PCA by
        # (1 + beta * K_intan / (alpha * K_tang)), where alpha*K_tang is the
        # tangible contribution.  Simpler: express adjustment as
        # beta * (K_intan / K_tang) * CWON_PCA.
        intan_ratio = k_intan_val / k_tang_val
        adjustment_usd = beta_j * intan_ratio * pca_val
        adjusted_pca = pca_val + adjustment_usd
        pca_gap_pct = adjustment_usd / pca_val * 100

        adjusted_tow = tow_val + adjustment_usd
        tow_gap_pct = adjustment_usd / tow_val * 100

        rows.append({
            "country": c.country,
            "iso3": c.iso,
            "beta_j": beta_j,
            "cwon_pca_official": pca_val / 1e12,
            "cwon_pca_adjusted": adjusted_pca / 1e12,
            "pca_gap_pct": round(pca_gap_pct, 1),
            "cwon_tow_official": tow_val / 1e12,
            "cwon_tow_adjusted": adjusted_tow / 1e12,
            "tow_gap_pct": round(tow_gap_pct, 1),
            "intan_ratio": round(intan_ratio, 3),
        })
    return pd.DataFrame(rows).sort_values("pca_gap_pct", ascending=False)


def make_fig10(solow_df: pd.DataFrame, lang: str = "en"):
    """Solow residual decomposition for 6 representative countries."""
    highlight = ["Japan", "United States", "Germany",
                 "Republic of Korea", "United Kingdom", "France"]
    labels = {
        "en": {
            "title": "Fig. 10. Solow-residual decomposition: M0 vs tempo-adjusted (M2) vs joint (M4)",
            "ylabel": "TFP (log level)",
            "M0": "M0 (Solow baseline)",
            "M2": "M2 (tempo-adjusted)",
            "M4": "M4 (joint)",
            "xlabel": "Year",
        },
        "ja": {
            "title": "図10. ソロー残差の分解: M0 vs テンポ調整(M2) vs 統合(M4)",
            "ylabel": "TFP（対数水準）",
            "M0": "M0（ソロー基準）",
            "M2": "M2（テンポ調整）",
            "M4": "M4（統合）",
            "xlabel": "年",
        },
    }[lang]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True)
    for ax, country in zip(axes.flat, highlight):
        cdf = solow_df[solow_df["country"] == country]
        if cdf.empty:
            ax.set_visible(False)
            continue
        years = cdf["year"].values
        # Demean for visual clarity
        tfp_m0 = cdf["tfp_M0"].values
        tfp_m2 = cdf["tfp_M2"].values
        tfp_m4 = cdf["tfp_M4"].values
        tfp_m0_d = tfp_m0 - tfp_m0.mean()
        tfp_m2_d = tfp_m2 - tfp_m2.mean()
        tfp_m4_d = tfp_m4 - tfp_m4.mean()

        ax.plot(years, tfp_m0_d, "-", color="#4c72b0", lw=1.5,
                label=labels["M0"])
        ax.plot(years, tfp_m2_d, "--", color="#c44e52", lw=1.5,
                label=labels["M2"])
        ax.plot(years, tfp_m4_d, ":", color="#55a868", lw=1.5,
                label=labels["M4"])
        ax.fill_between(years, tfp_m0_d, tfp_m2_d, alpha=0.15,
                        color="#c44e52")
        ax.set_title(country, fontsize=11)
        ax.grid(alpha=0.3)
    for ax in axes[-1]:
        ax.set_xlabel(labels["xlabel"])
    for ax in axes[:, 0]:
        ax.set_ylabel(labels["ylabel"], fontsize=9)
    handles, lbls = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.02), fontsize=10)
    fig.suptitle(labels["title"], y=0.99, fontsize=12)
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    out = os.path.join(FIG, f"fig10_solow_decomp_{lang}.png")
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print("wrote", out)


def make_fig11(cf_df: pd.DataFrame, lang: str = "en"):
    """Counterfactual wealth: CWON official vs beta-adjusted (bar chart)."""
    if cf_df.empty:
        print("skipping fig11: no counterfactual data")
        return
    top12 = cf_df.head(12)
    labels = {
        "en": {
            "title": "Fig. 11. National wealth: CWON official vs intangible-adjusted",
            "ylabel": "Produced capital (2019, USD trillion)",
            "official": "CWON official",
            "adjusted": r"+ $\beta \cdot K_I$ adjustment",
            "xlabel": "",
        },
        "ja": {
            "title": "図11. 国富: CWON公式値 vs 無形資本調整後",
            "ylabel": "生産資本（2019年、兆USD）",
            "official": "CWON公式値",
            "adjusted": r"$+\beta \cdot K_I$ 調整分",
            "xlabel": "",
        },
    }[lang]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(top12))
    w = 0.35
    ax.bar(x - w / 2, top12["cwon_pca_official"], w, color="#4c72b0",
           label=labels["official"])
    ax.bar(x + w / 2, top12["cwon_pca_adjusted"], w, color="#c44e52",
           label=labels["adjusted"])
    # Add percentage labels
    for i, (_, row) in enumerate(top12.iterrows()):
        ax.annotate(f"+{row['pca_gap_pct']:.1f}%",
                    xy=(i + w / 2, row["cwon_pca_adjusted"]),
                    ha="center", va="bottom", fontsize=8, color="#c44e52")
    ax.set_xticks(x)
    ax.set_xticklabels(top12["iso3"], fontsize=9)
    ax.set_ylabel(labels["ylabel"])
    ax.set_title(labels["title"], fontsize=12)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, f"fig11_counterfactual_wealth_{lang}.png")
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print("wrote", out)


def main():
    print("Preparing country panel...", flush=True)
    countries = prepare_countries()
    print(f"  {len(countries)} countries", flush=True)

    # Load fair_eval for beta estimates
    fair = pd.read_csv(os.path.join(DATA, "fair_eval.csv"))

    print("\n--- Solow residual decomposition ---", flush=True)
    solow = run_solow_decomposition(countries)
    solow.to_csv(os.path.join(DATA, "solow_decomposition.csv"), index=False)
    print(f"  {len(solow)} rows written", flush=True)

    print("\n--- Tempo artifact summary (Table 5) ---", flush=True)
    table5 = summarise_tempo_artifact(solow)
    table5.to_csv(os.path.join(TAB, "table5_tempo_artifact.csv"), index=False)
    print(table5[["Country", "mu1", "beta_j", "Tempo share %",
                   "Joint share %"]].to_string(index=False))

    print("\n--- Counterfactual wealth ---", flush=True)
    cf = run_counterfactual_wealth(countries, fair)
    cf.to_csv(os.path.join(DATA, "counterfactual_wealth.csv"), index=False)
    print(f"  {len(cf)} countries with beta > 0")
    if not cf.empty:
        print(cf[["country", "iso3", "beta_j", "intan_ratio", "pca_gap_pct",
                   "tow_gap_pct"]].to_string(index=False))

    print("\n--- Figures ---", flush=True)
    for lang in ("en", "ja"):
        make_fig10(solow, lang)
        make_fig11(cf, lang)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
