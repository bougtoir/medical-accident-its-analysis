#!/usr/bin/env python3
"""Rate-based reanalysis on genuine primary data (addresses Reviewer 2).

Inputs (all reproducible, provenance-tracked):
  physicians_by_specialty.csv   biennial 2004-2024 (measured, 主たる診療科別)
  litigation_by_specialty.csv   annual 2008-2024 (Supreme Court closed cases)
  facilities_hospital_by_specialty.csv  annual 2008-2024 (一般+精神科病院)
  medsafe_accidents_by_specialty.csv   annual 2015-2025 (JMSR/MAIS report counts)

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
    annual physician panel; (c) counts-vs-rates contrast; (d) annual hospital
    model 2016-2024 additionally controlling for the JMSR report rate, to test
    whether litigation findings are confounded by or collinear with broader
    medical accident reporting. Inference uses standard errors clustered by
    specialty, so the degrees of freedom are the number of clusters minus one
    (12 - 1 = 11); the interpolated observation count does NOT inflate them.
All numbers are written to results/reanalysis_results.json for the manuscript.
"""
import os, json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


def _cluster_p(coef, se, df):
    """Two-sided p-value from a t(df) distribution with cluster-robust SE."""
    if se is None or se == 0:
        return None
    t = coef / se
    return float(2.0 * stats.t.sf(abs(t), df))


def holm_adjust(pvals):
    """Holm step-down p-value adjustment for a family of tests."""
    pvals = [p if p is not None else 1.0 for p in pvals]
    n = len(pvals)
    if n == 0:
        return []
    arr = np.array(pvals, dtype=float)
    order = np.argsort(arr)
    sorted_p = arr[order]
    adj = np.empty(n)
    adj[0] = min(sorted_p[0] * n, 1.0)
    for i in range(1, n):
        adj[i] = min(max(adj[i - 1], sorted_p[i] * (n - i)), 1.0)
    # Enforce monotonicity and cap at 1
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(n)
    out[order] = adj
    return out.tolist()


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

# Procedure-oriented specialties used in heterogeneity checks.
SURGICAL = ["外科", "整形外科", "産婦人科", "泌尿器科"]



def load(name):
    df = pd.read_csv(os.path.join(HERE, name))
    df = df.set_index("specialty")
    df.columns = [int(c) for c in df.columns]
    return df.loc[CORE]


def load_jmsr():
    """JMSR/MAIS medical-accident report counts by specialty (2015 onward).
    The released CSV already contains broad core-specialty rows."""
    path = os.path.join(os.path.dirname(HERE), "data",
                        "medsafe_accidents_by_specialty.csv")
    df = pd.read_csv(path)
    df = df[df["specialty"].isin(CORE)].set_index("specialty")
    year_cols = [c for c in df.columns if str(c).isdigit()]
    df = df[year_cols].astype(float)
    df.columns = [int(c) for c in df.columns]
    return df.loc[CORE]


def load_media():
    """Nikkei Telecom 21 annual article counts (keywords: 医療事故 + 医療過誤),
    2004-2018. These are total national newspaper coverage, not specialty-specific."""
    path = os.path.join(os.path.dirname(HERE), "data",
                        "nikkei_media_counts_2004_2018.csv")
    df = pd.read_csv(path)
    df = df.set_index("year")
    return df["total_articles"].astype(float)


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
    # Small-cluster correction: inference uses t(G-1) rather than the large-
    # sample residual df. This is conservative when only 12 clusters are available.
    G = int(dd.specialty.nunique())
    df = G - 1
    coef = float(m.params[predictor])
    se = float(m.bse[predictor])
    tstat = coef / se if se > 0 else 0.0
    p = 2.0 * stats.t.sf(abs(tstat), df)
    tcrit95 = stats.t.ppf(0.975, df)
    ci_low, ci_high = coef - tcrit95 * se, coef + tcrit95 * se
    jocscp_coef = (float(m.params["jocscp_lag"])
                   if "jocscp_lag" in m.params else None)
    jocscp_se = (float(m.bse["jocscp_lag"])
                 if "jocscp_lag" in m.bse else None)
    jocscp_t = jocscp_coef / jocscp_se if jocscp_se else None
    jocscp_p = (2.0 * stats.t.sf(abs(jocscp_t), df)
                if jocscp_t is not None else None)
    return {
        "label": label, "outcome": outcome, "predictor": predictor,
        "n_obs": int(dd.shape[0]), "n_specialties": G,
        "n_waves": int(dd.year.nunique()),
        "coef": coef, "se": se, "t": tstat, "df": df,
        "ci_low": ci_low, "ci_high": ci_high, "p": p,
        "direction": "negative" if coef < 0 else "positive",
        "jocscp_coef": jocscp_coef, "jocscp_se": jocscp_se,
        "jocscp_t": jocscp_t, "jocscp_df": df, "jocscp_p": jocscp_p,
    }


