"""
Statistical and signal-processing methods for the arterial-pressure
device-validation analysis.

All functions are pure and deterministic given their inputs; the random
number generation lives in ``simulate.py`` so that the analysis layer can be
re-run reproducibly.

References for the methods implemented here:
  * Lin's concordance correlation coefficient and its decomposition
    (Lin 1989 Biometrics; Lin 2000 Biometrics).
  * Bland-Altman limits of agreement and the regression of the differences
    on the mean to detect proportional (gain) bias (Bland & Altman 1986, 1999).
  * Deming regression with jackknife confidence intervals
    (Linnet 1990 Stat Med).
  * Passing-Bablok non-parametric regression (Passing & Bablok 1983).
  * Second-order (under-/over-damped) dynamic response of a fluid-filled
    catheter-transducer system (Gardner 1981 Anesthesiology).
"""

from __future__ import annotations

import numpy as np
from scipy import stats


# ----------------------------------------------------------------------
# Lin's concordance correlation coefficient (CCC) and decomposition
# ----------------------------------------------------------------------
def lins_ccc(ref: np.ndarray, test: np.ndarray) -> dict:
    """Lin's CCC of ``test`` against the reference ``ref``.

    Returns the concordance correlation coefficient (``ccc``), Pearson's
    ``r`` (precision), the bias-correction factor ``C_b`` (accuracy), the
    scale shift ``v`` (= sd_test / sd_ref, i.e. the gain ratio) and the
    location shift ``u`` (normalised mean difference, i.e. the offset).

    The population (ddof=0) moments are used, consistent with Lin (1989).
    """
    ref = np.asarray(ref, dtype=float)
    test = np.asarray(test, dtype=float)
    n = ref.size

    m_ref, m_test = ref.mean(), test.mean()
    # population variances / covariance (ddof = 0), as in Lin (1989)
    s_ref = ref.std(ddof=0)
    s_test = test.std(ddof=0)
    cov = ((ref - m_ref) * (test - m_test)).mean()

    r = cov / (s_ref * s_test)
    ccc = 2 * cov / (s_ref ** 2 + s_test ** 2 + (m_ref - m_test) ** 2)
    c_b = ccc / r

    # decomposition of C_b (Lin 2000): C_b = 2 / (v + 1/v + u**2)
    v = s_test / s_ref                      # scale shift (gain)
    u = (m_test - m_ref) / np.sqrt(s_ref * s_test)   # location shift (offset)

    return {
        "n": n,
        "ccc": ccc,
        "r": r,
        "C_b": c_b,
        "v": v,
        "u": u,
    }


# ----------------------------------------------------------------------
# Bland-Altman analysis (mean bias + limits of agreement + proportional bias)
# ----------------------------------------------------------------------
def bland_altman(ref: np.ndarray, test: np.ndarray) -> dict:
    """Bland-Altman statistics for ``test`` vs ``ref``.

    Provides the *minimal* summary that is almost universally reported
    (mean bias and 95% limits of agreement, percentage error) **and** the
    regression of the differences on the mean, which is the part of the
    original Bland-Altman (1999) method that detects proportional
    (gain / scale) bias.
    """
    ref = np.asarray(ref, dtype=float)
    test = np.asarray(test, dtype=float)

    diff = test - ref
    mean = (test + ref) / 2.0

    bias = diff.mean()
    sd = diff.std(ddof=1)
    loa_lower = bias - 1.96 * sd
    loa_upper = bias + 1.96 * sd
    pe = 1.96 * sd / mean.mean() * 100.0     # Critchley percentage error

    # regression of the difference on the mean -> proportional-bias slope
    slope, intercept, slope_se, slope_ci, p_slope = _ols_slope_ci(mean, diff)

    return {
        "bias": bias,
        "sd_diff": sd,
        "loa_lower": loa_lower,
        "loa_upper": loa_upper,
        "pe": pe,
        "prop_slope": slope,
        "prop_intercept": intercept,
        "prop_slope_ci": slope_ci,
        "prop_slope_p": p_slope,
    }


