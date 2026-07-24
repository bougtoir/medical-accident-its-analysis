"""
Pharmacokinetic compartmental model for three-body scattering.

Maps the three-body resonant scattering problem onto a 3-compartment
pharmacokinetic model with first-order (linear) and Michaelis-Menten
(nonlinear) inter-compartmental transfer and elimination.

Compartment definitions
-----------------------
  Compartment 1: binary (0,1) + single 2
  Compartment 2: binary (0,2) + single 1
  Compartment 3: binary (1,2) + single 0

Transfer rate k_ij: rate of transition from compartment i to j
Elimination rate k_ei: rate of escape (system dissolution) from compartment i

Linear model
------------
  dP1/dt = -(k12 + k13 + ke1)*P1 + k21*P2 + k31*P3
  dP2/dt =  k12*P1 - (k21 + k23 + ke2)*P2 + k32*P3
  dP3/dt =  k13*P1 +  k23*P2 - (k31 + k32 + ke3)*P3

Nonlinear (Michaelis-Menten) model — for sticky chaos
------------------------------------------------------
  Transfer rate becomes: Vmax_ij * Pi / (Km_ij + Pi)
  This saturates at high "concentration" (probability), producing
  power-law tails in the lifetime distribution rather than pure
  exponential decay.

References
----------
Ginat & Perets, Nature 593 395 (2021)
Stone & Leigh, Nature 576 406 (2019)
"""

from __future__ import annotations

import dataclasses
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp
from scipy.optimize import minimize, differential_evolution
from scipy.linalg import expm

from simulations.threebody_scattering import ScatteringOutcome, BinaryConfig


# ---------------------------------------------------------------------------
# Configuration mapping
# ---------------------------------------------------------------------------

# Map binary pair → compartment index
PAIR_TO_COMPARTMENT = {
    (0, 1): 0,
    (0, 2): 1,
    (1, 2): 2,
}


def outcomes_to_transition_counts(outcomes: list[ScatteringOutcome]) -> dict:
    """
    Extract transition counts and dwell times from scattering outcomes.

    Returns
    -------
    dict with keys:
        'transition_matrix' : (3, 3) array of transition counts (i→j)
        'escape_counts' : (3,) array of escape counts from each compartment
        'dwell_times' : dict mapping compartment index → list of dwell times
        'lifetimes' : list of total lifetimes for escaped systems
        'escaper_from_compartment' : (3,) counts of which compartment led to escape
        'n_excursions' : list of excursion counts
    """
    trans = np.zeros((3, 3), dtype=int)
    esc_counts = np.zeros(3, dtype=int)
    dwell_times: dict[int, list[float]] = {0: [], 1: [], 2: []}
    lifetimes = []
    n_exc_list = []

    for outcome in outcomes:
        if outcome.status != "escape":
            continue

        seq = outcome.config_sequence
        if not seq:
            continue

        lifetimes.append(outcome.lifetime)
        n_exc_list.append(outcome.n_excursions)

        # Count transitions
        for k in range(len(seq) - 1):
            c_from = PAIR_TO_COMPARTMENT.get(seq[k].binary_pair)
            c_to = PAIR_TO_COMPARTMENT.get(seq[k + 1].binary_pair)
            if c_from is not None and c_to is not None and c_from != c_to:
                trans[c_from, c_to] += 1

        # Dwell times
        for k in range(len(seq)):
            c = PAIR_TO_COMPARTMENT.get(seq[k].binary_pair)
            if c is None:
                continue
            t_start = seq[k].t
            t_end = seq[k + 1].t if k + 1 < len(seq) else outcome.lifetime
            dwell_times[c].append(t_end - t_start)

        # Which compartment led to escape
        last_cfg = seq[-1]
        c_last = PAIR_TO_COMPARTMENT.get(last_cfg.binary_pair)
        if c_last is not None:
            esc_counts[c_last] += 1

    return {
        "transition_matrix": trans,
        "escape_counts": esc_counts,
        "dwell_times": dwell_times,
        "lifetimes": lifetimes,
        "escaper_from_compartment": esc_counts,
        "n_excursions": n_exc_list,
    }


