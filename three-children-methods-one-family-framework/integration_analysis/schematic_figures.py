"""
Schematic (conceptual) figures for the ONISHI integration paper.

These are the two non-data figures:
  * overview  -> the three frameworks on a common data basis (main Figure 1)
  * pipeline  -> the integrated IONE -> LINKO -> KOTHA pipeline (main Figure 2)

Design rules (see repository knowledge):
  * NO figure numbers and NO verbatim caption text are drawn on the figure.
    All descriptive text lives in the figure legend in the manuscript, so the
    figures can be renumbered / re-captioned without regenerating the images.
  * Only the schematic content itself (box labels, level labels, arrows) is
    rendered on the canvas.

Output PNGs are written into ``figures/`` next to the data-figure outputs so a
clean clone reproduces every figure with a single command.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.family"] = "DejaVu Sans"

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

C_LINKO = "#2196F3"   # blue
C_IONE = "#FF9800"    # orange
C_KOTHA = "#4CAF50"   # green
C_ALL3 = "#9C27B0"    # purple
C_ARROW = "#616161"


def _rounded_box(ax, x, y, w, h, color):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                         facecolor=color, edgecolor="white", linewidth=2,
                         alpha=0.92)
    ax.add_patch(box)


def overview():
    """Three frameworks on a common data basis (no title / no figure number)."""
    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    boxes = [
        (0.3, C_LINKO, "LINKO",
         "Latent Information Normalization\nfor Key Outcomes",
         ["ICR (information contribution ratio)",
          "Meta-analytic validity diagnostic",
          "Prism forest plot",
          "ICR-weighted pooling"],
         "Level: between studies"),
        (4.3, C_IONE, "IONE",
         "Incoherence-Oriented Neutralisation\nand Extraction",
         ["Coherent subgroup detection",
          "C1 incoherence indicator",
          "Within-stratum homogeneity (W)",
          "Hidden structure identification"],
         "Level: within studies"),
        (8.3, C_KOTHA, "KOTHA",
         "Knowledge-driven Observational-Trial\nHarmonisation Approach",
         ["Module K: counterfactual power",
          "Module T: Bayesian integration",
          "Module H: OIS / TSA / GRADE",
          "RCT-observational harmonisation"],
         "Level: between study types"),
    ]
    for x, color, name, subtitle, lines, level in boxes:
        cx = x + 1.7
        _rounded_box(ax, x, 2.65, 3.4, 2.95, color)
        ax.text(cx, 5.28, name, ha="center", va="center", fontsize=14,
                fontweight="bold", color="white")
        ax.text(cx, 4.85, subtitle, ha="center", va="center", fontsize=8.5,
                color="#EEEEEE")
        for i, line in enumerate(lines):
            ax.text(cx, 4.22 - i * 0.33, f"\u2022 {line}", ha="center",
                    va="center", fontsize=8, color="white")
        ax.text(cx, 2.35, level, ha="center", fontsize=8,
                color=color, fontstyle="italic")
        ax.annotate("", xy=(cx, 2.65), xytext=(cx, 1.5),
                    arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=1.5))

    _rounded_box(ax, 1.5, 0.0, 9.0, 1.5, "#78909C")
    ax.text(6.0, 1.05, "Common Data Sources", ha="center", va="center",
            fontsize=12, fontweight="bold", color="white")
    ax.text(6.0, 0.5, "RCT published data (Table 1)  |  Individual Patient Data "
            "(IPD)  |  Observational cohort data",
            ha="center", va="center", fontsize=9, color="white")

    plt.tight_layout()
    path = os.path.join(FIGDIR, "schematic_overview.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def pipeline():
    """Integrated IONE -> LINKO -> KOTHA pipeline (no title / no figure number)."""
    fig, ax = plt.subplots(figsize=(14, 7.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    phases = [
        (0.3, 4.85, 3.0, 2.05, "Phase 1: IONE", "Population decomposition", C_IONE,
         ["Detect incoherent populations", "Extract coherent subgroups",
          "Compute C1 and W"]),
        (4.0, 4.85, 3.0, 2.05, "Phase 2: LINKO", "Information quantification",
         C_LINKO,
         ["Compute ICR per subgroup", "Assess ICR discrepancy",
          "Generate prism forest plot"]),
        (7.7, 4.85, 3.0, 2.05, "Phase 3: KOTHA", "Evidence harmonisation", C_KOTHA,
         ["Module K: power simulation", "Module T: Bayesian synthesis",
          "Module H: OIS / TSA / GRADE"]),
        (11.4, 4.85, 2.3, 2.05, "Output", "Decision support", C_ALL3,
         ["Integrated evidence profile", "Subgroup-specific readout",
          "Uncertainty quantification"]),
    ]
    for x, y, w, h, title, subtitle, color, items in phases:
        _rounded_box(ax, x, y, w, h, color)
        ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white")
        ax.text(x + w / 2, y + h - 0.62, subtitle, ha="center", va="center",
                fontsize=8, color="#F0F0F0")
        for i, item in enumerate(items):
            ax.text(x + w / 2, y + h - 1.10 - i * 0.32, f"\u2022 {item}",
                    ha="center", va="center", fontsize=7.5, color="white")

    for x1, x2 in [(3.3, 4.0), (7.0, 7.7), (10.7, 11.4)]:
        ax.annotate("", xy=(x2, 5.875), xytext=(x1, 5.875),
                    arrowprops=dict(arrowstyle="-|>", color=C_ARROW, lw=2))

    _rounded_box(ax, 0.3, 0.0, 13.4, 1.5, "#546E7A")
    ax.text(7, 1.15, "Input Data Sources", ha="center", va="center",
            fontsize=12, fontweight="bold", color="white")
    for label, x in [("Observational\nCohort Data\n(for IONE)", 2.5),
                     ("Published RCT\nTable 1 Data\n(for LINKO)", 5.5),
                     ("Individual Patient\nData (IPD)\n(for LINKO + IONE)", 8.5),
                     ("RCT + Obs. Study\nEffect Estimates\n(for KOTHA)", 11.5)]:
        ax.text(x, 0.45, label, ha="center", va="center", fontsize=8,
                color="white")

    # cross-phase hand-offs (dashed)
    ax.annotate("", xy=(9.2, 4.85), xytext=(1.8, 4.85),
                arrowprops=dict(arrowstyle="-|>", color=C_IONE,
                                connectionstyle="arc3,rad=-0.45", lw=1.5,
                                ls="--"))
    ax.text(4.6, 3.05, "Subgroup risk profiles\nfeed Module K simulation",
            ha="center", va="center", fontsize=7.5, color=C_IONE,
            fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFF3E0",
                      edgecolor=C_IONE, alpha=0.9))
    ax.annotate("", xy=(9.2, 5.05), xytext=(5.5, 4.85),
                arrowprops=dict(arrowstyle="-|>", color=C_LINKO,
                                connectionstyle="arc3,rad=-0.35", lw=1.5,
                                ls="--"))
    ax.text(8.7, 3.75, "ICR as Bayesian weight\nin Module T",
            ha="center", va="center", fontsize=7.5, color=C_LINKO,
            fontstyle="italic",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#E3F2FD",
                      edgecolor=C_LINKO, alpha=0.9))
    for x in [1.8, 5.5, 9.2, 12.55]:
        ax.annotate("", xy=(x, 4.85), xytext=(x, 1.5),
                    arrowprops=dict(arrowstyle="-|>", color="#90A4AE", lw=1))

    plt.tight_layout()
    path = os.path.join(FIGDIR, "schematic_pipeline.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def build_all():
    return {"overview": overview(), "pipeline": pipeline()}


if __name__ == "__main__":
    for k, v in build_all().items():
        print(k, "->", v)
