"""
Generate Figure 1: Mechanism diagram for PBM-AVA hypothesis.
Output: PNG file (no .dot files per user environment constraints).
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent


def create_figure1():
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    # Title
    ax.text(5, 11.5, "Proposed Mechanism: PBM-Induced AVA Vasodilation\nfor Blood Pressure Reduction",
            ha="center", va="center", fontsize=13, fontweight="bold")

    # Flow boxes
    boxes = [
        (5, 10.2, "PBM Irradiation\n(630\u2013850 nm, 20\u2013100 mW/cm\u00b2)\nto palmar/plantar glabrous skin",
         "#E3F2FD"),
        (5, 8.6, "Photon absorption by\nCytochrome c Oxidase (CcO)\n& Nitrosyl-hemoglobin",
         "#E8F5E9"),
        (5, 7.0, "NO release from\nendothelial S-nitrosothiol stores",
         "#FFF3E0"),
        (5, 5.4, "sGC activation \u2192 cGMP\u2191 \u2192 PKG\nVascular smooth muscle relaxation",
         "#FFF3E0"),
        (5, 3.8, "AVA DILATION\n(diameter 20\u2013150 \u00b5m \u2192 fully patent)",
         "#FFEBEE"),
        (5, 2.2, "Parallel low-resistance pathways\nadded to systemic circulation\n\u2192 TPR reduction (5\u201310%)",
         "#F3E5F5"),
        (5, 0.6, "\u0394MAP = \u22124.5 to \u22129.0 mmHg\n(clinically significant)",
         "#E8EAF6"),
    ]

    box_h = 0.7
    box_w = 4.0

    for (x, y, text, color) in boxes:
        rect = mpatches.FancyBboxPatch(
            (x - box_w / 2, y - box_h),
            box_w, box_h * 2,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor="#333333",
            linewidth=1.2,
        )
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center", fontsize=9,
                fontweight="normal")

    # Arrows between boxes
    arrow_props = dict(
        arrowstyle="->,head_width=0.3,head_length=0.2",
        color="#1565C0",
        lw=2,
    )
    arrow_y_pairs = [
        (10.2 - box_h, 8.6 + box_h),
        (8.6 - box_h, 7.0 + box_h),
        (7.0 - box_h, 5.4 + box_h),
        (5.4 - box_h, 3.8 + box_h),
        (3.8 - box_h, 2.2 + box_h),
        (2.2 - box_h, 0.6 + box_h),
    ]

    for y_start, y_end in arrow_y_pairs:
        ax.annotate(
            "", xy=(5, y_end), xytext=(5, y_start),
            arrowprops=arrow_props,
        )

    # Side annotations
    ax.text(8.5, 8.6, "Penetration depth:\n660 nm: 14\u201321 mm\n830 nm: 20\u201326 mm",
            ha="center", va="center", fontsize=7.5, style="italic",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="#999999", alpha=0.8))

    ax.text(8.5, 3.8, "AVA location:\n1\u20133 mm depth\nin glabrous skin",
            ha="center", va="center", fontsize=7.5, style="italic",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="#999999", alpha=0.8))

    # Feedback loop annotation
    ax.annotate(
        "", xy=(1.2, 10.2), xytext=(1.2, 0.6),
        arrowprops=dict(
            arrowstyle="->,head_width=0.3",
            color="#C62828",
            lw=1.5,
            connectionstyle="arc3,rad=0.3",
        ),
    )
    ax.text(0.3, 5.4, "Closed-loop\nBP feedback\ncontrol",
            ha="center", va="center", fontsize=7.5, color="#C62828",
            fontweight="bold", rotation=90)

    plt.tight_layout()
    output_path = OUTPUT_DIR / "figure1_mechanism.png"
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close()
    print(f"Figure 1 saved: {output_path}")
    return output_path


if __name__ == "__main__":
    create_figure1()
