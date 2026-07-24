"""
05_county_neighbor_analysis.py
County-level and neighbor-comparison analysis for Round1 USA.

Analyses:
  1. Map Round1 stores → FIPS counties
  2. County-level crime baseline (ucr-json 2005-2008)
  3. State-level neighbor comparison (R1 states vs adjacent non-R1 states)
  4. Neighbor-pair DiD at state level

Data sources:
  - Round1 store data: round1_usa_stores.json (includes county names)
  - County crime: maliabadi/ucr-json (1977-2008 county-level UCR)
  - County adjacency: US Census Bureau county_adjacency.txt
  - State crime: CORGIS state_crime_full.csv (1960-2019)
"""

import os
import json
import warnings
import csv

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

C_R1 = "#E63946"
C_CTRL = "#457B9D"
C_ACCENT = "#2A9D8F"
C_DARK = "#1D3557"

# ── State abbrev mapping ──
STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}
NAME_TO_ABBR = {v: k for k, v in STATE_ABBR.items()}

# ── State adjacency ──
STATE_NEIGHBORS = {
    "AL": ["FL", "GA", "MS", "TN"],
    "AK": [],
    "AZ": ["CA", "CO", "NM", "NV", "UT"],
    "AR": ["LA", "MO", "MS", "OK", "TN", "TX"],
    "CA": ["AZ", "NV", "OR"],
    "CO": ["AZ", "KS", "NE", "NM", "OK", "UT", "WY"],
    "CT": ["MA", "NY", "RI"],
    "DE": ["MD", "NJ", "PA"],
    "FL": ["AL", "GA"],
    "GA": ["AL", "FL", "NC", "SC", "TN"],
    "HI": [],
    "ID": ["MT", "NV", "OR", "UT", "WA", "WY"],
    "IL": ["IN", "IA", "KY", "MO", "WI"],
    "IN": ["IL", "KY", "MI", "OH"],
    "IA": ["IL", "MN", "MO", "NE", "SD", "WI"],
    "KS": ["CO", "MO", "NE", "OK"],
    "KY": ["IL", "IN", "MO", "OH", "TN", "VA", "WV"],
    "LA": ["AR", "MS", "TX"],
    "ME": ["NH"],
    "MD": ["DE", "PA", "VA", "WV"],
    "MA": ["CT", "NH", "NY", "RI", "VT"],
    "MI": ["IN", "OH", "WI"],
    "MN": ["IA", "ND", "SD", "WI"],
    "MS": ["AL", "AR", "LA", "TN"],
    "MO": ["AR", "IL", "IA", "KS", "KY", "NE", "OK", "TN"],
    "MT": ["ID", "ND", "SD", "WY"],
    "NE": ["CO", "IA", "KS", "MO", "SD", "WY"],
    "NV": ["AZ", "CA", "ID", "OR", "UT"],
    "NH": ["MA", "ME", "VT"],
    "NJ": ["DE", "NY", "PA"],
    "NM": ["AZ", "CO", "OK", "TX", "UT"],
    "NY": ["CT", "MA", "NJ", "PA", "VT"],
    "NC": ["GA", "SC", "TN", "VA"],
    "ND": ["MN", "MT", "SD"],
    "OH": ["IN", "KY", "MI", "PA", "WV"],
    "OK": ["AR", "CO", "KS", "MO", "NM", "TX"],
    "OR": ["CA", "ID", "NV", "WA"],
    "PA": ["DE", "MD", "NJ", "NY", "OH", "WV"],
    "RI": ["CT", "MA"],
    "SC": ["GA", "NC"],
    "SD": ["IA", "MN", "MT", "ND", "NE", "WY"],
    "TN": ["AL", "AR", "GA", "KY", "MO", "MS", "NC", "VA"],
    "TX": ["AR", "LA", "NM", "OK"],
    "UT": ["AZ", "CO", "ID", "NM", "NV", "WY"],
    "VT": ["MA", "NH", "NY"],
    "VA": ["KY", "MD", "NC", "TN", "WV"],
    "WA": ["ID", "OR"],
    "WV": ["KY", "MD", "OH", "PA", "VA"],
    "WI": ["IA", "IL", "MI", "MN"],
    "WY": ["CO", "ID", "MT", "NE", "SD", "UT"],
}


