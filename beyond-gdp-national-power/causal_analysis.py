"""
Causal Identification Strengthening for Network Exclusion and State Collapse

Implements four complementary strategies to move beyond correlational evidence:
  A. Instrumental Variables (2SLS) — geo_barrier as instrument for closure
  B. Propensity Score Matching (PSM) — ATT with nearest-neighbour matching
  C. Natural Experiment framing — technical network exclusion as quasi-exogenous
  D. Robustness battery — E-values, permutation tests, leave-one-out, placebo

All results are saved to reports/ as text and returned as a dict for LaTeX integration.
"""

import warnings
warnings.filterwarnings("ignore")

import os
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import math
from itertools import combinations
from data import load_data

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


# ================================================================
# Helper: derive closure binary and disrupted assignment
# ================================================================

def prepare_df(df, disrupted_as="overtaken"):
    """Return df with closure_binary, outcome_binary adjusted for disrupted."""
    d = df.copy()
    d["closure_binary"] = (d["closure_type"] != "none").astype(int)
    if disrupted_as == "overtaken":
        d["outcome_bin"] = d["outcome"].isin(["overtaken", "disrupted"]).astype(int)
    else:
        d["outcome_bin"] = (d["outcome"] == "overtaken").astype(int)
    return d


COVARIATES = [
    "geo_barrier", "external_threat", "relative_pop",
    "tech_position", "institutional_quality",
    "regime_duration_yrs", "era_code", "has_external_patron",
]

COVARIATES_SHORT = [
    "geo_barrier", "external_threat", "tech_position",
    "institutional_quality", "era_code",
]


# ================================================================
# A. Instrumental Variables (2SLS)
# ================================================================

