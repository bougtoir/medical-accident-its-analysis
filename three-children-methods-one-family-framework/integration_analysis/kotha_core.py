"""
KOTHA core functions (vendored from bougtoir/wip rct-decomposition).

Knowledge-driven Observational-Trial Harmonization Approach:
Module K (counterfactual power), Module T (Bayesian integration),
Module H (OIS / TSA / GRADE linkage). Functions copied verbatim from the
KOTHA validation script so the ONISHI integration analysis is self-contained.
"""

import numpy as np
from scipy import stats


def compute_or(e_t, n_t, e_c, n_c, cc=0.5):
    """log-OR and SE with continuity correction."""
    a = e_t + cc
    b = (n_t - e_t) + cc
    c = e_c + cc
    d = (n_c - e_c) + cc
    logOR = np.log(a * d / (b * c))
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return logOR, se


def fixed_effect_meta(logOR, se):
    """Inverse-variance fixed-effect meta-analysis."""
    w = 1 / se ** 2
    pooled = np.sum(w * logOR) / np.sum(w)
    se_pooled = 1 / np.sqrt(np.sum(w))
    return pooled, se_pooled


def random_effects_meta(logOR, se):
    """DerSimonian-Laird random-effects meta-analysis."""
    logOR = np.asarray(logOR, dtype=float)
    se = np.asarray(se, dtype=float)
    w = 1 / se ** 2
    Q = np.sum(w * (logOR - np.sum(w * logOR) / np.sum(w)) ** 2)
    k = len(logOR)
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0, (Q - (k - 1)) / C) if C > 0 else 0.0
    w_re = 1 / (se ** 2 + tau2)
    pooled = np.sum(w_re * logOR) / np.sum(w_re)
    se_pooled = 1 / np.sqrt(np.sum(w_re))
    I2 = max(0, (Q - (k - 1)) / Q * 100) if Q > 0 else 0
    return pooled, se_pooled, tau2, I2


def weighted_meta(logOR, se, extra_weight):
    """Information-weighted meta-analysis: combine inverse-variance weights with
    an external per-study information weight (e.g. LINKO ICR). Returns pooled
    log-OR and SE using w_i = (1/se_i^2) * extra_weight_i (normalised)."""
    logOR = np.asarray(logOR, dtype=float)
    se = np.asarray(se, dtype=float)
    ew = np.asarray(extra_weight, dtype=float)
    ew = ew / ew.mean()  # normalise so mean weight = 1 (comparable to IV)
    w = (1 / se ** 2) * ew
    pooled = np.sum(w * logOR) / np.sum(w)
    se_pooled = np.sqrt(np.sum(w ** 2 * se ** 2)) / np.sum(w)
    return pooled, se_pooled


def power_analytical(p_control, OR, n_total, alpha=0.05):
    """Analytical power via Schoenfeld/event-based approximation.
    Returns (power, total_expected_events)."""
    p_treat = (p_control * OR) / (1 - p_control + p_control * OR)
    n_arm = n_total // 2
    e_ctrl = n_arm * p_control
    e_treat = n_arm * p_treat
    total_events = e_ctrl + e_treat
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    logOR = np.log(OR)
    se_logOR = 2 / np.sqrt(total_events) if total_events > 0 else np.inf
    z_effect = abs(logOR) / se_logOR
    power = stats.norm.cdf(z_effect - z_alpha)
    return power, total_events


