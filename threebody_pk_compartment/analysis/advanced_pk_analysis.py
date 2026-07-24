"""
Advanced PK analysis for three-body scattering.

Module 1: Nonlinear PK (Michaelis-Menten) model for sticky chaos tails
Module 2: Population PK (mixed-effects) for mass-ratio dependence
Module 3: Reverse application to TMDD pharmacokinetics

References
----------
Ginat & Perets, Nature 593 395 (2021)
Stone & Leigh, Nature 576 406 (2019)
Mager & Jusko, J Pharmacokinet Pharmacodyn 28, 507 (2001) — TMDD
"""

from __future__ import annotations

import json
import os

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.optimize import minimize, differential_evolution
from scipy.stats import kstest, linregress


# ===================================================================
# MODULE 1: Nonlinear PK model for sticky chaos
# ===================================================================

def nonlinear_pk_ode(t, P, params):
    """
    Nonlinear 3-compartment PK ODE with Michaelis-Menten kinetics.

    params = (Vmax_ij[6], Km_ij[6], Ve[3], Kme[3]) = 18 parameters
    Simplified: assume Km is shared across all transitions, reducing to:
    params = (Vmax_ij[6], Ve[3], Km_shared, Kme_shared) = 11 parameters

    For further reduction, use a "hybrid" model:
    - Inter-compartment transfers: linear (first-order) — k_ij * P_i
    - Elimination: nonlinear (MM) — Ve_i * P_i / (Km + P_i)

    This is physically motivated: inter-config transitions are fast
    (ergodic-like), but escape requires accessing a specific phase-space
    region (like enzyme saturation).
    """
    P1, P2, P3 = np.maximum(P, 0.0)

    # Unpack: [k12, k13, k21, k23, k31, k32, Ve1, Ve2, Ve3, Km]
    k12, k13, k21, k23, k31, k32 = params[:6]
    Ve1, Ve2, Ve3 = params[6:9]
    Km = params[9]

    # MM elimination
    def mm_elim(Ve, Pi):
        return Ve * Pi / (Km + Pi) if Pi > 0 else 0.0

    dP1 = -(k12 + k13) * P1 + k21 * P2 + k31 * P3 - mm_elim(Ve1, P1)
    dP2 = k12 * P1 - (k21 + k23) * P2 + k32 * P3 - mm_elim(Ve2, P2)
    dP3 = k13 * P1 + k23 * P2 - (k31 + k32) * P3 - mm_elim(Ve3, P3)

    return [dP1, dP2, dP3]


def nonlinear_pk_survival(t_eval, params, P0):
    """Compute survival probability S(t) for the nonlinear model."""
    sol = solve_ivp(
        nonlinear_pk_ode, [0, t_eval[-1]], P0, args=(params,),
        t_eval=t_eval, method="RK45", rtol=1e-8, atol=1e-10,
    )
    if sol.success:
        return np.sum(sol.y, axis=0)
    return np.ones(len(t_eval)) * np.nan


def nonlinear_pk_escape_pdf(t_eval, params, P0, dt=None):
    """Compute escape PDF f(t) = -dS/dt via numerical differentiation."""
    S = nonlinear_pk_survival(t_eval, params, P0)
    if dt is None:
        dt = np.diff(t_eval)
        dt = np.append(dt, dt[-1])
    f = -np.gradient(S, t_eval)
    return np.maximum(f, 0)


def stretched_exp_survival(t, params):
    """
    Stretched/modified exponential survival function.

    S(t) = w1*exp(-lam1*t) + w2*exp(-lam2*t) + w3*t^(-alpha)*exp(-lam3*t)

    The third term adds a power-law prefactor to model sticky chaos.
    This is the analytical prediction of nonlinear (MM) elimination:
    when elimination saturates, the slowest decay picks up an algebraic
    correction.

    params = [w1, w2, w3, lam1, lam2, lam3, alpha]
    """
    w1, w2, w3, lam1, lam2, lam3, alpha = params
    S = (w1 * np.exp(-lam1 * t)
         + w2 * np.exp(-lam2 * t)
         + w3 * np.maximum(t, 1e-10) ** (-alpha) * np.exp(-lam3 * t))
    return np.clip(S, 0, 1)


