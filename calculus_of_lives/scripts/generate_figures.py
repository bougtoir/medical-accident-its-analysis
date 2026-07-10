#!/usr/bin/env python3
"""
Generate conceptual figures (English) for the manuscript:
  "Beyond the Calculus of Lives"

Outputs (PNG + TIFF) into ../output:
  fig1_layers            two layers of the question (inside / outside the calculus)
  fig2_quadrant          supply-demand x expansion-contraction, with religious types
  fig3_asymptote         asymptotic model of liberation from the calculus
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "output"
OUT.mkdir(exist_ok=True)

INK = "#1a1a1a"
BLUE = "#2c5f8a"
RED = "#a83232"
GREEN = "#2f6b3f"
GREY = "#6b6b6b"
LIGHT = "#eef2f6"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": INK,
})


def _save(fig, stem):
    for ext in ("png", "tif"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, bbox_inches="tight",
                    facecolor="white")
    plt.close(fig)


def fig1_layers():
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    # Outer layer box
    outer = FancyBboxPatch((0.4, 0.6), 9.2, 8.8, boxstyle="round,pad=0.1,rounding_size=0.25",
                           linewidth=1.6, edgecolor=BLUE, facecolor=LIGHT)
    ax.add_patch(outer)
    ax.text(5, 8.9, "OUTER QUESTION (ethical / existential)", ha="center",
            va="center", fontsize=11.5, fontweight="bold", color=BLUE)
    ax.text(5, 8.05, "May human beings weigh and decide\nwho is to live and who is to die?",
            ha="center", va="center", fontsize=11, color=INK, style="italic")

    # Inner layer box
    inner = FancyBboxPatch((1.7, 1.5), 6.6, 4.4, boxstyle="round,pad=0.1,rounding_size=0.2",
                           linewidth=1.4, edgecolor=RED, facecolor="white")
    ax.add_patch(inner)
    ax.text(5, 5.35, "INNER QUESTION (technical / consequential)", ha="center",
            va="center", fontsize=11.5, fontweight="bold", color=RED)
    ax.text(5, 4.5, "Was the bombing necessary?\nDid it save more lives than it cost?",
            ha="center", va="center", fontsize=11, color=INK, style="italic")
    ax.text(5, 3.35, "efficiency of a weighing that is\nalready assumed to be legitimate",
            ha="center", va="center", fontsize=9.5, color=GREY)
    ax.text(5, 2.15, "the standard 'necessity' debate\nlives here", ha="center",
            va="center", fontsize=9.5, color=GREY)

    # Arrow moving the question outward
    arr = FancyArrowPatch((8.35, 3.7), (9.15, 3.7), arrowstyle="-|>",
                          mutation_scale=18, linewidth=2, color=INK)
    ax.add_patch(arr)
    ax.text(9.2, 4.35, "shift the\nlayer", ha="center", va="center", fontsize=9,
            color=INK)
    _save(fig, "fig1_layers")


def fig2_quadrant():
    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.axhline(0, color=INK, linewidth=1.2)
    ax.axvline(0, color=INK, linewidth=1.2)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # Axis labels
    ax.text(1.12, 0.06, "SUPPLY-INCREASING", ha="right", va="bottom",
            fontsize=10.5, fontweight="bold", color=RED)
    ax.text(-1.12, 0.06, "DEMAND-REDUCING", ha="left", va="bottom",
            fontsize=10.5, fontweight="bold", color=GREEN)
    ax.text(0.03, 1.12, "EXPANSION / CONQUEST", ha="left", va="top",
            fontsize=10.5, fontweight="bold", color=INK)
    ax.text(0.03, -1.12, "CONTRACTION / DEFENCE", ha="left", va="bottom",
            fontsize=10.5, fontweight="bold", color=INK)

    def cell(x, y, title, ex, color):
        ax.text(x, y + 0.16, title, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=color)
        ax.text(x, y - 0.16, ex, ha="center", va="center", fontsize=9,
                color=GREY, style="italic")

    cell(0.55, 0.6, "supply x expansion",
         "missionary monotheism;\nprosperity religion; colonial mission", RED)
    cell(-0.55, 0.6, "demand-reduction x expansion",
         "ascetic Protestantism\n(Weber's unintended capital)", BLUE)
    cell(0.55, -0.6, "supply x contraction",
         "communal redistribution;\ndefensive fertility cults", GREY)
    cell(-0.55, -0.6, "demand-reduction x contraction",
         "early Buddhism; monasticism;\npantheist / animist immanence", GREEN)

    _save(fig, "fig2_quadrant")


def fig3_asymptote():
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    x = np.linspace(0.02, 10, 400)

    supply = 10 - 9.4 * np.exp(-0.35 * x)      # rises toward a finite ceiling
    demand = 9.4 * np.exp(-0.5 * x) + 0.6      # falls toward a positive floor

    ax.plot(x, supply, color=RED, linewidth=2.2, label="technological path: raise supply")
    ax.plot(x, demand, color=GREEN, linewidth=2.2, label="ideational path: lower demand")

    ax.axhline(10, color=RED, linestyle="--", linewidth=1, alpha=0.7)
    ax.text(10, 10.15, "cosmic ceiling (finite universe)", ha="right", va="bottom",
            fontsize=9, color=RED)
    ax.axhline(0.6, color=GREEN, linestyle="--", linewidth=1, alpha=0.7)
    ax.text(0.1, 0.75, "irreducible need (embodied life)", ha="left", va="bottom",
            fontsize=9, color=GREEN)

    ax.annotate("residual scarcity:\nthe calculus never fully vanishes",
                xy=(7.5, (10 - 9.4*np.exp(-0.35*7.5) + 9.4*np.exp(-0.5*7.5)+0.6)/2),
                xytext=(4.4, 5.4), fontsize=9.2, color=INK,
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=1.2))

    ax.set_xlabel("progress (technology + thought), arbitrary units")
    ax.set_ylabel("resource level, arbitrary units")
    ax.set_ylim(0, 11)
    ax.set_xlim(0, 10)
    ax.legend(loc="center right", frameon=False, fontsize=9.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, "fig3_asymptote")


if __name__ == "__main__":
    fig1_layers()
    fig2_quadrant()
    fig3_asymptote()
    print("figures written to", OUT)
