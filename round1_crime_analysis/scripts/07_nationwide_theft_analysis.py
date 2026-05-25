"""
07_nationwide_theft_analysis.py
Nationwide municipality-level theft analysis using Tsukuba Social Engineering
Commons "全国の町丁別、手口別窃盗犯認知件数データベース" (2018-2023).

Data: 雨宮護氏, 筑波大学社会工学コモンズ データバンク
  - 7 theft types at town-block level, geocoded, all 47 prefectures
  - Types: ひったくり, 車上ねらい, 部品ねらい, 自販機ねらい,
           自動車盗, オートバイ盗, 自転車盗

Design:
  Panel: municipality × year (2018-2023)
  Treatment: municipality contains at least one Round1 store
  DiD: theft_count ~ post_r1 + C(municipality) + C(year), clustered by municipality
"""

import os
import json
import csv
import io
import zipfile
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
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


# CSV file mapping: data_year -> (zip_file, csv_path_in_zip)
CSV_MAP = {
    2023: ("DB2024-01.zip", "Theft2023_geocoded_J.csv"),
    2022: ("DB2023-01.zip", "Theft2022_geocoded_J.csv"),
    2021: ("DB2022-01.zip", "DB2022-01/Theft2021_geocoded_J.csv"),
    2020: ("DB2021-01.zip", "DB2021-01/Theft2020_geocoded_J.csv"),
    2019: ("DB2020-1.zip", "DB2020-1/Theft2019_geocoded_J.csv"),
    2018: ("DB2019-1.zip", "DB2019-1/Theft2018_geocoded_J.csv"),
}

THEFT_TYPES_EN = {
    "ひったくり": "Purse Snatching",
    "車上ねらい": "Car Break-in",
    "部品ねらい": "Parts Theft",
    "自動販売機ねらい": "Vending Machine",
    "自動車盗": "Car Theft",
    "オートバイ盗": "Motorcycle Theft",
    "自転車盗": "Bicycle Theft",
}


def load_year(year):
    """Load one year's theft CSV from zip, return DataFrame."""
    zipf, csv_path = CSV_MAP[year]
    zip_path = os.path.join(NPA_DIR, zipf)
    if not os.path.exists(zip_path):
        print(f"  [SKIP] {zip_path} not found")
        return None

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(csv_path) as f:
            data = f.read().decode("cp932", errors="replace")

    reader = csv.reader(io.StringIO(data))
    header = next(reader)
    rows = list(reader)
    print(f"  {year}: {len(rows):,} records")
    return rows


def build_panel(stores):
    """Build municipality × year panel from all theft CSVs."""
    # Map stores to (prefecture, city) -> first opening year
    r1_munis = {}
    for s in stores:
        pref = s["prefecture"]
        city = s["city"]
        key = f"{pref}_{city}"
        yr = s.get("open_year", 9999)
        if key not in r1_munis or yr < r1_munis[key]:
            r1_munis[key] = yr

    print(f"R1 municipalities: {len(r1_munis)}")

    # Load all years and aggregate by municipality
    all_rows = []
    for year in sorted(CSV_MAP.keys()):
        rows = load_year(year)
        if not rows:
            continue

        # Aggregate: (prefecture, city) -> {theft_type: count, total: count}
        muni_counts = {}
        for row in rows:
            if len(row) < 8:
                continue
            pref = row[6].strip()
            city = row[7].strip()
            modus = row[2].strip()
            if not pref or not city:
                continue

            key = f"{pref}_{city}"
            if key not in muni_counts:
                muni_counts[key] = {
                    "prefecture": pref,
                    "city": city,
                    "total": 0,
                }
                for jt in THEFT_TYPES_EN:
                    muni_counts[key][jt] = 0

            muni_counts[key]["total"] += 1
            if modus in muni_counts[key]:
                muni_counts[key][modus] += 1

        # Build panel rows
        for key, counts in muni_counts.items():
            first_r1 = r1_munis.get(key, np.nan)
            has_r1 = 1 if key in r1_munis else 0
            post_r1 = 1 if has_r1 and not np.isnan(first_r1) and year >= first_r1 else 0

            row_dict = {
                "year": year,
                "prefecture": counts["prefecture"],
                "city": counts["city"],
                "municipality": key,
                "total_theft": counts["total"],
                "has_r1": has_r1,
                "first_r1_year": first_r1,
                "post_r1": post_r1,
            }
            for jt, en in THEFT_TYPES_EN.items():
                col = en.lower().replace(" ", "_").replace("-", "_")
                row_dict[col] = counts.get(jt, 0)

            all_rows.append(row_dict)

    df = pd.DataFrame(all_rows)
    print(f"\nPanel: {len(df)} obs, {df['municipality'].nunique()} municipalities, "
          f"{df['year'].nunique()} years")
    print(f"R1 municipalities in panel: {df[df['has_r1']==1]['municipality'].nunique()}")
    print(f"Control municipalities: {df[df['has_r1']==0]['municipality'].nunique()}")
    return df, r1_munis