def fit_nonlinear_pk(lifetimes, P0, linear_rates, method="nm"):
    """
    Fit stretched exponential model (fast, no ODE solving).

    The model captures the power-law tail from sticky chaos
    via a stretched exponential with algebraic prefactor.
    """
    lt = np.sort(lifetimes)
    S_emp = 1 - np.arange(1, len(lt) + 1) / len(lt)

    # Subsample for speed
    n_pts = min(300, len(lt))
    idx = np.linspace(0, len(lt) - 1, n_pts, dtype=int)
    t_fit = lt[idx]
    S_fit = S_emp[idx]

    # Get eigenvalues of linear model for initial guess
    A_lin = np.zeros((3, 3))
    k12, k13, k21, k23, k31, k32 = linear_rates[:6]
    ke1, ke2, ke3 = linear_rates[6:9]
    A_lin[0, :] = [-(k12+k13+ke1), k21, k31]
    A_lin[1, :] = [k12, -(k21+k23+ke2), k32]
    A_lin[2, :] = [k13, k23, -(k31+k32+ke3)]
    eigs = np.sort(-np.real(np.linalg.eigvals(A_lin)))
    eigs = np.maximum(eigs, 1e-8)

    def objective(v):
        v = np.abs(v)
        # Ensure weights sum <= 1 and rates > 0
        w1, w2, w3 = v[0], v[1], v[2]
        lam1, lam2, lam3 = v[3], v[4], v[5]
        alpha = v[6]
        params = [w1, w2, w3, lam1, lam2, lam3, alpha]
        S_pred = stretched_exp_survival(t_fit, params)
        log_S_pred = np.log10(np.maximum(S_pred, 1e-15))
        log_S_fit = np.log10(np.maximum(S_fit, 1e-15))
        return np.sum((log_S_pred - log_S_fit) ** 2)

    # Initial guess from eigenvalues
    x0 = np.array([
        0.3, 0.3, 0.4 * np.median(lt) ** 0.5,  # weights (w3 scaled)
        eigs[2], eigs[1], eigs[0] * 0.1,  # rates (fast, mid, slow)
        0.5,  # power-law exponent
    ])

    result = minimize(objective, x0, method="Nelder-Mead",
                      options={"maxiter": 10000, "xatol": 1e-10, "fatol": 1e-10})

    best_params = np.abs(result.x)
    return best_params, result.fun


def compare_linear_vs_nonlinear(lifetimes, P0, A_linear, rates_linear):
    """
    Compare linear (multi-exponential) vs nonlinear (hybrid MM) models.

    Returns dict with both models' predictions and goodness-of-fit metrics.
    """
    lt = np.sort(lifetimes)
    S_emp = 1 - np.arange(1, len(lt) + 1) / len(lt)

    # Time grid for evaluation
    t_grid = np.logspace(np.log10(max(lt[0], 0.1)),
                         np.log10(lt[-1]), 500)

    # Linear model survival
    S_linear = np.zeros(len(t_grid))
    for i, ti in enumerate(t_grid):
        S_linear[i] = np.sum(expm(A_linear * ti) @ P0)

    # Fit nonlinear model
    linear_vec = np.array([
        rates_linear["k12"], rates_linear["k13"],
        rates_linear["k21"], rates_linear["k23"],
        rates_linear["k31"], rates_linear["k32"],
        rates_linear["ke1"], rates_linear["ke2"], rates_linear["ke3"],
    ])

    print("    Fitting stretched-exponential (nonlinear PK) model...")
    nl_params, nl_cost = fit_nonlinear_pk(lifetimes, P0, linear_vec)
    print(f"    Nonlinear fit cost: {nl_cost:.4f}")
    print(f"    Params: w=[{nl_params[0]:.4f}, {nl_params[1]:.4f}, {nl_params[2]:.4f}]")
    print(f"    Rates: λ=[{nl_params[3]:.6f}, {nl_params[4]:.6f}, {nl_params[5]:.6f}]")
    print(f"    Power-law exponent α = {nl_params[6]:.4f}")

    S_nonlinear = stretched_exp_survival(t_grid, nl_params)

    # Goodness of fit: log-space RMSE in the tail (top 10% of lifetimes)
    tail_mask = lt > np.percentile(lt, 90)
    lt_tail = lt[tail_mask]
    S_tail = S_emp[tail_mask]

    S_lin_tail = np.zeros(len(lt_tail))
    for i, ti in enumerate(lt_tail):
        S_lin_tail[i] = np.sum(expm(A_linear * ti) @ P0)

    S_nl_tail = stretched_exp_survival(lt_tail, nl_params)

    def log_rmse(S_pred, S_obs):
        valid = (S_pred > 1e-15) & (S_obs > 1e-15)
        if np.sum(valid) < 3:
            return float("inf")
        return np.sqrt(np.mean(
            (np.log10(S_pred[valid]) - np.log10(S_obs[valid])) ** 2
        ))

    rmse_linear = log_rmse(S_lin_tail, S_tail)
    rmse_nonlinear = log_rmse(S_nl_tail, S_tail)
    print(f"    Tail log-RMSE: linear={rmse_linear:.4f}, nonlinear={rmse_nonlinear:.4f}")

    # Power-law tail fit: S(t) ~ t^{-alpha} for large t
    tail_90 = lt > np.percentile(lt, 80)
    lt_t90 = lt[tail_90]
    S_t90 = S_emp[tail_90]
    valid_pl = (lt_t90 > 0) & (S_t90 > 0)
    if np.sum(valid_pl) > 5:
        slope, intercept, r_val, _, _ = linregress(
            np.log10(lt_t90[valid_pl]), np.log10(S_t90[valid_pl])
        )
        alpha_power_law = -slope
        print(f"    Power-law tail exponent: alpha = {alpha_power_law:.2f} (R²={r_val**2:.3f})")
    else:
        alpha_power_law = float("nan")

    return {
        "t_grid": t_grid,
        "S_linear": S_linear,
        "S_nonlinear": S_nonlinear,
        "nl_params": nl_params,
        "nl_cost": nl_cost,
        "rmse_linear_tail": rmse_linear,
        "rmse_nonlinear_tail": rmse_nonlinear,
        "alpha_power_law": alpha_power_law,
        "lt_sorted": lt,
        "S_empirical": S_emp,
    }


