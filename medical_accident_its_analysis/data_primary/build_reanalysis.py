#!/usr/bin/env python3
"""Rate-based reanalysis on genuine primary data (addresses Reviewer 2).

Inputs (all reproducible, provenance-tracked):
  physicians_by_specialty.csv   biennial 2004-2024 (measured, 主たる診療科別)
  litigation_by_specialty.csv   annual 2008-2024 (Supreme Court closed cases)
  facilities_hospital_by_specialty.csv  annual 2008-2024 (一般+精神科病院)

Design (agreed with author; supersedes the annual VAR/Granger which was not
defensible with interpolated biennial data):
  * Rates, not counts: exposure = litigation cases per 1,000 physicians, so
    associations are not driven by specialty size.
  * Measured points only: PRIMARY analysis on the biennial physician grid
    (2008,2010,...,2024 = 9 measured waves); no interpolated observations.
  * Panel across the 12 core specialties with specialty and wave fixed effects;
    outcome = biennial log-change in physicians / hospitals; predictor = the
    litigation rate at the start of each interval (lag).
  * JOCS-CP (Japan Obstetric Compensation System, launched Jan-2009) entered as
    an obstetrics-specific post-2009 indicator (structural confounder).
  * Sensitivity: (a) annual hospital panel 2008-2024; (b) linear-interpolation
    annual physician panel. Inference uses standard errors clustered by
    specialty, so the degrees of freedom are the number of clusters minus one
    (12 - 1 = 11); the interpolated observation count does NOT inflate them.
    (c) counts-vs-rates contrast.
All numbers are written to results/reanalysis_results.json for the manuscript.
"""
import os, json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")
os.makedirs(RES, exist_ok=True)

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]
CORE_EN = {"内科": "Internal medicine", "外科": "Surgery",
           "整形外科": "Orthopaedics", "形成外科": "Plastic surgery",
           "産婦人科": "Obstetrics & gynaecology", "小児科": "Paediatrics",
           "精神科": "Psychiatry", "眼科": "Ophthalmology",
           "耳鼻咽喉科": "Otolaryngology", "泌尿器科": "Urology",
           "皮膚科": "Dermatology", "麻酔科": "Anaesthesiology"}


def load(name):
    df = pd.read_csv(os.path.join(HERE, name))
    df = df.set_index("specialty")
    df.columns = [int(c) for c in df.columns]
    return df.loc[CORE]


def phys_frame(interpolate=False):
    P = load("physicians_by_specialty.csv")
    if interpolate:
        P = P.reindex(columns=range(P.columns.min(), P.columns.max() + 1))
        P = P.interpolate(axis=1, method="linear")
    return P


def long_panel(years, P=None):
    if P is None:
        P = phys_frame()
    L = load("litigation_by_specialty.csv")
    H = load("facilities_hospital_by_specialty.csv")
    rows = []
    for s in CORE:
        for y in years:
            if y in P.columns and not pd.isna(P.loc[s, y]) \
                    and y in L.columns and y in H.columns:
                rows.append(dict(specialty=s, year=y,
                                 phys=P.loc[s, y], lit=L.loc[s, y],
                                 hosp=H.loc[s, y]))
    d = pd.DataFrame(rows)
    d["litrate"] = 1000.0 * d["lit"] / d["phys"]          # cases / 1000 phys
    d["jocscp"] = ((d.specialty == "産婦人科") & (d.year >= 2009)).astype(int)
    return d


def add_changes(d, step):
    """log-changes over `step` years and lagged predictors, within specialty."""
    d = d.sort_values(["specialty", "year"]).copy()
    g = d.groupby("specialty")
    d["dlog_phys"] = g["phys"].transform(lambda x: np.log(x) - np.log(x.shift(1)))
    d["dlog_hosp"] = g["hosp"].transform(lambda x: np.log(x) - np.log(x.shift(1)))
    d["litrate_lag"] = g["litrate"].shift(1)
    d["lit_lag"] = g["lit"].shift(1)          # raw count (for counts-vs-rates)
    d["jocscp_lag"] = g["jocscp"].shift(1)
    return d


