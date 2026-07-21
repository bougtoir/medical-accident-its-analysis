"""Plot digitized LTFU data with fitted Weibull cumulative-incidence curves.

Reads data/*.csv and results/weibull_fits.csv (no hard-coded numbers) and
writes figures/weibull_real_fits.png.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)


def weibull_cdf(t, k, lam):
    return 1.0 - np.exp(-(t / lam) ** k)


def load(fn):
    df = pd.read_csv(os.path.join(DATA, fn), comment="#").dropna()
    return df[df["time_months"] > 0]


def main():
    fits = pd.read_csv(os.path.join(RESULTS, "weibull_fits.csv")).set_index("dataset")
    panels = [
        ("TB-Ethiopia", "ethiopia_ltfu_cif.csv", "Months"),
        ("TB-China", "china_ltfu_cif.csv", "Months"),
        ("ART/HIV-Ethiopia", "art_ltfu_cif.csv", "Months"),
        ("HIV-Maputo-ATT", "hiv_maputo_att_ltfu_cif.csv", "Months"),
        ("HIV-Maputo-BTT", "hiv_maputo_btt_ltfu_cif.csv", "Months"),
        ("HIV-Malawi-pre", "hiv_malawi_pre_ltfu_cif.csv", "Months"),
        ("HIV-Gambella", "hiv_gambella_ltfu_cif.csv", "Months"),
        ("Antipsychotic", "antipsychotic_ltfu_cif.csv", "Days"),
    ]
    fig, axes = plt.subplots(4, 2, figsize=(11, 15))
    for ax, (name, fn, unit) in zip(axes.ravel(), panels):
        df = load(fn)
        r = fits.loc[name]
        tmin = df["time_months"].min()
        tmax = df["time_months"].max()
        tt = np.linspace(max(0.01, tmin * 0.5), tmax, 300)
        color = "#c0392b" if r["k"] > 1 else "#2c6fbb"
        ax.scatter(df["time_months"], df["cum_ltfu_incidence"], s=16, color="#333",
                   label="Digitized data", zorder=3)
        ax.plot(tt, weibull_cdf(tt, r["k"], r["lam"]), color=color, lw=2,
                label=f"Weibull fit (k={r['k']:.2f}, 95%CI {r['k_lo']:.2f}-{r['k_hi']:.2f})")
        ax.set_title(f"{name}  \u2014  {r['hazard_pattern']}", fontsize=10.5)
        ax.set_xlabel(f"Time ({unit})")
        ax.set_ylabel("Cumulative LTFU incidence")
        ax.legend(fontsize=7.5, loc="best")
        ax.grid(alpha=0.3)
    fig.suptitle("Weibull fits to real, digitized treatment dropout curves\n"
                 "(seven infectious-disease curves + one non-infectious contrast): hazard shape "
                 "(k) is heterogeneous within TB and within HIV alike",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.975])
    out = os.path.join(FIGDIR, "weibull_real_fits.png")
    fig.savefig(out, dpi=150)
    print("wrote", out)


if __name__ == "__main__":
    main()