# ===================================================================
# MODULE 2: Population PK — mass-ratio dependence
# ===================================================================

def load_mass_scan(datadir):
    """Load mass scan results from Julia output."""
    path = os.path.join(datadir, "mass_scan.json")
    with open(path) as f:
        return json.load(f)


def population_pk_analysis(scan_data):
    """
    Analyse mass-ratio dependence of PK parameters.

    For each mass configuration, extract:
    - Rate constants k_ij, k_e_i
    - Half-lives (eigenvalues)
    - MRT (mean residence time)
    - Escape probabilities

    Then fit population-level relationships:
    - k_ij = f(mass_ratio) with inter-individual variability
    - This is the Population PK analogue
    """
    records = []
    for entry in scan_data:
        m1, m2, m3 = entry["masses"]
        M = m1 + m2 + m3
        q2, q3 = m2 / M, m3 / M  # mass fractions

        rates = entry["rates"]  # 3x3 list
        ke = entry["ke"]        # [3]

        # Build rate matrix A in column convention (dp/dt = A p):
        # A[j, i] is the rate from compartment i -> j.
        A = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                if i != j:
                    A[j, i] = rates[i][j]
            A[i, i] = -(sum(rates[i][j] for j in range(3) if j != i) + ke[i])

        # Eigenvalues → half-lives
        eigs = np.sort(np.real(np.linalg.eigvals(A)))
        half_lives = np.log(2) / (-eigs + 1e-30)

        # MRT
        P0 = np.array([1.0, 0.0, 0.0])  # always start with binary(1,2)
        try:
            mrt = -np.ones(3) @ np.linalg.inv(A) @ P0
        except np.linalg.LinAlgError:
            mrt = float("inf")

        # Reduced mass of initial binary
        mu12 = m1 * m2 / (m1 + m2)
        # Reduced mass of binary-single system
        mu_out = (m1 + m2) * m3 / M

        records.append({
            "m1": m1, "m2": m2, "m3": m3, "M": M,
            "q2": q2, "q3": q3,
            "mu12": mu12, "mu_out": mu_out,
            "rates_flat": [rates[i][j] for i in range(3) for j in range(3) if i != j],
            "ke": ke,
            "eigs": eigs.tolist(),
            "half_lives": half_lives.tolist(),
            "mrt": mrt,
            "lifetimes_median": entry["lifetimes_median"],
            "lifetimes_mean": entry["lifetimes_mean"],
            "mean_excursions": entry["mean_excursions"],
            "escaper_probs": entry["escaper_probs"],
            "n_escape": entry["n_escape"],
        })

    return records