def panel_fit(d, outcome, predictor, label, year_fe=True):
    dd = d.dropna(subset=[outcome, predictor]).copy()
    rhs = f"{predictor} + C(specialty)"
    if year_fe:
        rhs += " + C(year)"
    if "jocscp_lag" in dd and dd["jocscp_lag"].nunique() > 1:
        rhs += " + jocscp_lag"
    m = smf.ols(f"{outcome} ~ {rhs}", data=dd).fit(
        cov_type="cluster", cov_kwds={"groups": dd["specialty"]})
    coef = float(m.params[predictor])
    return {
        "label": label, "outcome": outcome, "predictor": predictor,
        "n_obs": int(dd.shape[0]), "n_specialties": int(dd.specialty.nunique()),
        "n_waves": int(dd.year.nunique()),
        "coef": coef, "se": float(m.bse[predictor]),
        "ci_low": float(m.conf_int().loc[predictor, 0]),
        "ci_high": float(m.conf_int().loc[predictor, 1]),
        "p": float(m.pvalues[predictor]),
        "direction": "negative" if coef < 0 else "positive",
        "jocscp_coef": (float(m.params["jocscp_lag"])
                        if "jocscp_lag" in m.params else None),
        "jocscp_p": (float(m.pvalues["jocscp_lag"])
                     if "jocscp_lag" in m.params else None),
    }


def equivalence_tost(d, outcome, margins=(0.01, 0.02)):
    """TOST equivalence test on the effect of a 1-SD higher lagged litigation
    rate on `outcome` (biennial log-change). Exposure standardised so the
    coefficient = expected log-change per +1 SD of litigation rate; margins are
    interpretable as fractional workforce change (0.01 = 1%). df = clusters-1
    (conservative for cluster-robust SE)."""
    dd = d.dropna(subset=[outcome, "litrate_lag"]).copy()
    dd["z"] = (dd["litrate_lag"] - dd["litrate_lag"].mean()) / dd["litrate_lag"].std()
    rhs = "z + C(specialty) + C(year)"
    if dd["jocscp_lag"].nunique() > 1:
        rhs += " + jocscp_lag"
    m = smf.ols(f"{outcome} ~ {rhs}", data=dd).fit(
        cov_type="cluster", cov_kwds={"groups": dd["specialty"]})
    coef, se = float(m.params["z"]), float(m.bse["z"])
    df = dd["specialty"].nunique() - 1
    tcrit = stats.t.ppf(0.95, df)
    ci90 = (coef - tcrit * se, coef + tcrit * se)
    out = {"outcome": outcome, "coef_per_SD": coef, "se": se, "df": df,
           "ci90_low": ci90[0], "ci90_high": ci90[1],
           "sd_litrate": float(dd["litrate_lag"].std()), "tests": []}
    for mg in margins:
        p_low = stats.t.sf((coef + mg) / se, df)      # H0: coef <= -mg
        p_high = stats.t.cdf((coef - mg) / se, df)     # H0: coef >= +mg
        p_tost = max(p_low, p_high)
        out["tests"].append({
            "margin": mg, "p_tost": float(p_tost),
            "equivalent": bool(ci90[0] > -mg and ci90[1] < mg),
            "interpretation": f"a 1-SD higher litigation rate shifts biennial "
                              f"{'physician' if 'phys' in outcome else 'facility'} "
                              f"growth by <{int(mg*100)}%"})
    return out


def per_specialty_corr(d):
    """Descriptive Spearman corr: litigation rate level vs physician growth."""
    from scipy.stats import spearmanr
    out = {}
    for s in CORE:
        ds = d[d.specialty == s].dropna(subset=["dlog_phys", "litrate_lag"])
        if ds.shape[0] >= 4:
            r, p = spearmanr(ds["litrate_lag"], ds["dlog_phys"])
            out[CORE_EN[s]] = {"rho": float(r), "p": float(p), "n": int(ds.shape[0])}
    return out