def run_did(df):
    """Run differential trend analysis for all theft categories.

    All R1 stores opened before 2018, so classical DiD with pre/post is
    not possible. Instead we test whether R1 municipalities show
    different theft TRENDS via has_r1 × year interaction, controlling
    for municipality and year fixed effects.
    """
    print(f"\n{'='*60}")
    print("NATIONWIDE DIFFERENTIAL TREND ANALYSIS — THEFT")
    print(f"{'='*60}")
    print("(All R1 stores opened pre-2018; testing R1 × trend interaction)")

    categories = [
        ("Total Theft", "total_theft"),
        ("Purse Snatching", "purse_snatching"),
        ("Car Break-in", "car_break_in"),
        ("Parts Theft", "parts_theft"),
        ("Car Theft", "car_theft"),
        ("Motorcycle Theft", "motorcycle_theft"),
        ("Bicycle Theft", "bicycle_theft"),
    ]

    results = {}
    for title, col in categories:
        if col not in df.columns:
            print(f"\n  {title}: column '{col}' not found, skipping")
            continue
        reg_data = df[["municipality", "year", col, "has_r1"]].dropna().copy()
        reg_data = reg_data.rename(columns={col: "crime"})
        reg_data["trend"] = reg_data["year"] - reg_data["year"].min()
        reg_data["r1_trend"] = reg_data["has_r1"] * reg_data["trend"]

        if reg_data["crime"].sum() == 0:
            print(f"\n  {title}: no data")
            continue

        try:
            model = smf.ols(
                "crime ~ r1_trend + C(municipality) + C(year)", data=reg_data
            ).fit(cov_type="cluster", cov_kwds={"groups": reg_data["municipality"]})
            coef = model.params["r1_trend"]
            se = model.bse["r1_trend"]
            pval = model.pvalues["r1_trend"]
            ci_lo, ci_hi = model.conf_int().loc["r1_trend"]
            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

            results[title] = {
                "coefficient": float(round(coef, 2)),
                "std_error": float(round(se, 2)),
                "p_value": float(round(pval, 4)),
                "ci_95": [float(round(ci_lo, 2)), float(round(ci_hi, 2))],
                "significant": bool(pval < 0.05),
                "n_obs": int(len(reg_data)),
                "interpretation": "negative = R1 municipalities show steeper decline",
            }
            print(f"\n  {title}:")
            print(f"    R1×trend:  {coef:+.2f} {sig}")
            print(f"    SE:        {se:.2f}")
            print(f"    p-value:   {pval:.4f}")
            print(f"    95% CI:    [{ci_lo:.2f}, {ci_hi:.2f}]")
        except Exception as e:
            print(f"\n  {title}: failed — {e}")
            results[title] = {"error": str(e)}

    with open(os.path.join(OUTPUT_DIR, "nationwide_theft_did.json"), "w") as f:
        json.dump(results, f, indent=2)
    return results