def ois_calculation(OR, alpha=0.05, power=0.80):
    """Optimal Information Size (required number of events)."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    logOR = np.log(OR)
    D = 4 * (z_alpha + z_beta) ** 2 / logOR ** 2
    return D


def cumulative_z(logOR_arr, se_arr):
    """Cumulative Z-statistic for Trial Sequential Analysis."""
    logOR_arr = np.asarray(logOR_arr, dtype=float)
    se_arr = np.asarray(se_arr, dtype=float)
    z_values, pooled_list, info_list = [], [], []
    for k in range(1, len(logOR_arr) + 1):
        w = 1 / se_arr[:k] ** 2
        pooled = np.sum(w * logOR_arr[:k]) / np.sum(w)
        se_pooled = 1 / np.sqrt(np.sum(w))
        z_values.append(pooled / se_pooled)
        pooled_list.append(pooled)
        info_list.append(np.sum(w))
    return np.array(z_values), np.array(pooled_list), np.array(info_list)


def bias_adjusted_normal(logY_rct, se_rct, logY_obs, se_obs, delta_grid):
    """Analytical normal bias-adjusted integration across a bias grid delta."""
    logY_rct = np.asarray(logY_rct, dtype=float)
    se_rct = np.asarray(se_rct, dtype=float)
    logY_obs = np.asarray(logY_obs, dtype=float)
    se_obs = np.asarray(se_obs, dtype=float)
    results = {}
    for delta in delta_grid:
        logY_adj = logY_obs + delta
        logY_all = np.concatenate([logY_rct, logY_adj])
        se_all = np.concatenate([se_rct, se_obs])
        pooled, se_p, tau2, I2 = random_effects_meta(logY_all, se_all)
        results[delta] = {
            'hr': float(np.exp(pooled)),
            'ci_lo': float(np.exp(pooled - 1.96 * se_p)),
            'ci_hi': float(np.exp(pooled + 1.96 * se_p)),
            'p_benefit': float(stats.norm.cdf(0, loc=pooled, scale=se_p)),
            'pooled': float(pooled), 'se': float(se_p),
        }
    return results


def power_prior_meta(logY_rct, se_rct, logY_obs, se_obs, alpha_grid,
                     n_iter=8000, n_warmup=2000):
    """Power-prior meta-analysis: discount observational likelihood by alpha.

    Model: y_i ~ Normal(mu, se_i^2 + tau^2); obs likelihood raised to power alpha.
    Simple 2-parameter random-walk Metropolis on (mu, log tau).
    """
    logY_rct = np.asarray(logY_rct, dtype=float)
    se_rct = np.asarray(se_rct, dtype=float)
    logY_obs = np.asarray(logY_obs, dtype=float)
    se_obs = np.asarray(se_obs, dtype=float)
    results = {}
    for alpha in alpha_grid:
        rng = np.random.default_rng(42)
        mu = 0.0
        log_tau = np.log(0.1)
        step_mu = 0.04
        step_log_tau = 0.08
        mu_samples = np.empty(n_iter)
        idx = 0

        def log_post(mu, log_tau):
            tau = np.exp(log_tau)
            var_rct = se_rct ** 2 + tau ** 2
            ll_rct = np.sum(stats.norm.logpdf(logY_rct, loc=mu, scale=np.sqrt(var_rct)))
            var_obs = se_obs ** 2 + tau ** 2
            ll_obs = alpha * np.sum(stats.norm.logpdf(logY_obs, loc=mu, scale=np.sqrt(var_obs)))
            lp_mu = stats.norm.logpdf(mu, 0, 10)
            lp_tau = stats.halfcauchy.logpdf(tau, scale=0.5) + log_tau
            return ll_rct + ll_obs + lp_mu + lp_tau

        current_lp = log_post(mu, log_tau)
        for it in range(n_warmup + n_iter):
            mu_p = mu + rng.normal(0, step_mu)
            lt_p = log_tau + rng.normal(0, step_log_tau)
            lp_p = log_post(mu_p, lt_p)
            if np.log(rng.uniform()) < lp_p - current_lp:
                mu, log_tau, current_lp = mu_p, lt_p, lp_p
            if it >= n_warmup:
                mu_samples[idx] = mu
                idx += 1
        mu_arr = mu_samples[:idx]
        hr_arr = np.exp(mu_arr)
        results[alpha] = {
            'hr_median': float(np.median(hr_arr)),
            'hr_lo': float(np.percentile(hr_arr, 2.5)),
            'hr_hi': float(np.percentile(hr_arr, 97.5)),
            'p_benefit': float(np.mean(hr_arr < 1.0)),
        }
    return results