def main():
    res = {"grid": {}, "descriptive": {}, "primary": [], "sensitivity": []}

    # ---- biennial measured grid (PRIMARY) ----
    bien = list(range(2008, 2025, 2))
    dbi = add_changes(long_panel(bien), 2)
    res["grid"]["biennial_years"] = bien
    res["grid"]["n_measured_waves"] = len(bien)

    # descriptive rate levels (first vs last wave)
    lp = long_panel(bien)
    desc = {}
    for s in CORE:
        a = lp[(lp.specialty == s) & (lp.year == bien[0])].iloc[0]
        b = lp[(lp.specialty == s) & (lp.year == bien[-1])].iloc[0]
        desc[CORE_EN[s]] = {
            "phys_first": int(a.phys), "phys_last": int(b.phys),
            "litrate_first": round(float(a.litrate), 3),
            "litrate_last": round(float(b.litrate), 3),
            "hosp_first": int(a.hosp), "hosp_last": int(b.hosp)}
    res["descriptive"]["biennial_first_last"] = {"first": bien[0], "last": bien[-1],
                                                  "by_specialty": desc}
    res["descriptive"]["spearman_litrate_vs_physgrowth"] = per_specialty_corr(dbi)

    # PRIMARY panel models (rate exposure)
    res["primary"].append(panel_fit(dbi, "dlog_phys", "litrate_lag",
                                    "Biennial physician growth ~ lagged litigation rate"))
    res["primary"].append(panel_fit(dbi, "dlog_hosp", "litrate_lag",
                                    "Biennial hospital growth ~ lagged litigation rate"))

    # EQUIVALENCE (TOST): is the litigation-rate effect equivalent to null?
    res["equivalence"] = [equivalence_tost(dbi, "dlog_phys"),
                          equivalence_tost(dbi, "dlog_hosp")]

    # counts-vs-rates contrast (same design, raw count exposure)
    res["sensitivity"].append(panel_fit(dbi, "dlog_phys", "lit_lag",
                              "COUNTS contrast: physician growth ~ lagged litigation COUNT"))

    # reverse direction: does workforce predict later litigation rate?
    drev = dbi.copy()
    drev["dlit"] = drev.groupby("specialty")["litrate"].transform(
        lambda x: x - x.shift(1))
    drev["phys_lag"] = drev.groupby("specialty")["phys"].shift(1)
    rev = drev.dropna(subset=["dlit", "phys_lag"])
    mrev = smf.ols("dlit ~ np.log(phys_lag) + C(specialty) + C(year)", data=rev).fit(
        cov_type="cluster", cov_kwds={"groups": rev["specialty"]})
    res["primary"].append({"label": "Reverse: change in litigation rate ~ lagged log physicians",
                           "coef": float(mrev.params["np.log(phys_lag)"]),
                           "p": float(mrev.pvalues["np.log(phys_lag)"]),
                           "n_obs": int(rev.shape[0])})

    # ---- SENSITIVITY (a): annual hospital panel 2008-2024 ----
    # hospital & litigation are annual; physician denominator interpolated
    ann = list(range(2008, 2025))
    Pint = phys_frame(interpolate=True)
    dan = add_changes(long_panel(ann, P=Pint), 1)
    res["sensitivity"].append(panel_fit(dan, "dlog_hosp", "litrate_lag",
                              "Annual hospital growth ~ lagged litigation rate (2008-2024)"))

    # ---- SENSITIVITY (b): linear-interpolated annual physicians ----
    dp = add_changes(long_panel(ann, P=Pint), 1)
    fit_interp = panel_fit(dp, "dlog_phys", "litrate_lag",
                           "SENSITIVITY interpolated-annual physician growth ~ lag rate")
    fit_interp["note"] = ("physicians linearly interpolated between the %d measured "
                          "biennial waves; standard errors are clustered by specialty so "
                          "inference df = clusters - 1 = %d and the interpolated "
                          "observation count does not inflate the degrees of freedom"
                          % (len(bien), dp["specialty"].nunique() - 1))
    res["sensitivity"].append(fit_interp)

    with open(os.path.join(RES, "reanalysis_results.json"), "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    # console summary
    print("PRIMARY (biennial measured grid, rate exposure):")
    for r in res["primary"]:
        print(" ", r["label"])
        print("    coef=%.5f p=%.4f n=%s" % (r.get("coef", float("nan")),
              r.get("p", float("nan")), r.get("n_obs")))
    print("\nEQUIVALENCE (TOST, per +1 SD litigation rate):")
    for e in res["equivalence"]:
        print("  %s: coef/SD=%+.4f 90%%CI[%+.4f,%+.4f]" % (
            e["outcome"], e["coef_per_SD"], e["ci90_low"], e["ci90_high"]))
        for t in e["tests"]:
            print("     margin +-%.0f%%: p_TOST=%.4f equivalent=%s" % (
                t["margin"] * 100, t["p_tost"], t["equivalent"]))
    print("\nSENSITIVITY:")
    for r in res["sensitivity"]:
        print("  %s: coef=%.5f p=%.4f n=%s" % (r["label"], r["coef"], r["p"],
              r["n_obs"]))


if __name__ == "__main__":
    main()
