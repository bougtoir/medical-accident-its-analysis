"""
09_us_county_analysis.py
US County-level crime analysis: Round1 counties vs control counties.

Data: FBI UCR Table 10 (county-level offenses known), 2014-2019.
Panel: county × year with R1 treatment indicator.
Model: crime_rate ~ r1_trend + C(county) + C(year), clustered SE.
"""

import os
import json
import io
import warnings
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.formula.api as smf
import urllib.request

warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

C_R1 = "#E63946"
C_CTRL = "#457B9D"

# FBI UCR Table 10 URLs by year (state-level HTML-format XLS files)
STATE_NAMES = {
    'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas',
    'CA': 'california', 'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware',
    'FL': 'florida', 'GA': 'georgia', 'HI': 'hawaii', 'ID': 'idaho',
    'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas',
    'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland',
    'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi',
    'MO': 'missouri', 'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada',
    'NH': 'new-hampshire', 'NJ': 'new-jersey', 'NM': 'new-mexico', 'NY': 'new-york',
    'NC': 'north-carolina', 'ND': 'north-dakota', 'OH': 'ohio', 'OK': 'oklahoma',
    'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode-island', 'SC': 'south-carolina',
    'SD': 'south-dakota', 'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah',
    'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 'WV': 'west-virginia',
    'WI': 'wisconsin', 'WY': 'wyoming',
}

CRIME_COLS = {
    "Violent crime": "violent_crime",
    "Murder and nonnegligent manslaughter": "murder",
    "Robbery": "robbery",
    "Aggravated assault": "aggravated_assault",
    "Property crime": "property_crime",
    "Burglary": "burglary",
    "Larceny- theft": "larceny_theft",
    "Motor vehicle theft": "motor_vehicle_theft",
}

CRIME_LABELS = {
    "violent_crime": "Violent Crime",
    "murder": "Murder",
    "robbery": "Robbery",
    "aggravated_assault": "Aggravated Assault",
    "property_crime": "Property Crime",
    "burglary": "Burglary",
    "larceny_theft": "Larceny-Theft",
    "motor_vehicle_theft": "Motor Vehicle Theft",
}


def url_for_state_year(state_abbr, year):
    """Build FBI UCR Table 10 URL for a state/year combo."""
    name = STATE_NAMES.get(state_abbr)
    if not name:
        return None
    if year in (2017, 2018, 2019):
        return f"https://ucr.fbi.gov/crime-in-the-u.s/{year}/crime-in-the-u.s.-{year}/tables/table-10/table-10-state-cuts/{name}.xls"
    if year == 2015:
        return f"https://ucr.fbi.gov/crime-in-the-u.s/2015/crime-in-the-u.s.-2015/tables/table-10/table-10-state-pieces/table_10_offenses_known_to_law_enforcement_{name}_by_metropolitan_and_nonmetropolitan_counties_2015.xls"
    if year == 2014:
        return f"https://ucr.fbi.gov/crime-in-the-u.s/2014/crime-in-the-u.s.-2014/tables/table-10/table-10-pieces/{name}.xls"
    return None


def download_and_parse(url, state_abbr, year):
    """Download HTML-format XLS and parse county crime table."""
    cache_dir = os.path.join(DATA_DIR, "ucr_county_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{state_abbr}_{year}.html")

    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            data = f.read()
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = resp.read()
        except Exception as e:
            return None
        with open(cache_file, "wb") as f:
            f.write(data)
        time.sleep(0.5)

    try:
        dfs = pd.read_html(data.decode("utf-8", errors="replace"))
    except Exception:
        try:
            dfs = pd.read_html(cache_file)
        except Exception:
            return None

    if not dfs:
        return None

    df = dfs[0]
    if df.shape[1] < 10:
        return None

    # Normalize column names
    col_map = {}
    for orig in df.columns:
        orig_str = str(orig).strip()
        if "county" in orig_str.lower():
            col_map[orig] = "county"
        elif "metropolitan" in orig_str.lower() or "metro" in orig_str.lower():
            col_map[orig] = "metro_type"
        else:
            for pattern, en_name in CRIME_COLS.items():
                if pattern.lower() in orig_str.lower():
                    col_map[orig] = en_name
                    break

    if "county" not in col_map.values():
        return None

    df = df.rename(columns=col_map)
    df = df[df["county"].notna()].copy()
    df["county"] = df["county"].astype(str).str.strip()
    df = df[df["county"].str.len() > 0].copy()
    df = df[~df["county"].str.contains("Total|total|TABLE|Note", na=False)].copy()

    for col in CRIME_COLS.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["state"] = state_abbr
    df["year"] = year

    return df


