"""K-level measurement consequences analysis.

Shows that the tempo correction changes measured capital, and the
growth-accounting quantities built on it, in ways that matter for
macroeconomic measurement.

Uses pre-computed full_solow.csv (TFP under M0/M2/Mobs) and observable_mu.csv
to derive K-level differences without requiring raw PWT/OECD data files.

Key identity:
    TFP = logY − α logK − (1−α) logLH
    ⟹ logK_obs − logK_M0 = (TFP_M0 − TFP_obs) / α

Produces:
  - k_level_diff.csv: per country-year K-level gap, TFP shift, labor-share shift
  - k_level_summary.json: cross-country summary
  - table5_k_level.csv: country-level manuscript results table
  - fig10_k_divergence_{en,ja}.png: K-level divergence time series
  - fig11_tfp_consequence_{en,ja}.png: ΔK → ΔTFP scatter
  - fig12_labor_share_{en,ja}.png: implied labor-share correction bar chart
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
TAB = os.path.join(ROOT, "tables")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)


def compute_k_gap_from_tfp(solow: pd.DataFrame) -> pd.DataFrame:
    """Derive K_obs/K_M0 gap from TFP difference.

    From the growth-accounting identity:
        TFP_M0 − TFP_obs = α (logK_obs − logK_M0)
    """
    df = solow.copy()
    df["delta_logK"] = (df["tfp_M0"] - df["tfp_Mobs"]) / df["alpha"]
    df["K_pct_diff"] = (np.exp(df["delta_logK"]) - 1) * 100
    df["TFP_shift"] = df["tfp_M0"] - df["tfp_Mobs"]
    df["TFP_shift_pct"] = df["TFP_shift"] * 100
    # Implied labor-share shift (percentage points):
    # If K rises by delta_logK, the capital contribution rises by α·delta_logK,
    # so residual (labor + TFP) falls by α·delta_logK.
    # In growth-accounting terms, the implied labor share shifts by
    # −α · delta_logK (in log-point units, ≈ percentage points for small values).
    df["ls_shift_pp"] = -df["alpha"] * df["delta_logK"] * 100
    return df


def summarise_k_levels(kdf: pd.DataFrame) -> dict:
    """Cross-country summary for the K-level analysis."""
    recent = kdf[(kdf["year"] >= 2010) & (kdf["year"] <= 2019)]
    by_c = recent.groupby("iso3").agg({
        "K_pct_diff": "mean",
        "TFP_shift_pct": "mean",
        "ls_shift_pp": "mean",
        "alpha": "first",
        "country": "first",
    }).reset_index()

    def stats(series, decimals=2):
        return {
            "median": round(float(series.median()), decimals),
            "mean": round(float(series.mean()), decimals),
            "q25": round(float(series.quantile(0.25)), decimals),
            "q75": round(float(series.quantile(0.75)), decimals),
            "min": round(float(series.min()), decimals),
            "max": round(float(series.max()), decimals),
        }

    summary = {
        "n_countries": int(by_c.shape[0]),
        "period": "2010-2019",
        "K_pct_diff": stats(by_c["K_pct_diff"]),
        "TFP_shift_pct": stats(by_c["TFP_shift_pct"]),
        "labor_share_shift_pp": stats(by_c["ls_shift_pp"], 3),
        "countries_K_higher_than_M0": int((by_c["K_pct_diff"] > 0).sum()),
        "countries_K_lower_than_M0": int((by_c["K_pct_diff"] < 0).sum()),
        "top5_K_diff": by_c.nlargest(5, "K_pct_diff")[
            ["iso3", "country", "K_pct_diff", "TFP_shift_pct", "ls_shift_pp"]
        ].round(2).to_dict("records"),
        "bottom5_K_diff": by_c.nsmallest(5, "K_pct_diff")[
            ["iso3", "country", "K_pct_diff", "TFP_shift_pct", "ls_shift_pp"]
        ].round(2).to_dict("records"),
    }

    # Growth-rate variance decomposition (2010-2019 period, consistent with above)
    var_rows = []
    for iso3, grp in recent.groupby("iso3"):
        grp = grp.sort_values("year")
        dtfp_M0 = np.diff(grp["tfp_M0"].values)
        dtfp_obs = np.diff(grp["tfp_Mobs"].values)
        var_M0 = float(np.var(dtfp_M0))
        var_obs = float(np.var(dtfp_obs))
        tempo_share = (var_M0 - var_obs) / var_M0 if var_M0 > 0 else np.nan
        var_rows.append({
            "iso3": iso3,
            "var_dTFP_M0": var_M0,
            "var_dTFP_obs": var_obs,
            "tempo_share": tempo_share,
        })
    vdf = pd.DataFrame(var_rows)
    summary["TFP_variance_reduction"] = {
        "median_pct": round(float(vdf["tempo_share"].median() * 100), 1),
        "mean_pct": round(float(vdf["tempo_share"].mean() * 100), 1),
        "positive_count": int((vdf["tempo_share"] > 0).sum()),
        "total_count": int(vdf.shape[0]),
    }

    return summary


def make_table_k_level(kdf: pd.DataFrame) -> pd.DataFrame:
    """Build the country-level K measurement consequences table."""
    recent = kdf[(kdf["year"] >= 2010) & (kdf["year"] <= 2019)]
    by_country = recent.groupby("iso3").agg({
        "country": "first",
        "K_pct_diff": "mean",
        "TFP_shift_pct": "mean",
        "ls_shift_pp": "mean",
    }).reset_index()
    table = by_country.sort_values("K_pct_diff").rename(columns={
        "country": "Country",
        "iso3": "ISO3",
        "K_pct_diff": "K gap (%)",
        "TFP_shift_pct": "TFP shift (pp)",
        "ls_shift_pp": "Labour-share shift (pp)",
    })
    value_columns = ["K gap (%)", "TFP shift (pp)", "Labour-share shift (pp)"]
    table = table[["Country", "ISO3", *value_columns]]
    table[value_columns] = table[value_columns].round(2)
    median = {"Country": "Median", "ISO3": ""}
    median.update({
        column: round(float(table[column].median()), 2)
        for column in value_columns
    })
    return pd.concat([table, pd.DataFrame([median])], ignore_index=True)


def make_fig_k_divergence(kdf: pd.DataFrame, lang: str = "en"):
    """K-level divergence over time for 6 representative countries."""
    highlight = ["JPN", "USA", "DEU", "KOR", "GBR", "SWE"]
    labels = {
        "en": {
            "title": "Capital stock: observable-tempo PIM vs standard PIM",
            "ylabel": "$K_{obs}/K_{M0} - 1$ (%)",
            "xlabel": "Year",
        },
        "ja": {
            "title": "\u8cc7\u672c\u30b9\u30c8\u30c3\u30af: \u89b3\u6e2c\u30c6\u30f3\u30ddPIM vs \u6a19\u6e96PIM",
            "ylabel": "$K_{obs}/K_{M0} - 1$ (%)",
            "xlabel": "\u5e74",
        },
    }[lang]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True)
    for ax, iso in zip(axes.flat, highlight):
        cdf = kdf[kdf["iso3"] == iso].sort_values("year")
        if cdf.empty:
            ax.set_visible(False)
            continue
        ax.plot(cdf["year"], cdf["K_pct_diff"], "-", color="#4c72b0", lw=1.5)
        ax.axhline(0, color="gray", ls="--", lw=0.8)
        ax.fill_between(cdf["year"], 0, cdf["K_pct_diff"],
                        alpha=0.15, color="#4c72b0")
        cname = cdf["country"].iloc[0] if "country" in cdf.columns else iso
        ax.set_title(cname, fontsize=11)
        ax.set_ylabel(labels["ylabel"], fontsize=8)
        ax.grid(alpha=0.3)
    for ax in axes[-1]:
        ax.set_xlabel(labels["xlabel"])
    fig.suptitle(labels["title"], y=0.99, fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    out = os.path.join(FIG, f"fig10_k_divergence_{lang}.png")
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print("wrote", out)


def make_fig_tfp_consequence(kdf: pd.DataFrame, lang: str = "en"):
    """Scatter: K-level change vs TFP shift (2010-2019 means by country)."""
    recent = kdf[(kdf["year"] >= 2010) & (kdf["year"] <= 2019)]
    by_c = recent.groupby("iso3").agg({
        "K_pct_diff": "mean",
        "TFP_shift_pct": "mean",
    }).reset_index()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(by_c["K_pct_diff"], by_c["TFP_shift_pct"],
               s=50, c="#4c72b0", alpha=0.7, edgecolors="white", lw=0.5)
    for _, row in by_c.iterrows():
        ax.annotate(row["iso3"], (row["K_pct_diff"], row["TFP_shift_pct"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points")

    x = by_c["K_pct_diff"].values
    y = by_c["TFP_shift_pct"].values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 5:
        slope, intercept = np.polyfit(x[mask], y[mask], 1)
        xr = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(xr, slope * xr + intercept, "--", color="#c44e52", lw=1.5,
                label=f"slope = {slope:.2f}")
        ax.legend(fontsize=9)

    ax.axhline(0, color="gray", ls=":", lw=0.8)
    ax.axvline(0, color="gray", ls=":", lw=0.8)
    labels = {
        "en": {
            "xlabel": "$\\Delta K$ = ($K_{obs}/K_{M0}$ \u2212 1) \u00d7 100  [%]",
            "ylabel": "$\\Delta$ TFP (M0 \u2212 obs)  [percentage points]",
            "title": "Measurement consequence: capital-level change \u2192 TFP shift\n"
                     "(country means, 2010\u20132019)",
        },
        "ja": {
            "xlabel": "$\\Delta K$ = ($K_{obs}/K_{M0}$ \u2212 1) \u00d7 100  [%]",
            "ylabel": "$\\Delta$ TFP (M0 \u2212 obs)  [\u30d1\u30fc\u30bb\u30f3\u30c6\u30fc\u30b8\u30fb\u30dd\u30a4\u30f3\u30c8]",
            "title": "\u8a08\u6e2c\u5e30\u7d50: \u8cc7\u672c\u6c34\u6e96\u5909\u5316 \u2192 TFP\u30b7\u30d5\u30c8\n"
                     "(\u56fd\u5225\u5e73\u5747\u30012010\u20132019)",
        },
    }[lang]
    ax.set_xlabel(labels["xlabel"])
    ax.set_ylabel(labels["ylabel"])
    ax.set_title(labels["title"])
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, f"fig11_tfp_consequence_{lang}.png")
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print("wrote", out)


def make_fig_labor_share(kdf: pd.DataFrame, lang: str = "en"):
    """Implied labor-share correction by country (bar chart)."""
    recent = kdf[(kdf["year"] >= 2010) & (kdf["year"] <= 2019)]
    by_c = recent.groupby("iso3").agg({
        "ls_shift_pp": "mean",
    }).reset_index().sort_values("ls_shift_pp")

    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#c44e52" if v < 0 else "#55a868" for v in by_c["ls_shift_pp"]]
    ax.bar(range(len(by_c)), by_c["ls_shift_pp"], color=colors, alpha=0.7)
    ax.set_xticks(range(len(by_c)))
    ax.set_xticklabels(by_c["iso3"], fontsize=7, rotation=45, ha="right")
    ax.axhline(0, color="black", lw=0.8)
    labels = {
        "en": {
            "ylabel": "Implied labor-share shift (pp)",
            "title": "Implied labor-share correction from tempo-adjusted capital\n"
                     "(country means, 2010\u20132019)",
        },
        "ja": {
            "ylabel": "\u542b\u610f\u52b4\u50cd\u5206\u914d\u7387\u30b7\u30d5\u30c8 (pp)",
            "title": "\u30c6\u30f3\u30dd\u8abf\u6574\u8cc7\u672c\u304b\u3089\u306e\u52b4\u50cd\u5206\u914d\u7387\u88dc\u6b63\n"
                     "(\u56fd\u5225\u5e73\u5747\u30012010\u20132019)",
        },
    }[lang]
    ax.set_ylabel(labels["ylabel"])
    ax.set_title(labels["title"])
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(FIG, f"fig12_labor_share_{lang}.png")
    plt.savefig(out, dpi=180, bbox_inches="tight")
    plt.close()
    print("wrote", out)


def main():
    print("Loading pre-computed data...", flush=True)
    solow = pd.read_csv(os.path.join(DATA, "full_solow.csv"))
    print(f"  full_solow.csv: {len(solow)} rows, "
          f"{solow['iso3'].nunique()} countries", flush=True)

    print("\n--- K-level gap analysis ---", flush=True)
    kdf = compute_k_gap_from_tfp(solow)
    kdf.to_csv(os.path.join(DATA, "k_level_diff.csv"), index=False)
    print(f"  {len(kdf)} rows written to k_level_diff.csv", flush=True)

    print("\n--- Summary ---", flush=True)
    summary = summarise_k_levels(kdf)
    with open(os.path.join(DATA, "k_level_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

    print("\n--- Table 5 ---", flush=True)
    table5 = make_table_k_level(kdf)
    table5_path = os.path.join(TAB, "table5_k_level.csv")
    table5.to_csv(table5_path, index=False)
    print(f"  {len(table5)} rows written to {table5_path}", flush=True)

    print("\n--- Figures ---", flush=True)
    for lang in ("en", "ja"):
        make_fig_k_divergence(kdf, lang)
        make_fig_tfp_consequence(kdf, lang)
        make_fig_labor_share(kdf, lang)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
