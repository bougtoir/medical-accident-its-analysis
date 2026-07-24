"""
Generate Figure 1: Mechanism diagram for montmorillonite caffeine adsorption sachet.
Shows the tea bag format and the selective adsorption mechanism.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent


def create_figure1():
    """Create mechanism diagram showing MMT sachet decaffeination."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle(
        "Figure 1. Portable montmorillonite sachet for on-demand decaffeination",
        fontsize=12,
        fontweight="bold",
        y=0.98,
    )

    # Panel A: Sachet design
    ax = axes[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("(A) Sachet design", fontsize=11, fontweight="bold")

    # Draw tea bag shape
    bag = mpatches.FancyBboxPatch(
        (2.5, 1), 5, 7, boxstyle="round,pad=0.3",
        facecolor="#F5E6D3", edgecolor="#8B4513", linewidth=2
    )
    ax.add_patch(bag)

    # String
    ax.plot([5, 5], [8, 10.5], color="#8B4513", linewidth=1.5)
    # Tag
    tag = mpatches.FancyBboxPatch(
        (3.8, 10.5), 2.4, 1.2, boxstyle="round,pad=0.1",
        facecolor="#FFFFFF", edgecolor="#8B4513", linewidth=1
    )
    ax.add_patch(tag)
    ax.text(5, 11.1, "caffe-out", ha="center", va="center", fontsize=8,
            fontweight="bold", color="#2E7D32")

    # MMT granules inside
    np.random.seed(42)
    for _ in range(25):
        x = np.random.uniform(3.0, 6.8)
        y = np.random.uniform(1.5, 7.2)
        size = np.random.uniform(0.15, 0.35)
        circle = plt.Circle((x, y), size, color="#A0522D", alpha=0.7)
        ax.add_patch(circle)

    # Labels
    ax.text(5, 0.3, "MMT granules\n(0.1-0.5 mm)", ha="center",
            fontsize=8, style="italic")
    ax.annotate("Nonwoven\nPP sachet", xy=(7.5, 4.5), xytext=(8.5, 4.5),
                fontsize=7, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="gray"))

    # Panel B: Adsorption mechanism (cross-section of MMT layers)
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")
    ax.set_title("(B) Selective interlayer adsorption", fontsize=11, fontweight="bold")

    # Draw MMT layers
    layer_colors = ["#D4A574", "#C8956E"]
    for i, y_pos in enumerate([1.5, 4.0, 6.5, 9.0]):
        color = layer_colors[i % 2]
        rect = mpatches.FancyBboxPatch(
            (1, y_pos), 8, 0.8, boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="#5D4037", linewidth=1
        )
        ax.add_patch(rect)
        ax.text(5, y_pos + 0.4, "MMT layer (SiO₂-Al₂O₃-SiO₂)",
                ha="center", va="center", fontsize=6, color="white")

    # Caffeine molecules (small, fitting in interlayer)
    caff_positions = [(2.5, 2.8), (5.0, 5.3), (7.5, 2.8), (3.5, 7.8)]
    for x, y in caff_positions:
        circle = plt.Circle((x, y), 0.3, color="#D32F2F", alpha=0.8)
        ax.add_patch(circle)
        ax.text(x, y, "C", ha="center", va="center", fontsize=7,
                color="white", fontweight="bold")

    # Polyphenol molecules (larger, excluded)
    poly_positions = [(1.5, 11.0), (5.0, 11.0), (8.5, 11.0)]
    for x, y in poly_positions:
        circle = plt.Circle((x, y), 0.5, color="#2E7D32", alpha=0.7)
        ax.add_patch(circle)
        ax.text(x, y, "P", ha="center", va="center", fontsize=7,
                color="white", fontweight="bold")

    # Arrows showing exclusion
    for x in [1.5, 5.0, 8.5]:
        ax.annotate("", xy=(x, 10.2), xytext=(x, 10.5),
                    arrowprops=dict(arrowstyle="->", color="red",
                                    linestyle="dashed"))
        ax.text(x, 10.0, "✗", ha="center", va="center", fontsize=10,
                color="red")

    # Legend
    ax.text(0.5, 0.5, "C = Caffeine (MW 194)", fontsize=7, color="#D32F2F")
    ax.text(0.5, 0.0, "P = Polyphenol (sterically excluded)", fontsize=7,
            color="#2E7D32")

    # Panel C: Usage protocol
    ax = axes[2]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")
    ax.set_title("(C) Consumer protocol", fontsize=11, fontweight="bold")

    steps = [
        (9.5, "① Immerse sachet\nin beverage", "#E3F2FD"),
        (6.5, "② Wait 3-5 min\n(gentle agitation)", "#FFF3E0"),
        (3.5, "③ Remove sachet\n→ Decaf beverage!", "#E8F5E9"),
    ]

    for y, text, color in steps:
        box = mpatches.FancyBboxPatch(
            (1.5, y), 7, 2.2, boxstyle="round,pad=0.3",
            facecolor=color, edgecolor="#424242", linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(5, y + 1.1, text, ha="center", va="center", fontsize=9)

    # Arrows between steps
    for y in [9.0, 6.0]:
        ax.annotate("", xy=(5, y - 0.3), xytext=(5, y + 0.3),
                    arrowprops=dict(arrowstyle="-|>", color="#424242",
                                    linewidth=2))

    # Result annotation
    ax.text(5, 0.8, "Caffeine: >80% removed\nPolyphenols: >90% retained\nTaste: unchanged",
            ha="center", va="center", fontsize=8, style="italic",
            bbox=dict(boxstyle="round", facecolor="#F3E5F5", alpha=0.8))

    plt.tight_layout()
    output_path = OUTPUT_DIR / "figure1_mechanism.png"
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print(f"Figure 1 saved: {output_path}")
    return output_path


if __name__ == "__main__":
    create_figure1()