def iv_2sls_analysis(df):
    """
    2SLS using geo_barrier as instrument for closure_binary.

    Exclusion restriction argument: geographic barriers (mountains, deserts,
    island isolation) affect state survival ONLY through their effect on
    network accessibility. Once we condition on external_threat, tech_position,
    institutional_quality, etc., the remaining variation in geo_barrier
    operates through network access channels.

    We also use linearmodels IV2SLS for proper standard errors.
    """
    print("=" * 70)
    print("A. INSTRUMENTAL VARIABLES (2SLS)")
    print("   Instrument: geo_barrier → closure_binary → outcome")
    print("=" * 70)

    d = prepare_df(df)
    results = {}

    # -- First stage: closure_binary ~ geo_barrier + controls --
    endog_vars = ["external_threat", "tech_position",
                  "institutional_quality", "era_code"]
    X_first = sm.add_constant(d[["geo_barrier"] + endog_vars].astype(float))
    y_first = d["closure_binary"].astype(float)

    first_stage = sm.OLS(y_first, X_first).fit()
    print("\n--- First Stage: closure_binary ~ geo_barrier + controls ---")
    print(f"  geo_barrier coefficient: {first_stage.params['geo_barrier']:.4f}")
    print(f"  geo_barrier t-stat:      {first_stage.tvalues['geo_barrier']:.3f}")
    print(f"  geo_barrier p-value:     {first_stage.pvalues['geo_barrier']:.4f}")
    print(f"  R²:                      {first_stage.rsquared:.4f}")
    print(f"  F-statistic:             {first_stage.fvalue:.3f}")
    print(f"  Partial F (geo_barrier): {first_stage.tvalues['geo_barrier']**2:.3f}")

    results["first_stage"] = {
        "coef_geo": float(first_stage.params['geo_barrier']),
        "t_geo": float(first_stage.tvalues['geo_barrier']),
        "p_geo": float(first_stage.pvalues['geo_barrier']),
        "R2": float(first_stage.rsquared),
        "F": float(first_stage.fvalue),
        "partial_F_geo": float(first_stage.tvalues['geo_barrier']**2),
    }

    weak_instrument = results["first_stage"]["partial_F_geo"] < 10
    print(f"\n  Weak instrument test (F > 10 rule): "
          f"{'FAIL — weak instrument' if weak_instrument else 'PASS'}")
    results["first_stage"]["weak_instrument"] = weak_instrument

    # -- Reduced form: outcome ~ geo_barrier + controls --
    y_out = d["outcome_bin"].astype(float)
    reduced = sm.OLS(y_out, X_first).fit()
    print(f"\n--- Reduced Form: outcome ~ geo_barrier + controls ---")
    print(f"  geo_barrier coefficient: {reduced.params['geo_barrier']:.4f}")
    print(f"  geo_barrier p-value:     {reduced.pvalues['geo_barrier']:.4f}")
    results["reduced_form"] = {
        "coef_geo": float(reduced.params['geo_barrier']),
        "p_geo": float(reduced.pvalues['geo_barrier']),
    }

    # -- Manual 2SLS --
    d["closure_hat"] = first_stage.fittedvalues
    X_second = sm.add_constant(
        d[["closure_hat"] + endog_vars].astype(float)
    )
    second_stage = sm.OLS(y_out, X_second).fit()
    print(f"\n--- Second Stage (2SLS): outcome ~ closure_hat + controls ---")
    print(f"  closure_hat coefficient: {second_stage.params['closure_hat']:.4f}")
    print(f"  closure_hat p-value:     {second_stage.pvalues['closure_hat']:.4f}")
    print(f"  R²:                      {second_stage.rsquared:.4f}")
    results["second_stage_manual"] = {
        "coef_closure": float(second_stage.params['closure_hat']),
        "p_closure": float(second_stage.pvalues['closure_hat']),
        "R2": float(second_stage.rsquared),
    }

    # -- linearmodels IV2SLS for correct standard errors --
    try:
        from linearmodels.iv import IV2SLS as LM_IV2SLS
        # endogenous: closure_binary; instrument: geo_barrier
        formula_dep = d["outcome_bin"].values
        exog = sm.add_constant(d[endog_vars].astype(float))
        endog = d[["closure_binary"]].astype(float)
        instruments = d[["geo_barrier"]].astype(float)

        iv_model = LM_IV2SLS(
            dependent=formula_dep,
            exog=exog,
            endog=endog,
            instruments=instruments,
        ).fit(cov_type="robust")

        print(f"\n--- linearmodels IV2SLS (robust SE) ---")
        print(f"  closure_binary coefficient: {iv_model.params['closure_binary']:.4f}")
        print(f"  closure_binary std error:   {iv_model.std_errors['closure_binary']:.4f}")
        print(f"  closure_binary p-value:     {iv_model.pvalues['closure_binary']:.4f}")
        ci = iv_model.conf_int().loc["closure_binary"]
        print(f"  95% CI: [{ci['lower']:.4f}, {ci['upper']:.4f}]")

        results["iv2sls_linearmodels"] = {
            "coef": float(iv_model.params['closure_binary']),
            "se": float(iv_model.std_errors['closure_binary']),
            "p": float(iv_model.pvalues['closure_binary']),
            "ci_lo": float(ci['lower']),
            "ci_hi": float(ci['upper']),
        }
    except Exception as e:
        print(f"\n  linearmodels IV2SLS failed: {e}")
        results["iv2sls_linearmodels"] = {"error": str(e)}

    # -- Hausman test: compare OLS vs 2SLS --
    X_ols = sm.add_constant(d[["closure_binary"] + endog_vars].astype(float))
    ols_model = sm.OLS(y_out, X_ols).fit()
    hausman_diff = (second_stage.params['closure_hat'] -
                    ols_model.params['closure_binary'])
    print(f"\n--- Hausman-like comparison ---")
    print(f"  OLS coefficient (closure):   {ols_model.params['closure_binary']:.4f}")
    print(f"  2SLS coefficient (closure):  {second_stage.params['closure_hat']:.4f}")
    print(f"  Difference:                  {hausman_diff:.4f}")
    results["hausman"] = {
        "ols_coef": float(ols_model.params['closure_binary']),
        "iv_coef": float(second_stage.params['closure_hat']),
        "diff": float(hausman_diff),
    }

    return results


# ================================================================
# B. Propensity Score Matching (PSM)
# ================================================================

