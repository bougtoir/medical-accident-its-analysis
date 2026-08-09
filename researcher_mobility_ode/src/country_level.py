#!/usr/bin/env python3
"""
Country-level ODE resolution for major AI/ML research nations.

This script derives each cohort author's most likely country from the
stratified sample works, then re-runs the endogenous ODE for a selected set
of major countries.  It is intended as a finer-grained complement to the
civilisation-level model: it shows, for example, how vulnerable the United
States, China, Japan, or Germany are independent of their broader group.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import ode_model_endogenous as odm
from cohort_extraction import estimate_rates


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results" / "country_level"
CACHE_FILE = BASE_DIR / "data" / "cohort" / "raw_sampled_works.json"

DEFAULT_COUNTRY_CODES = [
    "US", "CN", "GB", "DE", "JP", "IN", "KR", "CA", "FR", "AU",
    "IL", "SG", "IT", "NL", "CH", "ES", "SE", "BR", "RU", "TW",
]


def author_to_country(sample_path):
    """Map author OpenAlex id to the most common country_code in the sample."""
    with open(sample_path, "r", encoding="utf-8") as f:
        works = json.load(f)
    counter = defaultdict(Counter)
    for w in works:
        for auth in w.get("authorships", []):
            raw_id = (auth.get("author") or {}).get("id")
            if not raw_id:
                continue
            aid = raw_id.split("/")[-1]
            seen = set()
            for inst in auth.get("institutions", []):
                cc = inst.get("country_code")
                if cc and cc not in seen:
                    counter[aid][cc] += 1
                    seen.add(cc)
    return {aid: c.most_common(1)[0][0] for aid, c in counter.items()}


def build_country_mapping(codes):
    """Return alpha-2 -> country-name mapping restricted to requested codes."""
    with open(BASE_DIR / "data" / "country_civilization_mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)
    a2g = {}
    name_lookup = {}
    for a3, info in mapping.items():
        a2 = info.get("alpha_2")
        name = info.get("name")
        if a2 and name and a2 in codes:
            a2g[a2] = name
            name_lookup[name] = a2
    return a2g, name_lookup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--country-codes", nargs="+", default=DEFAULT_COUNTRY_CODES,
                        help="ISO-3166-1 alpha-2 codes to model at country level.")
    parser.add_argument("--safety-factor", type=float, default=0.5)
    parser.add_argument("--min-cohort", type=int, default=10,
                        help="Minimum cohort size to include a country.")
    args = parser.parse_args()

    cohort = pd.read_csv(odm.COHORT_DIR / "cohort.csv")
    author_country = author_to_country(CACHE_FILE)

    cohort["origin_country"] = cohort["author_id"].map(author_country)
    cohort = cohort.dropna(subset=["origin_country"])

    a2g, name_lookup = build_country_mapping(args.country_codes)
    cohort = cohort[cohort["origin_country"].isin(a2g)]
    cohort = cohort[cohort["origin_country"].map(cohort["origin_country"].value_counts()) >= args.min_cohort]

    # Rename group to country for the ODE run
    cohort["origin_group"] = cohort["origin_country"].map(a2g)

    if len(cohort) == 0:
        raise ValueError("No cohort authors matched the requested country codes")

    rates = estimate_rates(cohort).set_index("group")
    summary, sens, pnr = odm.run_endogenous_model(
        save=False,
        safety_factor=args.safety_factor,
        cohort_df=cohort,
        rates_df=rates,
        a2g=a2g,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(RESULTS_DIR / "equilibrium_summary.csv", index=False, encoding="utf-8-sig")
    sens.to_csv(RESULTS_DIR / "sensitivity.csv", index=False, encoding="utf-8-sig")
    pnr.to_csv(RESULTS_DIR / "point_of_no_return.csv", index=False, encoding="utf-8-sig")

    print("=== Country-level equilibrium ===")
    print(summary[["group", "T_equilibrium", "M_threshold", "margin_to_threshold_T",
                    "I0", "r", "r_obs", "r_critical"]].to_string(index=False))
    print(f"\nSaved to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
