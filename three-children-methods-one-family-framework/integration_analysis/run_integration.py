"""
ONISHI integration analysis: four combination patterns on shared IPD (IST).

Common dataset: International Stroke Trial (IST_corrected.csv, 19,435 randomized
patients; the complete-case analysis frame used here is 18,451 patients).
Treatment = aspirin allocation (RXASP), outcome = 14-day death (DIED),
covariates = baseline variables. The three constituent methods act on three
independent hierarchies:

  IONE  (research-internal)      -> latent subgroup incoherence (C1, W)
  LINKO (research-between)       -> endpoint information contribution (ICR)
  KOTHA (research-type-between)  -> counterfactual power / harmonised estimate

Patterns:
  1. LINKO + IONE   : per-subgroup ICR diagnoses the source of heterogeneity
  2. LINKO + KOTHA  : ICR informs the information weight in meta-integration
  3. IONE  + KOTHA  : subgroup risk profiles drive counterfactual power
  4. ONISHI (all 3) : sequential IONE -> LINKO -> KOTHA harmonisation
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ione_core as ione
import kotha_core as kotha
import linko_pca as linko
import schematic_figures

# Figures carry NO figure numbers and NO verbatim caption text (see repository
# knowledge): only panel locants "A)", "B)" ..., axis labels, in-plot legends,
# and computed data annotations. All descriptive text lives in the manuscript
# legends so figures can be renumbered without regeneration.

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "IST_corrected.csv")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

RNG = np.random.default_rng(42)
N_STRATA = 4

# Okabe-Ito colourblind-friendly palette
C_BLUE, C_ORANGE, C_GREEN, C_RED, C_PURPLE, C_GREY = (
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#999999")

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.family": "sans-serif",
})

from matplotlib.ticker import FixedLocator, FuncFormatter


def log_or_axis(ax, ticks):
    """Render an odds-ratio x-axis on a log scale (AJE convention for relative
    measures) with plain-number labels at the given tick positions."""
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


def prepare_data():
    df, all_vars, endpoint = linko.load_and_encode_ist(DATA)
    pred_vars = [v for v in all_vars if v != endpoint]
    keep = pred_vars + [endpoint, "RXASP_num", "COUNTRY"]
    adf = df[keep].dropna().reset_index(drop=True)
    return df, adf, all_vars, pred_vars, endpoint


def overall_effect(treat, Y):
    e_t = int(np.sum((treat == 1) & (Y == 1)))
    n_t = int(np.sum(treat == 1))
    e_c = int(np.sum((treat == 0) & (Y == 1)))
    n_c = int(np.sum(treat == 0))
    logOR, se = kotha.compute_or(e_t, n_t, e_c, n_c)
    return {"e_t": e_t, "n_t": n_t, "e_c": e_c, "n_c": n_c,
            "logOR": float(logOR), "se": float(se), "OR": float(np.exp(logOR))}


# ============================================================
# Shared IONE stratification (reused by patterns 1, 3, 4)
# ============================================================

def run_ione(adf, pred_vars, endpoint):
    X = adf[pred_vars].values.astype(float)
    Y = adf[endpoint].values.astype(float)
    treat = adf["RXASP_num"].values.astype(float)
    # predicted-probability (decision-power) strata -> interpretable risk profiles
    strata = ione.method_1a(X, Y, N_STRATA)

    c1_outcome = ione.compute_c1(Y, strata)
    W = ione.within_stratum_homogeneity_W(Y, strata)
    eff = ione.stratum_effect_logor(treat, Y, strata)
    logors = np.array([e["logOR"] for e in eff])
    ses = np.array([e["se"] for e in eff])
    pooled, se_p, tau2, I2 = kotha.random_effects_meta(logors, ses)
    c1_effect = 1.0 - I2 / 100.0  # incoherence of the aspirin EFFECT across strata

    return {
        "X": X, "Y": Y, "treat": treat, "strata": strata,
        "stratum_effects": eff, "c1_outcome": float(c1_outcome),
        "c1_effect": float(c1_effect), "W": float(W),
        "pooled_logOR": float(pooled), "pooled_se": float(se_p), "I2": float(I2),
    }


# ============================================================
# Pattern 1: LINKO + IONE  (per-subgroup ICR diagnosis)
# ============================================================

def pattern1(df, adf, all_vars, endpoint, ione_res):
    strata = ione_res["strata"]
    rows = []
    for e in ione_res["stratum_effects"]:
        s = e["stratum"]
        sub = adf[strata == s]
        icr = linko.icr_pca_for_subset(sub, all_vars, endpoint)
        rows.append({**e,
                     "icr_pca_reg": icr["icr_pca_reg"],
                     "icr_pca_loading": icr["icr_pca_loading"],
                     "icr_std": icr["icr_std"]})
    tab = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # A: forest of aspirin logOR per stratum
    y = np.arange(len(tab))
    axes[0].errorbar(np.exp(tab["logOR"]), y,
                     xerr=[np.exp(tab["logOR"]) - np.exp(tab["logOR"] - 1.96 * tab["se"]),
                           np.exp(tab["logOR"] + 1.96 * tab["se"]) - np.exp(tab["logOR"])],
                     fmt="o", color=C_BLUE, capsize=4)
    axes[0].axvline(1.0, color=C_GREY, ls="--")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([f"stratum {int(s)}\n(n={n:,}, ER={er:.1%})"
                             for s, n, er in zip(tab["stratum"], tab["n"], tab["event_rate"])])
    axes[0].set_xlabel("Aspirin OR (14-day death, log scale)")
    log_or_axis(axes[0], [0.7, 0.8, 0.9, 1.0, 1.1, 1.25])
    axes[0].set_title("A)", loc="left", fontweight="bold")
    axes[0].text(0.97, 0.06,
                 f"C1(effect)={ione_res['c1_effect']:.2f}, W={ione_res['W']:.2f}",
                 transform=axes[0].transAxes, fontsize=9, va="bottom", ha="right")
    # B: endpoint information share per subgroup (regression-based ICR;
    # unified with Pattern 4 so the subgroup ICR ranking is consistent).
    med = float(np.median(tab["icr_pca_reg"]))
    axes[1].bar([f"s{int(s)}\n(ER={er:.1%})" for s, er in zip(tab["stratum"], tab["event_rate"])],
                tab["icr_pca_reg"], color=C_ORANGE, alpha=0.9)
    axes[1].axhline(med, color=C_RED, ls="--", label=f"median ICR={med:.5f}")
    axes[1].set_ylabel("ICR_pca (regression-based, endpoint information share)")
    axes[1].set_title("B)", loc="left", fontweight="bold")
    axes[1].legend()
    p = os.path.join(FIGDIR, "pattern1_linko_ione.png")
    fig.savefig(p); plt.close(fig)

    return {"table": tab.to_dict(orient="records"),
            "c1_effect": ione_res["c1_effect"], "W": ione_res["W"],
            "figure": p}


# ============================================================
# Pattern 2: LINKO + KOTHA  (ICR-weighted meta-integration)
# ============================================================

def pattern2(df, all_vars, endpoint, min_n=300):
    # per-country ICR (LINKO)
    icr_tab = linko.icr_pca_by_group(df, all_vars, endpoint, "COUNTRY", min_n=min_n)
    # per-country aspirin effect (from raw df)
    sub = df[["COUNTRY", "RXASP_num", endpoint]].dropna()
    recs = []
    for g in icr_tab["group"]:
        d = sub[sub["COUNTRY"] == g]
        t = d["RXASP_num"].values
        y = d[endpoint].values
        e_t = int(np.sum((t == 1) & (y == 1))); n_t = int(np.sum(t == 1))
        e_c = int(np.sum((t == 0) & (y == 1))); n_c = int(np.sum(t == 0))
        if n_t < 20 or n_c < 20:
            continue
        lo, se = kotha.compute_or(e_t, n_t, e_c, n_c)
        icr = float(icr_tab[icr_tab["group"] == g]["icr_pca_reg"].iloc[0])
        recs.append({"country": g, "n": int(len(d)), "logOR": float(lo),
                     "se": float(se), "icr_pca_reg": icr})
    tab = pd.DataFrame(recs)

    logors = tab["logOR"].values
    ses = tab["se"].values
    p_iv, se_iv, tau2, I2 = kotha.random_effects_meta(logors, ses)
    p_fe, se_fe = kotha.fixed_effect_meta(logors, ses)
    p_icr, se_icr = kotha.weighted_meta(logors, ses, tab["icr_pca_reg"].values)
    # honest control: same estimator with EQUAL (uniform) information weights.
    # If se_unit ~= se_icr, the SE reduction vs IV-RE comes from dropping the
    # random-effects tau^2, NOT from ICR weighting itself.
    p_unit, se_unit = kotha.weighted_meta(logors, ses, np.ones_like(logors))

    fig, ax = plt.subplots(figsize=(9, max(5, 0.5 * len(tab) + 2)))
    yv = np.arange(len(tab))
    ax.errorbar(np.exp(logors), yv,
                xerr=[np.exp(logors) - np.exp(logors - 1.96 * ses),
                      np.exp(logors + 1.96 * ses) - np.exp(logors)],
                fmt="s", color=C_BLUE, capsize=3, ms=6)
    ax.axvline(1.0, color=C_GREY, ls="--")
    ax.axvline(np.exp(p_iv), color=C_GREEN, ls="-",
               label=f"IV-RE OR={np.exp(p_iv):.2f} (SE {se_iv:.3f})")
    ax.axvline(np.exp(p_icr), color=C_PURPLE, ls="-",
               label=f"ICR-weighted OR={np.exp(p_icr):.2f} (SE {se_icr:.3f})")
    ax.axvline(np.exp(p_unit), color=C_ORANGE, ls=":",
               label=f"equal-weight OR={np.exp(p_unit):.2f} (SE {se_unit:.3f})")
    ax.set_yticks(yv)
    ax.set_yticklabels([f"{c} (ICR={i:.3f})" for c, i in zip(tab["country"], tab["icr_pca_reg"])])
    ax.set_xlabel("Aspirin OR (14-day death, log scale)")
    log_or_axis(ax, [0.5, 0.75, 1.0, 1.5, 2.0])
    ax.text(0.02, 0.98, f"I\u00b2={I2:.0f}%", transform=ax.transAxes,
            fontsize=9, va="top", ha="left")
    ax.legend()
    p = os.path.join(FIGDIR, "pattern2_linko_kotha.png")
    fig.savefig(p); plt.close(fig)

    return {"table": tab.to_dict(orient="records"),
            "pooled_iv_OR": float(np.exp(p_iv)), "pooled_iv_se": float(se_iv),
            "pooled_fe_OR": float(np.exp(p_fe)), "pooled_fe_se": float(se_fe),
            "pooled_icr_OR": float(np.exp(p_icr)), "pooled_icr_se": float(se_icr),
            "pooled_unit_OR": float(np.exp(p_unit)), "pooled_unit_se": float(se_unit),
            "I2": float(I2), "figure": p}


# ============================================================
# Pattern 3: IONE + KOTHA  (subgroup risk profiles -> power)
# ============================================================

def pattern3(adf, ione_res):
    Y = ione_res["Y"]; treat = ione_res["treat"]
    ov = overall_effect(treat, Y)
    true_OR = ov["OR"]
    N = len(Y)
    eff = ione_res["stratum_effects"]
    OR_grid = np.arange(0.60, 1.01, 0.05)

    rows = []
    for e in eff:
        p_ctrl = e["event_rate"]
        pw, ev = kotha.power_analytical(p_ctrl, true_OR, N)
        rows.append({"stratum": e["stratum"], "n": e["n"], "event_rate": p_ctrl,
                     "power_at_pooled_OR": float(pw), "expected_events": float(ev)})
    tab = pd.DataFrame(rows)

    ois = kotha.ois_calculation(true_OR)
    total_events = int(np.sum(Y))
    info_fraction = total_events / ois
    rates = tab["event_rate"].values
    indirectness_ratio = rates.max() / rates.min() if rates.min() > 0 else np.inf

    # Required additional sample size to reach OIS (decision-grade evidence) for
    # an inconclusive trial: extra events needed, converted to patients via the
    # event rate (overall, and per subgroup risk profile from IONE).
    overall_er = float(np.mean(Y))
    additional_events = max(ois - total_events, 0.0)
    additional_n_overall = additional_events / overall_er if overall_er > 0 else np.inf
    additional_n_by_stratum = [
        {"stratum": int(e["stratum"]), "event_rate": float(e["event_rate"]),
         "additional_n": float(additional_events / e["event_rate"])
         if e["event_rate"] > 0 else np.inf}
        for e in eff
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for e in eff:
        rate = e["event_rate"]
        powers = [kotha.power_analytical(rate, orr, N)[0] for orr in OR_grid]
        axes[0].plot(OR_grid, powers, marker="o",
                     label=f"stratum {e['stratum']} (ER={rate:.1%})")
    axes[0].axhline(0.8, color=C_GREY, ls="--", label="80% power")
    axes[0].axvline(true_OR, color=C_RED, ls=":", label=f"pooled OR={true_OR:.2f}")
    axes[0].set_xlabel("Assumed true OR"); axes[0].set_ylabel("Power at IST N")
    axes[0].set_title("A)", loc="left", fontweight="bold")
    axes[0].legend(fontsize=8)
    axes[1].bar([f"s{int(s)}" for s in tab["stratum"]], tab["power_at_pooled_OR"], color=C_BLUE)
    axes[1].axhline(0.8, color=C_GREY, ls="--")
    axes[1].set_ylabel("Power at pooled OR")
    axes[1].set_title("B)", loc="left", fontweight="bold")
    axes[1].text(0.03, 0.97, f"OIS={ois:.0f} events, info fraction={info_fraction:.0%}",
                 transform=axes[1].transAxes, fontsize=9, va="top", ha="left")
    p = os.path.join(FIGDIR, "pattern3_ione_kotha.png")
    fig.savefig(p); plt.close(fig)

    return {"table": tab.to_dict(orient="records"), "true_OR": true_OR,
            "ois_events": float(ois), "total_events": total_events,
            "info_fraction": float(info_fraction),
            "additional_events_needed": float(additional_events),
            "additional_n_overall": float(additional_n_overall),
            "additional_n_by_stratum": additional_n_by_stratum,
            "indirectness_ratio": float(indirectness_ratio), "figure": p}


# ============================================================
# Pattern 4: ONISHI full  (sequential IONE -> LINKO -> KOTHA)
# ============================================================

def pattern4(df, adf, all_vars, endpoint, ione_res, p1, p3):
    tab = pd.DataFrame(p1["table"])
    strata_effects = ione_res["stratum_effects"]
    logors = np.array([e["logOR"] for e in strata_effects])
    ses = np.array([e["se"] for e in strata_effects])
    icr = tab["icr_pca_reg"].values

    # LINKO handoff: strata with above-median ICR anchor the estimate;
    # below-median ICR strata are discounted (power prior over alpha).
    med = np.median(icr)
    anchor = icr >= med
    logY_rct, se_rct = logors[anchor], ses[anchor]
    logY_obs, se_obs = logors[~anchor], ses[~anchor]

    naive_pooled, naive_se, _, I2 = kotha.random_effects_meta(logors, ses)
    icr_pooled, icr_se = kotha.weighted_meta(logors, ses, icr)

    alpha_grid = [0.0, 0.25, 0.5, 0.75, 1.0]
    if len(logY_obs) > 0 and len(logY_rct) > 0:
        pp = kotha.power_prior_meta(logY_rct, se_rct, logY_obs, se_obs, alpha_grid)
    else:
        pp = {}

    # KOTHA Module H: TSA cumulative Z across strata ordered by risk (event rate)
    order = np.argsort([e["event_rate"] for e in strata_effects])[::-1]
    cum_z, cum_pooled, cum_info = kotha.cumulative_z(logors[order], ses[order])

    from scipy import stats as _st
    p_benefit_naive = float(_st.norm.cdf(0, loc=naive_pooled, scale=naive_se))
    p_benefit_icr = float(_st.norm.cdf(0, loc=icr_pooled, scale=icr_se))

    # ---- 4-panel dashboard ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Panel A: IONE — subgroup effects + incoherence
    yv = np.arange(len(tab))
    axes[0, 0].errorbar(np.exp(logors), yv,
                        xerr=[np.exp(logors) - np.exp(logors - 1.96 * ses),
                              np.exp(logors + 1.96 * ses) - np.exp(logors)],
                        fmt="o", color=C_BLUE, capsize=4)
    axes[0, 0].axvline(1.0, color=C_GREY, ls="--")
    axes[0, 0].set_yticks(yv)
    axes[0, 0].set_yticklabels([f"s{int(s)}" for s in tab["stratum"]])
    axes[0, 0].set_xlabel("Aspirin OR (log scale)")
    log_or_axis(axes[0, 0], [0.7, 0.8, 0.9, 1.0, 1.1, 1.25])
    axes[0, 0].set_title("A)", loc="left", fontweight="bold")
    axes[0, 0].text(0.97, 0.06,
                    f"C1(effect)={ione_res['c1_effect']:.2f}, "
                    f"W={ione_res['W']:.2f}, I\u00b2={I2:.0f}%",
                    transform=axes[0, 0].transAxes, fontsize=9, va="bottom",
                    ha="right")

    # Panel B: LINKO — ICR per stratum (anchor vs discounted)
    colors = [C_GREEN if a else C_ORANGE for a in anchor]
    axes[0, 1].bar([f"s{int(s)}" for s in tab["stratum"]], icr, color=colors)
    axes[0, 1].axhline(med, color=C_RED, ls="--", label=f"median ICR={med:.3f}")
    axes[0, 1].set_ylabel("ICR_pca")
    axes[0, 1].set_title("B)", loc="left", fontweight="bold")
    axes[0, 1].legend(fontsize=8, title="green=anchor, orange=discounted")

    # Panel C: KOTHA power prior sensitivity
    if pp:
        alphas = list(pp.keys())
        hrs = [pp[a]["hr_median"] for a in alphas]
        los = [pp[a]["hr_lo"] for a in alphas]
        his = [pp[a]["hr_hi"] for a in alphas]
        axes[1, 0].plot(alphas, hrs, "o-", color=C_PURPLE)
        axes[1, 0].fill_between(alphas, los, his, color=C_PURPLE, alpha=0.2)
        axes[1, 0].axhline(1.0, color=C_GREY, ls="--")
        axes[1, 0].set_xlabel("Discount α on low-ICR strata")
        axes[1, 0].set_ylabel("Harmonised OR (95% CrI)")
        axes[1, 0].set_title("C)", loc="left", fontweight="bold")

    # Panel D: TSA cumulative Z
    axes[1, 1].plot(cum_info, cum_z, "o-", color=C_BLUE)
    axes[1, 1].axhline(1.96, color=C_RED, ls="--", label="Z=±1.96")
    axes[1, 1].axhline(-1.96, color=C_RED, ls="--")
    axes[1, 1].set_xlabel("Cumulative information (Σ 1/se²)")
    axes[1, 1].set_ylabel("Cumulative Z")
    axes[1, 1].set_title("D)", loc="left", fontweight="bold")
    axes[1, 1].text(0.03, 0.90,
                    f"info fraction={p3['info_fraction']:.0%}, "
                    f"need +{p3['additional_n_overall']:,.0f} pts",
                    transform=axes[1, 1].transAxes, fontsize=9, va="top")
    axes[1, 1].legend(fontsize=8)
    p = os.path.join(FIGDIR, "pattern4_onishi_full.png")
    fig.savefig(p); plt.close(fig)

    return {
        "c1_effect": ione_res["c1_effect"], "W": ione_res["W"], "I2": float(I2),
        "naive_pooled_OR": float(np.exp(naive_pooled)), "naive_p_benefit": p_benefit_naive,
        "icr_pooled_OR": float(np.exp(icr_pooled)), "icr_p_benefit": p_benefit_icr,
        "anchor_strata": [int(s) for s, a in zip(tab["stratum"], anchor) if a],
        "power_prior": {str(k): v for k, v in pp.items()},
        "tsa_final_z": float(cum_z[-1]),
        "ois_events": p3["ois_events"], "info_fraction": p3["info_fraction"],
        "additional_events_needed": p3["additional_events_needed"],
        "additional_n_overall": p3["additional_n_overall"],
        "figure": p,
    }


def main():
    df, adf, all_vars, pred_vars, endpoint = prepare_data()
    print(f"IST analysis frame: N={len(adf):,}, D={len(all_vars)} variables, "
          f"event rate={adf[endpoint].mean():.3f}")

    ione_res = run_ione(adf, pred_vars, endpoint)
    ov = overall_effect(ione_res["treat"], ione_res["Y"])
    print(f"Overall aspirin OR={ov['OR']:.3f} (logOR={ov['logOR']:.3f}, se={ov['se']:.3f})")
    print(f"IONE: C1(outcome)={ione_res['c1_outcome']:.3f}, "
          f"C1(effect)={ione_res['c1_effect']:.3f}, W={ione_res['W']:.3f}, I²={ione_res['I2']:.1f}%")

    p1 = pattern1(df, adf, all_vars, endpoint, ione_res)
    print("Pattern 1 done ->", p1["figure"])
    p2 = pattern2(df, all_vars, endpoint)
    print("Pattern 2 done ->", p2["figure"])
    p3 = pattern3(adf, ione_res)
    print("Pattern 3 done ->", p3["figure"])
    p4 = pattern4(df, adf, all_vars, endpoint, ione_res, p1, p3)
    print("Pattern 4 done ->", p4["figure"])
    schem = schematic_figures.build_all()
    print("Schematics done ->", schem)

    results = {
        "dataset": {"name": "International Stroke Trial (IST)", "N": int(len(adf)),
                    "n_randomized": int(len(df)),
                    "n_variables": len(all_vars), "event_rate": float(adf[endpoint].mean()),
                    "treatment": "RXASP (aspirin)", "outcome": "DIED (14-day)"},
        "overall_effect": ov,
        "ione": {k: ione_res[k] for k in
                 ["c1_outcome", "c1_effect", "W", "pooled_logOR", "pooled_se", "I2"]},
        "ione_stratum_effects": ione_res["stratum_effects"],
        "pattern1_linko_ione": p1,
        "pattern2_linko_kotha": p2,
        "pattern3_ione_kotha": p3,
        "pattern4_onishi_full": p4,
        "schematics": schem,
    }
    outp = os.path.join(HERE, "results.json")
    with open(outp, "w") as f:
        json.dump(results, f, indent=2, default=float)
    print("Results ->", outp)
    return results


if __name__ == "__main__":
    main()
