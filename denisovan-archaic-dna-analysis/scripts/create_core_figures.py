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
    "EUROPE": "#6b8e23",
    "MIDDLE_EAST": "#cd853f",
    "CENTRAL_SOUTH_ASIA": "#9370db",
    "EAST_ASIA": "#e67e22",
    "AMERICA": "#4682b4",
    "OCEANIA": "#8b0000",
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
    figure, axes = plt.subplots(1, 2, figsize=(16, 7))
    neanderthal = pairs.dropna(subset=["nean_corr"]).copy()
    neanderthal["pair_type"] = np.where(
        neanderthal["same_continent"] == 1, "intra", "inter"
    )
    admixed = neanderthal[neanderthal["any_admixed"] == 1]
    nonadmixed_intra = neanderthal[
        (neanderthal["any_admixed"] == 0)
        & (neanderthal["pair_type"] == "intra")
    ]
    nonadmixed_inter = neanderthal[
        (neanderthal["any_admixed"] == 0)
        & (neanderthal["pair_type"] == "inter")
    ]
    axes[0].scatter(
        nonadmixed_intra["geo_dist_km"] / 1000,
        nonadmixed_intra["nean_corr"],
        alpha=0.35,
        s=18,
        c="#4a90d9",
        label="Same continent",
        zorder=3,
    )
    axes[0].scatter(
        nonadmixed_inter["geo_dist_km"] / 1000,
        nonadmixed_inter["nean_corr"],
        alpha=0.35,
        s=18,
        c="#e74c3c",
        label="Cross-continent",
        zorder=3,
    )
    axes[0].scatter(
        admixed["geo_dist_km"] / 1000,
        admixed["nean_corr"],
        alpha=0.5,
        s=30,
        c="#f39c12",
        marker="^",
        label="Admixed population involved",
        zorder=4,
    )
    predictors = neanderthal[
        ["geo_dist_1000km", "any_admixed", "same_continent", "same_dataset"]
    ].to_numpy()
    design = np.column_stack([np.ones(len(neanderthal)), predictors])
    coefficients = np.linalg.lstsq(
        design, neanderthal["nean_corr"].to_numpy(), rcond=None
    )[0]
    distance_range = np.linspace(0, 22, 100)
    cross_continent = coefficients[0] + coefficients[1] * distance_range
    same_continent = cross_continent + coefficients[3]
    axes[0].plot(
        distance_range,
        cross_continent,
        "k--",
        linewidth=1.2,
        alpha=0.5,
        label="Expanded fit (cross-cont.)",
    )
    axes[0].plot(
        distance_range,
        same_continent,
        "b--",
        linewidth=1.2,
        alpha=0.5,
        label="Expanded fit (same cont.)",
    )
    supported_outliers = neanderthal[
        (neanderthal["nean_resid_z"] > 2)
        & (neanderthal["nean_fdr_pval"] < 0.10)
    ]
    for row in supported_outliers.itertuples():
        axes[0].annotate(
            f"{row.pop1}-{row.pop2}",
            (row.geo_dist_km / 1000, row.nean_corr),
            fontsize=6.5,
            xytext=(5, 5),
            textcoords="offset points",
            arrowprops={"arrowstyle": "-", "color": "gray", "alpha": 0.5},
        )
    axes[0].set_xlabel("Geographic distance (×1,000 km)", fontsize=11)
    axes[0].set_ylabel(
        "Neanderthal segment sharing\n(Pearson correlation)", fontsize=11
    )
    axes[0].set_title(
        "A. Neanderthal DNA sharing vs. distance",
        fontsize=12,
        fontweight="bold",
    )
    axes[0].legend(fontsize=7.5, loc="upper right")
    axes[0].set_xlim(-0.5, 22)
    axes[0].set_ylim(-0.15, 1.05)
    axes[0].grid(True, alpha=0.15)

    denisovan = pairs.dropna(subset=["deni_corr"]).copy()
    denisovan["oceania_involved"] = (
        (denisovan["region1"] == "OCEANIA")
        | (denisovan["region2"] == "OCEANIA")
    )
    denisovan["pair_type"] = np.where(
        denisovan["same_continent"] == 1, "intra", "inter"
    )
    oceania = denisovan[denisovan["oceania_involved"]]
    nonoceania_intra = denisovan[
        (~denisovan["oceania_involved"])
        & (denisovan["pair_type"] == "intra")
    ]
    nonoceania_inter = denisovan[
        (~denisovan["oceania_involved"])
        & (denisovan["pair_type"] == "inter")
    ]
    axes[1].scatter(
        nonoceania_intra["geo_dist_km"] / 1000,
        nonoceania_intra["deni_corr"],
        alpha=0.35,
        s=18,
        c="#4a90d9",
        label="Same continent",
        zorder=3,
    )
    axes[1].scatter(
        nonoceania_inter["geo_dist_km"] / 1000,
        nonoceania_inter["deni_corr"],
        alpha=0.35,
        s=18,
        c="#e74c3c",
        label="Cross-continent",
        zorder=3,
    )
    axes[1].scatter(
        oceania["geo_dist_km"] / 1000,
        oceania["deni_corr"],
        alpha=0.7,
        s=50,
        c="#8e44ad",
        marker="D",
        label="Oceania involved",
        zorder=4,
    )
    axes[1].set_xlabel("Geographic distance (×1,000 km)", fontsize=11)
    axes[1].set_ylabel(
        "Denisovan segment sharing\n(Pearson correlation)", fontsize=11
    )
    axes[1].set_title(
        "B. Denisovan DNA sharing vs. distance",
        fontsize=12,
        fontweight="bold",
    )
    axes[1].legend(fontsize=7.5, loc="upper right")
    axes[1].set_xlim(-0.5, 22)
    axes[1].set_ylim(-0.25, 1.05)
    axes[1].grid(True, alpha=0.15)
    figure.suptitle(
        "Archaic DNA sharing patterns vs. geographic distance",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )
    figure.text(
        0.5,
        -0.02,
        (
            "Data: high-confidence hmmix calls, 1000 Genomes + HGDP, "
            "66 populations, 3,134 individuals | Deduplicated 500-kb profiles; "
            f"QAP distance P = {statistics['nean']['distance_qap_p']:.4f} "
            f"(Neanderthal), {statistics['deni']['distance_qap_p']:.4f} (Denisovan)"
        ),
        ha="center",
        fontsize=7.5,
        color="#888888",
    )
    figure.tight_layout()
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
    figure, axes = plt.subplots(1, 2, figsize=(22, 10))
    for axis, matrix, panel_title, color_map in [
        (axes[0], neanderthal, "Neanderthal DNA sharing", "YlOrRd"),
        (axes[1], denisovan, "Denisovan DNA sharing", "PuRd"),
    ]:
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap=color_map, aspect="auto")
        axis.set_xticks(range(len(populations)))
        axis.set_yticks(range(len(populations)))
        axis.set_xticklabels(populations, rotation=90, fontsize=7)
        axis.set_yticklabels(populations, fontsize=7)
        for position, population in enumerate(populations):
            color = REGION_COLORS.get(regions[population], "black")
            axis.get_xticklabels()[position].set_color(color)
            axis.get_yticklabels()[position].set_color(color)
        axis.set_title(panel_title, fontsize=12, fontweight="bold", pad=10)
        figure.colorbar(
            image, ax=axis, fraction=0.046, pad=0.04, label="Correlation"
        )
    handles = [
        mpatches.Patch(color=color, label=region.replace("_", " ").title())
        for region, color in REGION_COLORS.items()
    ]
    figure.legend(
        handles=handles,
        ncol=6,
        loc="lower center",
        fontsize=9,
        title="Region",
        title_fontsize=10,
        bbox_to_anchor=(0.5, -0.02),
    )
    figure.suptitle(title, fontsize=14, fontweight="bold")
    figure.tight_layout(rect=[0, 0.03, 1, 0.96])
    save_figure(figure, figure_directory, stem)