def load_stores():
    """Load R1 US store data."""
    path = os.path.join(DATA_DIR, "round1_usa_stores.json")
    with open(path) as f:
        return json.load(f)


def build_county_panel(stores):
    """Build county × year panel from UCR Table 10."""
    print("Downloading FBI UCR Table 10 county data...")

    # Determine which states we need (R1 states + their neighbors for controls)
    r1_states = set(s["state"] for s in stores)
    all_states = set(STATE_NAMES.keys())
    target_states = all_states  # Download all states for complete controls

    years = [2014, 2015, 2017, 2018, 2019]
    all_dfs = []
    downloaded = 0
    failed = 0

    for year in years:
        year_count = 0
        for st in sorted(target_states):
            url = url_for_state_year(st, year)
            if not url:
                continue
            df = download_and_parse(url, st, year)
            if df is not None and len(df) > 0:
                all_dfs.append(df)
                year_count += len(df)
                downloaded += 1
            else:
                failed += 1
        print(f"  {year}: {year_count} county records")

    if not all_dfs:
        print("ERROR: No county data downloaded.")
        return None

    panel = pd.concat(all_dfs, ignore_index=True)

    # Build R1 county mapping
    r1_counties = {}
    for s in stores:
        key = f"{s['state']}_{s['county']}"
        yr = s.get("open_year", 9999)
        if key not in r1_counties or yr < r1_counties[key]:
            r1_counties[key] = yr

    panel["county_key"] = panel["state"] + "_" + panel["county"]
    panel["has_r1"] = panel["county_key"].apply(lambda k: 1 if k in r1_counties else 0)
    panel["first_r1_year"] = panel["county_key"].apply(
        lambda k: r1_counties.get(k, np.nan)
    )

    # Aggregate duplicate county rows (metro + nonmetro) to single county total
    group_cols = ["state", "county", "county_key", "year", "has_r1"]
    crime_cols = [c for c in CRIME_COLS.values() if c in panel.columns]
    agg_dict = {c: "sum" for c in crime_cols}
    agg_dict["first_r1_year"] = "first"
    panel = panel.groupby(group_cols, as_index=False).agg(agg_dict)

    panel["trend"] = panel["year"] - panel["year"].min()
    panel["r1_trend"] = panel["has_r1"] * panel["trend"]

    n_r1 = panel[panel["has_r1"] == 1]["county_key"].nunique()
    n_ctrl = panel[panel["has_r1"] == 0]["county_key"].nunique()
    print(f"\nPanel: {len(panel)} obs, {panel['county_key'].nunique()} counties, {panel['year'].nunique()} years")
    print(f"R1 counties: {n_r1}, Control: {n_ctrl}")
    print(f"Downloaded: {downloaded}, Failed: {failed}")

    return panel


def run_models(panel):
    """Run DiD models for each crime category."""
    print(f"\n{'='*60}")
    print("DIFFERENTIAL TREND ANALYSIS — US COUNTY LEVEL")
    print(f"{'='*60}")

    results = {}
    crime_cols = [c for c in CRIME_COLS.values() if c in panel.columns]

    for col in crime_cols:
        title = CRIME_LABELS.get(col, col)
        base_cols = ["county_key", "year", col, "r1_trend", "has_r1", "trend"]
        reg = panel[base_cols].dropna().copy()
        reg = reg.rename(columns={col: "crime_count"})

        if reg["county_key"].nunique() < 10:
            continue

        try:
            m = smf.ols(
                "crime_count ~ r1_trend + C(county_key) + C(year)", data=reg
            ).fit(cov_type="cluster", cov_kwds={"groups": reg["county_key"]})
            coef = m.params["r1_trend"]
            se = m.bse["r1_trend"]
            p = m.pvalues["r1_trend"]
            ci = m.conf_int().loc["r1_trend"].tolist()

            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            sign = "+" if coef > 0 else ""
            print(f"\n  {title}:")
            print(f"    R1×trend = {sign}{coef:.1f} {sig}  (p={p:.4f})")
            print(f"    95% CI: [{ci[0]:.1f}, {ci[1]:.1f}]")

            results[title] = {
                "coefficient": round(coef, 3),
                "std_error": round(se, 3),
                "p_value": round(p, 4),
                "ci_95": [round(ci[0], 3), round(ci[1], 3)],
                "n_obs": int(len(reg)),
                "n_counties": int(reg["county_key"].nunique()),
            }
        except Exception as e:
            print(f"  {title}: failed — {e}")

    return results