def _ols_slope_ci(x: np.ndarray, y: np.ndarray, alpha: float = 0.05):
    """Ordinary-least-squares slope with a two-sided CI and p-value.

    Uses Student's t; implemented with numpy + scipy so the module does not
    hard-depend on statsmodels for this simple case.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size
    xbar = x.mean()
    sxx = np.sum((x - xbar) ** 2)
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    dof = n - 2
    s2 = np.sum(resid ** 2) / dof
    slope_se = np.sqrt(s2 / sxx)
    tcrit = stats.t.ppf(1 - alpha / 2, dof)
    ci = (slope - tcrit * slope_se, slope + tcrit * slope_se)
    tstat = slope / slope_se
    p = 2 * stats.t.sf(abs(tstat), dof)
    return slope, intercept, slope_se, ci, p


# ----------------------------------------------------------------------
# Deming regression (errors in both variables) with jackknife CI
# ----------------------------------------------------------------------
def deming_regression(x: np.ndarray, y: np.ndarray, lam: float = 1.0,
                      alpha: float = 0.05) -> dict:
    """Deming regression of ``y`` on ``x``.

    ``lam`` is the ratio of the error variances var(err_x)/var(err_y)
    (lam = 1 is orthogonal / equal-variance Deming). Confidence intervals
    for the slope are obtained by the jackknife (Linnet 1990).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    slope, intercept = _deming_point(x, y, lam)

    # jackknife
    n = x.size
    slopes = np.empty(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        slopes[i], _ = _deming_point(x[mask], y[mask], lam)
    ps_i = n * slope - (n - 1) * slopes          # pseudo-values
    slope_se = np.sqrt(np.sum((ps_i - ps_i.mean()) ** 2) / (n * (n - 1)))

    tcrit = stats.t.ppf(1 - alpha / 2, n - 1)
    ci = (slope - tcrit * slope_se, slope + tcrit * slope_se)

    return {"slope": slope, "intercept": intercept,
            "slope_se": slope_se, "slope_ci": ci}


def _deming_point(x: np.ndarray, y: np.ndarray, lam: float):
    mx, my = x.mean(), y.mean()
    sxx = np.sum((x - mx) ** 2)
    syy = np.sum((y - my) ** 2)
    sxy = np.sum((x - mx) * (y - my))
    # Deming slope (lam = var(err_x)/var(err_y))
    term = syy - lam * sxx
    slope = (term + np.sqrt(term ** 2 + 4 * lam * sxy ** 2)) / (2 * sxy)
    intercept = my - slope * mx
    return slope, intercept


# ----------------------------------------------------------------------
# Passing-Bablok regression (non-parametric) with CI
# ----------------------------------------------------------------------
def passing_bablok(x: np.ndarray, y: np.ndarray, alpha: float = 0.05) -> dict:
    """Passing-Bablok non-parametric regression of ``y`` on ``x``.

    Slope is the shifted median of all pairwise slopes; the confidence
    interval follows the rank-based construction of Passing & Bablok (1983).
    """
    from scipy import stats

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size

    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            if dx == 0:
                continue
            s = dy / dx
            # exclude pairs giving slope of -1 (Passing-Bablok convention)
            if s != -1:
                slopes.append(s)
    slopes = np.sort(np.asarray(slopes))
    N = slopes.size

    # offset K: number of slopes strictly below -1
    K = int(np.sum(slopes < -1))
    if N % 2 == 1:
        slope = slopes[(N + 1) // 2 - 1 + K]
    else:
        slope = np.sqrt(slopes[N // 2 - 1 + K] * slopes[N // 2 + K])

    # confidence interval
    zcrit = stats.norm.ppf(1 - alpha / 2)
    C = zcrit * np.sqrt(n * (n - 1) * (2 * n + 5) / 18.0)
    M1 = int(round((N - C) / 2.0))
    M2 = N - M1 + 1
    M1 = max(M1, 1)
    M2 = min(M2, N)
    lo = slopes[M1 - 1 + K]
    hi = slopes[M2 - 1 + K] if (M2 - 1 + K) < N else slopes[-1]

    intercept = np.median(y - slope * x)
    return {"slope": slope, "intercept": intercept, "slope_ci": (lo, hi)}


# ----------------------------------------------------------------------
# Second-order dynamic response of a fluid-filled catheter-transducer system
# ----------------------------------------------------------------------
def second_order_gain_phase(freq: np.ndarray, fn: float, zeta: float):
    """Magnitude and phase of a second-order system at frequencies ``freq``.

    H(f) = 1 / [ 1 - (f/fn)^2 + i * 2*zeta*(f/fn) ]

    Returns (magnitude, phase_radians). ``fn`` is the natural (resonant)
    frequency in Hz and ``zeta`` the damping coefficient.
    """
    freq = np.asarray(freq, dtype=float)
    ratio = freq / fn
    denom_real = 1.0 - ratio ** 2
    denom_imag = 2.0 * zeta * ratio
    denom = denom_real + 1j * denom_imag
    H = 1.0 / denom
    return np.abs(H), np.angle(H)


def synth_arterial_wave(hr: float = 75.0, map_mmHg: float = 90.0,
                        pp_mmHg: float = 40.0, n_per_beat: int = 2000,
                        n_harmonics: int = 10):
    """Synthesise one cardiac cycle of an arterial pressure waveform.

    Uses a fixed set of relative harmonic amplitudes and phases that
    reproduce the canonical arterial pressure shape (steep upstroke,
    dicrotic notch). The waveform is scaled to the requested mean arterial
    pressure (``map_mmHg``) and pulse pressure (``pp_mmHg``).

    Returns (t, pressure, freqs, amps, phases, f1) where ``f1`` is the
    fundamental (heart-rate) frequency in Hz.
    """
    f1 = hr / 60.0
    # Relative harmonic amplitudes (fraction of the fundamental) and phases
    # (radians) for a representative radial arterial pressure waveform.
    rel_amp = np.array([1.00, 0.62, 0.42, 0.28, 0.18, 0.12,
                        0.08, 0.055, 0.035, 0.022])[:n_harmonics]
    phases = np.array([0.0, -1.1, -2.0, -2.9, -3.6, -4.2,
                       -4.7, -5.1, -5.5, -5.8])[:n_harmonics]
    harmonics = np.arange(1, len(rel_amp) + 1)
    freqs = harmonics * f1

    t = np.linspace(0.0, 1.0 / f1, n_per_beat, endpoint=False)
    ac = np.zeros_like(t)
    for a, ph, k in zip(rel_amp, phases, harmonics):
        ac += a * np.cos(2 * np.pi * k * f1 * t + ph)

    # scale AC component to the requested pulse pressure
    ac_pp = ac.max() - ac.min()
    ac = ac / ac_pp * pp_mmHg
    # centre so that the mean equals MAP
    pressure = ac - ac.mean() + map_mmHg
    return t, pressure, freqs, rel_amp * (pp_mmHg / ac_pp), phases, f1


def apply_dynamic_response(freqs, amps, phases, f1, fn, zeta,
                           map_mmHg, n_per_beat=2000):
    """Pass a harmonic-decomposed waveform through a second-order system.

    ``amps``/``phases`` describe the *true* AC harmonics (from
    :func:`synth_arterial_wave`); the DC term is ``map_mmHg``. Each harmonic
    is scaled and phase-shifted by the transfer function, and the distorted
    waveform is reconstructed.
    """
    harmonics = np.arange(1, len(amps) + 1)
    hf = harmonics * f1
    mag, ph_shift = second_order_gain_phase(hf, fn, zeta)

    t = np.linspace(0.0, 1.0 / f1, n_per_beat, endpoint=False)
    ac = np.zeros_like(t)
    for a, ph, k, m, dph in zip(amps, phases, harmonics, mag, ph_shift):
        ac += (a * m) * np.cos(2 * np.pi * k * f1 * t + ph + dph)
    return t, ac + map_mmHg


def wave_features(pressure: np.ndarray) -> dict:
    """Systolic, diastolic, mean and pulse pressure of a waveform."""
    sbp = float(np.max(pressure))
    dbp = float(np.min(pressure))
    return {"sbp": sbp, "dbp": dbp,
            "map": float(np.mean(pressure)), "pp": sbp - dbp}