def run_neighbor_did(df, stores):
    """Trend analysis using only R1 prefectures (same-prefecture controls)."""
    print(f"\n{'='*60}")
    print("SAME-PREFECTURE NEIGHBOR TREND ANALYSIS — THEFT")
    print(f"{'='*60}")

    r1_prefs = set()
    for s in stores:
        r1_prefs.add(s["prefecture"])

    sub = df[df["prefecture"].isin(r1_prefs)].copy()
    print(f"  Prefectures with R1: {len(r1_prefs)}")
    print(f"  R1 municipalities: {sub[sub['has_r1']==1]['municipality'].nunique()}")
    print(f"  Same-pref controls: {sub[sub['has_r1']==0]['municipality'].nunique()}")
    print(f"  Observations: {len(sub)}")

    sub["trend"] = sub["year"] - sub["year"].min()
    sub["r1_trend"] = sub["has_r1"] * sub["trend"]

    results = {}
    for title, col in [
        ("Total Theft", "total_theft"),
        ("Car Break-in", "car_break_in"),
        ("Bicycle Theft", "bicycle_theft"),
        ("Purse Snatching", "purse_snatching"),
    ]:
        if col not in sub.columns:
            continue
        reg_data = sub[["municipality", "year", col, "r1_trend"]].dropna()
        reg_data = reg_data.rename(columns={col: "crime"})
        try:
            model = smf.ols(
                "crime ~ r1_trend + C(municipality) + C(year)", data=reg_data
            ).fit(cov_type="cluster", cov_kwds={"groups": reg_data["municipality"]})
            coef = model.params["r1_trend"]
            pval = model.pvalues["r1_trend"]
            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
            results[title] = {
                "coefficient": float(round(coef, 2)),
                "p_value": float(round(pval, 4)),
            }
            print(f"  {title}: R1×trend={coef:+.2f} {sig} (p={pval:.4f})")
        except Exception as e:
            print(f"  {title}: failed — {e}")

    with open(os.path.join(OUTPUT_DIR, "nationwide_neighbor_theft_did.json"), "w") as f:
        json.dump(results, f, indent=2)
    return results


