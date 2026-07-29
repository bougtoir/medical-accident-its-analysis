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
    """A funnel / sieve. Every question the bomb raises pours in at the top,
    but a layer of common sense and preconception ('we are entitled to do the
    weighing') acts as a filter: only the inner, technical question passes
    through into public debate, while the outer, fundamental question is
    screened out and never comes into view."""
    from matplotlib.patches import Polygon, Rectangle
    fig, ax = plt.subplots(figsize=(8.0, 7.0))
    ax.set_xlim(0, 11.0); ax.set_ylim(0, 10.5); ax.axis("off")
    cx = 5.0  # funnel centre

    # --- inflow: everything the bomb puts in question ---
    ax.text(cx, 10.25, "Everything the bomb puts in question",
            ha="center", va="center", fontsize=10.5, color=GREY, style="italic")
    for x in (2.6, 5.0, 7.4):
        ax.add_patch(FancyArrowPatch((x, 9.85), (x, 9.35), arrowstyle="-|>",
                     mutation_scale=12, linewidth=1.4, color=GREY))

    # --- the OUTER question, screened out above the filter ---
    outer = FancyBboxPatch((1.7, 7.95), 6.6, 1.3,
                           boxstyle="round,pad=0.08,rounding_size=0.18",
                           linewidth=1.5, edgecolor=BLUE, facecolor="white",
                           linestyle=(0, (5, 3)), alpha=0.9)
    ax.add_patch(outer)
    ax.text(cx, 8.85, "OUTER QUESTION (ethical / existential)", ha="center",
            va="center", fontsize=10.5, fontweight="bold", color=BLUE)
    ax.text(cx, 8.25, "May human beings weigh and decide\nwho is to live and who is to die?",
            ha="center", va="center", fontsize=9.5, color=INK, style="italic")

    # --- the filter / sieve: common sense and preconception ---
    filt = Rectangle((0.8, 7.05), 8.4, 0.66, linewidth=1.4,
                     edgecolor=INK, facecolor=LIGHT, hatch="////")
    ax.add_patch(filt)
    ax.text(cx, 7.38,
            "COMMON SENSE / PRECONCEPTION:\n\u201Cwe are entitled to do the weighing\u201D",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color=INK,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                      edgecolor="none"))

    # outer question deflected off the filter -> stays unexamined
    ax.add_patch(FancyArrowPatch((8.4, 7.75), (9.5, 8.65), arrowstyle="-|>",
                 mutation_scale=14, linewidth=1.5, color=BLUE, alpha=0.85,
                 connectionstyle="arc3,rad=0.35"))
    ax.text(9.9, 7.0, "screened\nout\u2014never\ncomes\ninto view",
            ha="center", va="center", fontsize=8.4, color=BLUE)

    # --- the funnel: narrows attention to the inner question ---
    funnel = Polygon([(1.2, 7.05), (8.8, 7.05), (5.6, 2.35), (4.4, 2.35)],
                     closed=True, linewidth=1.5, edgecolor=RED,
                     facecolor="white")
    ax.add_patch(funnel)
    ax.text(cx, 6.25, "INNER QUESTION (technical / consequential)", ha="center",
            va="center", fontsize=10.2, fontweight="bold", color=RED)
    ax.text(cx, 5.45, "Was the bombing necessary?\nDid it save more lives than it cost?",
            ha="center", va="center", fontsize=9.8, color=INK, style="italic")
    ax.text(cx, 4.3, "efficiency of a weighing whose\nlegitimacy is already assumed",
            ha="center", va="center", fontsize=9, color=GREY)
    ax.add_patch(FancyArrowPatch((cx, 3.2), (cx, 2.35), arrowstyle="-|>",
                 mutation_scale=15, linewidth=1.6, color=RED))

    # --- spout / outflow: the public debate ---
    tube = Rectangle((4.4, 1.05), 1.2, 1.3, linewidth=1.5,
                     edgecolor=RED, facecolor="white")
    ax.add_patch(tube)
    out = FancyBboxPatch((1.9, 0.1), 6.2, 0.82,
                         boxstyle="round,pad=0.08,rounding_size=0.15",
                         linewidth=1.4, edgecolor=RED, facecolor=LIGHT)
    ax.add_patch(out)
    ax.text(cx, 0.5, "the public \u2018necessity\u2019 debate\u2014the only question that gets through",
            ha="center", va="center", fontsize=9.2, color=INK)
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