def psm_analysis(df):
    """
    Propensity Score Matching: estimate ATT of network closure on conquest.

    Step 1: Estimate propensity scores via logistic regression
    Step 2: Nearest-neighbour matching (caliper = 0.2 SD of logit-PS)
    Step 3: Estimate ATT from matched sample
    Step 4: Covariate balance assessment
    """
    print("\n" + "=" * 70)
    print("B. PROPENSITY SCORE MATCHING (PSM)")
    print("=" * 70)

    d = prepare_df(df)
    results = {}

    # Step 1: Propensity score estimation
    ps_covariates = [
        "geo_barrier", "external_threat", "tech_position",
        "institutional_quality", "era_code", "relative_pop",
    ]
    X_ps = d[ps_covariates].astype(float).values
    T = d["closure_binary"].values
    Y = d["outcome_bin"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_ps)

    ps_model = LogisticRegression(penalty="l2", C=1.0, max_iter=1000)
    ps_model.fit(X_scaled, T)
    ps_scores = ps_model.predict_proba(X_scaled)[:, 1]
    d["ps"] = ps_scores

    print(f"\n--- Propensity Score Distribution ---")
    for grp, label in [(0, "Open (T=0)"), (1, "Closed (T=1)")]:
        mask = T == grp
        print(f"  {label}: n={mask.sum()}, "
              f"mean={ps_scores[mask].mean():.3f}, "
              f"median={np.median(ps_scores[mask]):.3f}, "
              f"range=[{ps_scores[mask].min():.3f}, {ps_scores[mask].max():.3f}]")
    results["ps_distribution"] = {
        "open_mean": float(ps_scores[T == 0].mean()),
        "closed_mean": float(ps_scores[T == 1].mean()),
        "overlap_region": [
            float(max(ps_scores[T == 0].min(), ps_scores[T == 1].min())),
            float(min(ps_scores[T == 0].max(), ps_scores[T == 1].max())),
        ],
    }

    # Step 2: Nearest-neighbour matching with caliper
    logit_ps = np.log(ps_scores / (1 - ps_scores + 1e-10))
    caliper = 0.2 * logit_ps.std()
    print(f"\n  Caliper (0.2 × SD of logit-PS): {caliper:.3f}")

    treated_idx = np.where(T == 1)[0]
    control_idx = np.where(T == 0)[0]

    nn = NearestNeighbors(n_neighbors=1, metric="euclidean")
    nn.fit(logit_ps[control_idx].reshape(-1, 1))
    distances, indices = nn.kneighbors(logit_ps[treated_idx].reshape(-1, 1))

    matched_pairs = []
    for i, (dist, idx) in enumerate(zip(distances.ravel(), indices.ravel())):
        if dist <= caliper:
            matched_pairs.append((treated_idx[i], control_idx[idx]))

    n_matched = len(matched_pairs)
    n_unmatched = len(treated_idx) - n_matched
    print(f"\n--- Matching Results ---")
    print(f"  Treated units:   {len(treated_idx)}")
    print(f"  Matched:         {n_matched} ({n_matched/len(treated_idx)*100:.1f}%)")
    print(f"  Unmatched:       {n_unmatched}")

    results["matching"] = {
        "n_treated": int(len(treated_idx)),
        "n_matched": n_matched,
        "n_unmatched": n_unmatched,
        "caliper": float(caliper),
    }

    if n_matched < 5:
        print("  WARNING: Too few matched pairs for reliable inference.")
        results["att"] = {"error": "insufficient matches"}
        return results

    # Step 3: ATT estimation
    matched_treated = [p[0] for p in matched_pairs]
    matched_control = [p[1] for p in matched_pairs]

    att = Y[matched_treated].mean() - Y[matched_control].mean()
    # Bootstrap CI for ATT
    n_boot = 2000
    att_boots = []
    rng = np.random.RandomState(42)
    for _ in range(n_boot):
        boot_idx = rng.choice(n_matched, size=n_matched, replace=True)
        y_t = Y[[matched_treated[i] for i in boot_idx]]
        y_c = Y[[matched_control[i] for i in boot_idx]]
        att_boots.append(y_t.mean() - y_c.mean())
    att_boots = np.array(att_boots)
    att_ci_lo, att_ci_hi = np.percentile(att_boots, [2.5, 97.5])
    att_se = att_boots.std()
    att_p = 2 * min(
        (att_boots <= 0).mean(),
        (att_boots >= 0).mean(),
    )

    print(f"\n--- ATT (Average Treatment Effect on Treated) ---")
    print(f"  ATT = {att:.4f}")
    print(f"  Bootstrap SE = {att_se:.4f}")
    print(f"  95% CI = [{att_ci_lo:.4f}, {att_ci_hi:.4f}]")
    print(f"  p-value (permutation-like) = {att_p:.4f}")

    results["att"] = {
        "estimate": float(att),
        "se": float(att_se),
        "ci_lo": float(att_ci_lo),
        "ci_hi": float(att_ci_hi),
        "p": float(att_p),
        "n_matched_pairs": n_matched,
    }

    # Step 4: Covariate balance
    print(f"\n--- Covariate Balance (Standardised Mean Differences) ---")
    print(f"  {'Covariate':30s} {'Before':>8s} {'After':>8s} {'Improved':>9s}")
    balance = {}
    for j, cov in enumerate(ps_covariates):
        vals = d[cov].values.astype(float)
        # Before matching
        smd_before = ((vals[T == 1].mean() - vals[T == 0].mean()) /
                      np.sqrt((vals[T == 1].var() + vals[T == 0].var()) / 2 + 1e-10))
        # After matching
        vals_mt = vals[matched_treated]
        vals_mc = vals[matched_control]
        pooled_var = (vals_mt.var() + vals_mc.var()) / 2 + 1e-10
        smd_after = (vals_mt.mean() - vals_mc.mean()) / np.sqrt(pooled_var)
        improved = abs(smd_after) < abs(smd_before)
        print(f"  {cov:30s} {smd_before:>8.3f} {smd_after:>8.3f} {'Yes' if improved else 'No':>9s}")
        balance[cov] = {
            "smd_before": float(smd_before),
            "smd_after": float(smd_after),
            "improved": improved,
        }
    results["balance"] = balance

    return results


