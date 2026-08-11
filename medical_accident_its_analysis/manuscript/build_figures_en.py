#!/usr/bin/env python3
"""English figures for the rate-based re-analysis. All inputs come from the
reproducible data_primary CSVs and results/reanalysis_results.json (no hardcoded
numbers). Outputs PNGs to output/."""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(BASE)
DP = os.path.join(PROJ, "data_primary")
OUT = os.path.join(PROJ, "output")
os.makedirs(OUT, exist_ok=True)

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]
EN = {"内科": "Internal medicine", "外科": "Surgery", "整形外科": "Orthopaedics",
      "形成外科": "Plastic surgery", "産婦人科": "Obstetrics & gynaecology",
      "小児科": "Paediatrics", "精神科": "Psychiatry", "眼科": "Ophthalmology",
      "耳鼻咽喉科": "Otolaryngology", "泌尿器科": "Urology", "皮膚科": "Dermatology",
      "麻酔科": "Anaesthesiology"}


def load(name):
    df = pd.read_csv(os.path.join(DP, name)).set_index("specialty")
    df.columns = [int(c) for c in df.columns]
    return df.loc[CORE]


def _save(fig, outfile):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, outfile), dpi=200)
    plt.close(fig)


# Distinct visual styles for 12 specialties.  Colours are taken from the dark
# half of tab20 first, then two light indices, so no adjacent dark/light pair
# collides.  Markers and line styles ensure the figures remain interpretable
# in black-and-white print or for colour-vision-deficient readers.
_COLOR_IDX = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 1, 3]
_MARKERS = ["o", "s", "^", "v", "D", "P", "X", "*", "h", "p", "<", ">"]
_LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1)),
               (0, (1, 1)), (0, (5, 5)), (0, (5, 1, 1, 1, 1, 1)),
               (0, (3, 3)), (0, (10, 2)), (0, (1, 3))]


def _specialty_color(i):
    """Return a distinct colour for specialty i."""
    return plt.cm.tab20(_COLOR_IDX[i] / 19)


def _specialty_marker(i):
    return _MARKERS[i % len(_MARKERS)]


def _specialty_linestyle(i):
    return _LINESTYLES[i % len(_LINESTYLES)]


def plot_litigation_rate(P, L, bien, outfile, title):
    fig, ax = plt.subplots(figsize=(9, 6))
    for i, s in enumerate(CORE):
        rate = [1000.0 * L.loc[s, y] / P.loc[s, y] for y in bien]
        ax.plot(bien, rate, marker=_specialty_marker(i), ms=4, mfc="none",
                mew=0.8, label=EN[s], color=_specialty_color(i),
                ls=_specialty_linestyle(i), lw=1.2)
    ax.set_xlabel("Year")
    ax.set_ylabel("Closed malpractice claims per 1,000 physicians")
    ax.set_title(title)
    ax.legend(fontsize=7, ncol=2, loc="upper right")
    ax.grid(alpha=0.3)
    _save(fig, outfile)


def plot_physician_index(P, bien, outfile, title):
    fig, ax = plt.subplots(figsize=(9, 6))
    for i, s in enumerate(CORE):
        base = P.loc[s, bien[0]]
        idx = [100.0 * P.loc[s, y] / base for y in bien]
        ax.plot(bien, idx, marker=_specialty_marker(i), ms=4, mfc="none",
                mew=0.8, label=EN[s], color=_specialty_color(i),
                ls=_specialty_linestyle(i), lw=1.2)
    ax.axhline(100, color="k", lw=0.8, ls="--")
    ax.set_xlabel("Year")
    ax.set_ylabel("Physicians (2008 = 100)")
    ax.set_title(title)
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    ax.grid(alpha=0.3)
    _save(fig, outfile)


def plot_equivalence(eq, outfile, title, margin1=0.01, margin2=0.02):
    fig, ax = plt.subplots(figsize=(9, 4))
    labels = ["Physician growth", "Hospital growth"]
    ys = [1, 0]
    for e, y in zip(eq, ys):
        ax.plot([e["ci90_low"], e["ci90_high"]], [y, y], "b-", lw=2)
        ax.plot(e["coef_per_SD"], y, "bo", ms=7)
    for mg, c in [(margin1, "orange"), (margin2, "red")]:
        ax.axvline(mg, color=c, ls="--", lw=1, label=f"±{int(mg*100)}% margin")
        ax.axvline(-mg, color=c, ls="--", lw=1)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Effect of +1 SD litigation rate on biennial log-growth (90% CI)")
    ax.set_title(title)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_ylim(-0.6, 1.6)
    _save(fig, outfile)


