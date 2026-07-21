"""Rebuild the AHG analysis, figures, and submission files from source data."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-1kg", type=Path, required=True)
    parser.add_argument("--segments-hgdp", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=9_999)
    parser.add_argument("--sensitivity-permutations", type=int, default=999)
    parser.add_argument("--skip-o2-download", action="store_true")
    parser.add_argument(
        "--iasi-segments",
        type=Path,
        default=None,
        help="Optional Iasi et al. 2024 reference-matching segment file; "
        "when given, the ancient ABO-window summary is regenerated from it.",
    )
    parser.add_argument("--iasi-metadata", type=Path, default=None)
    return parser.parse_args()


def run(project_root: Path, arguments: list[str]) -> None:
    command = [sys.executable, *arguments]
    print("+", " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, cwd=project_root, check=True)


def main() -> None:
    args = parse_args()
    if (args.iasi_segments is None) != (args.iasi_metadata is None):
        sys.exit(
            "ERROR: --iasi-segments and --iasi-metadata must both be provided "
            "or both omitted."
        )
    project_root = Path(__file__).resolve().parents[1]
    first = str(args.segments_1kg.resolve())
    second = str(args.segments_hgdp.resolve())
    run(
        project_root,
        [
            "scripts/archaic_sharing_analysis.py",
            "--segments-1kg",
            first,
            "--segments-hgdp",
            second,
            "--output-dir",
            "data",
        ],
    )
    run(
        project_root,
        [
            "scripts/archaic_sharing_corrected.py",
            "--pairwise-input",
            "data/pairwise_sharing.csv",
            "--output-dir",
            "data",
            "--permutations",
            str(args.permutations),
            "--sensitivity-permutations",
            str(args.sensitivity_permutations),
        ],
    )
    run(
        project_root,
        [
            "scripts/archaic_sharing_window_sensitivity.py",
            "--segments-1kg",
            first,
            "--segments-hgdp",
            second,
            "--output",
            "data/window_size_sensitivity.csv",
            "--permutations",
            str(args.sensitivity_permutations),
        ],
    )
    run(
        project_root,
        [
            "scripts/analyze_abo_window.py",
            "--segments-1kg",
            first,
            "--segments-hgdp",
            second,
            "--output-dir",
            "data",
        ],
    )
    if not args.skip_o2_download:
        run(project_root, ["scripts/fetch_o2_frequencies.py"])
    if args.iasi_segments is not None and args.iasi_metadata is not None:
        run(
            project_root,
            [
                "scripts/build_ancient_abo_summary.py",
                "--iasi-segments",
                str(args.iasi_segments.resolve()),
                "--iasi-metadata",
                str(args.iasi_metadata.resolve()),
                "--output",
                "data/ancient_abo_summary.csv",
                "--provenance",
                "data/ancient_abo_provenance.json",
            ],
        )
    run(project_root, ["scripts/create_core_figures.py"])
    run(project_root, ["scripts/create_ajba_figures.py"])
    run(project_root, ["scripts/create_minard_figure.py"])
    run(project_root, ["scripts/create_bivariate_map.py"])
    run(project_root, ["scripts/validate_references.py"])
    run(project_root, ["scripts/create_ajba_submission.py"])


if __name__ == "__main__":
    main()
