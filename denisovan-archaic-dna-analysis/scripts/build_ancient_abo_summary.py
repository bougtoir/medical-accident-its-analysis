"""Reproducibly build the ancient ABO-window summary from Iasi et al. (2024).

The ancient ABO-window observations shown in the supporting temporal figure are
extracted directly from the public Neandertal-segment catalogue of Iasi et al.
(2024), rather than curated by hand. The primary source files are distributed on
Dryad (https://doi.org/10.5061/dryad.zw3r228gg) and are not redistributed here;
download them once and pass their paths to this script.

Required source files (Dryad doi:10.5061/dryad.zw3r228gg):
  * Neandertal_segments_matching_references_Shared_map.csv
      (from Neandertal_segments_matching_references_Shared_map.csv.zip)
  * Meta_Data_individuals.csv

Coordinate system. The Iasi et al. catalogue is on GRCh37/hg19, whereas the
primary hmmix analysis in this study is on GRCh38. The ABO gene on GRCh37 is
chr9:136,125,788-136,150,617. The 500-kb interval is positioned relative to the
ABO gene start exactly as in the GRCh38 primary analysis (whose 500-kb window
begins 233,278 bp upstream of the ABO gene start), giving a GRCh37 interval of
chr9:135,892,510-136,392,510.

Extraction rules (documented, deterministic):
  * Restrict to ancient individuals (metadata ``time == 'ancient'``).
  * Use the Neandertal reference-matching proportions computed on all diagnostic
    sites (``Sites_used == 'All_diagnostic_sites'``).
  * An individual has a detected ABO-window segment if at least one Neandertal
    segment overlaps the 500-kb interval. If several overlap, prefer the segment
    that overlaps the ABO gene; otherwise take the longest.
  * ``strict_abo_overlap`` is True when the chosen segment overlaps the ABO gene.
  * ``closest_reference`` is the archaic reference (Altai, Vindija, Chagyrskaya)
    with the largest matching proportion, or ``Tie`` when the maximum is shared.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ABO_CHROM = 9
ABO_GENE_START = 136_125_788
ABO_GENE_END = 136_150_617
GRCH38_WINDOW_OFFSET = 233_278
WINDOW_START = ABO_GENE_START - GRCH38_WINDOW_OFFSET
WINDOW_END = WINDOW_START + 500_000

REFERENCE_COLUMNS = {
    "prop_matching_Altai": "Altai",
    "prop_matching_Vindija33.19": "Vindija",
    "prop_matching_Chagyrskaya": "Chagyrskaya",
}
SOURCE_DOI = "10.5061/dryad.zw3r228gg"
SOURCE_ARTICLE_DOI = "10.1126/science.adq3010"
SEGMENT_COLUMNS = [
    "chrom",
    "pos",
    "pos_end",
    "pos_len",
    "prop_matching_Altai",
    "prop_matching_Vindija33.19",
    "prop_matching_Chagyrskaya",
    "prop_matching_Denisova",
    "all_reads",
    "sample",
    "Sites_used",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iasi-segments",
        type=Path,
        required=True,
        help="Path to Neandertal_segments_matching_references_Shared_map.csv",
    )
    parser.add_argument(
        "--iasi-metadata",
        type=Path,
        required=True,
        help="Path to Meta_Data_individuals.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/ancient_abo_summary.csv"),
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=Path("data/ancient_abo_provenance.json"),
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def closest_reference(row: pd.Series) -> str:
    values = {name: float(row[column]) for column, name in REFERENCE_COLUMNS.items()}
    maximum = max(values.values())
    winners = [name for name, value in values.items() if np.isclose(value, maximum)]
    return winners[0] if len(winners) == 1 else "Tie"


def choose_segment(segments: pd.DataFrame) -> pd.Series:
    overlapping_gene = segments[
        (segments["pos"] < ABO_GENE_END) & (segments["pos_end"] > ABO_GENE_START)
    ]
    candidates = overlapping_gene if not overlapping_gene.empty else segments
    return candidates.loc[candidates["pos_len"].idxmax()]


def main() -> None:
    args = parse_args()
    metadata = pd.read_csv(args.iasi_metadata)
    ancient = metadata[metadata["time"] == "ancient"].copy()

    segments = pd.read_csv(args.iasi_segments, usecols=SEGMENT_COLUMNS)
    segments = segments[
        (segments["chrom"] == ABO_CHROM)
        & (segments["Sites_used"] == "All_diagnostic_sites")
        & (segments["pos"] < WINDOW_END)
        & (segments["pos_end"] > WINDOW_START)
    ]

    records = []
    for individual in sorted(ancient["sample_name"]):
        meta_row = ancient[ancient["sample_name"] == individual].iloc[0]
        age_kya = round(float(meta_row["ML_BP_Mean"]) / 1000.0, 1)
        population = meta_row["population_cluster"]
        region = meta_row["superpopulation"]
        individual_segments = segments[segments["sample"] == individual]
        if individual_segments.empty:
            records.append(
                {
                    "individual": individual,
                    "age_kya": age_kya,
                    "population": population,
                    "region": region,
                    "closest_reference": "None",
                    "altai_proportion": np.nan,
                    "vindija_proportion": np.nan,
                    "chagyrskaya_proportion": np.nan,
                    "denisova_proportion": np.nan,
                    "all_reads": np.nan,
                    "segment_detected": False,
                    "strict_abo_overlap": False,
                    "source_doi": SOURCE_ARTICLE_DOI,
                    "provenance_note": "No Neandertal segment in the ABO 500-kb interval",
                }
            )
            continue
        segment = choose_segment(individual_segments)
        strict = bool(
            (segment["pos"] < ABO_GENE_END) and (segment["pos_end"] > ABO_GENE_START)
        )
        records.append(
            {
                "individual": individual,
                "age_kya": age_kya,
                "population": population,
                "region": region,
                "closest_reference": closest_reference(segment),
                "altai_proportion": round(float(segment["prop_matching_Altai"]), 3),
                "vindija_proportion": round(
                    float(segment["prop_matching_Vindija33.19"]), 3
                ),
                "chagyrskaya_proportion": round(
                    float(segment["prop_matching_Chagyrskaya"]), 3
                ),
                "denisova_proportion": round(
                    float(segment["prop_matching_Denisova"]), 3
                ),
                "all_reads": float(segment["all_reads"]),
                "segment_detected": True,
                "strict_abo_overlap": strict,
                "source_doi": SOURCE_ARTICLE_DOI,
                "provenance_note": "Extracted from public Iasi et al. 2024 segment catalogue; exploratory use only",
            }
        )

    summary = pd.DataFrame(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output, index=False)

    provenance = {
        "source_article_doi": SOURCE_ARTICLE_DOI,
        "source_data_doi": SOURCE_DOI,
        "reference_genome": "GRCh37/hg19",
        "abo_gene_grch37": {"chrom": ABO_CHROM, "start": 136_125_788, "end": ABO_GENE_END},
        "abo_window_grch37": {"chrom": ABO_CHROM, "start": WINDOW_START, "end": WINDOW_END},
        "sites_used": "All_diagnostic_sites",
        "genetic_map": "Shared_map",
        "ancient_individuals_assessed": int(len(summary)),
        "ancient_individuals_with_segment": int(summary["segment_detected"].sum()),
        "ancient_individuals_strict_abo_overlap": int(summary["strict_abo_overlap"].sum()),
        "segments_file": {
            "file_name": args.iasi_segments.name,
            "sha256": sha256(args.iasi_segments),
        },
        "metadata_file": {
            "file_name": args.iasi_metadata.name,
            "sha256": sha256(args.iasi_metadata),
        },
    }
    args.provenance.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(summary)} ancient individuals "
        f"({provenance['ancient_individuals_with_segment']} with an ABO-window segment, "
        f"{provenance['ancient_individuals_strict_abo_overlap']} strict ABO overlap) "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