def plot_counts_vs_rates(P, L, bien, outfile, title, colored=True):
    """Scatter of physician growth vs lagged litigation exposure, counts vs rates.

    If colored=True, points are coloured by specialty and a legend is added so
    the reader can identify which specialties drive any apparent outliers.
    """
    dgrow = {}
    for i, s in enumerate(CORE):
        for j, y in enumerate(bien[1:], 1):
            g = np.log(P.loc[s, y]) - np.log(P.loc[s, bien[j-1]])
            cnt = L.loc[s, bien[j-1]]
            rate = 1000.0 * L.loc[s, bien[j-1]] / P.loc[s, bien[j-1]]
            dgrow.setdefault("g", []).append(g)
            dgrow.setdefault("cnt", []).append(cnt)
            dgrow.setdefault("rate", []).append(rate)
            dgrow.setdefault("specialty", []).append(s)
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    if colored:
        for i, s in enumerate(CORE):
            mask = np.array(dgrow["specialty"]) == s
            color = _specialty_color(i)
            marker = _specialty_marker(i)
            kw = dict(s=35, alpha=0.85, marker=marker, edgecolors="black",
                      facecolors=color, linewidths=0.6, label=EN[s])
            axs[0].scatter(np.array(dgrow["cnt"])[mask],
                           np.array(dgrow["g"])[mask], **kw)
            axs[1].scatter(np.array(dgrow["rate"])[mask],
                           np.array(dgrow["g"])[mask], **kw)
        axs[0].legend(fontsize=6, ncol=2, loc="upper right")
        axs[1].legend(fontsize=6, ncol=2, loc="upper right")
    else:
        axs[0].scatter(dgrow["cnt"], dgrow["g"], s=12, alpha=0.6)
        axs[1].scatter(dgrow["rate"], dgrow["g"], s=12, alpha=0.6, color="green")
    axs[0].set_xlabel("Litigation COUNT (lagged)")
    axs[0].set_ylabel("Biennial physician log-growth")
    axs[0].set_title("(a) Count exposure (size-confounded)")
    axs[1].set_xlabel("Litigation RATE per 1,000 physicians (lagged)")
    axs[1].set_title("(b) Rate exposure (size-adjusted)")
    for a in axs:
        a.axhline(0, color="k", lw=0.6)
        a.grid(alpha=0.3)
    fig.suptitle(title)
    _save(fig, outfile)


def main():
    P, L, H = (load("physicians_by_specialty.csv"),
               load("litigation_by_specialty.csv"),
               load("facilities_hospital_by_specialty.csv"))
    res = json.load(open(os.path.join(PROJ, "results", "reanalysis_results.json")))
    bien = res["grid"]["biennial_years"]

    # Base figures (retained for other manuscripts)
    plot_litigation_rate(
        P, L, bien, "fig1_litigation_rate.png",
        "Figure 1. Litigation rate by specialty (rate, not count), 2008–2024")
    plot_physician_index(
        P, bien, "fig2_physician_index.png",
        "Figure 2. Physician workforce by specialty, indexed to 2008")
    plot_equivalence(
        res["equivalence"], "fig3_equivalence.png",
        "Figure 3. Equivalence (TOST): litigation-rate effect vs. null")
    plot_counts_vs_rates(
        P, L, bien, "fig4_counts_vs_rates.png",
        "Figure 4. Counts vs. rates: association disappears under size adjustment",
        colored=False)

    # Healthcare Analytics-specific figures with correct numbering
    plot_equivalence(
        res["equivalence"], "ha_Figure_1.png",
        "Figure 1. Equivalence (TOST): litigation-rate effect vs. null")
    plot_counts_vs_rates(
        P, L, bien, "ha_Figure_2.png",
        "Figure 2. Counts vs. rates: association disappears under size adjustment",
        colored=True)
    plot_litigation_rate(
        P, L, bien, "ha_Supplementary_Figure_1.png",
        "Supplementary Figure 1. Litigation rate by specialty (rate, not count), 2008–2024")
    plot_physician_index(
        P, bien, "ha_Supplementary_Figure_2.png",
        "Supplementary Figure 2. Physician workforce by specialty, indexed to 2008")

    print("wrote fig1-4 and ha_* figure files to", OUT)


if __name__ == "__main__":
    main()
