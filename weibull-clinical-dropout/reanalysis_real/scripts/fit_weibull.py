"""Fit a two-parameter Weibull cumulative-incidence model to digitized LTFU data.

Model:  F(t) = 1 - exp(-(t/lambda)^k)     (k>1 IFR, k<1 DFR, k=1 exponential)

Reads the digitized CSVs produced by digitize.py, fits by nonlinear least
squares, bootstraps a CI over the digitized points, and compares Weibull with
exponential (k=1) and log-normal alternatives by least-squares AIC.

All numbers are computed here from data/*.csv; nothing is hard-coded.
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results")
os.makedirs(RESULTS, exist_ok=True)
RNG = np.random.default_rng(20260714)


def weibull_cdf(t, k, lam):
    return 1.0 - np.exp(-(t / lam) ** k)


def expo_cdf(t, lam):
    return 1.0 - np.exp(-(t / lam))


def lognorm_cdf(t, mu, sigma):
    return norm.cdf((np.log(t) - mu) / sigma)


def load(path):
    df = pd.read_csv(path, comment="#")
    df = df.dropna()
    df = df[df["time_months"] > 0]
    df = df[(df["cum_ltfu_incidence"] > 0) & (df["cum_ltfu_incidence"] < 0.999)]
    return df["time_months"].to_numpy(float), df["cum_ltfu_incidence"].to_numpy(float)


def aic_ls(resid, n_params):
    n = len(resid)
    rss = float(np.sum(resid ** 2))
    return n * np.log(rss / n) + 2 * n_params, rss


def fit_one(t, f):
    # Weibull
    (k, lam), _ = curve_fit(weibull_cdf, t, f, p0=[1.0, np.median(t)],
                            bounds=([0.1, 0.1], [10, 1e3]), maxfev=20000)
    fit = weibull_cdf(t, k, lam)
    ss_res = np.sum((f - fit) ** 2)
    ss_tot = np.sum((f - f.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    aic_w, _ = aic_ls(f - fit, 2)
    # Exponential (k=1)
    (lam_e,), _ = curve_fit(expo_cdf, t, f, p0=[np.median(t)],
                            bounds=([0.1], [1e3]), maxfev=20000)
    aic_e, _ = aic_ls(f - expo_cdf(t, lam_e), 1)
    # Log-normal
    try:
        (mu, sig), _ = curve_fit(lognorm_cdf, t, f, p0=[np.log(np.median(t)), 1.0],
                                 bounds=([-5, 0.05], [10, 10]), maxfev=20000)
        aic_l, _ = aic_ls(f - lognorm_cdf(t, mu, sig), 2)
    except Exception:
        aic_l = np.nan
    # Bootstrap CI for k (resample digitized points)
    ks = []
    idx = np.arange(len(t))
    for _ in range(2000):
        s = RNG.choice(idx, len(idx), replace=True)
        if len(np.unique(t[s])) < 3:
            continue
        try:
            (kb, _lb), _ = curve_fit(weibull_cdf, t[s], f[s], p0=[k, lam],
                                     bounds=([0.1, 0.1], [10, 1e3]), maxfev=20000)
            ks.append(kb)
        except Exception:
            pass
    lo, hi = np.percentile(ks, [2.5, 97.5]) if ks else (np.nan, np.nan)
    return dict(k=k, k_lo=lo, k_hi=hi, lam=lam, r2=r2,
                aic_weibull=aic_w, aic_expo=aic_e, aic_lognorm=aic_l,
                n_points=len(t))


def main():
    specs = [
        ("TB-Ethiopia", "ethiopia_ltfu_cif.csv", "PMC10290796 Fig.1a (competing-risk CIF, 6 mo)"),
        ("TB-China", "china_ltfu_cif.csv", "PMC10167013 Fig.3 (All-TB KM retention, 12 mo)"),
        ("ART/HIV-Ethiopia", "art_ltfu_cif.csv", "PMC12953970 Fig.1A (retention KM, months)"),
        ("HIV-Maputo-ATT", "hiv_maputo_att_ltfu_cif.csv", "PMC13037074 Fig.3 (ATT retention KM, 0-80 mo)"),
        ("HIV-Maputo-BTT", "hiv_maputo_btt_ltfu_cif.csv", "PMC13037074 Fig.3 (BTT retention KM, 0-80 mo)"),
        ("HIV-Malawi-pre", "hiv_malawi_pre_ltfu_cif.csv", "PMC13191892 Fig.1 (pre-intervention care KM, 0-12 mo)"),
        ("HIV-Gambella", "hiv_gambella_ltfu_cif.csv", "PMC12903592 Fig.2 (overall LTFU KM, 12-48 mo)"),
        ("Antipsychotic", "antipsychotic_ltfu_cif.csv", "PMC12437960 (time-to-discontinuation KM, days)"),
    ]
    rows = []
    for name, fn, src in specs:
        t, f = load(os.path.join(DATA, fn))
        r = fit_one(t, f)
        r["dataset"] = name
        r["source"] = src
        pattern = ("IFR (k>1)" if r["k_lo"] > 1 else
                   "DFR (k<1)" if r["k_hi"] < 1 else
                   "indeterminate (CI spans 1)")
        r["hazard_pattern"] = pattern
        rows.append(r)
        print(f"{name}: k={r['k']:.3f} (95%CI {r['k_lo']:.3f}-{r['k_hi']:.3f}), "
              f"lambda={r['lam']:.2f}, R2={r['r2']:.4f}, n_pts={r['n_points']}, "
              f"AIC W/E/LN={r['aic_weibull']:.1f}/{r['aic_expo']:.1f}/{r['aic_lognorm']:.1f} "
              f"-> {pattern}")
    cols = ["dataset", "source", "k", "k_lo", "k_hi", "lam", "r2",
            "aic_weibull", "aic_expo", "aic_lognorm", "n_points", "hazard_pattern"]
    out = pd.DataFrame(rows)[cols]
    outpath = os.path.join(RESULTS, "weibull_fits.csv")
    out.to_csv(outpath, index=False)
    print("\nwrote", outpath)

    with open(os.path.join(RESULTS, "SUMMARY.md"), "w") as f:
        f.write("# Weibull fits to real TB LTFU curves (auto-generated)\n\n")
        f.write("| dataset | source | k (95% CI) | lambda | R2 | pattern |\n")
        f.write("|---|---|---|---|---|---|\n")
        for _, r in out.iterrows():
            f.write(f"| {r['dataset']} | {r['source']} | "
                    f"{r['k']:.2f} ({r['k_lo']:.2f}-{r['k_hi']:.2f}) | "
                    f"{r['lam']:.2f} | {r['r2']:.4f} | {r['hazard_pattern']} |\n")
        f.write("\nGenerated by scripts/fit_weibull.py from data/*.csv. "
                "The original 'uniform IFR across five countries' claim is not reproduced.\n")
    print("wrote", os.path.join(RESULTS, "SUMMARY.md"))


if __name__ == "__main__":
    main()