def _ols_r2(X, y):
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    yp = X @ beta
    ss_res = np.sum((y - yp) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return (1 - ss_res / ss_tot if ss_tot > 0 else 0.0), beta


def _vif(cols):
    """Variance inflation factors for a list of covariate arrays."""
    vifs = []
    for i in range(len(cols)):
        others = [cols[j] for j in range(len(cols)) if j != i]
        X = np.column_stack([np.ones(len(cols[i]))] + others)
        r2, _ = _ols_r2(X, cols[i])
        vifs.append(1.0 / (1.0 - r2) if r2 < 1 else np.inf)
    return vifs


def _shapley_r2(cols, y):
    """LMG / Shapley-value decomposition of R^2 across the covariates."""
    import itertools
    from math import factorial
    n = len(cols)
    names = list(range(n))

    def r2_of(idxs):
        if not idxs:
            return 0.0
        X = np.column_stack([np.ones(len(y))] + [cols[k] for k in idxs])
        return _ols_r2(X, y)[0]

    share = [0.0] * n
    for perm in itertools.permutations(names):
        prev = []
        for k in perm:
            share[k] += r2_of(prev + [k]) - r2_of(prev)
            prev = prev + [k]
    return [s / factorial(n) for s in share]


def fit_population_model(records, response="mrt"):
    """
    Fit population-level PK parameter relationships.

    Model: log(y) = a0 + a1*log(mu12) + a2*log(mu_out) + a3*log(M) + epsilon
    This is analogous to allometric scaling in clinical PK:
      CL = CL_ref * (BW/70)^alpha

    For three-body: y ∝ mu12^a1 * mu_out^a2 * M^a3, where y is the MRT
    (``response='mrt'``) or the median lifetime (``response='median'``).
    Also returns variance inflation factors (VIF) and an LMG/Shapley
    decomposition of R^2 to diagnose and fairly attribute the collinear
    covariates, plus an orthogonal-design-axis fit on (m2, m3).
    """
    key = "mrt" if response == "mrt" else "lifetimes_median"
    valid = [r for r in records
             if r.get(key, 0) > 0 and np.isfinite(r.get(key, 0))
             and r["mrt"] > 0 and np.isfinite(r["mrt"])]
    if len(valid) < 5:
        return None

    # Collinear reduced-mass covariates.
    c_mu12 = np.log([r["mu12"] for r in valid])
    c_muout = np.log([r["mu_out"] for r in valid])
    c_M = np.log([r["M"] for r in valid])
    # Design matrix: [1, log(mu12), log(mu_out), log(M)]
    X = np.column_stack([np.ones(len(valid)), c_mu12, c_muout, c_M])
    y = np.log([r[key] for r in valid])

    # OLS fit
    r_squared, beta = _ols_r2(X, y)
    y_pred = X @ beta

    # Prediction errors
    errors = y - y_pred
    omega = np.std(errors)  # inter-individual variability (eta in NONMEM)

    # Collinearity diagnostics + fair R^2 attribution.
    cov_cols = [c_mu12, c_muout, c_M]
    vif = _vif(cov_cols)
    shapley = _shapley_r2(cov_cols, y)

    # Orthogonal-design-axis fit on (m2, m3) (m1 fixed => nearly uncorrelated).
    c_m2 = np.log([r["m2"] for r in valid])
    c_m3 = np.log([r["m3"] for r in valid])
    Xo = np.column_stack([np.ones(len(valid)), c_m2, c_m3])
    r2_ortho, beta_ortho = _ols_r2(Xo, y)
    corr_m2m3 = float(np.corrcoef(c_m2, c_m3)[0, 1])

    print(f"    Population PK model ({response}): log(y) = {beta[0]:.2f} + "
          f"{beta[1]:.2f}*log(mu12) + {beta[2]:.2f}*log(mu_out) + "
          f"{beta[3]:.2f}*log(M)")
    print(f"    R² = {r_squared:.4f}  omega = {omega:.4f}")
    print(f"    → y ∝ mu12^{beta[1]:.2f} * mu_out^{beta[2]:.2f} * M^{beta[3]:.2f}")
    print(f"    VIF (mu12, mu_out, M) = "
          f"({vif[0]:.2f}, {vif[1]:.2f}, {vif[2]:.2f})")
    print(f"    Shapley/LMG R² shares = "
          f"({shapley[0]:.3f}, {shapley[1]:.3f}, {shapley[2]:.3f})")
    print(f"    Orthogonal (m2,m3) fit: R²={r2_ortho:.3f}, "
          f"m2^{beta_ortho[1]:.2f} m3^{beta_ortho[2]:.2f} "
          f"(corr[log m2, log m3]={corr_m2m3:.3f})")

    # Also fit escape probability of lightest body
    p_esc_lightest = []
    for r in valid:
        masses = [r["m1"], r["m2"], r["m3"]]
        lightest = np.argmin(masses)
        p_esc_lightest.append(r["escaper_probs"][lightest])

    mass_ratio_range = [min(r["m3"]) if isinstance(r["m3"], list) else r["m3"]
                        for r in valid]
    q_min = [min(r["m1"], r["m2"], r["m3"]) / r["M"] for r in valid]

    # Logistic model: P(lightest escapes) = 1 / (1 + exp(-(b0 + b1*log(q_min))))
    from scipy.optimize import curve_fit

    def logistic(x, b0, b1):
        return 1 / (1 + np.exp(-(b0 + b1 * x)))

    try:
        q_arr = np.array(q_min)
        p_arr = np.array(p_esc_lightest)
        valid_fit = (q_arr > 0) & np.isfinite(p_arr)
        popt, pcov = curve_fit(logistic, np.log(q_arr[valid_fit]),
                                p_arr[valid_fit], p0=[0, -1], maxfev=5000)
        print(f"    Lightest-body escape: logistic(b0={popt[0]:.2f}, b1={popt[1]:.2f})")
    except Exception as e:
        print(f"    Lightest-body escape fit failed: {e}")
        popt = None

    return {
        "response": response,
        "beta": beta.tolist(),
        "r_squared": r_squared,
        "omega": omega,
        "n": len(valid),
        "vif": [float(v) for v in vif],
        "shapley_r2": [float(s) for s in shapley],
        "beta_ortho": beta_ortho.tolist(),
        "r2_ortho": float(r2_ortho),
        "corr_m2m3": corr_m2m3,
        "records": valid,
        "logistic_params": popt.tolist() if popt is not None else None,
        "q_min": q_min,
        "p_esc_lightest": p_esc_lightest,
    }


# ===================================================================
# MODULE 3: TMDD reverse application
# ===================================================================

def tmdd_ode(t, y, params):
    """
    Target-Mediated Drug Disposition ODE.

    State variables:
      C  = free drug concentration
      R  = free receptor concentration
      CR = drug-receptor complex concentration

    Parameters:
      ksyn  = receptor synthesis rate
      kdeg  = receptor degradation rate
      kon   = association rate constant
      koff  = dissociation rate constant
      kint  = complex internalisation rate
      kel   = drug elimination rate
      Input = drug input rate (constant infusion)
    """
    C, R, CR = np.maximum(y, 0)
    ksyn, kdeg, kon, koff, kint, kel, Input = params

    dC = Input - kel * C - kon * C * R + koff * CR
    dR = ksyn - kdeg * R - kon * C * R + koff * CR
    dCR = kon * C * R - (koff + kint) * CR

    return [dC, dR, dCR]


def tmdd_steady_states(params):
    """
    Find steady states of the TMDD system analytically/numerically.

    At steady state: dC/dt = dR/dt = dCR/dt = 0

    From dR/dt = 0: R_ss = (ksyn + koff*CR_ss) / (kdeg + kon*C_ss)
    From dCR/dt = 0: CR_ss = kon*C_ss*R_ss / (koff + kint)
    From dC/dt = 0: C_ss = (Input + koff*CR_ss) / (kel + kon*R_ss)

    This is a nonlinear system; solve numerically.
    """
    from scipy.optimize import fsolve

    ksyn, kdeg, kon, koff, kint, kel, Input = params

    def equations(y):
        C, R, CR = np.maximum(y, 1e-15)
        eq1 = Input - kel * C - kon * C * R + koff * CR
        eq2 = ksyn - kdeg * R - kon * C * R + koff * CR
        eq3 = kon * C * R - (koff + kint) * CR
        return [eq1, eq2, eq3]

    # Multiple initial guesses to find all steady states
    steady_states = []
    guesses = [
        [Input / kel, ksyn / kdeg, 0.01],  # low binding
        [0.1, ksyn / kdeg, Input / kint],   # high binding
        [Input / (kel + kon * ksyn / kdeg), ksyn / kdeg, 1.0],  # intermediate
    ]

    for x0 in guesses:
        try:
            sol = fsolve(equations, x0, full_output=True)
            x_sol = sol[0]
            info = sol[1]
            if all(x_sol > -1e-10):
                x_sol = np.maximum(x_sol, 0)
                # Check if it's actually a steady state
                resid = np.max(np.abs(equations(x_sol)))
                if resid < 1e-8:
                    # Check if this is a new steady state
                    is_new = True
                    for ss in steady_states:
                        if np.allclose(x_sol, ss["state"], atol=1e-6):
                            is_new = False
                            break
                    if is_new:
                        steady_states.append({
                            "state": x_sol.tolist(),
                            "C": x_sol[0], "R": x_sol[1], "CR": x_sol[2],
                            "residual": resid,
                        })
        except Exception:
            pass

    return steady_states


def tmdd_stability_analysis(params, ss):
    """
    Analyse stability of a TMDD steady state via Jacobian eigenvalues.

    This is the direct analogue of Lagrange point stability analysis
    in the three-body problem.
    """
    ksyn, kdeg, kon, koff, kint, kel, Input = params
    C, R, CR = ss["C"], ss["R"], ss["CR"]

    # Jacobian of the TMDD system
    J = np.array([
        [-(kel + kon * R), -kon * C, koff],
        [-kon * R, -(kdeg + kon * C), koff],
        [kon * R, kon * C, -(koff + kint)],
    ])

    eigs = np.linalg.eigvals(J)
    is_stable = all(np.real(eigs) < 0)

    return {
        "eigenvalues": eigs.tolist(),
        "eigenvalues_real": np.real(eigs).tolist(),
        "is_stable": is_stable,
        "half_lives": (np.log(2) / (-np.real(eigs) + 1e-30)).tolist(),
    }


def tmdd_dose_response_bifurcation(base_params, dose_range):
    """
    Compute dose-response curve and identify bifurcation points.

    Analogous to mapping stability boundaries in three-body parameter space
    (Mardling-Aarseth criterion ↔ TMDD bifurcation condition).
    """
    results = []
    for dose in dose_range:
        params = list(base_params)
        params[6] = dose  # Input rate

        ss_list = tmdd_steady_states(params)
        for ss in ss_list:
            stab = tmdd_stability_analysis(params, ss)
            results.append({
                "dose": dose,
                "C_ss": ss["C"],
                "R_ss": ss["R"],
                "CR_ss": ss["CR"],
                "is_stable": stab["is_stable"],
                "eigenvalues_real": stab["eigenvalues_real"],
                "half_lives": stab["half_lives"],
            })

    return results


def tmdd_three_body_analogy():
    """
    Demonstrate the structural analogy between TMDD and three-body:

    TMDD:
      Drug(C) ↔ Receptor(R) → Complex(CR) → Internalisation
      Three states: free drug, free receptor, complex

    Three-body:
      Body 1 ↔ Body 2 → Binary(1,2) + Single 3 → Escape
      Three states: config 1, config 2, config 3

    The Jacobian structure is identical.
    """
    print("\n  TMDD ↔ Three-body structural analogy:")
    print("  " + "=" * 50)
    print(f"  {'TMDD':>20s}  {'Three-body':>20s}")
    print("  " + "-" * 50)
    print(f"  {'Drug (C)':>20s}  {'Binary(1,2)+3':>20s}")
    print(f"  {'Receptor (R)':>20s}  {'Binary(1,3)+2':>20s}")
    print(f"  {'Complex (CR)':>20s}  {'Binary(2,3)+1':>20s}")
    print(f"  {'Drug elimination':>20s}  {'Escape from C1':>20s}")
    print(f"  {'Receptor turnover':>20s}  {'Escape from C2':>20s}")
    print(f"  {'Internalisation':>20s}  {'Escape from C3':>20s}")
    print(f"  {'kon·C·R (binding)':>20s}  {'k_ij (transition)':>20s}")
    print(f"  {'Dose (Input)':>20s}  {'Initial condition':>20s}")
    print(f"  {'Steady state':>20s}  {'Equilibrium point':>20s}")
    print(f"  {'Jacobian eigvals':>20s}  {'Lagrange stability':>20s}")
    print("  " + "=" * 50)

    # Example TMDD parameters (typical monoclonal antibody)
    # ksyn, kdeg, kon, koff, kint, kel, Input
    base_params = (0.1, 0.01, 0.1, 0.001, 0.05, 0.01, 0.0)

    # Dose-response bifurcation analysis
    dose_range = np.logspace(-3, 2, 100)
    bifurcation = tmdd_dose_response_bifurcation(base_params, dose_range)

    return base_params, bifurcation