def plot_trends(panel):
    """Crime count trends: R1 vs non-R1 counties."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    plot_cols = [
        ("Property Crime", "property_crime"),
        ("Violent Crime", "violent_crime"),
        ("Larceny-Theft", "larceny_theft"),
        ("Burglary", "burglary"),
    ]

    for idx, (title, col) in enumerate(plot_cols):
        ax = axes[idx // 2][idx % 2]
        if col not in panel.columns:
            continue

        n_r1 = panel[panel["has_r1"] == 1]["county_key"].nunique()
        n_ctrl = panel[panel["has_r1"] == 0]["county_key"].nunique()

        for grp, color, label in [
            (1, C_R1, f"R1 counties (n={n_r1})"),
            (0, C_CTRL, f"Non-R1 (n={n_ctrl})"),
        ]:
            g = panel[panel["has_r1"] == grp].groupby("year")[col].mean()
            ax.plot(g.index, g.values, color=color, lw=2.5,
                    marker="o", markersize=6, label=label)

        ax.set_xlabel("Year", fontsize=11)
        ax.set_ylabel("Mean Offenses (per county)", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    plt.suptitle("US County Crime Trends: Round1 vs Non-Round1 Counties\n"
                 "(FBI UCR Table 10, 2014–2019)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(FIG_DIR, "fig_us01_county_trends.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Fig US01] County trends saved.")


def plot_indexed_trends(panel):
    """Index=100 (2014 base) crime trends for R1 vs non-R1."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    plot_cols = [
        ("Property Crime", "property_crime"),
        ("Violent Crime", "violent_crime"),
        ("Larceny-Theft", "larceny_theft"),
        ("Motor Vehicle Theft", "motor_vehicle_theft"),
    ]

    base_year = panel["year"].min()

    for idx, (title, col) in enumerate(plot_cols):
        ax = axes[idx // 2][idx % 2]
        if col not in panel.columns:
            continue

        for grp, color, label in [
            (1, C_R1, "R1 counties"),
            (0, C_CTRL, "Non-R1"),
        ]:
            g = panel[panel["has_r1"] == grp].groupby("year")[col].mean()
            base = g.loc[base_year] if base_year in g.index and g.loc[base_year] > 0 else 1
            indexed = g / base * 100
            ax.plot(indexed.index, indexed.values, color=color, lw=2.5,
                    marker="o", markersize=5, label=label)

        ax.axhline(y=100, color="gray", ls="--", alpha=0.4)
        ax.set_xlabel("Year", fontsize=10)
        ax.set_ylabel(f"Index ({base_year} = 100)", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8)

    plt.suptitle(f"Indexed Crime Trends: Round1 vs Non-Round1 Counties\n"
                 f"({base_year} = 100, FBI UCR Table 10)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(FIG_DIR, "fig_us02_county_indexed.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Fig US02] Indexed trends saved.")


def plot_forest(results):
    """Forest plot of DiD coefficients."""
    if not results:
        return

    categories = list(results.keys())
    coefs = [results[c]["coefficient"] for c in categories]
    cis = [results[c]["ci_95"] for c in categories]
    pvals = [results[c]["p_value"] for c in categories]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(categories))

    for i, (cat, coef, ci, p) in enumerate(zip(categories, coefs, cis, pvals)):
        color = C_R1 if p < 0.05 else "#999999"
        ax.errorbar(coef, i, xerr=[[coef - ci[0]], [ci[1] - coef]],
                    fmt="o", color=color, markersize=8, capsize=5, capthick=2, linewidth=2)
        sig = " ***" if p < 0.001 else " **" if p < 0.01 else " *" if p < 0.05 else ""
        ax.annotate(f"p={p:.4f}{sig}", xy=(ci[1] + 5, i), fontsize=8, va="center")

    ax.axvline(x=0, color="black", ls="--", alpha=0.5)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(categories, fontsize=10)
    ax.set_xlabel("R1×Trend Coefficient (change in offenses/year)", fontsize=11)
    ax.set_title("US County-Level DiD: Round1 Effect on Crime\n"
                 "(FBI UCR Table 10, 2014–2019)",
                 fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "fig_us03_county_forest.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Fig US03] Forest plot saved.")


def main():
    print("=" * 60)
    print("US COUNTY-LEVEL CRIME ANALYSIS")
    print("=" * 60)

    stores = load_stores()
    panel = build_county_panel(stores)
    if panel is None:
        print("Failed to build panel.")
        return

    # Save panel
    panel_path = os.path.join(OUTPUT_DIR, "us_county_panel.csv")
    panel.to_csv(panel_path, index=False)

    # Run models
    results = run_models(panel)

    # Save results
    results_path = os.path.join(OUTPUT_DIR, "us_county_did.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Plot
    plot_trends(panel)
    plot_indexed_trends(panel)
    plot_forest(results)

    print(f"\n{'='*60}")
    print("US COUNTY ANALYSIS COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
