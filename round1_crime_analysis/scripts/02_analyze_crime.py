"""
02_analyze_crime.py
Main analysis: Round1 store openings and crime trends in the United States.

Analyses:
  1. Descriptive: Round1 expansion timeline
  2. Pre/post crime trend in Round1 states (event study)
  3. Difference-in-Differences: Round1 states vs non-Round1 states
  4. Crime category breakdown (violent, property, murder, robbery, assault, etc.)

Data sources:
  - Round1 store data: compiled in 01_compile_round1_stores.py
  - Crime data: FBI UCR via CORGIS (1960-2019), state-level rates per 100k
"""

import os
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ── Colour palette ──
C_R1 = "#E63946"      # Round1 red
C_CTRL = "#457B9D"     # control blue
C_ACCENT = "#2A9D8F"   # accent teal
C_DARK = "#1D3557"     # dark navy
C_LIGHT = "#F1FAEE"    # light bg


def load_stores():
    path = os.path.join(DATA_DIR, "round1_usa_stores.json")
    with open(path) as f:
        stores = json.load(f)
    df = pd.DataFrame(stores)
    df["open_year"] = df["open_year"].astype(int)
    return df


def load_crime():
    path = os.path.join(DATA_DIR, "state_crime_full.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["State"] = df["State"].str.strip().str.strip('"')
    df["Year"] = df["Year"].astype(int)
    return df


# ── State abbrev ↔ name mapping ──
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


def get_first_opening_by_state(stores_df):
    """Return dict: state_abbr -> first_opening_year."""
    return stores_df.groupby("state")["open_year"].min().to_dict()


# ═══════════════════════════════════════════════════════════════════════
# Analysis 1: Round1 expansion timeline
# ═══════════════════════════════════════════════════════════════════════
def plot_expansion_timeline(stores_df):
    by_year = stores_df.groupby("open_year").size()
    cumul = by_year.cumsum()

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(by_year.index, by_year.values, color=C_R1, alpha=0.7, label="New stores")
    ax2 = ax1.twinx()
    ax2.plot(cumul.index, cumul.values, color=C_DARK, lw=2.5,
             marker="o", markersize=5, label="Cumulative")
    ax1.set_xlabel("Year", fontsize=12)
    ax1.set_ylabel("New stores opened", fontsize=12, color=C_R1)
    ax2.set_ylabel("Cumulative stores", fontsize=12, color=C_DARK)
    ax1.set_title("Round1 USA Expansion Timeline", fontsize=14, fontweight="bold")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig1_expansion_timeline.png"), dpi=200)
    plt.close(fig)
    print("[Fig 1] Expansion timeline saved.")


# ═══════════════════════════════════════════════════════════════════════
# Analysis 2: Crime trends — Round1 states vs non-Round1 states
# ═══════════════════════════════════════════════════════════════════════
def classify_states(stores_df, crime_df):
    """Classify states and add treatment info to crime_df."""
    first_open = get_first_opening_by_state(stores_df)
    # All state names in crime data
    crime_states = set(crime_df["State"].unique())
    r1_state_names = set()
    for abbr, yr in first_open.items():
        name = STATE_ABBR.get(abbr)
        if name and name in crime_states:
            r1_state_names.add(name)

    df = crime_df.copy()
    df["has_round1"] = df["State"].isin(r1_state_names).astype(int)
    df["first_r1_year"] = df["State"].map(
        lambda s: first_open.get(NAME_TO_ABBR.get(s, ""), np.nan)
    )
    df["post_r1"] = (df["Year"] >= df["first_r1_year"]).astype(int)
    df["post_r1"] = df["post_r1"].fillna(0).astype(int)
    return df


def plot_crime_trends_comparison(df):
    """Plot violent and property crime trends for R1 vs non-R1 states."""
    analysis_years = range(2005, 2020)
    sub = df[df["Year"].isin(analysis_years)]
    sub = sub[~sub["State"].str.contains("Total|United States", na=False)]

    crime_types = {
        "Violent Crime": "Data.Rates.Violent.All",
        "Property Crime": "Data.Rates.Property.All",
        "Murder": "Data.Rates.Violent.Murder",
        "Robbery": "Data.Rates.Violent.Robbery",
        "Assault": "Data.Rates.Violent.Assault",
        "Burglary": "Data.Rates.Property.Burglary",
    }

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for idx, (title, col) in enumerate(crime_types.items()):
        ax = axes[idx]
        for grp, color, label in [
            (1, C_R1, "Round1 states"),
            (0, C_CTRL, "Non-Round1 states"),
        ]:
            grp_data = sub[sub["has_round1"] == grp].groupby("Year")[col].mean()
            ax.plot(grp_data.index, grp_data.values, color=color,
                    lw=2, label=label, marker="o", markersize=3)
        ax.axvline(x=2010, color="gray", ls="--", alpha=0.5, label="First R1 (2010)")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Rate per 100k")
        if idx == 0:
            ax.legend(fontsize=8)

    fig.suptitle(
        "Crime Rates: Round1 States vs Non-Round1 States (2005–2019)",
        fontsize=14, fontweight="bold", y=1.01,
    )
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_crime_trends_comparison.png"),
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("[Fig 2] Crime trends comparison saved.")


# ═══════════════════════════════════════════════════════════════════════
# Analysis 3: Event study — normalised crime around first R1 opening
# ═══════════════════════════════════════════════════════════════════════
def plot_event_study(df):
    """Event study: center time at first Round1 opening year for each state."""
    r1_states = df[df["has_round1"] == 1].copy()
    r1_states["event_time"] = r1_states["Year"] - r1_states["first_r1_year"]
    r1_states = r1_states[
        (r1_states["event_time"] >= -5) & (r1_states["event_time"] <= 5)
    ]

    crime_types = {
        "Violent Crime": "Data.Rates.Violent.All",
        "Property Crime": "Data.Rates.Property.All",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, (title, col) in enumerate(crime_types.items()):
        ax = axes[idx]
        # Normalise to t=-1 (year before opening)
        baseline = r1_states[r1_states["event_time"] == -1].groupby("State")[col].mean()
        merged = r1_states.merge(
            baseline.rename("baseline"),
            left_on="State", right_index=True,
        )
        merged["norm_rate"] = (merged[col] / merged["baseline"]) * 100

        means = merged.groupby("event_time")["norm_rate"].agg(["mean", "sem"])
        ax.fill_between(
            means.index,
            means["mean"] - 1.96 * means["sem"],
            means["mean"] + 1.96 * means["sem"],
            alpha=0.2, color=C_R1,
        )
        ax.plot(means.index, means["mean"], color=C_R1, lw=2.5, marker="o")
        ax.axhline(y=100, color="gray", ls=":", alpha=0.5)
        ax.axvline(x=0, color=C_DARK, ls="--", alpha=0.7, label="R1 opening")
        ax.set_xlabel("Years relative to Round1 opening", fontsize=11)
        ax.set_ylabel("Normalised crime rate (t=-1 = 100)", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend()

    fig.suptitle(
        "Event Study: Crime Rates Around Round1 Store Opening",
        fontsize=14, fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_event_study.png"), dpi=200)
    plt.close(fig)
    print("[Fig 3] Event study saved.")


# ═══════════════════════════════════════════════════════════════════════
# Analysis 4: Difference-in-Differences regression
# ═══════════════════════════════════════════════════════════════════════
def run_did_regression(df):
    """Two-way fixed-effects DiD: state + year FE, treatment = post_r1."""
    analysis = df[(df["Year"] >= 2005) & (df["Year"] <= 2019)].copy()
    # Exclude national totals
    analysis = analysis[~analysis["State"].str.contains("Total|United States", na=False)]

    results = {}
    crime_types = {
        "Violent Crime": "Data.Rates.Violent.All",
        "Property Crime": "Data.Rates.Property.All",
        "Murder": "Data.Rates.Violent.Murder",
        "Robbery": "Data.Rates.Violent.Robbery",
        "Assault": "Data.Rates.Violent.Assault",
        "Burglary": "Data.Rates.Property.Burglary",
        "Larceny": "Data.Rates.Property.Larceny",
        "Motor Vehicle Theft": "Data.Rates.Property.Motor",
    }

    print("\n" + "=" * 70)
    print("DIFFERENCE-IN-DIFFERENCES REGRESSION RESULTS")
    print("Model: crime_rate ~ post_r1 + C(State) + C(Year)")
    print("Period: 2005–2019 | Treatment: post × Round1_state")
    print("=" * 70)

    for title, col in crime_types.items():
        sub = analysis[["State", "Year", col, "has_round1", "post_r1"]].dropna()
        sub = sub.rename(columns={col: "crime_rate"})

        try:
            model = smf.ols(
                "crime_rate ~ post_r1 + C(State) + C(Year)", data=sub
            ).fit(cov_type="cluster", cov_kwds={"groups": sub["State"]})
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
                "n_obs": int(len(sub)),
            }
            print(f"\n  {title}:")
            print(f"    DiD coef (post_r1): {coef:+.3f} {sig}")
            print(f"    SE (clustered):     {se:.3f}")
            print(f"    p-value:            {pval:.4f}")
            print(f"    95% CI:             [{ci_lo:.3f}, {ci_hi:.3f}]")
        except Exception as e:
            print(f"\n  {title}: regression failed — {e}")
            results[title] = {"error": str(e)}

    # Save results
    with open(os.path.join(OUTPUT_DIR, "did_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {os.path.join(OUTPUT_DIR, 'did_results.json')}")
    return results


# ═══════════════════════════════════════════════════════════════════════
# Analysis 5: DiD coefficient forest plot
# ═══════════════════════════════════════════════════════════════════════
def plot_did_forest(results):
    """Forest plot of DiD coefficients across crime types."""
    labels = []
    coefs = []
    cis_lo = []
    cis_hi = []
    colors = []

    for crime_type, res in results.items():
        if "error" in res:
            continue
        labels.append(crime_type)
        coefs.append(res["coefficient"])
        cis_lo.append(res["ci_95"][0])
        cis_hi.append(res["ci_95"][1])
        colors.append(C_R1 if res["significant"] else C_CTRL)

    y_pos = np.arange(len(labels))
    errors_lo = [c - lo for c, lo in zip(coefs, cis_lo)]
    errors_hi = [hi - c for c, hi in zip(coefs, cis_hi)]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(coefs, y_pos, xerr=[errors_lo, errors_hi],
                fmt="o", markersize=8, capsize=5,
                color=C_DARK, ecolor="gray", elinewidth=1.5)
    for i, (c, col) in enumerate(zip(coefs, colors)):
        ax.plot(c, i, "o", color=col, markersize=8, zorder=5)

    ax.axvline(x=0, color="gray", ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel("DiD Coefficient (change in rate per 100k)", fontsize=12)
    ax.set_title(
        "Difference-in-Differences: Effect of Round1 Opening on Crime Rates\n"
        "(Red = p < 0.05, Blue = not significant)",
        fontsize=12, fontweight="bold",
    )
    ax.invert_yaxis()
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_did_forest_plot.png"), dpi=200)
    plt.close(fig)
    print("[Fig 4] DiD forest plot saved.")


# ═══════════════════════════════════════════════════════════════════════
# Analysis 6: State-level heatmap — crime change around R1 opening
# ═══════════════════════════════════════════════════════════════════════
def plot_state_heatmap(df, stores_df):
    """Heatmap: % change in crime (3yr post vs 3yr pre opening) by state."""
    first_open = get_first_opening_by_state(stores_df)

    rows = []
    for abbr, open_yr in first_open.items():
        state_name = STATE_ABBR.get(abbr)
        if not state_name:
            continue
        pre = df[(df["State"] == state_name) &
                 (df["Year"] >= open_yr - 3) &
                 (df["Year"] < open_yr)]
        post = df[(df["State"] == state_name) &
                  (df["Year"] >= open_yr) &
                  (df["Year"] < open_yr + 3)]

        if len(pre) == 0 or len(post) == 0:
            continue

        row = {"state": abbr, "open_year": open_yr}
        for crime_name, col in [
            ("Violent", "Data.Rates.Violent.All"),
            ("Property", "Data.Rates.Property.All"),
            ("Murder", "Data.Rates.Violent.Murder"),
            ("Robbery", "Data.Rates.Violent.Robbery"),
        ]:
            pre_mean = pre[col].mean()
            post_mean = post[col].mean()
            if pre_mean > 0:
                row[crime_name] = ((post_mean - pre_mean) / pre_mean) * 100
            else:
                row[crime_name] = np.nan
        rows.append(row)

    heat_df = pd.DataFrame(rows).set_index("state")
    heat_df = heat_df.sort_values("open_year")

    crime_cols = ["Violent", "Property", "Murder", "Robbery"]
    plot_data = heat_df[crime_cols]

    fig, ax = plt.subplots(figsize=(10, max(8, len(plot_data) * 0.4)))
    im = ax.imshow(plot_data.values, cmap="RdYlGn_r", aspect="auto",
                   vmin=-30, vmax=30)
    ax.set_xticks(range(len(crime_cols)))
    ax.set_xticklabels(crime_cols, fontsize=11)
    ax.set_yticks(range(len(plot_data)))
    ylabels = [f"{idx} ({int(heat_df.loc[idx, 'open_year'])})"
               for idx in plot_data.index]
    ax.set_yticklabels(ylabels, fontsize=9)

    for i in range(len(plot_data)):
        for j in range(len(crime_cols)):
            val = plot_data.iloc[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:+.1f}%", ha="center", va="center",
                        fontsize=8, color="black" if abs(val) < 20 else "white")

    plt.colorbar(im, ax=ax, label="% change (3yr post vs 3yr pre)")
    ax.set_title(
        "Crime Rate Change Around Round1 Opening (by State)\n"
        "Green = decrease, Red = increase",
        fontsize=12, fontweight="bold",
    )
    ax.set_xlabel("Crime Category")
    ax.set_ylabel("State (opening year)")
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig5_state_heatmap.png"), dpi=200)
    plt.close(fig)
    print("[Fig 5] State heatmap saved.")

    heat_df.to_csv(os.path.join(OUTPUT_DIR, "crime_change_by_state.csv"))
    return heat_df


# ═══════════════════════════════════════════════════════════════════════
# Analysis 7: Parallel trends test (pre-treatment)
# ═══════════════════════════════════════════════════════════════════════
def test_parallel_trends(df):
    """Test whether R1 and non-R1 states had parallel trends pre-treatment."""
    pre = df[(df["Year"] >= 2005) & (df["Year"] < 2010)].copy()
    pre = pre[~pre["State"].str.contains("Total|United States", na=False)]

    print("\n" + "=" * 70)
    print("PARALLEL TRENDS TEST (2005–2009, pre-treatment)")
    print("=" * 70)

    results = {}
    for title, col in [
        ("Violent Crime", "Data.Rates.Violent.All"),
        ("Property Crime", "Data.Rates.Property.All"),
    ]:
        sub = pre[["State", "Year", col, "has_round1"]].dropna()
        sub = sub.rename(columns={col: "rate"})
        sub["year_trend"] = sub["Year"] - 2005

        model = smf.ols(
            "rate ~ year_trend * has_round1 + C(State)", data=sub
        ).fit(cov_type="cluster", cov_kwds={"groups": sub["State"]})

        interaction = model.params.get("year_trend:has_round1", np.nan)
        p_int = model.pvalues.get("year_trend:has_round1", np.nan)

        results[title] = {
            "interaction_coef": float(round(interaction, 3)),
            "p_value": float(round(p_int, 4)),
            "parallel": bool(p_int > 0.05),
        }
        status = "PASS (parallel)" if p_int > 0.05 else "FAIL (not parallel)"
        print(f"\n  {title}:")
        print(f"    Interaction (trend × R1):  {interaction:+.3f}")
        print(f"    p-value:                   {p_int:.4f}")
        print(f"    Result:                    {status}")

    with open(os.path.join(OUTPUT_DIR, "parallel_trends_test.json"), "w") as f:
        json.dump(results, f, indent=2)
    return results


# ═══════════════════════════════════════════════════════════════════════
# Analysis 8: Store density analysis
# ═══════════════════════════════════════════════════════════════════════
def plot_dose_response(df, stores_df):
    """Dose–response: states with more Round1 stores vs fewer."""
    n_stores = stores_df[stores_df["open_year"] <= 2019].groupby("state").size()
    n_stores = n_stores.rename("n_stores")
    n_stores_map = n_stores.to_dict()

    sub = df[(df["Year"] >= 2015) & (df["Year"] <= 2019)].copy()
    sub = sub[~sub["State"].str.contains("Total|United States", na=False)]
    sub["state_abbr"] = sub["State"].map(NAME_TO_ABBR)
    sub["n_stores"] = sub["state_abbr"].map(n_stores_map).fillna(0).astype(int)

    sub["dose_group"] = pd.cut(
        sub["n_stores"],
        bins=[-1, 0, 2, 5, 100],
        labels=["0 (control)", "1-2", "3-5", "6+"],
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for idx, (title, col) in enumerate([
        ("Violent Crime", "Data.Rates.Violent.All"),
        ("Property Crime", "Data.Rates.Property.All"),
    ]):
        ax = axes[idx]
        groups = sub.groupby("dose_group")[col]
        means = groups.mean()
        sems = groups.sem()
        colours = [C_CTRL, C_ACCENT, "#E9C46A", C_R1]
        ax.bar(range(len(means)), means.values, yerr=sems.values * 1.96,
               color=colours, capsize=5, alpha=0.8)
        ax.set_xticks(range(len(means)))
        ax.set_xticklabels(means.index, fontsize=10)
        ax.set_xlabel("Number of Round1 stores in state", fontsize=11)
        ax.set_ylabel("Mean crime rate per 100k (2015-2019)", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")

    fig.suptitle(
        "Dose-Response: Crime Rates by Round1 Store Density (2015–2019)",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig6_dose_response.png"), dpi=200)
    plt.close(fig)
    print("[Fig 6] Dose-response saved.")


# ═══════════════════════════════════════════════════════════════════════
# Summary table
# ═══════════════════════════════════════════════════════════════════════
def create_summary_table(df, stores_df, did_results):
    """Create comprehensive summary table."""
    first_open = get_first_opening_by_state(stores_df)
    r1_states = [STATE_ABBR.get(a) for a in first_open if STATE_ABBR.get(a)]
    non_r1 = [s for s in df["State"].unique()
              if s not in r1_states and "Total" not in s and "United" not in s]

    sub_2019 = df[df["Year"] == 2019]
    r1_2019 = sub_2019[sub_2019["State"].isin(r1_states)]
    nr_2019 = sub_2019[sub_2019["State"].isin(non_r1)]

    summary = []
    for title, col in [
        ("Violent Crime", "Data.Rates.Violent.All"),
        ("Property Crime", "Data.Rates.Property.All"),
        ("Murder", "Data.Rates.Violent.Murder"),
        ("Robbery", "Data.Rates.Violent.Robbery"),
        ("Assault", "Data.Rates.Violent.Assault"),
        ("Burglary", "Data.Rates.Property.Burglary"),
    ]:
        r1_mean = r1_2019[col].mean()
        nr_mean = nr_2019[col].mean()
        did = did_results.get(title, {})
        summary.append({
            "Crime Type": title,
            "R1 States Mean (2019)": round(r1_mean, 1),
            "Non-R1 States Mean (2019)": round(nr_mean, 1),
            "Difference": round(r1_mean - nr_mean, 1),
            "DiD Coefficient": did.get("coefficient", "N/A"),
            "DiD p-value": did.get("p_value", "N/A"),
            "DiD Significant": did.get("significant", "N/A"),
        })

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(os.path.join(OUTPUT_DIR, "summary_table.csv"), index=False)
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    return summary_df


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("Loading data...")
    stores_df = load_stores()
    crime_df = load_crime()

    print(f"  Stores: {len(stores_df)} Round1 USA locations")
    print(f"  Crime:  {len(crime_df)} state-year observations, "
          f"{crime_df['Year'].min()}-{crime_df['Year'].max()}")

    # Classify states
    df = classify_states(stores_df, crime_df)
    r1_count = df[df["has_round1"] == 1]["State"].nunique()
    nr_count = df[df["has_round1"] == 0]["State"].nunique()
    print(f"  Round1 states: {r1_count}, Non-Round1 states: {nr_count}")

    # Run analyses
    print("\n── Analysis 1: Expansion timeline ──")
    plot_expansion_timeline(stores_df)

    print("\n── Analysis 2: Crime trends comparison ──")
    plot_crime_trends_comparison(df)

    print("\n── Analysis 3: Event study ──")
    plot_event_study(df)

    print("\n── Analysis 4: Difference-in-Differences regression ──")
    did_results = run_did_regression(df)

    print("\n── Analysis 5: DiD forest plot ──")
    plot_did_forest(did_results)

    print("\n── Analysis 6: State heatmap ──")
    plot_state_heatmap(df, stores_df)

    print("\n── Analysis 7: Parallel trends test ──")
    test_parallel_trends(df)

    print("\n── Analysis 8: Dose-response ──")
    plot_dose_response(df, stores_df)

    print("\n── Summary table ──")
    create_summary_table(df, stores_df, did_results)

    print("\n" + "=" * 70)
    print("ALL ANALYSES COMPLETE")
    print(f"  Figures: {FIG_DIR}")
    print(f"  Output:  {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
