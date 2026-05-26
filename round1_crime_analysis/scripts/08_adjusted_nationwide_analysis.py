"""
08_adjusted_nationwide_analysis.py
Confounding-adjusted nationwide theft analysis.

Covariates (SSDSE-A 2024, Census 2020):
  - Population (per-capita standardization)
  - Age composition (under-15, working-age, elderly ratios)
  - Population density (per habitable km²)
  - Per-capita local tax revenue (income proxy)
  - Unemployment rate
  - Foreign population ratio
  - Single-person household ratio
  - Net migration rate (residential instability)

Design:
  Panel: city × year (2018-2023), wards aggregated to parent city
  Model: theft_rate ~ r1_trend + covariates + C(city) + C(year), clustered SE
  Graphs: per-capita rates, 2018=100 index, standardized coefficients
"""

import os
import json
import csv
import io
import re
import zipfile
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
NPA_DIR = os.path.join(DATA_DIR, "npa_nationwide")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

C_R1 = "#E63946"
C_CTRL = "#457B9D"
C_ADJ = "#2A9D8F"

CSV_MAP = {
    2023: ("DB2024-01.zip", "Theft2023_geocoded_J.csv"),
    2022: ("DB2023-01.zip", "Theft2022_geocoded_J.csv"),
    2021: ("DB2022-01.zip", "DB2022-01/Theft2021_geocoded_J.csv"),
    2020: ("DB2021-01.zip", "DB2021-01/Theft2020_geocoded_J.csv"),
    2019: ("DB2020-1.zip", "DB2020-1/Theft2019_geocoded_J.csv"),
    2018: ("DB2019-1.zip", "DB2019-1/Theft2018_geocoded_J.csv"),
}

THEFT_TYPES_EN = {
    "ひったくり": "purse_snatching",
    "車上ねらい": "car_break_in",
    "部品ねらい": "parts_theft",
    "自動販売機ねらい": "vending_machine",
    "自動車盗": "car_theft",
    "オートバイ盗": "motorcycle_theft",
    "自転車盗": "bicycle_theft",
}

THEFT_LABELS = {
    "total_theft": "Total Theft",
    "purse_snatching": "Purse Snatching",
    "car_break_in": "Car Break-in",
    "parts_theft": "Parts Theft",
    "car_theft": "Car Theft",
    "motorcycle_theft": "Motorcycle Theft",
    "bicycle_theft": "Bicycle Theft",
}

# Designated cities whose wards need aggregation to city level
DESIGNATED_CITIES = [
    "札幌市", "仙台市", "さいたま市", "千葉市", "横浜市", "川崎市",
    "相模原市", "新潟市", "静岡市", "浜松市", "名古屋市", "京都市",
    "大阪市", "堺市", "神戸市", "岡山市", "広島市", "北九州市",
    "福岡市", "熊本市",
]


def ward_to_city(pref, city):
    """Map ward-level municipality to parent designated city if applicable."""
    for dc in DESIGNATED_CITIES:
        if city.startswith(dc) and city != dc:
            return dc
    return city