def plot_trends(df):
    """Plot R1 vs non-R1 municipality theft trends."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for idx, (title, col) in enumerate([
        ("Total Theft", "total_theft"),
        ("Bicycle Theft", "bicycle_theft"),
    ]):
        ax = axes[idx]
        for grp, color, label in [
            (1, C_R1, f"R1 municipalities (n={df[df['has_r1']==1]['municipality'].nunique()})"),
            (0, C_CTRL, f"Non-R1 (n={df[df['has_r1']==0]['municipality'].nunique()})"),
        ]:
            g = df[df["has_r1"] == grp].groupby("year")[col].mean()
            ax.plot(g.index, g.values, color=color, lw=2,
                    marker="o", markersize=5, label=label)
        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel(f"Mean {title} per Municipality", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    plt.suptitle("Japan Nationwide: R1 vs Non-R1 Municipality Theft Trends (2018-2023)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp12_nationwide_theft_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP12] Nationwide theft trends saved.")


def plot_forest(results):
    """Forest plot of DiD coefficients for all theft categories."""
    categories = [k for k in results if "error" not in results[k]]
    if not categories:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = list(range(len(categories)))

    for i, cat in enumerate(reversed(categories)):
        r = results[cat]
        coef = r["coefficient"]
        ci = r["ci_95"]
        sig = r["significant"]
        color = C_R1 if sig else "#888888"
        ax.errorbar(coef, i, xerr=[[coef - ci[0]], [ci[1] - coef]],
                    fmt="o", color=color, capsize=4, markersize=8, lw=2)

    ax.axvline(x=0, color="gray", ls="--", alpha=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(reversed(categories)), fontsize=10)
    ax.set_xlabel("R1 x Trend Coefficient (per year)", fontsize=11)
    ax.set_title("Nationwide: Round1 Differential Theft Trends (2018-2023)",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp13_nationwide_theft_forest.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP13] Nationwide theft forest plot saved.")


def plot_by_prefecture(df):
    """Plot per-prefecture R1 effect (difference in mean theft)."""
    prefs_with_r1 = df[df["has_r1"] == 1]["prefecture"].unique()

    pref_effects = []
    for pref in prefs_with_r1:
        pref_data = df[df["prefecture"] == pref]
        r1_mean = pref_data[pref_data["has_r1"] == 1]["total_theft"].mean()
        ctrl_mean = pref_data[pref_data["has_r1"] == 0]["total_theft"].mean()
        n_r1 = pref_data[pref_data["has_r1"] == 1]["municipality"].nunique()
        n_ctrl = pref_data[pref_data["has_r1"] == 0]["municipality"].nunique()
        if n_ctrl > 0:
            pref_effects.append({
                "prefecture": pref,
                "r1_mean": r1_mean,
                "ctrl_mean": ctrl_mean,
                "diff": r1_mean - ctrl_mean,
                "n_r1": n_r1,
                "n_ctrl": n_ctrl,
            })

    pref_effects.sort(key=lambda x: x["diff"])

    fig, ax = plt.subplots(figsize=(10, max(6, len(pref_effects) * 0.35)))
    y_pos = list(range(len(pref_effects)))
    colors = [C_R1 if e["diff"] < 0 else C_CTRL for e in pref_effects]
    ax.barh(y_pos, [e["diff"] for e in pref_effects], color=colors, alpha=0.7)
    ax.set_yticks(y_pos)
    PREF_ROMAJI = {
        "北海道": "Hokkaido", "青森県": "Aomori", "岩手県": "Iwate",
        "秋田県": "Akita", "宮城県": "Miyagi", "福島県": "Fukushima",
        "東京都": "Tokyo", "神奈川県": "Kanagawa", "千葉県": "Chiba",
        "埼玉県": "Saitama", "栃木県": "Tochigi", "群馬県": "Gunma",
        "茨城県": "Ibaraki", "新潟県": "Niigata", "長野県": "Nagano",
        "石川県": "Ishikawa", "静岡県": "Shizuoka", "愛知県": "Aichi",
        "三重県": "Mie", "岐阜県": "Gifu", "大阪府": "Osaka",
        "京都府": "Kyoto", "兵庫県": "Hyogo", "和歌山県": "Wakayama",
        "岡山県": "Okayama", "広島県": "Hiroshima", "香川県": "Kagawa",
        "愛媛県": "Ehime", "高知県": "Kochi", "徳島県": "Tokushima",
        "福岡県": "Fukuoka", "佐賀県": "Saga", "熊本県": "Kumamoto",
        "大分県": "Oita", "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima",
        "沖縄県": "Okinawa",
    }
    ax.set_yticklabels([PREF_ROMAJI.get(e["prefecture"], e["prefecture"]) for e in pref_effects], fontsize=8)
    ax.axvline(x=0, color="gray", ls="--")
    ax.set_xlabel("R1 - Control Mean Theft Count", fontsize=11)
    ax.set_title("Per-Prefecture: R1 vs Non-R1 Municipality Mean Theft",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig_jp14_prefecture_theft_diff.png"), dpi=200)
    plt.close(fig)
    print("[Fig JP14] Prefecture theft difference saved.")


def main():
    print("=" * 60)
    print("NATIONWIDE MUNICIPALITY-LEVEL THEFT ANALYSIS")
    print("=" * 60)

    with open(os.path.join(DATA_DIR, "round1_japan_stores.json")) as f:
        stores = json.load(f)

    print(f"\nLoading theft data from {len(CSV_MAP)} years...")
    df, r1_munis = build_panel(stores)

    # Summary stats
    print(f"\nYearly totals:")
    for y in sorted(df["year"].unique()):
        yr_data = df[df["year"] == y]
        print(f"  {y}: {yr_data['total_theft'].sum():,} thefts across "
              f"{yr_data['municipality'].nunique()} municipalities")

    # Run DiD
    did_results = run_did(df)
    neighbor_results = run_neighbor_did(df, stores)

    # Figures
    plot_trends(df)
    plot_forest(did_results)
    plot_by_prefecture(df)

    # Save panel
    df.to_csv(os.path.join(OUTPUT_DIR, "nationwide_theft_panel.csv"),
              index=False, encoding="utf-8")

    print(f"\n{'='*60}")
    print("NATIONWIDE THEFT ANALYSIS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