def sensitivity_figure(pairs: pd.DataFrame, figure_directory: Path) -> None:
    valid = pairs.dropna(subset=["nean_corr"]).copy()
    nonadmixed = valid[valid["any_admixed"] == 0]
    full_r = valid["geo_dist_km"].corr(valid["nean_corr"])
    nonadmixed_r = nonadmixed["geo_dist_km"].corr(nonadmixed["nean_corr"])
    figure, axis = plt.subplots(figsize=(16, 9))
    axis.scatter(
        valid["geo_dist_km"] / 1000,
        valid["nean_corr"],
        alpha=0.15,
        s=8,
        c="gray",
        label="All pairs",
    )
    distance_range = np.linspace(0, 20, 100)
    full_slope, full_intercept = np.polyfit(
        valid["geo_dist_km"] / 1000, valid["nean_corr"], 1
    )
    nonadmixed_slope, nonadmixed_intercept = np.polyfit(
        nonadmixed["geo_dist_km"] / 1000, nonadmixed["nean_corr"], 1
    )
    axis.plot(
        distance_range,
        full_slope * distance_range + full_intercept,
        "b-",
        linewidth=1.5,
        alpha=0.7,
        label=f"All pairs (r={full_r:.3f})",
    )
    axis.plot(
        distance_range,
        nonadmixed_slope * distance_range + nonadmixed_intercept,
        "r--",
        linewidth=1.5,
        alpha=0.7,
        label=f"Excl. admixed (r={nonadmixed_r:.3f})",
    )
    axis.set_xlabel("Geographic distance (×1,000 km)")
    axis.set_ylabel("Neanderthal segment sharing (Pearson r)")
    axis.set_title(
        "Sensitivity analysis: effect of excluding admixed populations"
    )
    axis.legend(fontsize=9)
    axis.grid(True, alpha=0.15)
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
    save_figure(figure, figure_directory, "fig5_window_sensitivity")


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
        "Pairwise archaic DNA segment sharing across 31 key populations",
    )
    heatmap_figure(
        pairs,
        populations,
        args.figure_dir,
        "figS1_full_heatmap",
        "Pairwise archaic-segment profile similarity in all 66 populations",
    )
    sensitivity_figure(pairs, args.figure_dir)
    window_path = args.data_dir / "window_size_sensitivity.csv"
    if window_path.exists():
        window_sensitivity_figure(
            pd.read_csv(window_path), args.figure_dir
        )


if __name__ == "__main__":
    main()