def load_stores():
    path = os.path.join(DATA_DIR, "round1_usa_stores.json")
    with open(path) as f:
        return json.load(f)


def load_state_crime():
    path = os.path.join(DATA_DIR, "state_crime_full.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["State"] = df["State"].str.strip().str.strip('"')
    df["Year"] = df["Year"].astype(int)
    df = df[~df["State"].str.contains("Total|United States", na=False)]
    return df


def load_county_crime(ucr_json_dir):
    """Load county-level crime from ucr-json (2005-2008)."""
    rows = []
    for year in range(2005, 2009):
        path = os.path.join(ucr_json_dir, f"{year}.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        for entry in data:
            fips_state = entry.get("fips_state_code", "")
            fips_county = entry.get("fips_county_code", "")
            if not fips_state or not fips_county:
                continue
            fips = f"{fips_state}{fips_county}"
            rows.append({
                "year": year,
                "fips": fips,
                "fips_state": fips_state,
                "fips_county": fips_county,
                "population": entry.get("county_population", 0),
                "violent_crimes": entry.get("violent_crimes", 0),
                "property_crimes": entry.get("property_crimes", 0),
                "murder": entry.get("murder", 0),
                "robbery": entry.get("robbery", 0),
                "aggravated_assaults": entry.get("aggravated_assaults", 0),
                "burglary": entry.get("burglary", 0),
                "larceny": entry.get("larceny", 0),
                "auto_thefts": entry.get("auto_thefts", 0),
                "grand_total": entry.get("grand_total", 0),
                "coverage": entry.get("coverage_indicator", 0),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        print("County crime data: 0 rows (no matching JSON files found)")
        return df
    print(f"County crime data: {len(df)} rows ({df['year'].nunique()} years, "
          f"{df['fips'].nunique()} counties)")
    return df


# ── FIPS state code → abbreviation ──
FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "12": "FL", "13": "GA",
    "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO",
    "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ",
    "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC",
    "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT",
    "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}
ABBR_TO_FIPS = {v: k for k, v in FIPS_TO_ABBR.items()}


# ═══════════════════════════════════════════════════════════════════
# Part A: County-Level Baseline (2005-2008 pre-treatment)
# ═══════════════════════════════════════════════════════════════════
def analyze_county_baseline(stores, county_df):
    """Summarize pre-treatment county crime for Round1 counties."""
    r1_states = set(s["state"] for s in stores)
    r1_counties = {}
    for s in stores:
        key = (s["state"], s.get("county", ""))
        if key not in r1_counties:
            r1_counties[key] = s["open_year"]
        else:
            r1_counties[key] = min(r1_counties[key], s["open_year"])

    county_df = county_df.copy()
    county_df["state_abbr"] = county_df["fips_state"].map(FIPS_TO_ABBR)

    # Aggregate 2005-2008 per county
    agg = county_df.groupby(["fips", "state_abbr"]).agg({
        "population": "mean",
        "violent_crimes": "mean",
        "property_crimes": "mean",
        "murder": "mean",
        "grand_total": "mean",
    }).reset_index()

    # Mark R1 states
    agg["has_r1_state"] = agg["state_abbr"].isin(r1_states).astype(int)

    # Compute rates per 100k
    for col in ["violent_crimes", "property_crimes", "murder", "grand_total"]:
        agg[f"{col}_rate"] = np.where(
            agg["population"] > 0,
            agg[col] / agg["population"] * 100000,
            np.nan,
        )

    print(f"\n{'='*60}")
    print("COUNTY-LEVEL BASELINE (2005-2008 Pre-Treatment)")
    print(f"{'='*60}")
    print(f"Total counties: {len(agg)}")

    for label, rate_col in [
        ("Total Crime", "grand_total_rate"),
        ("Violent Crime", "violent_crimes_rate"),
        ("Property Crime", "property_crimes_rate"),
    ]:
        r1_mean = agg[agg["has_r1_state"] == 1][rate_col].mean()
        ctrl_mean = agg[agg["has_r1_state"] == 0][rate_col].mean()
        print(f"\n  {label} rate (per 100k):")
        print(f"    Future R1 state counties: {r1_mean:.1f}")
        print(f"    Non-R1 state counties:    {ctrl_mean:.1f}")

    agg.to_csv(os.path.join(OUTPUT_DIR, "county_baseline_2005_2008.csv"),
               index=False, encoding="utf-8")
    print(f"\n  Saved: county_baseline_2005_2008.csv")
    return agg


# ═══════════════════════════════════════════════════════════════════
# Part B: Neighbor State Comparison (state-level, 2005-2019)
# ═══════════════════════════════════════════════════════════════════
def run_neighbor_state_analysis(stores, crime_df):
    """Compare R1 states to their adjacent non-R1 neighbor states."""
    r1_states = set(s["state"] for s in stores)
    first_open = {}
    for s in stores:
        st = s["state"]
        if st not in first_open or s["open_year"] < first_open[st]:
            first_open[st] = s["open_year"]

    # Build neighbor pairs: R1 state → adjacent non-R1 states
    neighbor_pairs = []
    for r1_st in r1_states:
        for nb in STATE_NEIGHBORS.get(r1_st, []):
            if nb not in r1_states:
                neighbor_pairs.append((r1_st, nb))

    print(f"\n{'='*60}")
    print("NEIGHBOR STATE COMPARISON")
    print(f"{'='*60}")
    print(f"R1 states: {len(r1_states)}")
    print(f"Neighbor pairs (R1 → non-R1 adjacent): {len(neighbor_pairs)}")

    # DiD using only R1 states and their non-R1 neighbors
    neighbor_non_r1 = set(nb for _, nb in neighbor_pairs)
    relevant_states = r1_states | neighbor_non_r1
    relevant_names = set()
    for abbr in relevant_states:
        name = STATE_ABBR.get(abbr)
        if name:
            relevant_names.add(name)

    sub = crime_df[
        (crime_df["State"].isin(relevant_names)) &
        (crime_df["Year"] >= 2005) &
        (crime_df["Year"] <= 2019)
    ].copy()

    sub["state_abbr"] = sub["State"].map(NAME_TO_ABBR)
    sub["is_r1"] = sub["state_abbr"].isin(r1_states).astype(int)
    sub["first_r1_year"] = sub["state_abbr"].map(
        lambda a: first_open.get(a, np.nan)
    )
    sub["post_r1"] = (sub["Year"] >= sub["first_r1_year"]).astype(int)
    sub["post_r1"] = sub["post_r1"].fillna(0).astype(int)

    crime_types = {
        "Violent Crime": "Data.Rates.Violent.All",
        "Property Crime": "Data.Rates.Property.All",
        "Murder": "Data.Rates.Violent.Murder",
        "Robbery": "Data.Rates.Violent.Robbery",
        "Burglary": "Data.Rates.Property.Burglary",
    }

    results = {}
    print(f"\nModel: crime ~ post_r1 + C(State) + C(Year)")
    print(f"Sample: R1 states + adjacent non-R1 neighbors only")
    print(f"N states in sample: {sub['State'].nunique()}")

    for title, col in crime_types.items():
        reg_data = sub[["State", "Year", col, "is_r1", "post_r1"]].dropna()
        reg_data = reg_data.rename(columns={col: "crime_rate"})
        try:
            model = smf.ols(
                "crime_rate ~ post_r1 + C(State) + C(Year)", data=reg_data
            ).fit(cov_type="cluster", cov_kwds={"groups": reg_data["State"]})
            coef = model.params["post_r1"]
            se = model.bse["post_r1"]
            pval = model.pvalues["post_r1"]
            ci_lo, ci_hi = model.conf_int().loc["post_r1"]
            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

            results[title] = {
                "coefficient": float(round(coef, 3)),
                "std_error": float(round(se, 3)),
                "p_value": float(round(pval, 4)),
                "ci_95": [float(round(ci_lo, 3)), float(round(ci_hi, 3))],
                "significant": bool(pval < 0.05),
                "n_obs": int(len(reg_data)),
            }
            print(f"\n  {title}:")
            print(f"    DiD coef:  {coef:+.3f} {sig}")
            print(f"    SE:        {se:.3f}")
            print(f"    p-value:   {pval:.4f}")
            print(f"    95% CI:    [{ci_lo:.3f}, {ci_hi:.3f}]")
        except Exception as e:
            print(f"\n  {title}: failed — {e}")
            results[title] = {"error": str(e)}

    with open(os.path.join(OUTPUT_DIR, "neighbor_state_did_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Saved: neighbor_state_did_results.json")
    return results


def plot_neighbor_forest(results):
    """Forest plot for neighbor-state DiD."""
    labels, coefs, cis_lo, cis_hi, colors = [], [], [], [], []
    for crime, res in results.items():
        if "error" in res:
            continue
        labels.append(crime)
        coefs.append(res["coefficient"])
        cis_lo.append(res["ci_95"][0])
        cis_hi.append(res["ci_95"][1])
        colors.append(C_R1 if res["significant"] else C_CTRL)

    if not labels:
        return

    y_pos = np.arange(len(labels))
    err_lo = [c - lo for c, lo in zip(coefs, cis_lo)]
    err_hi = [hi - c for c, hi in zip(coefs, cis_hi)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.errorbar(coefs, y_pos, xerr=[err_lo, err_hi],
                fmt="o", markersize=8, capsize=5,
                color=C_DARK, ecolor="gray", elinewidth=1.5)
    for i, (c, col) in enumerate(zip(coefs, colors)):
        ax.plot(c, i, "o", color=col, markersize=8, zorder=5)

    ax.axvline(x=0, color="gray", ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("DiD Coefficient (change in rate per 100k)", fontsize=12)
    ax.set_title(
        "Neighbor State DiD: Round1 States vs Adjacent Non-R1 States\n"
        "(Red = p<0.05, Blue = not significant)",
        fontsize=12, fontweight="bold",
    )
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig7_neighbor_state_forest.png"), dpi=200)
    plt.close(fig)
    print("[Fig 7] Neighbor state forest plot saved.")


def plot_neighbor_trends(stores, crime_df):
    """Crime trends: R1 states vs their non-R1 neighbors."""
    r1_states = set(s["state"] for s in stores)
    neighbor_non_r1 = set()
    for st in r1_states:
        for nb in STATE_NEIGHBORS.get(st, []):
            if nb not in r1_states:
                neighbor_non_r1.add(nb)

    r1_names = {STATE_ABBR[a] for a in r1_states if a in STATE_ABBR}
    nb_names = {STATE_ABBR[a] for a in neighbor_non_r1 if a in STATE_ABBR}

    sub = crime_df[
        (crime_df["Year"] >= 2005) & (crime_df["Year"] <= 2019) &
        (crime_df["State"].isin(r1_names | nb_names))
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, (title, col) in enumerate([
        ("Violent Crime", "Data.Rates.Violent.All"),
        ("Property Crime", "Data.Rates.Property.All"),
    ]):
        ax = axes[idx]
        for names, color, label in [
            (r1_names, C_R1, "Round1 states"),
            (nb_names, C_CTRL, "Adjacent non-R1 neighbors"),
        ]:
            grp = sub[sub["State"].isin(names)].groupby("Year")[col].mean()
            ax.plot(grp.index, grp.values, color=color, lw=2,
                    marker="o", markersize=3, label=label)
        ax.axvline(x=2010, color="gray", ls="--", alpha=0.5)
        ax.set_xlabel("Year")
        ax.set_ylabel(f"{title} Rate (per 100k)")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
    plt.suptitle("Round1 States vs Adjacent Non-R1 Neighbor States (2005-2019)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig8_neighbor_trends.png"), dpi=200)
    plt.close(fig)
    print("[Fig 8] Neighbor trends comparison saved.")


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("ROUND1 USA: COUNTY & NEIGHBOR ANALYSIS")
    print("=" * 60)

    stores = load_stores()
    crime_df = load_state_crime()

    # County baseline (ucr-json)
    ucr_dir = os.path.expanduser("~/ucr-json/data/parsed/normalized")
    if os.path.isdir(ucr_dir):
        county_df = load_county_crime(ucr_dir)
        analyze_county_baseline(stores, county_df)
    else:
        print("\n  [SKIP] ucr-json not found — county baseline skipped")

    # Neighbor state analysis
    nb_results = run_neighbor_state_analysis(stores, crime_df)
    plot_neighbor_forest(nb_results)
    plot_neighbor_trends(stores, crime_df)

    print("\n" + "=" * 60)
    print("NEIGHBOR ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