def panel_fit_with_trends(d, outcome, predictor, label):
    """Primary model augmented with specialty-specific linear time trends."""
    dd = d.dropna(subset=[outcome, predictor]).copy()
    rhs = f"{predictor} + C(specialty) + C(year) + C(specialty):year"
    if "jocscp_lag" in dd and dd["jocscp_lag"].nunique() > 1:
        rhs += " + jocscp_lag"
    m = smf.ols(f"{outcome} ~ {rhs}", data=dd).fit(
        cov_type="cluster", cov_kwds={"groups": dd["specialty"]})
    G = int(dd.specialty.nunique())
    df = G - 1
    coef = float(m.params[predictor])
    se = float(m.bse[predictor])
    tstat = coef / se if se > 0 else 0.0
    p = 2.0 * stats.t.sf(abs(tstat), df)
    tcrit95 = stats.t.ppf(0.975, df)
    ci_low, ci_high = coef - tcrit95 * se, coef + tcrit95 * se
    return {
        "label": label, "outcome": outcome, "predictor": predictor,
        "n_obs": int(dd.shape[0]), "n_specialties": G,
        "n_waves": int(dd.year.nunique()),
        "coef": coef, "se": se, "t": tstat, "df": df,
        "ci_low": ci_low, "ci_high": ci_high, "p": p,
        "direction": "negative" if coef < 0 else "positive",
    }