# ---------------------------------------------------------------------------
# Linear 3-compartment PK model
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class LinearPKParams:
    """Parameters for the linear 3-compartment model."""
    k12: float   # transfer rate 1→2
    k13: float   # transfer rate 1→3
    k21: float   # transfer rate 2→1
    k23: float   # transfer rate 2→3
    k31: float   # transfer rate 3→1
    k32: float   # transfer rate 3→2
    ke1: float   # elimination (escape) rate from compartment 1
    ke2: float   # elimination (escape) rate from compartment 2
    ke3: float   # elimination (escape) rate from compartment 3

    def rate_matrix(self) -> NDArray:
        """Return the 3x3 rate matrix A such that dP/dt = A @ P."""
        A = np.array([
            [-(self.k12 + self.k13 + self.ke1), self.k21, self.k31],
            [self.k12, -(self.k21 + self.k23 + self.ke2), self.k32],
            [self.k13, self.k23, -(self.k31 + self.k32 + self.ke3)],
        ])
        return A

    def eigenvalues(self) -> NDArray:
        """Eigenvalues of the rate matrix (negative real parts = decay rates)."""
        return np.linalg.eigvals(self.rate_matrix())

    def half_lives(self) -> NDArray:
        """Half-lives corresponding to each eigenvalue."""
        eigs = self.eigenvalues()
        return np.log(2) / (-np.real(eigs))

    def to_vector(self) -> NDArray:
        return np.array([
            self.k12, self.k13, self.k21, self.k23,
            self.k31, self.k32, self.ke1, self.ke2, self.ke3,
        ])

    @classmethod
    def from_vector(cls, v: NDArray) -> "LinearPKParams":
        return cls(*v)


def linear_pk_survival(t: NDArray, params: LinearPKParams,
                       P0: NDArray | None = None) -> NDArray:
    """
    Survival probability S(t) = sum of compartment probabilities.

    S(t) = 1^T @ exp(A*t) @ P0

    Parameters
    ----------
    t : array of time points
    params : LinearPKParams
    P0 : initial probability distribution (default: uniform 1/3)

    Returns
    -------
    S : array of survival probabilities
    """
    A = params.rate_matrix()
    if P0 is None:
        P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    S = np.zeros(len(t))
    for i, ti in enumerate(t):
        P_t = expm(A * ti) @ P0
        S[i] = np.sum(P_t)
    return S


def linear_pk_compartment_probs(t: NDArray, params: LinearPKParams,
                                P0: NDArray | None = None) -> NDArray:
    """
    Individual compartment probabilities P_i(t).

    Returns
    -------
    P : (len(t), 3) array
    """
    A = params.rate_matrix()
    if P0 is None:
        P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    P = np.zeros((len(t), 3))
    for i, ti in enumerate(t):
        P[i] = expm(A * ti) @ P0
    return P


def linear_pk_escape_pdf(t: NDArray, params: LinearPKParams,
                         P0: NDArray | None = None) -> NDArray:
    """
    Probability density function for escape time (= lifetime distribution).

    f(t) = -dS/dt = -1^T @ A @ exp(A*t) @ P0

    This is the PK-predicted lifetime distribution, directly comparable
    to the histogram of lifetimes from numerical scattering.
    """
    A = params.rate_matrix()
    if P0 is None:
        P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    ones = np.ones(3)
    f = np.zeros(len(t))
    for i, ti in enumerate(t):
        eAt = expm(A * ti)
        f[i] = -ones @ A @ eAt @ P0
    return f


# ---------------------------------------------------------------------------
# Estimate PK parameters from scattering data
# ---------------------------------------------------------------------------

def estimate_pk_params_from_counts(
    data: dict,
    total_time_in_compartment: NDArray | None = None,
) -> LinearPKParams:
    """
    Estimate transition rates from observed transition counts and dwell times.

    Uses maximum-likelihood for a continuous-time Markov chain:
      k_ij = N_ij / T_i
    where N_ij is the number of i→j transitions and T_i is total time in state i.
    """
    trans = data["transition_matrix"].astype(float)
    esc = data["escape_counts"].astype(float)

    if total_time_in_compartment is None:
        total_time = np.array([
            sum(data["dwell_times"][i]) for i in range(3)
        ])
    else:
        total_time = total_time_in_compartment

    # Avoid division by zero
    total_time = np.maximum(total_time, 1e-10)

    k12 = trans[0, 1] / total_time[0]
    k13 = trans[0, 2] / total_time[0]
    k21 = trans[1, 0] / total_time[1]
    k23 = trans[1, 2] / total_time[1]
    k31 = trans[2, 0] / total_time[2]
    k32 = trans[2, 1] / total_time[2]
    ke1 = esc[0] / total_time[0]
    ke2 = esc[1] / total_time[1]
    ke3 = esc[2] / total_time[2]

    return LinearPKParams(k12, k13, k21, k23, k31, k32, ke1, ke2, ke3)