def load_ssdse():
    """Load SSDSE-A census data into a dict keyed by (pref, city)."""
    path = os.path.join(DATA_DIR, "SSDSE-A-2024.csv")
    with open(path, "rb") as f:
        data = f.read().decode("cp932")
    lines = data.split("\n")
    reader = csv.reader(io.StringIO("\n".join(lines[3:])))

    covariates = {}
    for row in reader:
        if len(row) < 128:
            continue
        pref = row[1].strip()
        city = row[2].strip()
        if not pref or not city:
            continue

        def safe_float(idx):
            try:
                v = row[idx].strip().replace(",", "")
                return float(v) if v else np.nan
            except (IndexError, ValueError):
                return np.nan

        pop = safe_float(3)
        if np.isnan(pop) or pop <= 0:
            continue

        under15 = safe_float(9)
        working_age = safe_float(12)
        elderly = safe_float(15)
        foreign_pop = safe_float(21)
        transfer_in = safe_float(24)
        transfer_out = safe_float(25)
        households = safe_float(27)
        single_hh = safe_float(30)
        area = safe_float(36)
        hab_area = safe_float(37)
        local_tax = safe_float(82)
        employed = safe_float(102)
        unemployed = safe_float(105)

        labor_force = (0 if np.isnan(employed) else employed) + (0 if np.isnan(unemployed) else unemployed)

        key = f"{pref}_{city}"
        covariates[key] = {
            "population": pop,
            "under15_ratio": under15 / pop if not np.isnan(under15) else np.nan,
            "working_age_ratio": working_age / pop if not np.isnan(working_age) else np.nan,
            "elderly_ratio": elderly / pop if not np.isnan(elderly) else np.nan,
            "pop_density": pop / hab_area if not np.isnan(hab_area) and hab_area > 0 else np.nan,
            "per_capita_tax": (local_tax * 1000) / pop if not np.isnan(local_tax) else np.nan,
            "unemployment_rate": unemployed / labor_force if labor_force > 0 else np.nan,
            "foreign_ratio": foreign_pop / pop if not np.isnan(foreign_pop) else np.nan,
            "single_hh_ratio": single_hh / households if not np.isnan(households) and households > 0 else np.nan,
            "net_migration_rate": (transfer_in - transfer_out) / pop if not np.isnan(transfer_in) and not np.isnan(transfer_out) else np.nan,
        }

    print(f"SSDSE covariates loaded: {len(covariates)} municipalities")
    return covariates


def load_year(year):
    """Load one year's theft CSV from zip."""
    zipf, csv_path = CSV_MAP[year]
    zip_path = os.path.join(NPA_DIR, zipf)
    if not os.path.exists(zip_path):
        print(f"  [SKIP] {zip_path} not found")
        return None
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(csv_path) as f:
            data = f.read().decode("cp932", errors="replace")
    reader = csv.reader(io.StringIO(data))
    next(reader)
    rows = list(reader)
    print(f"  {year}: {len(rows):,} records")
    return rows


def build_panel(stores, covariates):
    """Build city × year panel with covariates, aggregating wards."""
    # R1 store mapping: (pref, city) -> first opening year, with ward aggregation
    r1_cities = {}
    for s in stores:
        pref = s["prefecture"]
        city = ward_to_city(pref, s["city"])
        key = f"{pref}_{city}"
        yr = s.get("open_year", 9999)
        if key not in r1_cities or yr < r1_cities[key]:
            r1_cities[key] = yr

    print(f"R1 cities (after ward aggregation): {len(r1_cities)}")

    all_rows = []
    for year in sorted(CSV_MAP.keys()):
        rows = load_year(year)
        if not rows:
            continue

        city_counts = {}
        for row in rows:
            if len(row) < 8:
                continue
            pref = row[6].strip()
            raw_city = row[7].strip()
            modus = row[2].strip()
            if not pref or not raw_city:
                continue

            city = ward_to_city(pref, raw_city)
            key = f"{pref}_{city}"

            if key not in city_counts:
                city_counts[key] = {
                    "prefecture": pref, "city": city, "total": 0,
                }
                for jt in THEFT_TYPES_EN.values():
                    city_counts[key][jt] = 0

            city_counts[key]["total"] += 1
            en_name = THEFT_TYPES_EN.get(modus)
            if en_name and en_name in city_counts[key]:
                city_counts[key][en_name] += 1

        for key, counts in city_counts.items():
            first_r1 = r1_cities.get(key, np.nan)
            has_r1 = 1 if key in r1_cities else 0

            cov = covariates.get(key, {})
            pop = cov.get("population", np.nan)

            row_dict = {
                "year": year,
                "prefecture": counts["prefecture"],
                "city": counts["city"],
                "municipality": key,
                "total_theft": counts["total"],
                "has_r1": has_r1,
                "first_r1_year": first_r1,
                "population": pop,
                "theft_rate": counts["total"] / pop * 100000 if pop and pop > 0 else np.nan,
            }
            for en_col in THEFT_TYPES_EN.values():
                row_dict[en_col] = counts.get(en_col, 0)
                row_dict[f"{en_col}_rate"] = (
                    counts.get(en_col, 0) / pop * 100000
                    if pop and pop > 0 else np.nan
                )

            for cov_name in [
                "under15_ratio", "working_age_ratio", "elderly_ratio",
                "pop_density", "per_capita_tax", "unemployment_rate",
                "foreign_ratio", "single_hh_ratio", "net_migration_rate",
            ]:
                row_dict[cov_name] = cov.get(cov_name, np.nan)

            all_rows.append(row_dict)

    df = pd.DataFrame(all_rows)
    df["trend"] = df["year"] - df["year"].min()
    df["r1_trend"] = df["has_r1"] * df["trend"]

    print(f"\nPanel: {len(df)} obs, {df['municipality'].nunique()} cities, "
          f"{df['year'].nunique()} years")
    r1_n = df[df["has_r1"] == 1]["municipality"].nunique()
    ctrl_n = df[df["has_r1"] == 0]["municipality"].nunique()
    print(f"R1 cities: {r1_n}, Control: {ctrl_n}")

    matched = df["population"].notna().sum()
    print(f"Population matched: {matched}/{len(df)} ({matched/len(df)*100:.1f}%)")
    return df, r1_cities