def heterogeneity_fit(d, outcome, predictor, label, group_col, group_kind):
    """Estimate a model with an interaction between the exposure and a
    time-invariant binary group indicator (e.g. high baseline litigation or
    surgical specialty). Only the interaction is included; a main effect for
    the group would be collinear with specialty fixed effects."""
    dd = d.dropna(subset=[outcome, predictor]).copy()
    if group_kind == "litrate":
        # high-litigation = above-median specialty mean lagged litigation rate
        group_mean = dd.groupby("specialty")[group_col].transform("mean")
        dd["high_group"] = (group_mean > group_mean.median()).astype(int)
        group_label = "high litigation"
    elif group_kind == "surgical":
        dd["high_group"] = dd["specialty"].isin(SURGICAL).astype(int)
        group_label = "surgical"
    else:
        raise ValueError(group_kind)
    rhs = f"{predictor} + {predictor}:high_group + C(specialty) + C(year)"
    if "jocscp_lag" in dd and dd["jocscp_lag"].nunique() > 1:
        rhs += " + jocscp_lag"
    m = smf.ols(f"{outcome} ~ {rhs}", data=dd).fit(
        cov_type="cluster", cov_kwds={"groups": dd["specialty"]})
    G = int(dd.specialty.nunique())
    df = G - 1

    def _inf(coef, se):
        t = coef / se if se > 0 else 0.0
        p = 2.0 * stats.t.sf(abs(t), df)
        return coef, se, t, p

    main_coef = float(m.params[predictor])
    main_se = float(m.bse[predictor])
    main_t, main_p = _inf(main_coef, main_se)[2:]
    interact_coef = float(m.params[f"{predictor}:high_group"])
    interact_se = float(m.bse[f"{predictor}:high_group"])
    interact_t, interact_p = _inf(interact_coef, interact_se)[2:]
    return {
        "label": label, "outcome": outcome, "predictor": predictor,
        "group": group_label,
        "n_obs": int(dd.shape[0]), "n_specialties": G,
        "n_waves": int(dd.year.nunique()),
        "coef": main_coef, "se": main_se, "t": main_t, "df": df, "p": main_p,
        "interact_coef": interact_coef, "interact_se": interact_se,
        "interact_t": interact_t, "interact_p": interact_p,
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
    # Power / minimum detectable effect for the per-SD coefficient
    # MDE = smallest effect detectable (two-sided, 80% power) given cluster-robust SE
    t_975 = stats.t.ppf(0.975, df)
    t_80 = stats.t.ppf(0.80, df)
    mde_80 = float((t_975 + t_80) * se)
    out = {"outcome": outcome, "coef_per_SD": coef, "se": se, "df": df,
           "ci90_low": ci90[0], "ci90_high": ci90[1],
           "mde_80pct": mde_80 * 100,
           "sd_litrate": float(dd["litrate_lag"].std()), "tests": []}
    for mg in margins:
        p_low = stats.t.sf((coef + mg) / se, df)      # H0: coef <= -mg
        p_high = stats.t.cdf((coef - mg) / se, df)     # H0: coef >= +mg
        p_tost = max(p_low, p_high)
        # Power to declare equivalence within this margin if the true effect is zero
        power_eq = 2.0 * stats.t.cdf(mg / se, df) - 1.0
        out["tests"].append({
            "margin": mg, "p_tost": float(p_tost),
            "equivalent": bool(ci90[0] > -mg and ci90[1] < mg),
            "power_if_null": float(power_eq),
            "interpretation": f"a 1-SD higher litigation rate shifts biennial "
                              f"{'physician' if 'phys' in outcome else 'facility'} "
                              f"growth by <{int(mg*100)}%"})
    return out


def bootstrap_cluster(d, outcome, predictor, label, R=1999, seed=42):
    """Cluster block bootstrap for the `predictor` coefficient.

    Resamples specialty clusters with replacement, re-fits the panel model,
    and reports (a) a percentile bootstrap 95% CI for the coefficient and
    (b) a bootstrap p-value based on the distribution of |t| statistics.
    This is a small-cluster robustness check rather than a replacement for
    the analytical t(G-1) inference.
    """
    dd = d.dropna(subset=[outcome, predictor]).copy()
    clusters = dd["specialty"].unique()
    rng = np.random.default_rng(seed)

    # observed fit and t-statistic
    obs = panel_fit(dd, outcome, predictor, label, year_fe=True)
    t_obs = abs(float(obs["t"]))

    coefs, t_boot = [], []
    for b in range(R):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        blocks = []
        for i, cl in enumerate(sampled):
            sub = dd[dd.specialty == cl].copy()
            sub["cluster_boot"] = f"{cl}_{b}_{i}"
            blocks.append(sub)
        dbb = pd.concat(blocks, ignore_index=True)
        rhs = f"{predictor} + C(specialty)"
        if dbb["year"].nunique() > 1:
            rhs += " + C(year)"
        if "jocscp_lag" in dbb and dbb["jocscp_lag"].nunique() > 1:
            rhs += " + jocscp_lag"
        try:
            m = smf.ols(f"{outcome} ~ {rhs}", data=dbb).fit(
                cov_type="cluster", cov_kwds={"groups": dbb["cluster_boot"]},
                disp=0)
            coef_b = float(m.params[predictor])
            se_b = float(m.bse[predictor])
            df_b = max(dbb["cluster_boot"].nunique() - 1, 1)
            t_b = abs(coef_b / se_b) if se_b > 0 else 0.0
            coefs.append(coef_b)
            t_boot.append(t_b)
        except Exception:
            continue
    coefs = np.array(coefs)
    p_bootstrap = float(np.mean(np.array(t_boot) >= t_obs)) if t_boot else None
    ci = (float(np.percentile(coefs, 2.5)),
          float(np.percentile(coefs, 97.5))) if len(coefs) else (None, None)
    return {
        "label": label, "outcome": outcome, "predictor": predictor,
        "R": len(t_boot), "t_obs": t_obs, "p_bootstrap": p_bootstrap,
        "coef_boot_mean": float(np.mean(coefs)) if len(coefs) else None,
        "coef_boot_ci_low": ci[0], "coef_boot_ci_high": ci[1],
        "obs_coef": obs["coef"], "obs_p": obs["p"]
    }


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


def jmsr_lit_correlation(lit, jmsr):
    """Correlation between litigation counts and JMSR report counts over the
    overlapping 2015-2024 window, both pooled and within-specialty detrended."""
    years = sorted(set(lit.columns) & set(jmsr.columns))
    x_raw, y_raw = [], []
    for s in CORE:
        for y in years:
            if pd.isna(lit.loc[s, y]) or pd.isna(jmsr.loc[s, y]):
                continue
            x_raw.append(float(lit.loc[s, y]))
            y_raw.append(float(jmsr.loc[s, y]))
    r_raw, p_raw = stats.pearsonr(x_raw, y_raw)

    resid_x, resid_y = [], []
    for s in CORE:
        vals_x = [float(lit.loc[s, y]) for y in years
                  if not pd.isna(lit.loc[s, y]) and not pd.isna(jmsr.loc[s, y])]
        vals_y = [float(jmsr.loc[s, y]) for y in years
                  if not pd.isna(lit.loc[s, y]) and not pd.isna(jmsr.loc[s, y])]
        if len(vals_x) >= 4:
            t = np.arange(len(vals_x))
            x_d = np.array(vals_x) - np.polyval(np.polyfit(t, vals_x, 1), t)
            y_d = np.array(vals_y) - np.polyval(np.polyfit(t, vals_y, 1), t)
            resid_x.extend(x_d.tolist())
            resid_y.extend(y_d.tolist())
    r_det, p_det = stats.pearsonr(resid_x, resid_y)
    return {
        "years": years,
        "n_specialty_years": len(x_raw),
        "pooled_r": float(r_raw),
        "pooled_p": float(p_raw),
        "detrended_r": float(r_det),
        "detrended_p": float(p_det),
    }


def jmsr_hospital_sensitivity():
    """Annual hospital growth 2016-2024, controlling for both litigation rate
    and JMSR report rate (rates per 1,000 physicians). Tests whether the
    litigation result is confounded by or collinear with broader accident
    reporting; uses the interpolated physician denominator for both rates."""
    Pint = phys_frame(interpolate=True)
    L = load("litigation_by_specialty.csv")
    H = load("facilities_hospital_by_specialty.csv")
    M = load_jmsr()
    years = list(range(2016, 2025))
    rows = []
    for s in CORE:
        for y in years:
            prev = y - 1
            if prev not in Pint.columns or y not in H.columns \
                    or prev not in L.columns or prev not in M.columns:
                continue
            p_prev = Pint.loc[s, prev]
            h_prev = H.loc[s, prev]
            h_now = H.loc[s, y]
            l_prev = L.loc[s, prev]
            m_prev = M.loc[s, prev]
            if pd.isna(p_prev) or pd.isna(h_prev) or pd.isna(h_now) \
                    or pd.isna(l_prev) or pd.isna(m_prev):
                continue
            rows.append({
                "specialty": s,
                "year": y,
                "dlog_hosp": np.log(h_now) - np.log(h_prev),
                "litrate": 1000.0 * l_prev / p_prev,
                "medrate": 1000.0 * m_prev / p_prev,
            })
    d = pd.DataFrame(rows)
    m = smf.ols("dlog_hosp ~ litrate + medrate + C(specialty) + C(year)",
                data=d).fit(cov_type="cluster", cov_kwds={"groups": d["specialty"]})
    df = d.specialty.nunique() - 1
    def _p(coef, se):
        t = coef / se if se > 0 else 0.0
        return 2.0 * stats.t.sf(abs(t), df)
    return {
        "label": "JMSR-adjusted annual hospital growth (2016-2024) ~ lit rate + JMSR rate",
        "outcome": "dlog_hosp",
        "n_obs": int(d.shape[0]),
        "n_specialties": int(d.specialty.nunique()),
        "n_waves": int(d.year.nunique()),
        "lit_coef": float(m.params["litrate"]),
        "lit_se": float(m.bse["litrate"]),
        "lit_p": _p(m.params["litrate"], m.bse["litrate"]),
        "med_coef": float(m.params["medrate"]),
        "med_se": float(m.bse["medrate"]),
        "med_p": _p(m.params["medrate"], m.bse["medrate"]),
        "r_lit_med": float(d[["litrate", "medrate"]].corr().iloc[0, 1]),
    }


def media_lit_correlation(lit, media):
    """Correlation between total annual newspaper coverage and (a) total
    litigation counts and (b) the lagged specialty-specific litigation rate
    in the 2009-2018 window for which media data are available."""
    years = sorted(set(lit.columns) & set(media.index) & set(range(2008, 2019)))
    # total counts
    total_lit = lit[years].sum(axis=0)
    r_total, p_total = stats.pearsonr(media.loc[years].values, total_lit.values)

    # within-panel correlation: lagged litrate vs media (next year)
    Pint = phys_frame(interpolate=True)
    litrate_vals, media_vals = [], []
    for s in CORE:
        for y in years:
            if pd.isna(Pint.loc[s, y]) or pd.isna(lit.loc[s, y]) or pd.isna(media.loc[y]):
                continue
            litrate_vals.append(1000.0 * lit.loc[s, y] / Pint.loc[s, y])
            media_vals.append(media.loc[y])
    r_panel, p_panel = stats.pearsonr(litrate_vals, media_vals)
    return {
        "years": years,
        "total_r": float(r_total),
        "total_p": float(p_total),
        "panel_r": float(r_panel),
        "panel_p": float(p_panel),
        "n_total": len(years),
        "n_panel": len(litrate_vals),
    }


def media_hospital_sensitivity():
    """Annual hospital growth 2009-2018 with lagged litigation rate and total
    newspaper article counts (per 1,000 national articles). Because total media
    coverage is a national yearly variable, it is collinear with full year fixed
    effects; the sensitivity therefore uses specialty fixed effects plus a
    linear time trend."""
    Pint = phys_frame(interpolate=True)
    L = load("litigation_by_specialty.csv")
    H = load("facilities_hospital_by_specialty.csv")
    M = load_media()
    years = list(range(2009, 2019))
    rows = []
    for s in CORE:
        for y in years:
            prev = y - 1
            if prev not in Pint.columns or y not in H.columns \
                    or prev not in L.columns or prev not in M.index:
                continue
            p_prev = Pint.loc[s, prev]
            h_prev = H.loc[s, prev]
            h_now = H.loc[s, y]
            l_prev = L.loc[s, prev]
            m_prev = M.loc[prev]
            if pd.isna(p_prev) or pd.isna(h_prev) or pd.isna(h_now) \
                    or pd.isna(l_prev) or pd.isna(m_prev):
                continue
            rows.append({
                "specialty": s,
                "year": y,
                "dlog_hosp": np.log(h_now) - np.log(h_prev),
                "litrate": 1000.0 * l_prev / p_prev,
                "media": m_prev / 1000.0,  # per 1,000 articles
            })
    d = pd.DataFrame(rows)
    m = smf.ols("dlog_hosp ~ litrate + media + C(specialty) + year",
                data=d).fit(cov_type="cluster", cov_kwds={"groups": d["specialty"]})
    df = d.specialty.nunique() - 1
    def _p(coef, se):
        t = coef / se if se > 0 else 0.0
        return 2.0 * stats.t.sf(abs(t), df)
    return {
        "label": "Media-adjusted annual hospital growth (2009-2018) ~ lit rate + media count",
        "outcome": "dlog_hosp",
        "n_obs": int(d.shape[0]),
        "n_specialties": int(d.specialty.nunique()),
        "n_waves": int(d.year.nunique()),
        "lit_coef": float(m.params["litrate"]),
        "lit_se": float(m.bse["litrate"]),
        "lit_p": _p(m.params["litrate"], m.bse["litrate"]),
        "media_coef": float(m.params["media"]),
        "media_se": float(m.bse["media"]),
        "media_p": _p(m.params["media"], m.bse["media"]),
        "r_lit_media": float(d[["litrate", "media"]].corr().iloc[0, 1]),
    }


def policy_simulation(res):
    """Counterfactual 10-year (5 biennia) projection of physician counts under
    alternative policy levers. Baseline drift is the observed mean biennial
    log-change per specialty. Litigation-elimination scenarios subtract the
    empirical litigation coefficient (point estimate and 95% lower bound)
    multiplied by the specialty's mean litigation rate. The MDE lever adds
    the minimum detectable per-SD effect to baseline growth as a benchmark
    for the smallest policy effect this panel could detect with 80% power."""
    P = phys_frame()
    L = load("litigation_by_specialty.csv")
    T = 5  # 5 biennia = 10 years, 2024 -> 2034
    mde = res["equivalence"][0]["mde_80pct"] / 100.0
    coef = res["primary"][0]["coef"]
    ci_low = res["primary"][0]["ci_low"]

    rows = []
    totals = {"phys_2024": 0, "base_2034": 0,
              "lit_zero_point_2034": 0, "lit_zero_lower_2034": 0,
              "mde_2034": 0}
    for s in CORE:
        phys_cols = sorted([c for c in P.columns if not pd.isna(P.loc[s, c])])
        dlogs = [np.log(P.loc[s, phys_cols[i + 1]]) - np.log(P.loc[s, phys_cols[i]])
                 for i in range(len(phys_cols) - 1)]
        base_g = float(np.mean(dlogs))
        common = sorted([c for c in L.columns
                         if c in P.columns and not pd.isna(L.loc[s, c])
                         and not pd.isna(P.loc[s, c])])
        rates = [1000.0 * L.loc[s, c] / P.loc[s, c] for c in common]
        rate_mean = float(np.mean(rates)) if rates else 0.0
        n0 = int(P.loc[s, 2024])

        g_lit_point = base_g - coef * rate_mean
        g_lit_lower = base_g - ci_low * rate_mean
        g_mde = base_g + mde

        n_base = int(round(n0 * np.exp(T * base_g)))
        n_lit_pt = int(round(n0 * np.exp(T * g_lit_point)))
        n_lit_lb = int(round(n0 * np.exp(T * g_lit_lower)))
        n_mde = int(round(n0 * np.exp(T * g_mde)))

        rows.append({
            "specialty": CORE_EN[s],
            "phys_2024": n0,
            "baseline_growth_per_biennium": round(base_g, 5),
            "mean_litigation_rate": round(rate_mean, 3),
            "projected_baseline": n_base,
            "projected_litigation_zero_point": n_lit_pt,
            "projected_litigation_zero_lower": n_lit_lb,
            "projected_mde_lever": n_mde,
            "pct_change_baseline": round(100.0 * (n_base / n0 - 1), 2),
            "pct_change_lit_zero_point": round(100.0 * (n_lit_pt / n0 - 1), 2),
            "pct_change_lit_zero_lower": round(100.0 * (n_lit_lb / n0 - 1), 2),
            "pct_change_mde": round(100.0 * (n_mde / n0 - 1), 2),
            "marginal_pct_lit_point": round(100.0 * (n_lit_pt / n_base - 1), 2),
            "marginal_pct_lit_lower": round(100.0 * (n_lit_lb / n_base - 1), 2),
            "marginal_pct_mde": round(100.0 * (n_mde / n_base - 1), 2),
        })
        totals["phys_2024"] += n0
        totals["base_2034"] += n_base
        totals["lit_zero_point_2034"] += n_lit_pt
        totals["lit_zero_lower_2034"] += n_lit_lb
        totals["mde_2034"] += n_mde

    totals["marginal_pct_lit_point"] = round(100.0 * (totals["lit_zero_point_2034"] / totals["base_2034"] - 1), 2)
    totals["marginal_pct_lit_lower"] = round(100.0 * (totals["lit_zero_lower_2034"] / totals["base_2034"] - 1), 2)
    totals["marginal_pct_mde"] = round(100.0 * (totals["mde_2034"] / totals["base_2034"] - 1), 2)

    res["policy_simulation"] = {
        "horizon_biennia": T,
        "horizon_year": 2024 + 2 * T,
        "mde_per_biennium": mde,
        "specialties": rows,
        "totals": totals,
        "note": "Projected physician counts are deterministic extrapolations of observed baseline growth plus the indicated policy effect. They are intended as decision-analytics counterfactuals, not forecasts."
    }


def main():
    res = {"grid": {}, "descriptive": {}, "primary": [], "sensitivity": [],
           "heterogeneity": [], "trend_sensitivity": []}

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

    # BOOTSTRAP small-cluster robustness check (block resampling of specialties)
    res["bootstrap"] = [
        bootstrap_cluster(dbi, "dlog_phys", "litrate_lag",
                          "Biennial physician growth ~ lagged litigation rate"),
        bootstrap_cluster(dbi, "dlog_hosp", "litrate_lag",
                          "Biennial hospital growth ~ lagged litigation rate")
    ]

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
    rev_df = rev["specialty"].nunique() - 1
    rev_coef = float(mrev.params["np.log(phys_lag)"])
    rev_se = float(mrev.bse["np.log(phys_lag)"])
    rev_p = _cluster_p(rev_coef, rev_se, rev_df)
    res["primary"].append({"label": "Reverse: change in litigation rate ~ lagged log physicians",
                           "coef": rev_coef, "se": rev_se, "df": rev_df, "p": rev_p,
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

    # ---- SENSITIVITY (c): JMSR report-rate control (annual hospital 2016-2024) ----
    res["jmsr_correlation"] = jmsr_lit_correlation(load("litigation_by_specialty.csv"),
                                                   load_jmsr())
    res["sensitivity"].append(jmsr_hospital_sensitivity())

    # ---- SENSITIVITY (d): media coverage control (annual hospital 2009-2018) ----
    res["media_correlation"] = media_lit_correlation(load("litigation_by_specialty.csv"),
                                                     load_media())
    res["sensitivity"].append(media_hospital_sensitivity())

    # ---- HETEROGENEITY: high-litigation and surgical-specialty interactions ----
    res["heterogeneity"].append(heterogeneity_fit(
        dbi, "dlog_phys", "litrate_lag",
        "Heterogeneity (high-litigation) physician growth ~ lagged litigation rate",
        "litrate_lag", "litrate"))
    res["heterogeneity"].append(heterogeneity_fit(
        dbi, "dlog_phys", "litrate_lag",
        "Heterogeneity (surgical) physician growth ~ lagged litigation rate",
        "litrate_lag", "surgical"))
    res["heterogeneity"].append(heterogeneity_fit(
        dbi, "dlog_hosp", "litrate_lag",
        "Heterogeneity (high-litigation) hospital growth ~ lagged litigation rate",
        "litrate_lag", "litrate"))
    res["heterogeneity"].append(heterogeneity_fit(
        dbi, "dlog_hosp", "litrate_lag",
        "Heterogeneity (surgical) hospital growth ~ lagged litigation rate",
        "litrate_lag", "surgical"))

    # ---- SENSITIVITY (e): specialty-specific linear time trends ----
    res["trend_sensitivity"].append(panel_fit_with_trends(
        dbi, "dlog_phys", "litrate_lag",
        "Trend robustness: physician growth ~ lagged litigation rate + specialty trends"))
    res["trend_sensitivity"].append(panel_fit_with_trends(
        dbi, "dlog_hosp", "litrate_lag",
        "Trend robustness: hospital growth ~ lagged litigation rate + specialty trends"))

    # ---- MULTIPLE COMPARISON ADJUSTMENT (exploratory tests only) ----
    # Primary equivalence tests are confirmatory and not adjusted. Sensitivity
    # and JOCS-CP indicator tests are exploratory; report Holm-adjusted p-values.
    exploratory = []
    for r in res["primary"]:
        if "jocscp_p" in r and r["jocscp_p"] is not None:
            exploratory.append({"label": f"{r['label']} (JOCS-CP indicator)",
                                "raw_p": r["jocscp_p"]})
    for r in res["sensitivity"]:
        if "coef" in r:
            exploratory.append({"label": r["label"], "raw_p": r["p"]})
        if "lit_p" in r:
            exploratory.append({"label": f"{r['label']} (litigation rate)",
                                "raw_p": r["lit_p"]})
        if "med_p" in r and "media" not in r["label"]:
            exploratory.append({"label": f"{r['label']} (JMSR report rate)",
                                "raw_p": r["med_p"]})
        if "media_p" in r:
            exploratory.append({"label": f"{r['label']} (media count)",
                                "raw_p": r["media_p"]})
    for r in res.get("heterogeneity", []):
        exploratory.append({"label": f"{r['label']} (main effect)",
                            "raw_p": r["p"]})
        exploratory.append({"label": f"{r['label']} (interaction)",
                            "raw_p": r["interact_p"]})
    for r in res.get("trend_sensitivity", []):
        exploratory.append({"label": r["label"], "raw_p": r["p"]})
    raw_ps = [e["raw_p"] for e in exploratory]
    adj_ps = holm_adjust(raw_ps)
    res["multiple_comparison"] = {
        "note": "Holm step-down adjustment applied to exploratory sensitivity tests and the JOCS-CP indicator; primary equivalence tests are confirmatory and not included in this family.",
        "tests": [{"label": e["label"], "raw_p": e["raw_p"], "holm_p": a}
                  for e, a in zip(exploratory, adj_ps)]
    }

    # Policy lever counterfactual simulation
    policy_simulation(res)

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
        if "lit_coef" in r and "media_coef" not in r:
            print("  %s: lit coef=%.5f p=%.4f; jmsr coef=%.5f p=%.4f n=%s" % (
                r["label"], r["lit_coef"], r["lit_p"], r["med_coef"], r["med_p"], r["n_obs"]))
        elif "lit_coef" in r and "media_coef" in r:
            print("  %s: lit coef=%.5f p=%.4f; media coef=%.5f p=%.4f n=%s" % (
                r["label"], r["lit_coef"], r["lit_p"], r["media_coef"], r["media_p"], r["n_obs"]))
        else:
            print("  %s: coef=%.5f p=%.4f n=%s" % (r["label"], r.get("coef", np.nan),
                  r.get("p", np.nan), r["n_obs"]))
    print("\nHETEROGENEITY:")
    for r in res.get("heterogeneity", []):
        print("  %s: main coef=%.5f p=%.4f; interact coef=%.5f p=%.4f n=%s" % (
            r["label"], r["coef"], r["p"], r["interact_coef"], r["interact_p"], r["n_obs"]))
    print("\nTREND SENSITIVITY:")
    for r in res.get("trend_sensitivity", []):
        print("  %s: coef=%.5f p=%.4f n=%s" % (
            r["label"], r["coef"], r["p"], r["n_obs"]))
    print("\nJMSR-LITIGATION CORRELATION (2015-2024):")
    c = res["jmsr_correlation"]
    print("  pooled r=%.3f p=%.4f; detrended r=%.3f p=%.4f" % (
        c["pooled_r"], c["pooled_p"], c["detrended_r"], c["detrended_p"]))
    print("\nMEDIA-LITIGATION CORRELATION:")
    m = res["media_correlation"]
    print("  total media vs total litigation r=%.3f p=%.4f; panel litrate vs media r=%.3f p=%.4f" % (
        m["total_r"], m["total_p"], m["panel_r"], m["panel_p"]))


if __name__ == "__main__":
    main()
