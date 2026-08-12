"""Age-stratified positive predictive value (PPV) analysis.

The simulation uses an age-adjusted aggregate prevalence. This script shows why the
aggregate matters: PPV is extremely low in younger age groups and rises with age.
All inputs are the same public data sources used by prepare_parameters.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from prepare_parameters import (
    AGE_COLS,
    CHILD_TEEN_COLS,
    POPULATION_2023,
    load_incidence_rate,
    load_pop,
)


def compute_age_group_ppv(
    cancer: Dict[str, Any], age_group: str, incidence_per_100k: float
) -> Dict[str, float]:
    """Return PPV metrics for a single cancer and age group, per 100,000 in that group."""
    population = 100_000.0
    actual_cases = incidence_per_100k
    sensitivity = cancer["sensitivity"]
    specificity = cancer["specificity"]

    tp = actual_cases * sensitivity
    fp = (population - actual_cases) * (1.0 - specificity)
    positives = tp + fp
    ppv = tp / positives if positives > 0 else 0.0
    fp_to_tp = fp / tp if tp > 0 else float("inf")

    return {
        "cancer": cancer["name"],
        "age_group": age_group,
        "incidence_per_100k": incidence_per_100k,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "true_positives": tp,
        "false_positives": fp,
        "total_positives": positives,
        "ppv": ppv,
        "fp_to_tp_ratio": fp_to_tp,
    }


def build_age_specific_table(cancers: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build a table of age-specific PPVs for all cancers and all age groups.

    Incidence rates for sex-specific cancers are expressed per 100,000 total
    population in each age group so that the aggregate PPV matches the main
    simulation.
    """
    pop_both = load_pop("Both")
    pop_male = load_pop("Male")
    pop_female = load_pop("Female")
    sex_pop = {"Both": pop_both, "Male": pop_male, "Female": pop_female}

    rows = []
    for cancer in cancers:
        sex = cancer["sex"]
        site = cancer["site"]
        rate_row = load_incidence_rate(sex, site)
        for age_group in AGE_COLS:
            rate = rate_row[age_group]
            if pd.isna(rate) or rate == "-":
                continue
            total_pop = float(pop_both[age_group])
            sex_p = float(sex_pop[sex][age_group])
            # Convert rate per 100,000 of the sex group to rate per 100,000 total.
            incidence_per_100k_total = float(rate) * sex_p / total_pop if total_pop > 0 else 0.0
            rows.append(compute_age_group_ppv(cancer, age_group, incidence_per_100k_total))
    return pd.DataFrame(rows)


def weighted_ppv_for_distribution(
    cancers: List[Dict[str, Any]], age_distribution: Dict[str, float]
) -> pd.DataFrame:
    """Return aggregate PPV for each cancer under the supplied age distribution.

    age_distribution: {age_group: population_share} where shares sum to 1.
    """
    age_df = build_age_specific_table(cancers)
    rows = []
    for cancer in cancers:
        sub = age_df[age_df["cancer"] == cancer["name"]].copy()
        sub["weight"] = sub["age_group"].map(age_distribution)
        sub = sub[sub["weight"].notna()]
        if sub.empty:
            continue
        tp = (sub["true_positives"] * sub["weight"]).sum()
        fp = (sub["false_positives"] * sub["weight"]).sum()
        positives = tp + fp
        rows.append(
            {
                "cancer": cancer["name"],
                "distribution": "custom",
                "true_positives": tp,
                "false_positives": fp,
                "total_positives": positives,
                "ppv": tp / positives if positives > 0 else 0.0,
                "fp_to_tp_ratio": fp / tp if tp > 0 else float("inf"),
            }
        )
    return pd.DataFrame(rows)


def plot_ppv_by_age(age_df: pd.DataFrame, output_path: Path) -> None:
    """Line plot of PPV by age group for each cancer (adults 20+ only)."""
    from prepare_parameters import ADULT_COLS
    adult_ages = [a for a in ADULT_COLS if a in age_df["age_group"].unique()]
    age_df = age_df[age_df["age_group"].isin(adult_ages)].copy()
    age_df["age_group"] = pd.Categorical(age_df["age_group"], categories=adult_ages, ordered=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    for cancer in sorted(age_df["cancer"].unique()):
        sub = age_df[age_df["cancer"] == cancer].sort_values("age_group")
        ax.plot(sub["age_group"].astype(str), sub["ppv"] * 100.0, marker="o", label=cancer)

    ax.set_xlabel("Age group")
    ax.set_ylabel("Positive predictive value (%)")
    ax.set_title("Age-specific PPV of a blood-based MCED test (sensitivity=0.70, specificity=0.99)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.set_ylim(bottom=0)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Age-stratified PPV analysis")
    parser.add_argument("--params", type=Path, default=Path("parameters.yaml"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()

    with open(args.params, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    args.output.mkdir(parents=True, exist_ok=True)

    cancers = params["cancers"]

    # Age-specific PPV table.
    age_df = build_age_specific_table(cancers)
    age_df = age_df.round(3)
    age_df.to_csv(args.output / "age_specific_ppv.csv", index=False)

    # Weighted PPV using the full 2023 Japanese age distribution (all ages).
    # This matches the per-100,000 total-population rates used by the main simulation.
    pop_both = load_pop("Both")
    total_distribution = {}
    for col in AGE_COLS:
        total_distribution[col] = float(pop_both[col])
    total_pop = sum(total_distribution.values())
    total_distribution = {k: v / total_pop for k, v in total_distribution.items()}

    weighted = weighted_ppv_for_distribution(cancers, total_distribution)
    weighted["distribution"] = "japan_total_2023"
    weighted = weighted.round(3)
    weighted.to_csv(args.output / "weighted_ppv_by_distribution.csv", index=False)

    # Plot.
    plot_ppv_by_age(age_df, args.output / "ppv_by_age.png")

    # Console summary.
    print("=" * 60)
    print("Age-stratified PPV analysis")
    print("=" * 60)
    print(f"Outputs written to: {args.output.resolve()}")
    print("\nAggregate PPV under 2023 Japanese total population age distribution:")
    for _, row in weighted.iterrows():
        print(f"  {row['cancer']}: PPV={row['ppv']*100:.2f}%, FP/TP={row['fp_to_tp_ratio']:.1f}")


if __name__ == "__main__":
    main()