def fit_pk_params_to_lifetime_distribution(
    lifetimes: NDArray,
    P0: NDArray | None = None,
    method: str = "differential_evolution",
) -> tuple[LinearPKParams, float]:
    """
    Fit PK parameters by maximising the likelihood of observed lifetimes.

    For the linear model, the lifetime PDF is a sum of three exponentials:
      f(t) = A1*alpha*exp(-alpha*t) + A2*beta*exp(-beta*t) + A3*gamma*exp(-gamma*t)

    We fit the 9 rate parameters by minimising negative log-likelihood.
    """
    if P0 is None:
        P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    lifetimes = np.asarray(lifetimes)

    def neg_log_likelihood(v):
        params = LinearPKParams.from_vector(np.abs(v))
        A = params.rate_matrix()
        ones = np.ones(3)

        nll = 0.0
        for t in lifetimes:
            eAt = expm(A * t)
            ft = -ones @ A @ eAt @ P0
            if ft <= 0:
                return 1e10
            nll -= np.log(ft)
        return nll

    if method == "differential_evolution":
        bounds = [(1e-4, 10.0)] * 9
        result = differential_evolution(neg_log_likelihood, bounds,
                                        seed=42, maxiter=200, tol=1e-6,
                                        polish=True)
    else:
        x0 = np.ones(9) * 0.1
        result = minimize(neg_log_likelihood, x0, method="Nelder-Mead",
                          options={"maxiter": 10000})

    best_params = LinearPKParams.from_vector(np.abs(result.x))
    return best_params, result.fun


# ---------------------------------------------------------------------------
# Nonlinear (Michaelis-Menten) model — for sticky chaos
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class NonlinearPKParams:
    """
    Parameters for the nonlinear (MM-type) 3-compartment model.

    Transfer rate from i to j: Vmax_ij * Pi / (Km_ij + Pi)
    Elimination rate from i:   Ve_i * Pi / (Kme_i + Pi)
    """
    Vmax_12: float
    Vmax_13: float
    Vmax_21: float
    Vmax_23: float
    Vmax_31: float
    Vmax_32: float
    Km_12: float
    Km_13: float
    Km_21: float
    Km_23: float
    Km_31: float
    Km_32: float
    Ve_1: float
    Ve_2: float
    Ve_3: float
    Kme_1: float
    Kme_2: float
    Kme_3: float

    def to_vector(self) -> NDArray:
        return np.array([
            self.Vmax_12, self.Vmax_13, self.Vmax_21, self.Vmax_23,
            self.Vmax_31, self.Vmax_32,
            self.Km_12, self.Km_13, self.Km_21, self.Km_23,
            self.Km_31, self.Km_32,
            self.Ve_1, self.Ve_2, self.Ve_3,
            self.Kme_1, self.Kme_2, self.Kme_3,
        ])

    @classmethod
    def from_vector(cls, v: NDArray) -> "NonlinearPKParams":
        return cls(*v)


def nonlinear_pk_ode(t: float, P: NDArray,
                     params: NonlinearPKParams) -> NDArray:
    """RHS of the nonlinear PK ODE."""
    P1, P2, P3 = np.maximum(P, 0)  # clamp to non-negative

    def mm(V, K, S):
        return V * S / (K + S) if S > 0 else 0.0

    dP1 = (- mm(params.Vmax_12, params.Km_12, P1)
           - mm(params.Vmax_13, params.Km_13, P1)
           - mm(params.Ve_1, params.Kme_1, P1)
           + mm(params.Vmax_21, params.Km_21, P2)
           + mm(params.Vmax_31, params.Km_31, P3))

    dP2 = (  mm(params.Vmax_12, params.Km_12, P1)
           - mm(params.Vmax_21, params.Km_21, P2)
           - mm(params.Vmax_23, params.Km_23, P2)
           - mm(params.Ve_2, params.Kme_2, P2)
           + mm(params.Vmax_32, params.Km_32, P3))

    dP3 = (  mm(params.Vmax_13, params.Km_13, P1)
           + mm(params.Vmax_23, params.Km_23, P2)
           - mm(params.Vmax_31, params.Km_31, P3)
           - mm(params.Vmax_32, params.Km_32, P3)
           - mm(params.Ve_3, params.Kme_3, P3))

    return np.array([dP1, dP2, dP3])


def nonlinear_pk_survival(t: NDArray, params: NonlinearPKParams,
                          P0: NDArray | None = None) -> NDArray:
    """Survival probability for the nonlinear model (numerical integration)."""
    if P0 is None:
        P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])

    sol = solve_ivp(
        nonlinear_pk_ode,
        [0, t[-1]],
        P0,
        args=(params,),
        t_eval=t,
        method="RK45",
        rtol=1e-8,
        atol=1e-10,
    )

    return np.sum(sol.y, axis=0)


# ---------------------------------------------------------------------------
# PK-derived summary statistics (the "pharmacokinetic" language)
# ---------------------------------------------------------------------------

