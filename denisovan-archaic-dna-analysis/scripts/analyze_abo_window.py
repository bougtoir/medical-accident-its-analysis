"""Reproduce ABO-window summaries from the public hmmix segment files."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ABO_CHROM = "chr9"
ABO_START = 133_233_278
ABO_END = 133_276_024
WINDOW_START = 133_000_000
WINDOW_END = 133_500_000
MIN_PROBABILITY = 0.8
ARCHAIC_REFERENCES = ["Altai", "Vindija", "Chagyrskaya"]
INDIGENOUS_AMERICAS = {"Pima", "Maya", "Colombian"}
ADMIXED_AMERICAS = {"PEL", "MXL", "CLM", "PUR"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-1kg", type=Path, required=True)
    parser.add_argument("--segments-hgdp", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    return parser.parse_args()


def analysis_group(population: str, region: str) -> str:
    if population in INDIGENOUS_AMERICAS:
        return "Indigenous Americas"
    if population in ADMIXED_AMERICAS:
        return "Admixed Americas"
    return {
        "EUROPE": "Europe",
        "MIDDLE_EAST": "Middle East",
        "CENTRAL_SOUTH_ASIA": "Central/South Asia",
        "EAST_ASIA": "East Asia",
        "OCEANIA": "Oceania",
        "AFRICA": "Africa",
        "AMERICA": "Other Americas",
    }.get(region, region.title().replace("_", " "))


def closest_reference(row: pd.Series) -> str:
    values = row[ARCHAIC_REFERENCES].astype(float)
    maximum = values.max()
    winners = values.index[np.isclose(values, maximum)].tolist()
    return winners[0] if len(winners) == 1 else "Tie"


def scan_file(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = [
        "name",
        "haplotype",
        "pop",
        "region",
        "chrom",
        "start",
        "end",
        "mean_prob",
        "ND_type",
        "Altai",
        "Vindija",
        "Denisova",
        "Chagyrskaya",
    ]
    population_rows: list[pd.DataFrame] = []
    window_rows: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, sep="\t", usecols=columns, chunksize=250_000):
        population_rows.append(chunk[["name", "pop", "region"]].drop_duplicates())
        selected = chunk[
            (chunk["chrom"] == ABO_CHROM)
            & (chunk["start"] < WINDOW_END)
            & (chunk["end"] > WINDOW_START)
            & (chunk["mean_prob"] >= MIN_PROBABILITY)
        ].copy()
        if not selected.empty:
            window_rows.append(selected)
    populations = pd.concat(population_rows, ignore_index=True).drop_duplicates()
    window = pd.concat(window_rows, ignore_index=True)
    return populations, window


def population_summary(
    populations: pd.DataFrame, window: pd.DataFrame
) -> pd.DataFrame:
    denominator = (
        populations.groupby(["pop", "region"], as_index=False)["name"]
        .nunique()
        .rename(columns={"name": "n_total"})
    )
    neanderthal = window[window["ND_type"].isin(["Neanderthal", "Both"])].copy()
    neanderthal["strict_overlap"] = (
        (neanderthal["start"] < ABO_END) & (neanderthal["end"] > ABO_START)
    )
    records = []
    for (population, region), group in neanderthal.groupby(["pop", "region"]):
        strict = group[group["strict_overlap"]]
        records.append(
            {
                "pop": population,
                "region": region,
                "n_window_individuals": group["name"].nunique(),
                "n_window_segments": len(group),
                "n_strict_individuals": strict["name"].nunique(),
                "n_strict_segments": len(strict),
            }
        )
    counts = pd.DataFrame.from_records(records)
    summary = denominator.merge(counts, on=["pop", "region"], how="left").fillna(0)
    integer_columns = [
        "n_total",
        "n_window_individuals",
        "n_window_segments",
        "n_strict_individuals",
        "n_strict_segments",
    ]
    summary[integer_columns] = summary[integer_columns].astype(int)
    summary["window_individual_frequency"] = (
        summary["n_window_individuals"] / summary["n_total"]
    )
    summary["strict_individual_frequency"] = (
        summary["n_strict_individuals"] / summary["n_total"]
    )
    summary["analysis_group"] = [
        analysis_group(population, region)
        for population, region in zip(summary["pop"], summary["region"])
    ]
    return summary.sort_values(["analysis_group", "pop"]).reset_index(drop=True)


def segment_summary(window: pd.DataFrame) -> pd.DataFrame:
    segments = window[window["ND_type"].isin(["Neanderthal", "Both"])].copy()
    for column in ARCHAIC_REFERENCES + ["Denisova"]:
        segments[column] = pd.to_numeric(segments[column], errors="coerce")
    segments["closest_reference"] = segments.apply(closest_reference, axis=1)
    segments["strict_overlap"] = (
        (segments["start"] < ABO_END) & (segments["end"] > ABO_START)
    )
    segments["segment_length"] = segments["end"] - segments["start"]
    segments["analysis_group"] = [
        analysis_group(population, region)
        for population, region in zip(segments["pop"], segments["region"])
    ]
    return segments.sort_values(["analysis_group", "pop", "name", "haplotype"])


def grouped_sublineage_summary(segments: pd.DataFrame) -> pd.DataFrame:
    counts = (
        segments.groupby(["analysis_group", "closest_reference"], as_index=False)
        .size()
        .rename(columns={"size": "n_segments"})
    )
    totals = (
        counts.groupby("analysis_group", as_index=False)["n_segments"]
        .sum()
        .rename(columns={"n_segments": "group_total"})
    )
    counts = counts.merge(totals, on="analysis_group")
    counts["proportion"] = counts["n_segments"] / counts["group_total"]
    return counts.sort_values(["analysis_group", "closest_reference"])


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    population_frames = []
    window_frames = []
    for path in [args.segments_1kg, args.segments_hgdp]:
        populations, window = scan_file(path)
        population_frames.append(populations)
        window_frames.append(window)
    populations = pd.concat(population_frames, ignore_index=True).drop_duplicates()
    window = pd.concat(window_frames, ignore_index=True)
    populations_summary = population_summary(populations, window)
    segments = segment_summary(window)
    sublineages = grouped_sublineage_summary(segments)
    denisovan = window[window["ND_type"].isin(["Denisova", "Both"])].copy()
    denisovan["strict_overlap"] = (
        (denisovan["start"] < ABO_END) & (denisovan["end"] > ABO_START)
    )

    populations_summary.to_csv(
        args.output_dir / "abo_population_summary.csv", index=False
    )
    segments.to_csv(args.output_dir / "abo_neanderthal_segments.csv", index=False)
    sublineages.to_csv(args.output_dir / "abo_sublineage_summary.csv", index=False)
    denisovan.to_csv(args.output_dir / "abo_denisovan_segments.csv", index=False)
    print(f"Individuals: {populations['name'].nunique():,}")
    print(f"Populations: {populations['pop'].nunique():,}")
    print(f"Neanderthal/Both segments in 500-kb window: {len(segments):,}")
    print(f"Strict ABO-overlapping segments: {segments['strict_overlap'].sum():,}")
    print(f"Denisovan/Both segments in 500-kb window: {len(denisovan):,}")


if __name__ == "__main__":
    main()
