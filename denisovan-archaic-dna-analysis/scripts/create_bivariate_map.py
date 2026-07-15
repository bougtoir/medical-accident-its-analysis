"""Bivariate global map of per-population archaic-segment coverage.

Both encoded quantities are derived from this study's own population profiles
(``data/population_profiles_500kb.npz``): the mean per-bin frequency of
Neanderthal and of Denisovan segments across the analysed autosomal bins for
each population. Circle area encodes mean Neanderthal coverage and colour
encodes mean Denisovan coverage. Coordinates are the approximate sampling
locations in ``data/population_metadata.csv``.

This figure therefore contains no hand-entered literature values; it is a
descriptive geographic display of the same segment calls used in the pairwise
analysis and is not itself an input to any statistical model.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
FIGURE_DIR = PROJECT_DIR / "figures"


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    profiles = np.load(DATA_DIR / "population_profiles_500kb.npz", allow_pickle=False)
    populations = [str(name) for name in profiles["populations"]]
    coverage = pd.DataFrame(
        {
            "population": populations,
            "neanderthal": profiles["neanderthal"].mean(axis=1),
            "denisovan": profiles["denisovan"].mean(axis=1),
        }
    )
    metadata = pd.read_csv(DATA_DIR / "population_metadata.csv")
    merged = coverage.merge(
        metadata[["population", "region", "latitude", "longitude"]],
        on="population",
        how="inner",
    )

    figure, axis = plt.subplots(figsize=(16, 8))
    axis.set_xlim(-170, 190)
    axis.set_ylim(-60, 85)
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.grid(alpha=0.2, linewidth=0.5)
    axis.axhline(0, color="#bbbbbb", linewidth=0.6)

    sizes = 40 + 6000 * merged["neanderthal"]
    scatter = axis.scatter(
        merged["longitude"],
        merged["latitude"],
        s=sizes,
        c=merged["denisovan"],
        cmap="viridis",
        alpha=0.8,
        edgecolor="black",
        linewidth=0.4,
        zorder=3,
    )
    colorbar = figure.colorbar(scatter, ax=axis, fraction=0.025, pad=0.02)
    colorbar.set_label("Mean Denisovan segment coverage (this study)")

    reference_value = float(np.quantile(merged["neanderthal"], 0.9))
    for fraction, label in [(reference_value, f"Neanderthal ~{reference_value:.3f}")]:
        axis.scatter(
            [],
            [],
            s=40 + 6000 * fraction,
            c="#cccccc",
            edgecolor="black",
            linewidth=0.4,
            label=label,
        )
    axis.legend(
        title="Circle area = mean Neanderthal coverage",
        loc="lower left",
        frameon=True,
        fontsize=8,
        title_fontsize=8,
    )

    axis.set_title(
        "Bivariate global context: per-population archaic-segment coverage",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.01,
        "Both quantities are mean per-bin segment frequencies computed in this "
        "study from hmmix calls (Zenodo:14136628; 1000 Genomes and HGDP); "
        "coordinates are approximate sampling locations.",
        ha="center",
        fontsize=8,
        color="#666666",
    )
    figure.tight_layout(rect=[0, 0.03, 1, 1])
    png_path = FIGURE_DIR / "fig9_bivariate_world_map.png"
    figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    with Image.open(png_path) as image:
        image.convert("RGB").save(
            png_path.with_suffix(".tiff"), compression="tiff_lzw", dpi=(300, 300)
        )
    print(f"Saved: {png_path} ({len(merged)} populations)")


if __name__ == "__main__":
    main()
