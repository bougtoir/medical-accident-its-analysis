"""Evaluate whether distance decay is robust to genomic window size."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from archaic_sharing_analysis import (
    build_profiles,
    expand_haplotype_bin_presence,
    make_bin_index,
    pairwise_results,
    population_metadata,
    read_segments,
)
from archaic_sharing_corrected import qap_regression


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-1kg", type=Path, required=True)
    parser.add_argument("--segments-hgdp", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/window_size_sensitivity.csv"))
    parser.add_argument(
        "--window-sizes", type=int, nargs="+", default=[250_000, 500_000, 1_000_000]
    )
    parser.add_argument("--minimum-probability", type=float, default=0.8)
    parser.add_argument("--minimum-population-size", type=int, default=7)
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    all_segments = pd.concat(
        [
            read_segments(args.segments_1kg, "1000 Genomes"),
            read_segments(args.segments_hgdp, "HGDP"),
        ],
        ignore_index=True,
    )
    metadata = population_metadata(all_segments, args.minimum_population_size)
    included = metadata[metadata["included"]]
    populations = included["population"].tolist()
    population_sizes = dict(
        zip(included["population"], included["n_individuals"], strict=True)
    )
    high_confidence = all_segments[
        all_segments["mean_prob"] >= args.minimum_probability
    ]
    ancestry_segments = {
        "Neanderthal": high_confidence[
            high_confidence["ND_type"].isin(["Neanderthal", "Both"])
        ],
        "Denisovan": high_confidence[
            high_confidence["ND_type"].isin(["Denisova", "Both"])
        ],
    }
    rng = np.random.default_rng(args.seed)
    records = []
    for window_size in args.window_sizes:
        _, bin_lookup = make_bin_index(window_size)
        profiles = {}
        for ancestry, segments in ancestry_segments.items():
            presence = expand_haplotype_bin_presence(segments, window_size)
            profiles[ancestry] = build_profiles(
                presence, populations, population_sizes, bin_lookup
            )
        pairs = pairwise_results(
            metadata,
            populations,
            profiles["Neanderthal"],
            profiles["Denisovan"],
            max(10, int(100 * 500_000 / window_size)),
            max(10, int(50 * 500_000 / window_size)),
        )
        pairs["geo_dist_1000km"] = pairs["geo_dist_km"] / 1000
        for response_column, ancestry in [
            ("nean_corr", "Neanderthal"),
            ("deni_corr", "Denisovan"),
        ]:
            valid = pairs.dropna(subset=[response_column])
            if len(valid) != len(pairs):
                raise ValueError(
                    f"{window_size}-bp {ancestry} matrix is incomplete"
                )
            result = qap_regression(
                valid,
                populations,
                response_column,
                ["geo_dist_1000km"],
                args.permutations,
                rng,
            )
            records.append(
                {
                    "window_size_bp": window_size,
                    "ancestry": ancestry,
                    "populations": len(populations),
                    "pairs": len(valid),
                    "raw_distance_r": float(
                        stats.pearsonr(
                            valid["geo_dist_1000km"], valid[response_column]
                        ).statistic
                    ),
                    "distance_qap_beta": result["coefficients"][1],
                    "distance_qap_p_two_sided": result["p_values"][1],
                    "distance_only_r_squared": result["r_squared"],
                    "qap_permutations": args.permutations,
                }
            )
    output = pd.DataFrame(records)
    output.to_csv(args.output, index=False)
    print(output.to_string(index=False))


if __name__ == "__main__":
    main()