# ================================================================
# C. Natural Experiment Framing
# (Technical network exclusion as quasi-exogenous treatment)
# ================================================================

def natural_experiment_analysis(df):
    """
    Frame the 7 technical_network_exclusion polities as a natural experiment.

    These polities were excluded from dominant maritime/trade networks not by
    policy choice but by geographic/technological constraints. This quasi-random
    assignment allows a difference-based estimate.

    We compare:
      - Treatment: polities reclassified as technical_network_exclusion (n=7)
      - Control: polities with closure_type == 'none' (open, n=60)
      - Additional comparison: policy-closed (maritime_ban + sakoku + bloc)
    """
    print("\n" + "=" * 70)
    print("C. NATURAL EXPERIMENT FRAMING")
    print("   Technical network exclusion as quasi-exogenous treatment")
    print("=" * 70)

    results = {}

    # Apply 7-country reclassification
    from sensitivity_technical_network_exclusion import (
        STRONG_CANDIDATES, MODERATE_CANDIDATES,
        apply_technical_network_exclusion,
    )
    all_candidates = STRONG_CANDIDATES + MODERATE_CANDIDATES
    d = prepare_df(df)
    d_reclass = apply_technical_network_exclusion(d, all_candidates)

    # Groups
    tech_excl = d_reclass[d_reclass["closure_type"] == "technical_network_exclusion"]
    open_grp = d_reclass[d_reclass["closure_type"] == "none"]
    policy_closed = d_reclass[d_reclass["closure_type"].isin(
        ["maritime_ban", "sakoku", "bloc"]
    )]

    print(f"\n--- Group Sizes ---")
    print(f"  Technical exclusion (quasi-exogenous): n={len(tech_excl)}")
    print(f"  Open (control):                       n={len(open_grp)}")
    print(f"  Policy-closed (endogenous):            n={len(policy_closed)}")

    # Conquest rates
    for name, grp in [("Technical exclusion", tech_excl),
                       ("Open", open_grp),
                       ("Policy-closed", policy_closed)]:
        rate = grp["outcome_bin"].mean()
        n = len(grp)
        ci_lo, ci_hi = _wilson_ci(grp["outcome_bin"].sum(), n)
        print(f"\n  {name}: {rate:.1%} ({grp['outcome_bin'].sum()}/{n}), "
              f"95% CI [{ci_lo:.1%}, {ci_hi:.1%}]")

    # Fisher exact: tech_excl vs open
    a = tech_excl["outcome_bin"].sum()
    b = len(tech_excl) - a
    c = open_grp["outcome_bin"].sum()
    dd = len(open_grp) - c
    table = np.array([[a, b], [c, dd]])
    or_val, p_fisher = stats.fisher_exact(table, alternative="greater")
    print(f"\n--- Fisher Exact Test: Tech Exclusion vs Open ---")
    print(f"  OR = {or_val:.3f}, p (one-sided) = {p_fisher:.4f}")

    results["tech_vs_open"] = {
        "tech_rate": float(tech_excl["outcome_bin"].mean()),
        "open_rate": float(open_grp["outcome_bin"].mean()),
        "or": float(or_val),
        "p_fisher": float(p_fisher),
        "n_tech": int(len(tech_excl)),
        "n_open": int(len(open_grp)),
    }

    # Fisher exact: tech_excl vs policy_closed
    a2 = tech_excl["outcome_bin"].sum()
    b2 = len(tech_excl) - a2
    c2 = policy_closed["outcome_bin"].sum()
    d2 = len(policy_closed) - c2
    table2 = np.array([[a2, b2], [c2, d2]])
    or2, p2 = stats.fisher_exact(table2, alternative="two-sided")
    print(f"\n--- Fisher Exact Test: Tech Exclusion vs Policy-Closed ---")
    print(f"  OR = {or2:.3f}, p (two-sided) = {p2:.4f}")

    results["tech_vs_policy"] = {
        "tech_rate": float(tech_excl["outcome_bin"].mean()),
        "policy_rate": float(policy_closed["outcome_bin"].mean()),
        "or": float(or2),
        "p_fisher": float(p2),
    }

    # Covariate comparison (balance check for natural experiment)
    print(f"\n--- Covariate Comparison: Tech Exclusion vs Open ---")
    print(f"  {'Variable':30s} {'Tech Excl':>10s} {'Open':>10s} {'Diff':>8s} {'p (MW)':>8s}")
    cov_balance = {}
    for cov in COVARIATES:
        t_vals = tech_excl[cov].astype(float)
        o_vals = open_grp[cov].astype(float)
        u_stat, p_mw = stats.mannwhitneyu(t_vals, o_vals, alternative="two-sided")
        diff = t_vals.mean() - o_vals.mean()
        print(f"  {cov:30s} {t_vals.mean():>10.3f} {o_vals.mean():>10.3f} "
              f"{diff:>+8.3f} {p_mw:>8.4f}")
        cov_balance[cov] = {
            "tech_mean": float(t_vals.mean()),
            "open_mean": float(o_vals.mean()),
            "diff": float(diff),
            "p_mw": float(p_mw),
        }
    results["covariate_balance"] = cov_balance

    # Dose-response: open < policy-closed < tech-excluded
    print(f"\n--- Dose-Response Pattern ---")
    groups = [
        ("Open (no closure)", open_grp),
        ("Policy-closed", policy_closed),
        ("Tech excluded", tech_excl),
    ]
    rates = []
    for name, grp in groups:
        rate = grp["outcome_bin"].mean()
        rates.append(rate)
        print(f"  {name:30s}: {rate:.1%} (n={len(grp)})")

    # Cochran-Armitage trend test (manual)
    ns = [len(g) for _, g in groups]
    xs = [g["outcome_bin"].sum() for _, g in groups]
    scores = [0, 1, 2]  # dose levels
    N = sum(ns)
    p_bar = sum(xs) / N
    T_num = sum(scores[i] * xs[i] for i in range(3)) - p_bar * sum(scores[i] * ns[i] for i in range(3))
    T_den = math.sqrt(
        p_bar * (1 - p_bar) * (
            sum(scores[i]**2 * ns[i] for i in range(3)) -
            (sum(scores[i] * ns[i] for i in range(3)))**2 / N
        )
    )
    if T_den > 0:
        z_trend = T_num / T_den
        p_trend = 1 - stats.norm.cdf(z_trend)
    else:
        z_trend = 0
        p_trend = 1.0
    print(f"\n  Cochran-Armitage trend test: z = {z_trend:.3f}, p = {p_trend:.4f}")
    results["dose_response"] = {
        "rates": [float(r) for r in rates],
        "z_trend": float(z_trend),
        "p_trend": float(p_trend),
    }

    return results


