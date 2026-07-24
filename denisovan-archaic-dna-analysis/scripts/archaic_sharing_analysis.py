"""Build deduplicated population archaic-segment profiles and pairwise similarities."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from archaic_sharing_common import (
    ADMIXED_EUR_FRAC,
    CHROM_SIZES,
    CONTINENT_MAP,
    POP_COORDS,
    haversine,
)


SEGMENT_COLUMNS = [
    "name",
    "haplotype",
    "pop",
    "region",
    "chrom",
    "start",
    "end",
    "mean_prob",
    "ND_type",
]
ANALYSIS_RELEASE = "ajba-critical-revision-2026-07"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-1kg", type=Path, required=True)
    parser.add_argument("--segments-hgdp", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--bin-size", type=int, default=500_000)
    parser.add_argument("--min-probability", type=float, default=0.8)
    parser.add_argument("--min-population-size", type=int, default=7)
    parser.add_argument("--min-neanderthal-bins", type=int, default=100)
    parser.add_argument("--min-denisovan-bins", type=int, default=50)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def code_commit(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def read_segments(path: Path, dataset: str) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t", usecols=SEGMENT_COLUMNS)
    frame["dataset"] = dataset
    return frame


def make_bin_index(bin_size: int) -> tuple[list[tuple[str, int]], dict[tuple[str, int], int]]:
    labels = []
    for chromosome in sorted(CHROM_SIZES, key=lambda value: int(value.removeprefix("chr"))):
        for bin_number in range(CHROM_SIZES[chromosome] // bin_size + 1):
            labels.append((chromosome, bin_number))
    return labels, {label: index for index, label in enumerate(labels)}


def expand_haplotype_bin_presence(
    segments: pd.DataFrame, bin_size: int
) -> pd.DataFrame:
    pieces = []
    columns = ["name", "haplotype", "pop", "chrom", "bin_number"]
    for chromosome, chromosome_segments in segments.groupby("chrom", sort=False):
        if chromosome not in CHROM_SIZES:
            continue
        starts = (chromosome_segments["start"].to_numpy(dtype=np.int64) // bin_size)
        ends = (chromosome_segments["end"].to_numpy(dtype=np.int64) // bin_size)
        ends = np.minimum(ends, CHROM_SIZES[chromosome] // bin_size)
        counts = ends - starts + 1
        valid = counts > 0
        chromosome_segments = chromosome_segments.loc[valid]
        starts = starts[valid]
        counts = counts[valid]
        repeated_positions = np.repeat(np.arange(len(chromosome_segments)), counts)
        group_starts = np.repeat(np.cumsum(counts) - counts, counts)
        offsets = np.arange(counts.sum()) - group_starts
        repeated = chromosome_segments[
            ["name", "haplotype", "pop", "chrom"]
        ].iloc[repeated_positions].reset_index(drop=True)
        repeated["bin_number"] = np.repeat(starts, counts) + offsets
        pieces.append(repeated)
    if not pieces:
        return pd.DataFrame(columns=columns)
    expanded = pd.concat(pieces, ignore_index=True)
    return expanded.drop_duplicates(columns).reset_index(drop=True)


def build_profiles(
    presence: pd.DataFrame,
    populations: list[str],
    population_sizes: dict[str, int],
    bin_lookup: dict[tuple[str, int], int],
) -> np.ndarray:
    profiles = np.zeros((len(populations), len(bin_lookup)), dtype=np.float32)
    population_lookup = {
        population: index for index, population in enumerate(populations)
    }
    counts = (
        presence.groupby(["pop", "chrom", "bin_number"], sort=False)
        .size()
        .rename("haplotypes")
        .reset_index()
    )
    for population, chromosome, bin_number, haplotypes in counts.itertuples(
        index=False, name=None
    ):
        if population not in population_lookup:
            continue
        bin_index = bin_lookup[(chromosome, int(bin_number))]
        denominator = 2 * population_sizes[population]
        profiles[population_lookup[population], bin_index] = haplotypes / denominator
    if np.nanmax(profiles) > 1:
        raise ValueError("A population-bin frequency exceeded 1 after deduplication")
    return profiles


def pearson_union(first: np.ndarray, second: np.ndarray, minimum_bins: int) -> tuple[float, int]:
    mask = (first > 0) | (second > 0)
    n_bins = int(mask.sum())
    if n_bins <= minimum_bins:
        return np.nan, n_bins
    first_masked = first[mask]
    second_masked = second[mask]
    if np.std(first_masked) == 0 or np.std(second_masked) == 0:
        return np.nan, n_bins
    return float(np.corrcoef(first_masked, second_masked)[0, 1]), n_bins


def spearman_union(first: np.ndarray, second: np.ndarray, minimum_bins: int) -> float:
    mask = (first > 0) | (second > 0)
    if int(mask.sum()) <= minimum_bins:
        return np.nan
    return float(stats.spearmanr(first[mask], second[mask]).statistic)


def cosine_similarity(first: np.ndarray, second: np.ndarray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    return float(np.dot(first, second) / denominator) if denominator else np.nan


def pearson_full(first: np.ndarray, second: np.ndarray) -> float:
    if np.std(first) == 0 or np.std(second) == 0:
        return np.nan
    return float(np.corrcoef(first, second)[0, 1])


def jaccard_presence(first: np.ndarray, second: np.ndarray) -> float:
    first_present = first > 0
    second_present = second > 0
    union = first_present | second_present
    if not union.any():
        return np.nan
    return float((first_present & second_present).sum() / union.sum())


def population_metadata(
    all_segments: pd.DataFrame, minimum_size: int
) -> pd.DataFrame:
    individuals = all_segments[["name", "pop", "region", "dataset"]].drop_duplicates()
    records = []
    for population, group in individuals.groupby("pop", sort=True):
        datasets = "+".join(sorted(group["dataset"].unique()))
        region_values = sorted(group["region"].unique())
        if len(region_values) != 1:
            raise ValueError(f"Inconsistent region labels for {population}: {region_values}")
        coordinate = POP_COORDS.get(population)
        records.append(
            {
                "population": population,
                "region": region_values[0],
                "continent": CONTINENT_MAP.get(population, "UNK"),
                "dataset": datasets,
                "n_individuals": group["name"].nunique(),
                "latitude": coordinate[0] if coordinate else np.nan,
                "longitude": coordinate[1] if coordinate else np.nan,
                "coordinate_source": "analysis metadata; verify against source sampling documentation",
                "eur_admixture_fraction": ADMIXED_EUR_FRAC.get(population, 0.0),
                "recent_admixture_flag": int(population in ADMIXED_EUR_FRAC),
            }
        )
    metadata = pd.DataFrame(records)
    metadata["included"] = (
        (metadata["n_individuals"] >= minimum_size)
        & metadata["latitude"].notna()
        & metadata["longitude"].notna()
        & (metadata["continent"] != "UNK")
    )
    return metadata


def pairwise_results(
    metadata: pd.DataFrame,
    populations: list[str],
    neanderthal_profiles: np.ndarray,
    denisovan_profiles: np.ndarray,
    minimum_neanderthal_bins: int,
    minimum_denisovan_bins: int,
) -> pd.DataFrame:
    metadata_index = metadata.set_index("population")
    population_index = {
        population: position for position, population in enumerate(populations)
    }
    records = []
    for first_population, second_population in combinations(populations, 2):
        first = metadata_index.loc[first_population]
        second = metadata_index.loc[second_population]
        first_index = population_index[first_population]
        second_index = population_index[second_population]
        neanderthal_pearson, neanderthal_bins = pearson_union(
            neanderthal_profiles[first_index],
            neanderthal_profiles[second_index],
            minimum_neanderthal_bins,
        )
        denisovan_pearson, denisovan_bins = pearson_union(
            denisovan_profiles[first_index],
            denisovan_profiles[second_index],
            minimum_denisovan_bins,
        )
        records.append(
            {
                "pop1": first_population,
                "pop2": second_population,
                "region1": first["region"],
                "region2": second["region"],
                "continent1": first["continent"],
                "continent2": second["continent"],
                "dataset1": first["dataset"],
                "dataset2": second["dataset"],
                "n1": int(first["n_individuals"]),
                "n2": int(second["n_individuals"]),
                "nean_corr": neanderthal_pearson,
                "deni_corr": denisovan_pearson,
                "nean_spearman": spearman_union(
                    neanderthal_profiles[first_index],
                    neanderthal_profiles[second_index],
                    minimum_neanderthal_bins,
                ),
                "deni_spearman": spearman_union(
                    denisovan_profiles[first_index],
                    denisovan_profiles[second_index],
                    minimum_denisovan_bins,
                ),
                "nean_cosine": cosine_similarity(
                    neanderthal_profiles[first_index],
                    neanderthal_profiles[second_index],
                ),
                "deni_cosine": cosine_similarity(
                    denisovan_profiles[first_index],
                    denisovan_profiles[second_index],
                ),
                "nean_full_corr": pearson_full(
                    neanderthal_profiles[first_index],
                    neanderthal_profiles[second_index],
                ),
                "deni_full_corr": pearson_full(
                    denisovan_profiles[first_index],
                    denisovan_profiles[second_index],
                ),
                "nean_jaccard": jaccard_presence(
                    neanderthal_profiles[first_index],
                    neanderthal_profiles[second_index],
                ),
                "deni_jaccard": jaccard_presence(
                    denisovan_profiles[first_index],
                    denisovan_profiles[second_index],
                ),
                "nean_nonzero_union_bins": neanderthal_bins,
                "deni_nonzero_union_bins": denisovan_bins,
                "geo_dist_km": haversine(
                    float(first["latitude"]),
                    float(first["longitude"]),
                    float(second["latitude"]),
                    float(second["longitude"]),
                ),
                "same_dataset": int(first["dataset"] == second["dataset"]),
                "same_continent": int(first["continent"] == second["continent"]),
                "any_admixed": int(
                    bool(first["recent_admixture_flag"])
                    or bool(second["recent_admixture_flag"])
                ),
                "max_admix_eur": max(
                    float(first["eur_admixture_fraction"]),
                    float(second["eur_admixture_fraction"]),
                ),
            }
        )
    return pd.DataFrame(records)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_frames = [
        read_segments(args.segments_1kg, "1000 Genomes"),
        read_segments(args.segments_hgdp, "HGDP"),
    ]
    all_segments = pd.concat(source_frames, ignore_index=True)
    metadata = population_metadata(all_segments, args.min_population_size)
    included = metadata[metadata["included"]].copy()
    populations = included["population"].tolist()
    population_sizes = dict(
        zip(included["population"], included["n_individuals"], strict=True)
    )
    high_confidence = all_segments[
        all_segments["mean_prob"] >= args.min_probability
    ].copy()
    neanderthal = high_confidence[
        high_confidence["ND_type"].isin(["Neanderthal", "Both"])
    ]
    denisovan = high_confidence[
        high_confidence["ND_type"].isin(["Denisova", "Both"])
    ]
    bin_labels, bin_lookup = make_bin_index(args.bin_size)
    neanderthal_presence = expand_haplotype_bin_presence(
        neanderthal, args.bin_size
    )
    denisovan_presence = expand_haplotype_bin_presence(denisovan, args.bin_size)
    neanderthal_profiles = build_profiles(
        neanderthal_presence, populations, population_sizes, bin_lookup
    )
    denisovan_profiles = build_profiles(
        denisovan_presence, populations, population_sizes, bin_lookup
    )
    pairs = pairwise_results(
        metadata,
        populations,
        neanderthal_profiles,
        denisovan_profiles,
        args.min_neanderthal_bins,
        args.min_denisovan_bins,
    )
    metadata.to_csv(args.output_dir / "population_metadata.csv", index=False)
    pairs.to_csv(args.output_dir / "pairwise_sharing.csv", index=False)
    np.savez_compressed(
        args.output_dir / "population_profiles_500kb.npz",
        populations=np.asarray(populations),
        chromosomes=np.asarray([label[0] for label in bin_labels]),
        bin_numbers=np.asarray([label[1] for label in bin_labels], dtype=np.int32),
        neanderthal=neanderthal_profiles,
        denisovan=denisovan_profiles,
    )
    quality = pd.DataFrame(
        [
            {
                "ancestry": "Neanderthal",
                "maximum_frequency": float(neanderthal_profiles.max()),
                "bins_over_one": int((neanderthal_profiles > 1).sum()),
                "nonzero_population_bins": int((neanderthal_profiles > 0).sum()),
            },
            {
                "ancestry": "Denisovan",
                "maximum_frequency": float(denisovan_profiles.max()),
                "bins_over_one": int((denisovan_profiles > 1).sum()),
                "nonzero_population_bins": int((denisovan_profiles > 0).sum()),
            },
        ]
    )
    quality.to_csv(args.output_dir / "profile_quality_checks.csv", index=False)
    provenance = {
        "analysis_release": ANALYSIS_RELEASE,
        "analysis_code_commit": code_commit(Path(__file__).resolve().parents[1]),
        "segments_1kg": {
            "file_name": args.segments_1kg.name,
            "sha256": sha256(args.segments_1kg),
        },
        "segments_hgdp": {
            "file_name": args.segments_hgdp.name,
            "sha256": sha256(args.segments_hgdp),
        },
        "minimum_probability": args.min_probability,
        "minimum_population_size": args.min_population_size,
        "bin_size": args.bin_size,
        "individuals": int(
            all_segments[["dataset", "name"]].drop_duplicates().shape[0]
        ),
        "included_populations": len(populations),
        "population_pairs": len(pairs),
        "frequency_definition": (
            "unique individual-haplotype presence per ancestry type and genomic bin, "
            "divided by twice the number of sampled individuals"
        ),
    }
    (args.output_dir / "analysis_provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(provenance, indent=2))
    print(quality.to_string(index=False))


if __name__ == "__main__":
    main()
