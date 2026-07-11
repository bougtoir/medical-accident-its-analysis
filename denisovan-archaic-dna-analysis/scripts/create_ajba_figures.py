"""Create cautious, data-traceable ABO figures for the AJBA package."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont


DATA_DIR = Path("data")
FIGURE_DIR = Path("figures")
ABO_START = 133_233_278
ABO_END = 133_276_024
WINDOW_START = 133_000_000
WINDOW_END = 133_500_000
COLORS = {
    "Altai": "#2f91df",
    "Vindija": "#ff9800",
    "Chagyrskaya": "#4caf50",
    "Tie": "#9e9e9e",
    "Unresolved": "#6f42c1",
    "None": "#c7c7c7",
}


def save_figure(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    figure.savefig(
        FIGURE_DIR / f"{stem}.tiff",
        dpi=300,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)


def create_figure_3() -> None:
    figure, axis = plt.subplots(figsize=(13.2, 6.8))
    axis.set_xlim(72, 0)
    axis.set_ylim(0, 8)
    axis.set_xlabel("Approximate time before present (thousand years)")
    axis.set_yticks([])
    axis.grid(axis="x", alpha=0.2)
    streams = [
        ("African source populations", 6.6, 72, 48, "#78909c"),
        ("West Eurasian branch", 5.3, 55, 0, "#ef6c00"),
        ("East Asian branch", 4.0, 52, 0, "#1565c0"),
        ("South Asian branch", 2.8, 52, 0, "#7e57c2"),
        ("Sahul/Oceanian branch", 1.6, 50, 0, "#8d3c2e"),
        ("First American branch", 0.5, 25, 0, "#2e7d32"),
    ]
    for label, y, start, end, color in streams:
        axis.plot([start, end], [y, y], color=color, linewidth=12, alpha=0.72)
        axis.text(end + 0.5 if end else 1, y + 0.18, label, color=color, fontsize=9)
    add_arrow(axis, (52, 6.6), (50, 5.3), "#ef6c00")
    add_arrow(axis, (52, 6.6), (48, 4.0), "#1565c0")
    add_arrow(axis, (52, 6.6), (48, 2.8), "#7e57c2")
    add_arrow(axis, (48, 2.8), (45, 1.6), "#8d3c2e")
    add_arrow(axis, (25, 4.0), (22, 0.5), "#2e7d32")
    axis.axvspan(55, 45, ymin=0.58, ymax=0.88, color="#ffcc80", alpha=0.24)
    axis.text(
        50,
        7.25,
        "Major Neanderthal admixture interval",
        ha="center",
        fontsize=10,
        color="#e65100",
    )
    axis.scatter(
        [47, 42, 35],
        [3.5, 2.25, 1.1],
        marker="*",
        s=180,
        color="#6a1b9a",
        edgecolor="white",
        linewidth=0.8,
        zorder=5,
    )
    axis.text(
        39,
        3.15,
        "Multiple Denisovan-related introgression events\nare represented schematically",
        ha="center",
        fontsize=9,
        color="#6a1b9a",
    )
    axis.axvline(15, color="#455a64", linestyle="--", linewidth=1.2)
    axis.text(15, 7.1, "Peopling of the Americas\nby ~15 kya", ha="center", fontsize=9)
    axis.text(
        2,
        7.7,
        "Schematic context for human dispersal and archaic introgression",
        ha="right",
        va="top",
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.015,
        "Line widths and branch positions are illustrative; the diagram is not a quantitative migration estimate.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=[0, 0.04, 1, 1])
    save_figure(figure, "fig3_minard_migration")


def create_figure_5() -> None:
    summary = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")
    segments = pd.read_csv(DATA_DIR / "abo_neanderthal_segments.csv")
    group_order = [
        "Europe",
        "Middle East",
        "Central/South Asia",
        "East Asia",
        "Oceania",
        "Admixed Americas",
        "Indigenous Americas",
    ]
    reference_order = ["Vindija", "Altai", "Chagyrskaya", "Tie"]
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 6.6), gridspec_kw={"width_ratios": [1.25, 1]})
    left = axes[0]
    cumulative = np.zeros(len(group_order))
    totals = []
    for reference in reference_order:
        values = []
        for group in group_order:
            rows = summary[
                (summary["analysis_group"] == group)
                & (summary["closest_reference"] == reference)
            ]
            values.append(float(rows["proportion"].iloc[0]) if len(rows) else 0.0)
            if reference == reference_order[0]:
                group_rows = summary[summary["analysis_group"] == group]
                totals.append(
                    int(group_rows["group_total"].iloc[0]) if len(group_rows) else 0
                )
        left.barh(
            group_order,
            np.asarray(values) * 100,
            left=cumulative,
            color=COLORS[reference],
            label=reference,
            edgecolor="white",
            linewidth=0.5,
        )
        cumulative += np.asarray(values) * 100
    for index, total in enumerate(totals):
        left.text(101, index, f"n={total}", va="center", fontsize=9)
    left.set_xlim(0, 112)
    left.set_xlabel("Segment composition (%)")
    left.set_title("A. Closest-reference composition in the 500-kb interval")
    left.legend(
        frameon=False,
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
    )
    left.grid(axis="x", alpha=0.2)
    left.invert_yaxis()

    right = axes[1]
    highlighted = segments[
        segments["pop"].isin(["Bougainville", "Maya", "Pima"])
    ].copy()
    highlighted["label"] = highlighted["name"] + " (" + highlighted["pop"] + ")"
    highlighted = highlighted.sort_values(["pop", "name"])
    y_positions = np.arange(len(highlighted))[::-1]
    right.axvspan(
        ABO_START / 1e6,
        ABO_END / 1e6,
        color="#ffd54f",
        alpha=0.55,
        label="ABO gene",
    )
    for y, (_, row) in zip(y_positions, highlighted.iterrows()):
        color = "#d62728" if bool(row["strict_overlap"]) else "#6f42c1"
        right.plot(
            [max(row["start"], WINDOW_START) / 1e6, min(row["end"], WINDOW_END) / 1e6],
            [y, y],
            linewidth=10,
            solid_capstyle="butt",
            color=color,
        )
        right.text(
            min(row["end"], WINDOW_END) / 1e6 + 0.006,
            y,
            row["closest_reference"],
            va="center",
            fontsize=8,
        )
    right.set_yticks(y_positions, highlighted["label"])
    right.set_xlim(WINDOW_START / 1e6, WINDOW_END / 1e6)
    right.set_xlabel("Chromosome 9 position (Mb; GRCh38)")
    right.set_title("B. Traceable segments in selected HGDP individuals")
    right.grid(axis="x", alpha=0.2)
    right.legend(
        handles=[
            plt.Line2D([0], [0], color="#d62728", lw=8, label="Overlaps ABO"),
            plt.Line2D([0], [0], color="#6f42c1", lw=8, label="Window only"),
            plt.Rectangle((0, 0), 1, 1, color="#ffd54f", alpha=0.55, label="ABO gene"),
        ],
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
    )
    figure.suptitle(
        "Neanderthal-like segments in the ABO-centered interval",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.01,
        "Ties are retained rather than forced to a single reference. The Maya segment is within the 500-kb interval but does not overlap ABO.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=[0, 0.1, 1, 0.94])
    save_figure(figure, "fig5_abo_sublineage")


def create_figure_6() -> None:
    o2 = pd.read_csv(DATA_DIR / "o2_frequency_summary.csv")
    population = pd.read_csv(DATA_DIR / "abo_population_summary.csv")
    selected_o2 = o2[
        o2["population"].isin(
            [
                "Munda",
                "Paradise",
                "Rawaki",
                "GBR",
                "FIN",
                "TSI",
                "IBS",
                "PUR",
                "PEL",
                "MXL",
                "CEU",
            ]
        )
    ].sort_values("frequency", ascending=True)
    selected_window = population[
        population["pop"].isin(
            [
                "PapuanSepik",
                "PapuanHighlands",
                "Bougainville",
                "JPT",
                "GBR",
                "PEL",
                "Pima",
                "Maya",
                "Colombian",
            ]
        )
    ].sort_values("window_individual_frequency", ascending=True)
    display_names = {
        "GBR": "British",
        "PUR": "Puerto Rican",
        "TSI": "Toscani",
        "FIN": "Finnish",
        "IBS": "Iberian",
        "PEL": "Peruvian",
        "MXL": "Mexican ancestry",
        "CEU": "Utah European",
        "JPT": "Japanese",
        "PapuanSepik": "Papuan Sepik",
        "PapuanHighlands": "Papuan Highlands",
    }
    selected_o2 = selected_o2.assign(
        display_population=selected_o2["population"].map(display_names).fillna(
            selected_o2["population"]
        )
    )
    selected_window = selected_window.assign(
        display_population=selected_window["pop"].map(display_names).fillna(
            selected_window["pop"]
        )
    )
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 6.8))
    source_colors = {
        "Solomon Islands": "#7b1fa2",
        "1000 Genomes Phase 3": "#1976d2",
    }
    axes[0].barh(
        selected_o2["display_population"],
        selected_o2["frequency"] * 100,
        color=[source_colors[group] for group in selected_o2["group"]],
    )
    for index, row in enumerate(selected_o2.itertuples()):
        axes[0].text(row.frequency * 100 + 0.25, index, f"{row.frequency * 100:.1f}%", va="center", fontsize=8)
    axes[0].set_xlabel("T-allele frequency (%)")
    axes[0].set_title("A. O2-defining rs41302905 T allele")
    axes[0].grid(axis="x", alpha=0.2)
    axes[0].legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color=color, label=label)
            for label, color in source_colors.items()
        ],
        frameon=False,
        loc="lower right",
    )

    axes[1].barh(
        selected_window["display_population"],
        selected_window["window_individual_frequency"] * 100,
        color="#d95f02",
    )
    for index, row in enumerate(selected_window.itertuples()):
        label = f"{row.n_window_individuals}/{row.n_total}"
        axes[1].text(
            row.window_individual_frequency * 100 + 1,
            index,
            label,
            va="center",
            fontsize=8,
        )
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel("Individuals carrying a segment (%)")
    axes[1].set_title("B. Neanderthal-like segments in the 500-kb ABO interval")
    axes[1].grid(axis="x", alpha=0.2)
    figure.suptitle(
        "ABO allele and introgression-window summaries use different data sources",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.01,
        "Panel A: Ensembl/1000 Genomes and Ohashi et al. (2006). Panel B: hmmix segment calls; labels show carriers/individuals.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=[0, 0.04, 1, 0.94])
    save_figure(figure, "fig6_o2_introgression")


def add_box(
    axis: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    facecolor: str,
    edgecolor: str,
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.8,
    )
    axis.add_patch(box)
    axis.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=10,
        wrap=True,
    )


def add_arrow(
    axis: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    dashed: bool = False,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        color=color,
        linewidth=2,
        linestyle="--" if dashed else "-",
    )
    axis.add_patch(arrow)


def create_figure_7() -> None:
    population = pd.read_csv(DATA_DIR / "abo_population_summary.csv")
    segments = pd.read_csv(DATA_DIR / "abo_neanderthal_segments.csv")
    indigenous_population = population[
        population["analysis_group"] == "Indigenous Americas"
    ]
    indigenous_segments = segments[
        segments["analysis_group"] == "Indigenous Americas"
    ]
    n_total = int(indigenous_population["n_total"].sum())
    n_carriers = int(indigenous_population["n_window_individuals"].sum())
    n_strict = int(indigenous_population["n_strict_individuals"].sum())
    n_vindija = int(
        (indigenous_segments["closest_reference"] == "Vindija").sum()
    )
    figure, axis = plt.subplots(figsize=(12.5, 7.0))
    axis.set_xlim(0, 12)
    axis.set_ylim(0, 8)
    axis.axis("off")
    add_box(axis, (4.4, 6.7), 3.2, 0.75, "Out-of-Africa populations\nwith Neanderthal ancestry", "#eceff1", "#455a64")
    add_box(axis, (1.0, 4.9), 3.1, 0.85, "West Eurasian ancestry\n(Vindija-related signal common)", "#fff3e0", "#ef6c00")
    add_box(axis, (7.9, 4.9), 3.1, 0.85, "East Asian ancestry\n(Altai/Chagyrskaya-related signal common)", "#e3f2fd", "#1565c0")
    add_box(axis, (1.8, 2.8), 3.2, 0.95, "Ancient North Eurasian ancestry\n~35% contribution in a published model", "#fff8e1", "#f9a825")
    add_box(axis, (7.0, 2.8), 3.2, 0.95, "Northeast Asian ancestry\n~65% contribution in the same model", "#e8f5e9", "#2e7d32")
    observation = (
        "Present-day Indigenous HGDP sample\n"
        f"{n_carriers}/{n_total} window carriers; {n_strict} overlaps ABO\n"
        f"{n_vindija}/{len(indigenous_segments)} segments Vindija-closest"
    )
    add_box(axis, (3.65, 0.65), 4.7, 1.15, observation, "#fce4ec", "#c2185b")
    add_arrow(axis, (5.2, 6.7), (3.0, 5.75), "#ef6c00")
    add_arrow(axis, (6.8, 6.7), (9.0, 5.75), "#1565c0")
    add_arrow(axis, (2.6, 4.9), (3.2, 3.75), "#f9a825")
    add_arrow(axis, (9.4, 4.9), (8.6, 3.75), "#2e7d32")
    add_arrow(axis, (3.7, 2.8), (5.0, 1.8), "#c2185b", dashed=True)
    add_arrow(axis, (8.3, 2.8), (7.0, 1.8), "#c2185b", dashed=True)
    axis.text(
        6,
        7.75,
        "Ancient North Eurasian pathway hypothesis for an ABO-window observation",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
    )
    axis.text(
        6,
        0.18,
        "Dashed arrows indicate a hypothesis, not a migration inference. The observed sample is too small for regional estimation.",
        ha="center",
        fontsize=10,
        color="#8e244d",
    )
    figure.tight_layout()
    save_figure(figure, "fig7_ane_model")


def create_figure_8() -> None:
    ancient = pd.read_csv(DATA_DIR / "ancient_abo_summary.csv")
    modern = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")
    figure, axes = plt.subplots(1, 2, figsize=(13.2, 6.8))
    detected = ancient[ancient["segment_detected"]].copy()
    undetected = ancient[~ancient["segment_detected"]].copy()
    detected["maximum_proportion"] = detected[
        ["altai_proportion", "vindija_proportion", "chagyrskaya_proportion"]
    ].max(axis=1)
    detected["maximum_proportion"] = detected["maximum_proportion"].fillna(0.55)
    for reference, group in detected.groupby("closest_reference"):
        axes[0].scatter(
            group["age_kya"],
            group["maximum_proportion"],
            color=COLORS.get(reference, COLORS["Unresolved"]),
            s=70,
            label=reference,
            edgecolor="black",
            linewidth=0.4,
        )
        for row in group.itertuples():
            axes[0].annotate(
                row.individual,
                (row.age_kya, row.maximum_proportion),
                xytext=(3, 5),
                textcoords="offset points",
                fontsize=8,
            )
    axes[0].scatter(
        undetected["age_kya"],
        np.full(len(undetected), 0.04),
        marker="x",
        color=COLORS["None"],
        s=55,
        label="No segment recorded",
    )
    for row in undetected.itertuples():
        axes[0].annotate(
            row.individual,
            (row.age_kya, 0.04),
            xytext=(3, 5),
            textcoords="offset points",
            fontsize=7,
            rotation=35,
        )
    axes[0].set_xlim(43, 5)
    axes[0].set_ylim(0, 1.05)
    axes[0].set_xlabel("Age (thousand years ago)")
    axes[0].set_ylabel("Highest recorded reference-match proportion")
    axes[0].set_title("A. Descriptive ancient-genome extraction")
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)

    groups = [
        "Europe",
        "Central/South Asia",
        "East Asia",
        "Oceania",
        "Admixed Americas",
        "Indigenous Americas",
    ]
    cumulative = np.zeros(len(groups))
    for reference in ["Vindija", "Altai", "Chagyrskaya", "Tie"]:
        values = []
        for group in groups:
            rows = modern[
                (modern["analysis_group"] == group)
                & (modern["closest_reference"] == reference)
            ]
            values.append(float(rows["proportion"].iloc[0]) if len(rows) else 0.0)
        axes[1].bar(
            groups,
            np.asarray(values) * 100,
            bottom=cumulative,
            color=COLORS[reference],
            label=reference,
            edgecolor="white",
            linewidth=0.5,
        )
        cumulative += np.asarray(values) * 100
    for index, group in enumerate(groups):
        rows = modern[modern["analysis_group"] == group]
        total = int(rows["group_total"].iloc[0]) if len(rows) else 0
        axes[1].text(index, 102, f"n={total}", ha="center", fontsize=8)
    axes[1].set_ylim(0, 110)
    axes[1].set_ylabel("Segment composition (%)")
    axes[1].set_title("B. Modern hmmix segments in the 500-kb interval")
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].legend(frameon=False, ncol=2, loc="lower left")
    axes[1].grid(axis="y", alpha=0.2)
    figure.suptitle(
        "Ancient and modern ABO-window summaries are descriptive and method-dependent",
        fontsize=15,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.01,
        "Ancient and modern calls were produced by different pipelines; this figure does not constitute a formal temporal test.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=[0, 0.04, 1, 0.94])
    save_figure(figure, "fig8_temporal_dynamics")


def main() -> None:
    create_figure_3()
    create_figure_5()
    create_figure_6()
    create_figure_7()
    create_figure_8()
    source = FIGURE_DIR / "fig4_bivariate_world_map.png"
    target = FIGURE_DIR / "fig9_bivariate_world_map.png"
    with Image.open(source) as image:
        output = image.convert("RGB")
    draw = ImageDraw.Draw(output)
    draw.rectangle((0, output.height - 120, output.width, output.height), fill="white")
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font = (
        ImageFont.truetype(str(font_path), 24)
        if font_path.exists()
        else ImageFont.load_default()
    )
    footer = (
        "Contextual approximate values from Sankararaman et al. (2014, 2016), "
        "Jacobs et al. (2019), and Liu et al. (2024)"
    )
    left, _, right, _ = draw.textbbox((0, 0), footer, font=font)
    draw.text(
        ((output.width - (right - left)) / 2, output.height - 72),
        footer,
        fill="#666666",
        font=font,
    )
    output.save(target, format="PNG", dpi=(300, 300))
    print("Created AJBA Figures 5-9 source files")


if __name__ == "__main__":
    main()
