"""Create core and supplementary figures from the dependence-aware analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REGION_COLORS = {
    "EUROPE": "#4c78a8",
    "MIDDLE_EAST": "#f58518",
    "CENTRAL_SOUTH_ASIA": "#b279a2",
    "EAST_ASIA": "#54a24b",
    "AMERICA": "#e45756",
    "OCEANIA": "#72b7b2",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--figure-dir", type=Path, default=Path("figures"))
    return parser.parse_args()


def save_figure(figure: plt.Figure, directory: Path, stem: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    figure.savefig(directory / f"{stem}.png", dpi=300, bbox_inches="tight")
    figure.savefig(
        directory / f"{stem}.tiff",
        dpi=300,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)


def distance_figure(
    pairs: pd.DataFrame,
    statistics: dict[str, object],
    figure_directory: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 6.2), sharex=True)
    for axis, column, prefix, title, color in [
        (
            axes[0],
            "nean_corr",
            "nean",
            "A. Neanderthal profile similarity",
            "#4c78a8",
        ),
        (
            axes[1],
            "deni_corr",
            "deni",
            "B. Denisovan profile similarity",
            "#b279a2",
        ),
    ]:
        valid = pairs.dropna(subset=[column])
        nonadmixed = valid[valid["any_admixed"] == 0]
        admixed = valid[valid["any_admixed"] == 1]
        axis.scatter(
            nonadmixed["geo_dist_km"] / 1000,
            nonadmixed[column],
            s=13,
            alpha=0.27,
            color=color,
            edgecolor="none",
            label="No designated recently admixed population",
        )
        axis.scatter(
            admixed["geo_dist_km"] / 1000,
            admixed[column],
            s=20,
            alpha=0.55,
            color="#f58518",
            marker="^",
            edgecolor="none",
            label="Designated recently admixed population involved",
        )
        slope, intercept = np.polyfit(
            valid["geo_dist_km"] / 1000, valid[column], 1
        )
        distance_range = np.linspace(0, valid["geo_dist_km"].max() / 1000, 200)
        axis.plot(
            distance_range,
            intercept + slope * distance_range,
            color="black",
            linewidth=1.4,
            label="Descriptive distance-only fit",
        )
        values = statistics[prefix]
        axis.text(
            0.03,
            0.04,
            (
                f"Raw r = {values['raw_r']:.3f}\n"
                f"Expanded-model partial r = {values['partial_r']:.3f}\n"
                f"QAP distance P = {values['distance_qap_p']:.4f}"
            ),
            transform=axis.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#cccccc"},
        )
        axis.set_title(title)
        axis.set_xlabel("Great-circle distance (×1,000 km)")
        axis.grid(alpha=0.2)
    axes[0].set_ylabel("Population-level archaic-segment profile similarity (Pearson r)")
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")
    figure.suptitle(
        "Archaic-segment profile similarity declines with geographic distance",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.01,
        (
            "Each point is a dependent population pair. P values use population-label "
            "quadratic assignment permutations, not row-wise tests."
        ),
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=[0, 0.05, 1, 0.95])
    save_figure(figure, figure_directory, "fig1_sharing_vs_distance")


def similarity_matrix(
    pairs: pd.DataFrame, populations: list[str], column: str
) -> np.ndarray:
    index = {population: position for position, population in enumerate(populations)}
    matrix = np.eye(len(populations))
    for first, second, value in pairs[["pop1", "pop2", column]].itertuples(
        index=False, name=None
    ):
        if first not in index or second not in index:
            continue
        first_index = index[first]
        second_index = index[second]
        matrix[first_index, second_index] = value
        matrix[second_index, first_index] = value
    return matrix


def heatmap_figure(
    pairs: pd.DataFrame,
    populations: list[str],
    figure_directory: Path,
    stem: str,
    title: str,
) -> None:
    regions = {}
    for first, second, region_first, region_second in pairs[
        ["pop1", "pop2", "region1", "region2"]
    ].itertuples(index=False, name=None):
        regions[first] = region_first
        regions[second] = region_second
    neanderthal = similarity_matrix(pairs, populations, "nean_corr")
    denisovan = similarity_matrix(pairs, populations, "deni_corr")
    figure, axes = plt.subplots(1, 2, figsize=(14.2, 7.2))
    for axis, matrix, panel_title, color_map in [
        (axes[0], neanderthal, "A. Neanderthal", "YlGnBu"),
        (axes[1], denisovan, "B. Denisovan", "magma"),
    ]:
        image = axis.imshow(matrix, vmin=-0.2, vmax=1, cmap=color_map, aspect="auto")
        axis.set_xticks(range(len(populations)))
        axis.set_yticks(range(len(populations)))
        axis.set_xticklabels(populations, rotation=90, fontsize=5.5)
        axis.set_yticklabels(populations, fontsize=5.5)
        for position, population in enumerate(populations):
            color = REGION_COLORS.get(regions[population], "black")
            axis.get_xticklabels()[position].set_color(color)
            axis.get_yticklabels()[position].set_color(color)
        axis.set_title(panel_title)
        figure.colorbar(image, ax=axis, fraction=0.045, pad=0.03, label="Pearson r")
    handles = [
        mpatches.Patch(color=color, label=region.replace("_", " ").title())
        for region, color in REGION_COLORS.items()
    ]
    figure.legend(
        handles=handles,
        frameon=False,
        ncol=6,
        loc="lower center",
        fontsize=8,
    )
    figure.suptitle(title, fontsize=14, fontweight="bold")
    figure.tight_layout(rect=[0, 0.06, 1, 0.95])
    save_figure(figure, figure_directory, stem)


def sensitivity_figure(sensitivity: pd.DataFrame, figure_directory: Path) -> None:
    subset_order = [
        "all",
        "nonadmixed",
        "zero_distance_excluded",
        "1000_genomes_only",
        "hgdp_only",
        "minimum_n_10",
        "minimum_n_15",
        "minimum_n_20",
        "leave_out_AMR",
        "leave_out_EAS",
        "leave_out_EUR",
        "leave_out_OCE",
        "leave_out_SAS",
        "leave_out_WAS",
    ]
    pearson = sensitivity[
        (sensitivity["metric"] == "Pearson")
        & sensitivity["subset"].isin(subset_order)
    ].copy()
    pearson["subset"] = pd.Categorical(
        pearson["subset"], categories=subset_order, ordered=True
    )
    pearson = pearson.sort_values("subset")
    figure, axis = plt.subplots(figsize=(10.6, 7.4))
    positions = np.arange(len(subset_order))
    offsets = {"Neanderthal": -0.13, "Denisovan": 0.13}
    colors = {"Neanderthal": "#4c78a8", "Denisovan": "#b279a2"}
    for ancestry in ["Neanderthal", "Denisovan"]:
        rows = pearson[pearson["ancestry"] == ancestry].set_index("subset")
        values = [
            rows.loc[subset, "raw_distance_r"] if subset in rows.index else np.nan
            for subset in subset_order
        ]
        axis.scatter(
            values,
            positions + offsets[ancestry],
            s=48,
            color=colors[ancestry],
            label=ancestry,
            zorder=3,
        )
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set_yticks(positions)
    axis.set_yticklabels(
        [subset.replace("_", " ") for subset in subset_order], fontsize=9
    )
    axis.invert_yaxis()
    axis.set_xlabel("Descriptive Pearson correlation with geographic distance")
    axis.set_title(
        "Distance decay is evaluated across population and dataset sensitivities",
        fontsize=13,
        fontweight="bold",
    )
    axis.grid(axis="x", alpha=0.2)
    axis.legend(frameon=False)
    figure.tight_layout()
    save_figure(figure, figure_directory, "fig4_sensitivity_admixed")


def window_sensitivity_figure(
    window_sensitivity: pd.DataFrame, figure_directory: Path
) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 5.4))
    for ancestry, color, marker in [
        ("Neanderthal", "#4c78a8", "o"),
        ("Denisovan", "#b279a2", "s"),
    ]:
        rows = window_sensitivity[
            window_sensitivity["ancestry"] == ancestry
        ].sort_values("window_size_bp")
        axis.plot(
            rows["window_size_bp"] / 1000,
            rows["raw_distance_r"],
            marker=marker,
            color=color,
            linewidth=1.8,
            label=ancestry,
        )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xlabel("Genomic window size (kb)")
    axis.set_ylabel("Descriptive distance correlation")
    axis.set_title(
        "Geographic distance decay across genomic window sizes",
        fontsize=13,
        fontweight="bold",
    )
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    figure.tight_layout()
    save_figure(figure, figure_directory, "figS2_window_sensitivity")


def main() -> None:
    args = parse_args()
    pairs = pd.read_csv(args.data_dir / "pairwise_sharing_corrected.csv")
    statistics = json.loads(
        (args.data_dir / "correction_stats.json").read_text(encoding="utf-8")
    )
    metadata = pd.read_csv(args.data_dir / "population_metadata.csv")
    populations = metadata[metadata["included"]]["population"].tolist()
    representative = [
        population
        for population in [
            "CEU",
            "FIN",
            "GBR",
            "IBS",
            "TSI",
            "Russian",
            "Basque",
            "Sardinian",
            "Bedouin",
            "Druze",
            "Palestinian",
            "PJL",
            "BEB",
            "GIH",
            "STU",
            "Kalash",
            "Burusho",
            "Uygur",
            "CHB",
            "JPT",
            "KHV",
            "CDX",
            "Yakut",
            "Mongolian",
            "Colombian",
            "PEL",
            "Maya",
            "Pima",
            "PapuanHighlands",
            "PapuanSepik",
            "Bougainville",
        ]
        if population in populations
    ]
    distance_figure(pairs, statistics, args.figure_dir)
    heatmap_figure(
        pairs,
        representative,
        args.figure_dir,
        "fig2_sharing_heatmap",
        "Pairwise archaic-segment profile similarity in 31 prespecified populations",
    )
    heatmap_figure(
        pairs,
        populations,
        args.figure_dir,
        "figS1_full_heatmap",
        "Pairwise archaic-segment profile similarity in all 66 populations",
    )
    sensitivity = pd.read_csv(args.data_dir / "sensitivity_analysis.csv")
    sensitivity_figure(sensitivity, args.figure_dir)
    window_path = args.data_dir / "window_size_sensitivity.csv"
    if window_path.exists():
        window_sensitivity_figure(
            pd.read_csv(window_path), args.figure_dir
        )


if __name__ == "__main__":
    main()
