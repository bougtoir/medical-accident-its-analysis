"""Fetch rs41302905 population frequencies and add published Solomon Island data."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import pandas as pd


ENSEMBL_URL = "https://rest.ensembl.org/variation/human/rs41302905?pops=1"
SOLOMON_ROWS = [
    {
        "population": "Munda",
        "group": "Solomon Islands",
        "frequency": 0.051,
        "sample_size": 39,
        "source": "Ohashi et al. 2006",
        "source_doi": "10.1007/s10038-006-0375-8",
    },
    {
        "population": "Paradise",
        "group": "Solomon Islands",
        "frequency": 0.163,
        "sample_size": 46,
        "source": "Ohashi et al. 2006",
        "source_doi": "10.1007/s10038-006-0375-8",
    },
    {
        "population": "Rawaki",
        "group": "Solomon Islands",
        "frequency": 0.141,
        "sample_size": 46,
        "source": "Ohashi et al. 2006",
        "source_doi": "10.1007/s10038-006-0375-8",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("data/o2_frequency_summary.csv")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request = urllib.request.Request(
        ENSEMBL_URL, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows = []
    for population in payload["populations"]:
        name = population["population"]
        if not name.startswith("1000GENOMES:phase_3:"):
            continue
        if population["allele"] != "T":
            continue
        code = name.rsplit(":", 1)[-1]
        if code in {"ALL", "AFR", "AMR", "EAS", "EUR", "SAS"}:
            continue
        rows.append(
            {
                "population": code,
                "group": "1000 Genomes Phase 3",
                "frequency": population["frequency"],
                "sample_size": "",
                "source": "Ensembl Variation",
                "source_doi": "",
            }
        )
    output = pd.DataFrame(SOLOMON_ROWS + sorted(rows, key=lambda row: row["population"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(f"Saved {len(output)} population-frequency rows to {args.output}")


if __name__ == "__main__":
    main()