def pk_summary(params: LinearPKParams) -> dict:
    """
    Compute PK-style summary statistics for the three-body system.

    Returns
    -------
    dict with keys:
        'half_lives' : three half-lives (fast, medium, slow distribution phases)
        'eigenvalues' : eigenvalues of the rate matrix
        'mean_lifetime' : expected lifetime (= mean residence time, MRT)
        'clearance' : total elimination rate (analogous to drug clearance)
        'volume_of_distribution' : effective phase-space volume per compartment
        'AUC' : area under the survival curve (= MRT)
    """
    A = params.rate_matrix()
    eigs = np.linalg.eigvals(A)
    eigs_sorted = np.sort(np.real(eigs))  # most negative first

    half_lives = np.log(2) / (-eigs_sorted)

    # Mean residence time = -1^T @ A^{-1} @ P0
    P0 = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
    try:
        A_inv = np.linalg.inv(A)
        mrt = -np.ones(3) @ A_inv @ P0
    except np.linalg.LinAlgError:
        mrt = float('inf')

    # Total clearance = sum of elimination rates weighted by steady-state fractions
    total_ke = params.ke1 + params.ke2 + params.ke3

    return {
        "half_lives": half_lives,
        "eigenvalues": eigs_sorted,
        "mean_lifetime": float(mrt),
        "clearance": float(total_ke),
        "AUC": float(mrt),  # AUC = MRT for unit dose
    }


# ---------------------------------------------------------------------------
# Phase-space flux prediction (Ginat & Perets analytic rates)
# ---------------------------------------------------------------------------

def phase_space_flux_rates(
    masses: tuple[float, float, float],
    E_total: float,
) -> LinearPKParams:
    """
    Predict transition rates from phase-space volume arguments
    (statistical mechanics approach, cf. Stone & Leigh 2019).

    For equal masses, all rates should be equal by symmetry.
    For unequal masses, the rate from configuration i depends on the
    binding energy and available phase space.

    This is a simplified version; the full Ginat & Perets calculation
    includes angular momentum dependence.
    """
    m = np.array(masses)
    M = np.sum(m)

    # For each binary pair (i,j), the available phase space scales as
    # mu_ij^{3/2} * m_k^{3/2} * |E_bin|^{5/2}
    # where mu_ij is the reduced mass and m_k is the single body mass.

    rates = np.zeros((3, 3))
    ke = np.zeros(3)

    pairs = [(0, 1), (0, 2), (1, 2)]

    for idx_from, (i, j) in enumerate(pairs):
        k = 3 - i - j
        mu_from = m[i] * m[j] / (m[i] + m[j])

        for idx_to, (p, q) in enumerate(pairs):
            if idx_from == idx_to:
                continue
            r = 3 - p - q
            mu_to = m[p] * m[q] / (m[p] + m[q])

            # Relative phase-space volume (simplified)
            flux = (mu_to ** 1.5 * m[r] ** 1.5) / (mu_from ** 1.5 * m[k] ** 1.5)
            rates[idx_from, idx_to] = flux

        # Escape probability ∝ phase space of the continuum
        ke[idx_from] = (m[k] / M) ** 1.5

    # Normalise to get rates (characteristic timescale = dynamical time)
    t_dyn = 1.0 / np.sqrt(M)  # approximate dynamical time
    total_rate = np.sum(rates) + np.sum(ke)
    rates /= total_rate / (1.0 / t_dyn)
    ke /= total_rate / (1.0 / t_dyn)

    return LinearPKParams(
        k12=rates[0, 1], k13=rates[0, 2],
        k21=rates[1, 0], k23=rates[1, 2],
        k31=rates[2, 0], k32=rates[2, 1],
        ke1=ke[0], ke2=ke[1], ke3=ke[2],
    )


if __name__ == "__main__":
    # Quick test with equal masses
    print("Phase-space flux predicted rates (equal masses):")
    params = phase_space_flux_rates((1.0, 1.0, 1.0), E_total=-0.5)
    print(f"  k12={params.k12:.4f}  k13={params.k13:.4f}")
    print(f"  k21={params.k21:.4f}  k23={params.k23:.4f}")
    print(f"  k31={params.k31:.4f}  k32={params.k32:.4f}")
    print(f"  ke1={params.ke1:.4f}  ke2={params.ke2:.4f}  ke3={params.ke3:.4f}")

    summary = pk_summary(params)
    print(f"\nPK summary:")
    print(f"  Half-lives: {summary['half_lives']}")
    print(f"  Mean lifetime (MRT): {summary['mean_lifetime']:.4f}")
    print(f"  Eigenvalues: {summary['eigenvalues']}")
