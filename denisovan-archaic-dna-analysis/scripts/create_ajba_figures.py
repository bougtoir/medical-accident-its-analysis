"""Create cautious, data-traceable ABO figures for the AJBA package."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


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
    raise RuntimeError(
        "Figure 3 must be generated with scripts/create_minard_figure.py."
    )


def create_figure_5() -> None:
    summary = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")
    segments = pd.read_csv(DATA_DIR / "abo_neanderthal_segments.csv")
    group_order = [
        "East Asia",
        "Oceania",
        "Indigenous Americas",
        "Admixed Americas",
        "Europe",
    ]
    labels = {
        "East Asia": "East Asia",
        "Oceania": "Oceania",
        "Indigenous Americas": "Indigenous\nAmericas",
        "Admixed Americas": "Admixed\nAmericas",
        "Europe": "Europe",
    }
    reference_order = ["Altai", "Chagyrskaya", "Vindija"]
    reference_colors = {
        "Altai": "#d94e4e",
        "Chagyrskaya": "#ffa726",
        "Vindija": "#3b8ad8",
    }
    figure, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    left = axes[0]
    positions = np.arange(len(group_order))
    width = 0.25
    classifiable_totals: dict[str, int] = {}
    for reference in reference_order:
        values: list[float] = []
        for group in group_order:
            group_rows = summary[
                (summary["analysis_group"] == group)
                & (summary["closest_reference"].isin(reference_order))
            ]
            classifiable_total = int(group_rows["n_segments"].sum())
            classifiable_totals[group] = classifiable_total
            rows = group_rows[group_rows["closest_reference"] == reference]
            count = int(rows["n_segments"].iloc[0]) if len(rows) else 0
            values.append(
                100 * count / classifiable_total if classifiable_total else 0
            )
        offset = (reference_order.index(reference) - 1) * width
        bars = left.bar(
            positions + offset,
            values,
            width,
            color=reference_colors[reference],
            label=reference,
            alpha=0.9,
        )
        for bar, value in zip(bars, values):
            if value >= 1:
                left.text(
                    bar.get_x() + bar.get_width() / 2,
                    value + 1.2,
                    f"{value:.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                )
    left.set_xticks(
        positions,
        [
            f"{labels[group]}\n(n={classifiable_totals[group]})"
            for group in group_order
        ],
        fontsize=7.5,
    )
    left.set_ylim(0, 110)
    left.set_ylabel("Proportion of segments (%)")
    left.set_title(
        "A. Neanderthal sub-lineage composition\nat the ABO locus",
        fontsize=11,
        fontweight="bold",
    )
    left.legend(fontsize=8, loc="upper right")
    left.grid(axis="y", alpha=0.2)

    right = axes[1]
    selected = segments[
        (
            (segments["name"] == "HGDP00656")
            & (segments["pop"] == "Bougainville")
            & (segments["start"] == 133_231_000)
        )
        | (
            (segments["name"] == "HGDP01058")
            & (segments["pop"] == "Pima")
            & (segments["start"] == 133_254_000)
        )
        | (
            (segments["name"] == "HGDP00877")
            & (segments["pop"] == "Maya")
            & (segments["start"] == 133_294_000)
        )
    ].copy()
    selected["display"] = selected["name"] + "\n(" + selected["pop"] + ")"
    selected = (
        selected.set_index("name")
        .loc[["HGDP00656", "HGDP01058", "HGDP00877"]]
        .reset_index()
    )
    y_positions = np.arange(len(selected))[::-1]
    right.axvspan(
        ABO_START,
        ABO_END,
        color="#fff4bf",
        alpha=0.9,
        label="ABO gene",
        zorder=0,
    )
    for y_value, row in zip(y_positions, selected.itertuples()):
        right.barh(
            y_value,
            row.end - row.start,
            left=row.start,
            height=0.38,
            color="#79c37c" if row.pop == "Bougainville" else "#5398dd",
            edgecolor="#333333",
            linewidth=0.6,
        )
        right.text(
            row.start + (row.end - row.start) / 2,
            y_value,
            row.closest_reference,
            ha="center",
            va="center",
            fontsize=7,
            color="white",
            fontweight="bold",
        )
    right.set_yticks(y_positions, selected["display"], fontsize=8)
    right.set_xlim(133_050_000, 133_550_000)
    right.ticklabel_format(axis="x", style="plain", useOffset=False)
    right.set_xticks(
        [133_100_000, 133_200_000, 133_300_000, 133_400_000, 133_500_000],
        ["133.1", "133.2", "133.3", "133.4", "133.5"],
    )
    right.set_xlabel("Chromosome 9 position (Mb, GRCh38)")
    right.set_title(
        "B. Selected archaic segments near ABO",
        fontsize=11,
        fontweight="bold",
    )
    right.grid(axis="x", alpha=0.2)
    right.legend(frameon=False, fontsize=8, loc="lower right")
    right.text(
        133_505_000,
        -0.75,
        "Pima: strict overlap\nMaya: window only",
        fontsize=7,
        ha="right",
        color="#555555",
    )
    figure.suptitle(
        "Archaic Neanderthal sub-lineages at the ABO locus",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.005,
        "Equal maximum-similarity ties are excluded; the 2/2 Indigenous result is a segment summary, not a regional estimate.",
        ha="center",
        fontsize=8,
        color="#666666",
    )
    figure.tight_layout(rect=[0, 0.04, 1, 0.93])
    save_figure(figure, "fig5_abo_sublineage")


def create_figure_6() -> None:
    o2 = pd.read_csv(DATA_DIR / "o2_frequency_summary.csv")
    population = pd.read_csv(DATA_DIR / "abo_population_summary.csv")
    allele_order = [
        "Munda",
        "Rawaki",
        "Paradise",
        "GBR",
        "PUR",
        "TSI",
        "FIN",
        "IBS",
        "GIH",
        "PEL",
        "BEB",
        "CLM",
        "MXL",
        "CEU",
        "JPT",
        "CHB",
    ]
    region_by_population = {
        "Munda": "Oceania",
        "Rawaki": "Oceania",
        "Paradise": "Oceania",
        "GBR": "Europe",
        "TSI": "Europe",
        "FIN": "Europe",
        "IBS": "Europe",
        "CEU": "Europe",
        "PUR": "Americas",
        "PEL": "Americas",
        "CLM": "Americas",
        "MXL": "Americas",
        "GIH": "South Asia",
        "BEB": "South Asia",
        "JPT": "East Asia",
        "CHB": "East Asia",
    }
    region_colors = {
        "Oceania": "#4caf50",
        "Europe": "#2196f3",
        "Americas": "#f44336",
        "South Asia": "#9c27b0",
        "East Asia": "#ff9800",
    }
    o2_values = o2.set_index("population")["frequency"].to_dict()
    allele_frequencies = np.asarray(
        [100 * float(o2_values.get(name, 0)) for name in allele_order]
    )
    allele_colors = [
        region_colors[region_by_population[name]] for name in allele_order
    ]
    carrier_order = [
        "Surui",
        "Karitiana",
        "Maya",
        "Pima",
        "PEL",
        "MXL",
        "PUR",
        "CLM",
        "Bougainville",
        "PapuanHighlands",
        "PapuanSepik",
    ]
    carrier = (
        population.set_index("pop").reindex(carrier_order).reset_index()
    )
    carrier_colors = [
        "#2196f3"
        if row.analysis_group in {"Indigenous Americas", "Other Americas"}
        else "#ff9800"
        if row.analysis_group == "Admixed Americas"
        else "#4caf50"
        for row in carrier.itertuples()
    ]

    figure, axes = plt.subplots(1, 2, figsize=(14, 6))
    y_allele = np.arange(len(allele_order))
    axes[0].barh(y_allele, allele_frequencies, color=allele_colors)
    axes[0].set_yticks(y_allele, allele_order, fontsize=8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("rs41302905 T allele frequency (%)")
    axes[0].set_title(
        "A. O2-defining rs41302905 T allele frequency",
        fontsize=11,
        fontweight="bold",
    )
    axes[0].grid(axis="x", alpha=0.2)
    for index, value in enumerate(allele_frequencies):
        if value > 0:
            axes[0].text(
                value + 0.2,
                index,
                f"{value:.1f}%",
                va="center",
                fontsize=7,
            )
    axes[0].legend(
        handles=[
            mpatches.Patch(color=color, label=region)
            for region, color in region_colors.items()
        ],
        fontsize=7,
        frameon=False,
        loc="lower right",
    )

    y_carrier = np.arange(len(carrier))
    carrier_frequencies = carrier["window_individual_frequency"].fillna(0) * 100
    axes[1].barh(y_carrier, carrier_frequencies, color=carrier_colors)
    axes[1].set_yticks(y_carrier, carrier_order, fontsize=8)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel(
        "Individuals with a segment in the 500-kb ABO interval (%)"
    )
    axes[1].set_title(
        "B. Neanderthal-classified ABO-window carrier frequency",
        fontsize=11,
        fontweight="bold",
    )
    axes[1].grid(axis="x", alpha=0.2)
    for index, row in enumerate(carrier.itertuples()):
        carriers = 0 if pd.isna(row.n_window_individuals) else int(row.n_window_individuals)
        total = 0 if pd.isna(row.n_total) else int(row.n_total)
        value = (
            0
            if pd.isna(row.window_individual_frequency)
            else 100 * row.window_individual_frequency
        )
        axes[1].text(
            value + 1,
            index,
            f"{carriers}/{total}",
            va="center",
            fontsize=7,
        )
    axes[1].legend(
        handles=[
            mpatches.Patch(color="#2196f3", label="Indigenous Americas"),
            mpatches.Patch(color="#ff9800", label="Admixed Americas"),
            mpatches.Patch(color="#4caf50", label="Oceania"),
        ],
        fontsize=7,
        frameon=False,
        loc="lower right",
    )
    figure.suptitle(
        "O2-defining allele and ABO-window segment-carrier frequencies",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.005,
        "The panels use different sources and summarize different biological quantities.",
        ha="center",
        fontsize=8,
        color="#666666",
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
    sublineage = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")

    def classifiable(group: str) -> tuple[int, int]:
        rows = sublineage[
            (sublineage["analysis_group"] == group)
            & (sublineage["closest_reference"] != "Tie")
        ]
        total = int(rows["n_segments"].sum())
        vindija_rows = rows[rows["closest_reference"] == "Vindija"]
        vindija = (
            int(vindija_rows["n_segments"].iloc[0]) if len(vindija_rows) else 0
        )
        return vindija, total

    europe_vindija, europe_total = classifiable("Europe")
    east_vindija, east_total = classifiable("East Asia")
    oceania_vindija, oceania_total = classifiable("Oceania")
    figure, axis = plt.subplots(figsize=(14, 9))
    axis.set_xlim(0, 14)
    axis.set_ylim(0, 9)
    axis.axis("off")
    axis.text(
        7,
        8.7,
        "ANE dual ancestry model — contextual hypothesis",
        fontsize=13,
        fontweight="bold",
        ha="center",
    )
    for y_value, label in [
        (8.0, "~50 kya"),
        (7.0, "~45 kya"),
        (6.0, "~35 kya"),
        (5.0, "~25 kya"),
        (4.0, "~15 kya"),
        (3.0, "~10 kya"),
        (1.5, "Present"),
    ]:
        axis.text(0.3, y_value, label, fontsize=8, ha="right", color="gray")
        axis.axhline(
            y=y_value, xmin=0.02, xmax=0.06, color="gray", linewidth=0.5
        )

    boxes = [
        (
            (3, 7.7, 3, 0.5),
            "Out of Africa → Neanderthal admixture",
            "#e8eaf6",
            "black",
            9,
        ),
        (
            (1.5, 6.5, 2.5, 0.5),
            "West Eurasian\nbranch",
            "#fff3e0",
            "#e65100",
            8,
        ),
        (
            (9.7, 6.5, 2.5, 0.5),
            "East Asian\nbranch",
            "#e3f2fd",
            "#1565c0",
            8,
        ),
        (
            (4.5, 5.5, 3.5, 0.7),
            "ANE (Ancient North Eurasian)\nMal'ta 24 kya | Yana 31.6 kya | Sunghir 33 kya",
            "#fff9c4",
            "#f57f17",
            8,
        ),
        (
            (4.9, 3.7, 3.1, 0.75),
            "Beringian population context\npublished model: ANE + East Asian ancestry",
            "#e8f5e9",
            "#2e7d32",
            8,
        ),
        (
            (1.0, 1.15, 3.4, 0.9),
            (
                "Present-day Europe\n"
                f"Vindija-closest: {europe_vindija}/{europe_total} "
                "classifiable ABO-window segments"
            ),
            "#fff5e6",
            "#e65100",
            7.5,
        ),
        (
            (5.1, 1.15, 3.8, 0.9),
            (
                "Indigenous American records\nPima: 1 strict overlap; "
                "Maya: 1 window-only\nboth Vindija-closest"
            ),
            "#fce4ec",
            "#c62828",
            7.5,
        ),
        (
            (9.6, 1.15, 3.4, 0.9),
            (
                "East Asia / Oceania\n"
                f"Vindija-closest: {east_vindija}/{east_total} and "
                f"{oceania_vindija}/{oceania_total}"
            ),
            "#e3f2fd",
            "#1565c0",
            7.5,
        ),
    ]
    for coordinates, text, face, edge, fontsize in boxes:
        x_value, y_value, width, height = coordinates
        patch = FancyBboxPatch(
            (x_value, y_value),
            width,
            height,
            boxstyle="round,pad=0.1",
            facecolor=face,
            edgecolor=edge,
        )
        axis.add_patch(patch)
        axis.text(
            x_value + width / 2,
            y_value + height / 2,
            text,
            fontsize=fontsize,
            ha="center",
            va="center",
            fontweight="bold" if "ANE (" in text else "normal",
        )
    axis.text(
        8.5,
        5.85,
        "Yana2: Chagyrskaya-closest upstream record\n"
        "Mal'ta: no segment recorded in extracted interval\n"
        "Ancient and modern calls used different pipelines",
        fontsize=7,
        ha="left",
        color="#e65100",
        style="italic",
    )
    arrows = [
        ((4.5, 7.75), (2.8, 7.0), "#e65100", "solid"),
        ((4.5, 7.75), (10.9, 7.0), "#1565c0", "solid"),
        ((2.8, 6.5), (5.1, 6.0), "#e65100", "solid"),
        ((10.9, 6.5), (7.8, 5.95), "#1565c0", "solid"),
        ((6.25, 5.5), (6.45, 4.45), "#f57f17", "solid"),
        ((10.9, 6.5), (7.9, 4.2), "#1565c0", "solid"),
        ((6.45, 3.7), (2.7, 2.05), "#e65100", "dashed"),
        ((6.45, 3.7), (7.0, 2.05), "#c62828", "dashed"),
        ((7.2, 3.7), (11.3, 2.05), "#1565c0", "dashed"),
    ]
    for start, end, color, style in arrows:
        axis.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.5,
                color=color,
                linestyle=style,
                connectionstyle="arc3,rad=0.03",
            )
        )
    axis.text(
        7,
        0.45,
        "Dashed arrows denote a testable hypothesis, not an inferred migration route.",
        fontsize=8,
        ha="center",
        color="#555555",
    )
    axis.text(
        10.7,
        3.65,
        "Two modern records cannot estimate\na regional frequency or pathway.",
        fontsize=7.5,
        ha="center",
        color="#c62828",
        bbox={
            "boxstyle": "round",
            "facecolor": "#fff5f5",
            "edgecolor": "#c62828",
        },
    )
    figure.tight_layout()
    save_figure(figure, "fig7_ane_model")


def create_figure_8() -> None:
    ancient = pd.read_csv(DATA_DIR / "ancient_abo_summary.csv")
    modern = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")
    figure, axes = plt.subplots(1, 2, figsize=(16, 8))
    detected = ancient[ancient["segment_detected"]].copy()
    undetected = ancient[~ancient["segment_detected"]].copy()
    detected["maximum_proportion"] = detected[
        ["altai_proportion", "vindija_proportion", "chagyrskaya_proportion"]
    ].max(axis=1)
    reference_colors = {
        "Altai": "#2196f3",
        "Vindija": "#ff9800",
        "Chagyrskaya": "#4caf50",
    }
    for reference, group in detected.groupby("closest_reference"):
        axes[0].scatter(
            group["age_kya"],
            group["maximum_proportion"],
            color=reference_colors.get(reference, "#777777"),
            s=55,
            label=reference,
            zorder=3,
        )
        for row in group.itertuples():
            axes[0].annotate(
                row.individual,
                (row.age_kya, row.maximum_proportion),
                xytext=(3, 4),
                textcoords="offset points",
                fontsize=7,
            )
    axes[0].scatter(
        undetected["age_kya"],
        np.zeros(len(undetected)),
        facecolor="white",
        edgecolor="#777777",
        s=48,
        label="No segment recorded",
        zorder=3,
    )
    axes[0].axvspan(15, 25, color="#ffb2b2", alpha=0.25)
    axes[0].text(
        20,
        0.08,
        "Beringian\ncontext interval",
        ha="center",
        fontsize=7,
        color="#b71c1c",
    )
    axes[0].invert_xaxis()
    axes[0].set_xlim(42, -1)
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_xlabel("Approximate age (thousand years)")
    axes[0].set_ylabel("Maximum similarity to an archaic reference")
    axes[0].set_title(
        "A. Ancient ABO-window observations",
        fontsize=11,
        fontweight="bold",
    )
    axes[0].grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=7, loc="lower left")

    ancient_classifiable = detected[
        (detected["age_kya"] > 8)
        & detected["closest_reference"].isin(reference_colors)
    ]
    modern_groups = [
        "Europe",
        "Central/South Asia",
        "East Asia",
        "Oceania",
        "Indigenous Americas",
    ]
    display_groups = ["Ancient records\n(>8 kya)"] + modern_groups
    counts: dict[str, dict[str, int]] = {
        display_groups[0]: {
            reference: int(
                (ancient_classifiable["closest_reference"] == reference).sum()
            )
            for reference in reference_colors
        }
    }
    for group in modern_groups:
        rows = modern[
            (modern["analysis_group"] == group)
            & (modern["closest_reference"].isin(reference_colors))
        ]
        counts[group] = {
            reference: int(
                rows.loc[
                    rows["closest_reference"] == reference, "n_segments"
                ].sum()
            )
            for reference in reference_colors
        }
    cumulative = np.zeros(len(display_groups))
    for reference in ["Altai", "Vindija", "Chagyrskaya"]:
        values: list[float] = []
        for group in display_groups:
            total = sum(counts[group].values())
            values.append(100 * counts[group][reference] / total if total else 0)
        axes[1].bar(
            display_groups,
            values,
            bottom=cumulative,
            color=reference_colors[reference],
            label=reference,
        )
        cumulative += np.asarray(values)
    axes[1].tick_params(axis="x", rotation=30, labelsize=8)
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("Classifiable segment proportion (%)")
    axes[1].set_title(
        "B. Ancient and modern descriptive composition",
        fontsize=11,
        fontweight="bold",
    )
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")
    axes[1].grid(axis="y", alpha=0.2)
    for index, group in enumerate(display_groups):
        axes[1].text(
            index,
            102,
            f"n={sum(counts[group].values())}",
            ha="center",
            fontsize=7,
            clip_on=False,
        )
    figure.suptitle(
        "Temporal dynamics of Neanderthal sub-lineages at the ABO locus",
        fontsize=14,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.005,
        "Ancient and modern calls used different pipelines; no formal temporal comparison is made.",
        ha="center",
        fontsize=8,
        color="#666666",
    )
    figure.tight_layout(rect=[0, 0.04, 1, 0.93])
    save_figure(figure, "fig8_temporal_dynamics")


def main() -> None:
    create_figure_5()
    create_figure_6()
    create_figure_7()
    create_figure_8()
    print("Created AJBA Figures 5-8 source files")


if __name__ == "__main__":
    main()