# ================================================================
# D. Robustness Battery
# ================================================================

def robustness_analysis(df):
    """
    Comprehensive robustness checks using DOMINANT (stock vs flow) as
    the main exposure variable — this is the paper's primary finding.

    D1. E-value (sensitivity to unmeasured confounding)
    D2. Permutation test (placebo assignment)
    D3. Leave-one-out stability
    D4. Alternative outcome definitions
    D5. Bootstrap confidence intervals for key estimates
    D6. VIF (multicollinearity check)
    """
    print("\n" + "=" * 70)
    print("D. ROBUSTNESS BATTERY")
    print("   (Exposure = dominant_binary: stock=1, flow=0)")
    print("=" * 70)

    d = prepare_df(df)
    results = {}

    # Use dominant_binary as the main exposure (stock vs flow)
    EXPOSURE = "dominant_binary"

    # --- D1: E-value ---
    print("\n--- D1. E-value (Sensitivity to Unmeasured Confounders) ---")
    # E-value for the observed OR from Fisher exact test
    table = pd.crosstab(d[EXPOSURE], d["outcome_bin"])
    table = table.reindex(index=[1, 0], columns=[1, 0])
    a, b = table.iloc[0, 0], table.iloc[0, 1]
    c, dd_val = table.iloc[1, 0], table.iloc[1, 1]
    or_observed = (a * dd_val) / (b * c) if b * c > 0 else float('inf')

    # E-value formula: E = OR + sqrt(OR * (OR - 1))
    if or_observed >= 1:
        e_val = or_observed + math.sqrt(or_observed * (or_observed - 1))
    else:
        or_inv = 1 / or_observed
        e_val = or_inv + math.sqrt(or_inv * (or_inv - 1))

    # E-value for lower CI bound
    log_or = math.log(or_observed)
    se_log_or = math.sqrt(1/a + 1/b + 1/c + 1/dd_val)
    or_lo = math.exp(log_or - 1.96 * se_log_or)
    if or_lo >= 1:
        e_val_ci = or_lo + math.sqrt(or_lo * (or_lo - 1))
    else:
        e_val_ci = 1.0

    print(f"  Observed OR (closed vs open): {or_observed:.3f}")
    print(f"  E-value (point estimate):     {e_val:.3f}")
    print(f"  E-value (lower 95% CI):       {e_val_ci:.3f}")
    print(f"\n  Interpretation: An unmeasured confounder would need to be")
    print(f"  associated with both closure and conquest by an OR of at least")
    print(f"  {e_val:.1f} to fully explain the observed association.")
    print(f"  To shift the CI to include the null, it would need OR ≥ {e_val_ci:.1f}.")

    results["e_value"] = {
        "or_observed": float(or_observed),
        "e_value_point": float(e_val),
        "e_value_ci": float(e_val_ci),
        "or_ci_lo": float(or_lo),
    }

    # --- D2: Permutation test ---
    print(f"\n--- D2. Permutation Test (Placebo Assignment) ---")
    n_perm = 10000
    rng = np.random.RandomState(42)
    observed_diff = (d.loc[d[EXPOSURE] == 1, "outcome_bin"].mean() -
                     d.loc[d[EXPOSURE] == 0, "outcome_bin"].mean())
    perm_diffs = []
    T_vec = d[EXPOSURE].values
    Y_vec = d["outcome_bin"].values
    for _ in range(n_perm):
        T_perm = rng.permutation(T_vec)
        diff = Y_vec[T_perm == 1].mean() - Y_vec[T_perm == 0].mean()
        perm_diffs.append(diff)
    perm_diffs = np.array(perm_diffs)
    p_perm = (perm_diffs >= observed_diff).mean()

    print(f"  Observed risk difference: {observed_diff:.4f}")
    print(f"  Permutation p-value (n={n_perm}): {p_perm:.4f}")
    print(f"  Permutation distribution: mean={perm_diffs.mean():.4f}, "
          f"sd={perm_diffs.std():.4f}")

    results["permutation"] = {
        "observed_diff": float(observed_diff),
        "p_perm": float(p_perm),
        "n_perm": n_perm,
    }

    # --- D3: Leave-one-out analysis ---
    print(f"\n--- D3. Leave-One-Out Stability ---")
    # For each polity, remove it and recalculate the main OR
    loo_ors = []
    loo_ps = []
    for i in range(len(d)):
        d_loo = d.drop(d.index[i])
        ct = pd.crosstab(d_loo[EXPOSURE], d_loo["outcome_bin"])
        ct = ct.reindex(index=[1, 0], columns=[1, 0]).fillna(0)
        a_l, b_l = ct.iloc[0, 0], ct.iloc[0, 1]
        c_l, d_l = ct.iloc[1, 0], ct.iloc[1, 1]
        if b_l * c_l > 0:
            or_l = (a_l * d_l) / (b_l * c_l)
        else:
            or_l = float('inf')
        table_l = np.array([[a_l, b_l], [c_l, d_l]])
        _, p_l = stats.fisher_exact(table_l, alternative="greater")
        loo_ors.append(or_l)
        loo_ps.append(p_l)

    loo_ors = np.array(loo_ors)
    loo_ps = np.array(loo_ps)
    finite_ors = loo_ors[np.isfinite(loo_ors)]

    print(f"  Full-sample OR: {or_observed:.3f}")
    print(f"  LOO OR range: [{finite_ors.min():.3f}, {finite_ors.max():.3f}]")
    print(f"  LOO OR mean:  {finite_ors.mean():.3f}")
    print(f"  LOO p-value range: [{loo_ps.min():.4f}, {loo_ps.max():.4f}]")
    print(f"  Sign changes (OR < 1): {(finite_ors < 1).sum()}")
    print(f"  Always significant (p < 0.05): "
          f"{'Yes' if (loo_ps < 0.05).all() else 'No'}")
    # Most influential polity (search over all loo_ors, replacing inf with or_observed)
    max_change_idx = np.argmax(np.abs(np.where(np.isfinite(loo_ors), loo_ors, or_observed) - or_observed))
    loo_or_display = loo_ors[max_change_idx]
    print(f"  Most influential polity: {d.iloc[max_change_idx]['entity']} "
          f"(OR changes to {loo_or_display:.3f})")

    results["loo"] = {
        "full_or": float(or_observed),
        "loo_or_range": [float(finite_ors.min()), float(finite_ors.max())],
        "loo_or_mean": float(finite_ors.mean()),
        "loo_p_range": [float(loo_ps.min()), float(loo_ps.max())],
        "sign_changes": int((finite_ors < 1).sum()),
        "always_sig": bool((loo_ps < 0.05).all()),
    }

    # --- D4: Alternative outcome definitions ---
    print(f"\n--- D4. Alternative Outcome Definitions ---")
    for mode, label in [("overtaken", "Disrupted → overtaken"),
                         ("survived", "Disrupted → survived")]:
        d_alt = prepare_df(df, disrupted_as=mode)
        ct = pd.crosstab(d_alt[EXPOSURE], d_alt["outcome_bin"])
        ct = ct.reindex(index=[1, 0], columns=[1, 0]).fillna(0)
        a_a, b_a = ct.iloc[0, 0], ct.iloc[0, 1]
        c_a, d_a = ct.iloc[1, 0], ct.iloc[1, 1]
        or_a = (a_a * d_a) / (b_a * c_a) if b_a * c_a > 0 else float('inf')
        _, p_a = stats.fisher_exact(
            np.array([[a_a, b_a], [c_a, d_a]]), alternative="greater"
        )
        print(f"  {label:30s}: OR = {or_a:.3f}, p = {p_a:.4f}")
        results[f"alt_outcome_{mode}"] = {
            "or": float(or_a),
            "p": float(p_a),
        }

    # --- D5: Bootstrap CI ---
    print(f"\n--- D5. Bootstrap 95% CI for OR ---")
    n_boot = 5000
    boot_ors = []
    rng_boot = np.random.RandomState(123)
    for _ in range(n_boot):
        idx = rng_boot.choice(len(d), size=len(d), replace=True)
        t_boot = d[EXPOSURE].values[idx]
        y_boot = d["outcome_bin"].values[idx]
        a_b = ((t_boot == 1) & (y_boot == 1)).sum()
        b_b = ((t_boot == 1) & (y_boot == 0)).sum()
        c_b = ((t_boot == 0) & (y_boot == 1)).sum()
        d_b = ((t_boot == 0) & (y_boot == 0)).sum()
        # Haldane correction
        if a_b == 0 or b_b == 0 or c_b == 0 or d_b == 0:
            a_b += 0.5; b_b += 0.5; c_b += 0.5; d_b += 0.5
        or_b = (a_b * d_b) / (b_b * c_b)
        if np.isfinite(or_b):
            boot_ors.append(or_b)
    boot_ors = np.array(boot_ors)
    ci_lo_b, ci_hi_b = np.percentile(boot_ors, [2.5, 97.5])
    print(f"  Bootstrap OR: median = {np.median(boot_ors):.3f}")
    print(f"  Bootstrap 95% CI: [{ci_lo_b:.3f}, {ci_hi_b:.3f}]")

    results["bootstrap_or"] = {
        "median": float(np.median(boot_ors)),
        "ci_lo": float(ci_lo_b),
        "ci_hi": float(ci_hi_b),
        "n_boot": n_boot,
    }

    # --- D6: VIF check ---
    print(f"\n--- D6. Variance Inflation Factor (Multicollinearity) ---")
    X_vif = d[COVARIATES].astype(float)
    X_vif = sm.add_constant(X_vif)
    vif_data = []
    for i, col in enumerate(X_vif.columns):
        if col == "const":
            continue
        vif = variance_inflation_factor(X_vif.values, i)
        vif_data.append((col, vif))
        print(f"  {col:30s}: VIF = {vif:.2f}")
    results["vif"] = {col: float(v) for col, v in vif_data}
    max_vif = max(v for _, v in vif_data)
    print(f"\n  Max VIF: {max_vif:.2f} ({'OK' if max_vif < 5 else 'WARNING: possible multicollinearity'})")

    return results


# ================================================================
# Helpers
# ================================================================

def _wilson_ci(x, n, alpha=0.05):
    """Wilson score interval for a proportion."""
    if n == 0:
        return 0.0, 1.0
    z = stats.norm.ppf(1 - alpha / 2)
    p_hat = x / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return max(0, centre - margin), min(1, centre + margin)


# ================================================================
# Main: run all analyses and save results
# ================================================================

def run_all():
    df = load_data()
    print(f"Data loaded: N = {len(df)}")
    print(f"Closure: {(df['closure_type'] != 'none').sum()} closed, "
          f"{(df['closure_type'] == 'none').sum()} open")
    print()

    all_results = {}

    # A. IV
    all_results["iv_2sls"] = iv_2sls_analysis(df)

    # B. PSM
    all_results["psm"] = psm_analysis(df)

    # C. Natural experiment
    all_results["natural_experiment"] = natural_experiment_analysis(df)

    # D. Robustness
    all_results["robustness"] = robustness_analysis(df)

    # Save results
    out_path = os.path.join(REPORT_DIR, "causal_analysis_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n{'=' * 70}")
    print(f"Results saved to {out_path}")
    print(f"{'=' * 70}")

    return all_results


if __name__ == "__main__":
    run_all()