def run_models(df):
    """Run unadjusted and adjusted models for each theft category."""
    print(f"\n{'='*60}")
    print("DIFFERENTIAL TREND ANALYSIS — UNADJUSTED vs ADJUSTED")
    print(f"{'='*60}")

    cov_cols = [
        "pop_density", "under15_ratio", "elderly_ratio",
        "per_capita_tax", "unemployment_rate",
        "foreign_ratio", "single_hh_ratio", "net_migration_rate",
    ]

    categories = [
        ("Total Theft", "theft_rate"),
        ("Bicycle Theft", "bicycle_theft_rate"),
        ("Car Break-in", "car_break_in_rate"),
        ("Parts Theft", "parts_theft_rate"),
        ("Motorcycle Theft", "motorcycle_theft_rate"),
        ("Purse Snatching", "purse_snatching_rate"),
        ("Car Theft", "car_theft_rate"),
    ]

    results = {}
    for title, col in categories:
        if col not in df.columns:
            continue

        base_cols = ["municipality", "year", col, "r1_trend", "has_r1", "trend"]
        reg_base = df[base_cols].dropna().copy()
        reg_base = reg_base.rename(columns={col: "crime_rate"})

        # Unadjusted model
        try:
            m_unadj = smf.ols(
                "crime_rate ~ r1_trend + C(municipality) + C(year)", data=reg_base
            ).fit(cov_type="cluster", cov_kwds={"groups": reg_base["municipality"]})
            unadj_coef = m_unadj.params["r1_trend"]
            unadj_se = m_unadj.bse["r1_trend"]
            unadj_p = m_unadj.pvalues["r1_trend"]
            unadj_ci = m_unadj.conf_int().loc["r1_trend"].tolist()
        except Exception as e:
            print(f"  {title} unadjusted: failed — {e}")
            continue

        # Adjusted model
        adj_cols = base_cols + [c for c in cov_cols if c in df.columns]
        reg_adj = df[adj_cols].dropna().copy()
        reg_adj = reg_adj.rename(columns={col: "crime_rate"})

        # Interact time-invariant covariates with trend so they explain
        # differential crime trends across municipalities. Static levels
        # are already absorbed by C(municipality) fixed effects.
        cov_trend_terms = [f"{c}:trend" for c in cov_cols if c in reg_adj.columns]
        cov_formula = " + ".join(cov_trend_terms)
        try:
            m_adj = smf.ols(
                f"crime_rate ~ r1_trend + {cov_formula} + C(municipality) + C(year)",
                data=reg_adj,
            ).fit(cov_type="cluster", cov_kwds={"groups": reg_adj["municipality"]})
            adj_coef = m_adj.params["r1_trend"]
            adj_se = m_adj.bse["r1_trend"]
            adj_p = m_adj.pvalues["r1_trend"]
            adj_ci = m_adj.conf_int().loc["r1_trend"].tolist()
        except Exception as e:
            print(f"  {title} adjusted: failed — {e}")
            adj_coef = adj_se = adj_p = np.nan
            adj_ci = [np.nan, np.nan]

        sig_u = "***" if unadj_p < 0.001 else "**" if unadj_p < 0.01 else "*" if unadj_p < 0.05 else ""
        sig_a = "***" if adj_p < 0.001 else "**" if adj_p < 0.01 else "*" if adj_p < 0.05 else "" if not np.isnan(adj_p) else "?"

        results[title] = {
            "unadjusted": {
                "coefficient": round(float(unadj_coef), 3),
                "std_error": round(float(unadj_se), 3),
                "p_value": round(float(unadj_p), 4),
                "ci_95": [round(float(unadj_ci[0]), 3), round(float(unadj_ci[1]), 3)],
                "n_obs": int(len(reg_base)),
            },
            "adjusted": {
                "coefficient": round(float(adj_coef), 3) if not np.isnan(adj_coef) else None,
                "std_error": round(float(adj_se), 3) if not np.isnan(adj_se) else None,
                "p_value": round(float(adj_p), 4) if not np.isnan(adj_p) else None,
                "ci_95": [round(float(adj_ci[0]), 3), round(float(adj_ci[1]), 3)] if not np.isnan(adj_ci[0]) else None,
                "n_obs": int(len(reg_adj)),
                "covariates": cov_cols,
            },
        }

        print(f"\n  {title}:")
        print(f"    Unadjusted: R1×trend = {unadj_coef:+.3f} {sig_u}  (p={unadj_p:.4f})")
        print(f"    Adjusted:   R1×trend = {adj_coef:+.3f} {sig_a}  (p={adj_p:.4f})")
        pct_change = ((adj_coef - unadj_coef) / abs(unadj_coef) * 100) if unadj_coef != 0 and not np.isnan(adj_coef) else 0
        print(f"    Change:     {pct_change:+.1f}%")

    with open(os.path.join(OUTPUT_DIR, "adjusted_theft_did.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    return results


def plot_per_capita_trends(df):
    """Per-capita theft rate trends: R1 vs non-R1."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    rate_cols = [
        ("Total Theft Rate", "theft_rate"),
        ("Bicycle Theft Rate", "bicycle_theft_rate"),
    ]

    for idx, (title, col) in enumerate(rate_cols):
        ax = axes[idx]
        for grp, color, label in [
            (1, C_R1, f"R1 cities (n={df[df['has_r1']==1]['municipality'].nunique()})"),
            (0, C_CTRL, f"Non-R1 (n={df[df['has_r1']==0]['municipality'].nunique()})"),
        ]:
            g = df[df["has_r1"] == grp].groupby("year")[col].mean()
            ax.plot(g.index, g.values, color=color, lw=2.5,
                    marker="o", markersize=6, label=label)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel("Rate per 100k Population", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    plt.suptitle("Per-Capita Theft Rates: R1 vs Non-R1 Municipalities (2018-2023)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp15_percapita_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP15] Per-capita trends saved.")


def plot_indexed_trends(df):
    """Index=100 (2018 base) theft trends for R1 vs non-R1."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    rate_cols = [
        ("Total Theft", "theft_rate"),
        ("Bicycle Theft", "bicycle_theft_rate"),
        ("Car Break-in", "car_break_in_rate"),
        ("Motorcycle Theft", "motorcycle_theft_rate"),
    ]

    for idx, (title, col) in enumerate(rate_cols):
        ax = axes[idx // 2][idx % 2]
        for grp, color, label in [
            (1, C_R1, "R1 cities"),
            (0, C_CTRL, "Non-R1"),
        ]:
            g = df[df["has_r1"] == grp].groupby("year")[col].mean()
            base = g.iloc[0] if len(g) > 0 and g.iloc[0] > 0 else 1
            indexed = g / base * 100
            ax.plot(indexed.index, indexed.values, color=color, lw=2.5,
                    marker="o", markersize=5, label=label)
        ax.axhline(y=100, color="gray", ls="--", alpha=0.4)
        ax.set_xlabel("Year", fontsize=10)
        ax.set_ylabel("Index (2018 = 100)", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)

    plt.suptitle("Indexed Theft Rate Trends (2018 = 100): R1 vs Non-R1",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp16_indexed_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP16] Indexed trends saved.")


def plot_comparison_forest(results):
    """Side-by-side forest plot: unadjusted vs adjusted coefficients."""
    categories = [k for k in results if results[k]["adjusted"]["coefficient"] is not None]
    if not categories:
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    y_pos = np.arange(len(categories))
    offset = 0.15

    for i, cat in enumerate(reversed(categories)):
        # Unadjusted
        u = results[cat]["unadjusted"]
        coef_u = u["coefficient"]
        ci_u = u["ci_95"]
        ax.errorbar(coef_u, i + offset, xerr=[[coef_u - ci_u[0]], [ci_u[1] - coef_u]],
                    fmt="s", color=C_CTRL, capsize=4, markersize=7, lw=1.5,
                    label="Unadjusted" if i == 0 else "")

        # Adjusted
        a = results[cat]["adjusted"]
        coef_a = a["coefficient"]
        ci_a = a["ci_95"]
        sig_color = C_R1 if a["p_value"] and a["p_value"] < 0.05 else "#888888"
        ax.errorbar(coef_a, i - offset, xerr=[[coef_a - ci_a[0]], [ci_a[1] - coef_a]],
                    fmt="o", color=sig_color, capsize=4, markersize=8, lw=2,
                    label="Adjusted" if i == 0 else "")

    ax.axvline(x=0, color="gray", ls="--", alpha=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(reversed(categories)), fontsize=10)
    ax.set_xlabel("R1 × Trend Coefficient (per 100k pop, per year)", fontsize=11)
    ax.set_title("Unadjusted vs Adjusted: Round1 Differential Theft Trends\n"
                 "(Adjusted for: density, age, tax, unemployment, foreign pop, "
                 "single HH, migration)",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=10, loc="lower left")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp17_adjusted_forest.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP17] Adjusted forest plot saved.")


def plot_covariate_balance(df):
    """Show covariate distributions for R1 vs non-R1 municipalities."""
    cov_labels = {
        "pop_density": "Pop Density\n(per hab. km²)",
        "elderly_ratio": "Elderly Ratio\n(65+)",
        "per_capita_tax": "Per-Capita Tax\n(¥1000)",
        "unemployment_rate": "Unemployment\nRate",
        "single_hh_ratio": "Single HH\nRatio",
        "foreign_ratio": "Foreign Pop\nRatio",
    }

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    # Use 2020 data for cleaner comparison
    snap = df[df["year"] == 2020].copy() if 2020 in df["year"].values else df[df["year"] == df["year"].min()].copy()

    for idx, (col, label) in enumerate(cov_labels.items()):
        ax = axes[idx]
        r1_vals = snap[snap["has_r1"] == 1][col].dropna()
        ctrl_vals = snap[snap["has_r1"] == 0][col].dropna()

        if len(r1_vals) > 0 and len(ctrl_vals) > 0:
            bp = ax.boxplot([ctrl_vals, r1_vals], tick_labels=["Non-R1", "R1"],
                           widths=0.5, patch_artist=True)
            bp["boxes"][0].set_facecolor(C_CTRL)
            bp["boxes"][0].set_alpha(0.6)
            bp["boxes"][1].set_facecolor(C_R1)
            bp["boxes"][1].set_alpha(0.6)

        ax.set_title(label, fontsize=9, fontweight="bold")

    plt.suptitle("Covariate Balance: R1 vs Non-R1 Municipalities",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp18_covariate_balance.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP18] Covariate balance saved.")


def main():
    print("=" * 60)
    print("CONFOUNDING-ADJUSTED NATIONWIDE THEFT ANALYSIS")
    print("=" * 60)

    with open(os.path.join(DATA_DIR, "round1_japan_stores.json")) as f:
        stores = json.load(f)

    covariates = load_ssdse()

    print(f"\nLoading theft data...")
    df, r1_cities = build_panel(stores, covariates)

    # Summary stats
    print(f"\nYearly per-capita theft rates (mean):")
    for y in sorted(df["year"].unique()):
        yr = df[df["year"] == y]
        r1_rate = yr[yr["has_r1"] == 1]["theft_rate"].mean()
        ctrl_rate = yr[yr["has_r1"] == 0]["theft_rate"].mean()
        print(f"  {y}: R1={r1_rate:,.0f}  Non-R1={ctrl_rate:,.0f}  per 100k")

    # Run models
    results = run_models(df)

    # Figures
    plot_per_capita_trends(df)
    plot_indexed_trends(df)
    plot_comparison_forest(results)
    plot_covariate_balance(df)

    # Save panel
    df.to_csv(os.path.join(OUTPUT_DIR, "adjusted_theft_panel.csv"),
              index=False, encoding="utf-8")

    print(f"\n{'='*60}")
    print("ADJUSTED ANALYSIS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
