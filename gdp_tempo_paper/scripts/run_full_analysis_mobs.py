"""
Full integrated analysis: M0–M4 + M_obs (observable tempo from asset composition).

Combines the original run_paper_analyses.py pipeline with the new observable-μ
approach from asset_specific_tempo.py. Produces a single comprehensive set of
results for the RIW resubmission.

All analyses:
  1. Fair evaluation (in-sample RMSE/MAPE) — M0, M1, M2, M3, M4, M_obs
  2. Out-of-sample prediction (2015–19 MAPE) — M0, M1, M2, M3, M4, M_obs
  3. Solow residual decomposition — M0 vs M2 vs M_obs
  4. Bootstrap CI on OOS MAPE difference (M0 − M_obs)
  5. RPIM (Brass relational PIM) — M0, M2, M4, M_obs vs CWON
  6. Extended OOS metrics (direction accuracy, CWON trajectory)
  7. Comprehensive figures
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_sources

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
TAB = os.path.join(ROOT, "tables")
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

DELTA_I = 0.15

ASSET_MU = {
    "N111G": 2.0, "N112G": 2.0, "N1131G": 0.5,
    "N1132G": 0.3, "N11MG": 0.8, "N117G": 3.0,
}
ASSET_COMPONENTS = ["N111G", "N112G", "N1131G", "N1132G", "N117G"]
ASSET_COMPONENTS_FALLBACK = ["N111G", "N112G", "N11MG", "N117G"]

COUNTRIES = [
    "Australia", "Austria", "Belgium", "Canada", "Chile", "China",
    "Colombia", "Costa Rica", "Czech Republic", "Denmark", "Estonia",
    "Finland", "France", "Germany", "Greece", "Hungary", "Iceland",
    "Ireland", "Israel", "Italy", "Japan", "Republic of Korea",
    "Latvia", "Lithuania", "Luxembourg", "Mexico", "Netherlands",
    "New Zealand", "Norway", "Poland", "Portugal", "Slovakia",
    "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey",
    "United Kingdom", "United States",
]
ISO3 = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN",
    "Chile": "CHL", "China": "CHN", "Colombia": "COL", "Costa Rica": "CRI",
    "Czech Republic": "CZE", "Denmark": "DNK", "Estonia": "EST",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC",
    "Hungary": "HUN", "Iceland": "ISL", "Ireland": "IRL", "Israel": "ISR",
    "Italy": "ITA", "Japan": "JPN", "Republic of Korea": "KOR", "Latvia": "LVA",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Mexico": "MEX",
    "Netherlands": "NLD", "New Zealand": "NZL", "Norway": "NOR",
    "Poland": "POL", "Portugal": "PRT", "Slovakia": "SVK",
    "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE",
    "Switzerland": "CHE", "Turkey": "TUR", "United Kingdom": "GBR",
    "United States": "USA",
}

OOS_TEST_YEARS = (2015, 2016, 2017, 2018, 2019)


# ── PIM helpers ───────────────────────────────────────────────────────────
def geom_weights(mu, S=12):
    mu = max(mu, 0.01)
    theta = mu / (1.0 + mu)
    s = np.arange(S + 1)
    w = (1 - theta) * theta ** s
    return w / w.sum()

def pim_instant(I, delta, K0):
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        K[t] = (1 - delta[t-1]) * K[t-1] + I[t-1]
    return K

def pim_lagged(I, delta, K0, mu, S=12):
    w = geom_weights(mu, S)
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        inv = sum(w[s] * I[t-1-s] for s in range(min(S+1, t)))
        K[t] = (1 - delta[t-1]) * K[t-1] + inv
    return K

def pim_lagged_tempo(I, delta, K0, mu0, mu1, years, S=12):
    t0 = years[0]
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        mu_t = max(0.01, mu0 + mu1 * (years[t] - t0))
        w = geom_weights(mu_t, S)
        inv = sum(w[s] * I[t-1-s] for s in range(min(S+1, t)))
        K[t] = (1 - delta[t-1]) * K[t-1] + inv
    return K

def pim_observable_tempo(I, delta, K0, mu_series, S=12):
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        mu_t = max(0.01, float(mu_series[t]))
        w = geom_weights(mu_t, S)
        inv = sum(w[s] * I[t-1-s] for s in range(min(S+1, t)))
        K[t] = (1 - delta[t-1]) * K[t-1] + inv
    return K

def build_intan_stock(Y, rnd_share, g=0.03):
    s = pd.Series(rnd_share).ffill().bfill()
    if s.isna().all():
        return None
    s = s.fillna(s.median()).values
    I_R = Y * s / 100.0
    K = np.zeros_like(I_R, dtype=float)
    K[0] = I_R[0] / (DELTA_I + g)
    for t in range(1, len(K)):
        K[t] = (1 - DELTA_I) * K[t-1] + I_R[t-1]
    return K


# ── Test metrics ──────────────────────────────────────────────────────────
def test_B_growth(logY, logK, logLH, alpha):
    dY = np.diff(logY); dK = np.diff(logK); dLH = np.diff(logLH)
    pred = alpha * dK + (1 - alpha) * dLH
    g = np.mean(dY - pred)
    resid = dY - (g + pred)
    return float(np.sqrt(np.mean(resid**2)) * 100)

def test_A_levels(logY, logK, logLH, alpha):
    raw_tfp = logY - alpha * logK - (1 - alpha) * logLH
    decades = np.arange(len(logY)) // 10
    tfp_smooth = np.zeros_like(raw_tfp)
    for d in np.unique(decades):
        m = decades == d
        tfp_smooth[m] = raw_tfp[m].mean()
    resid = logY - (alpha * logK + (1 - alpha) * logLH + tfp_smooth)
    return float(np.mean(np.abs(np.expm1(resid))) * 100)

def test_B_growth_intan(logY, logK_tang, logK_intan, logL, alpha, beta):
    dY = np.diff(logY); dK = np.diff(logK_tang); dI = np.diff(logK_intan)
    dL = np.diff(logL)
    w_L = 1 - alpha - beta
    pred = alpha * dK + beta * dI + w_L * dL
    g = np.mean(dY - pred)
    resid = dY - (g + pred)
    return float(np.sqrt(np.mean(resid**2)) * 100)


# ── Fitting helpers ───────────────────────────────────────────────────────
def fit_mu_const(I, delta, K0, logY, logLH, alpha):
    best = (np.inf, 0.4)
    for mu in np.linspace(0.01, 6.0, 25):
        K = pim_lagged(I, delta, K0, mu)
        K = np.where(K > 0, K, 1e-6)
        r = test_B_growth(logY, np.log(K), logLH, alpha)
        if r < best[0]:
            best = (r, mu)
    return best[1]

def fit_tempo(I, delta, K0, logY, logLH, alpha, years):
    best = (np.inf, 0.4, 0.0)
    for mu0 in np.linspace(0.05, 5.0, 10):
        for mu1 in np.linspace(-0.08, 0.12, 11):
            K = pim_lagged_tempo(I, delta, K0, mu0, mu1, years)
            K = np.where(K > 0, K, 1e-6)
            r = test_B_growth(logY, np.log(K), logLH, alpha)
            if r < best[0]:
                best = (r, mu0, mu1)
    return best[1], best[2]

def fit_beta_given_K(K_tang, K_intan, logY, logL, alpha):
    logK_tang = np.log(np.where(K_tang > 0, K_tang, 1e-6))
    logK_intan = np.log(np.where(K_intan > 0, K_intan, 1e-6))
    best = (np.inf, 0.0)
    for beta in np.linspace(0.0, 0.34, 18):
        if alpha + beta >= 0.95:
            continue
        r = test_B_growth_intan(logY, logK_tang, logK_intan, logL, alpha, beta)
        if r < best[0]:
            best = (r, beta)
    return best[1]

def demean_logratio(hat, obs):
    mask = np.isfinite(hat) & np.isfinite(obs) & (hat > 0) & (obs > 0)
    if mask.sum() < 6:
        return None
    lhat = np.log(hat[mask]); lobs = np.log(obs[mask])
    d = (lhat - lhat.mean()) - (lobs - lobs.mean())
    return float(np.sqrt(np.mean(d**2)))

def fit_joint(I, delta, K0, K_intan, logY, logL, alpha, ki, pca, lambda_w=0.3):
    logI = np.log(np.where(K_intan > 0, K_intan, 1e-6))
    best = None
    for mu in np.linspace(0.01, 6.0, 25):
        K_m = pim_lagged(I, delta, K0, mu)
        K_m = np.where(K_m > 0, K_m, 1e-6)
        logK = np.log(K_m)
        aligned_m = np.array([K_m[ii] if ii is not None else np.nan for ii in ki])
        for beta in np.linspace(0.0, 0.34, 18):
            if alpha + beta >= 0.95:
                continue
            dY = np.diff(logY); dK = np.diff(logK); dI = np.diff(logI)
            dL = np.diff(logL)
            w_L = 1 - alpha - beta
            pred = alpha * dK + beta * dI + w_L * dL
            g = np.mean(dY - pred)
            L_p = float(np.mean((dY - g - pred)**2))
            aligned = aligned_m + beta * np.array([
                K_intan[ii] if ii is not None else np.nan for ii in ki])
            rm = demean_logratio(aligned, pca)
            if rm is None:
                continue
            L_w = rm**2
            score = L_p + lambda_w * L_w
            if best is None or score < best[0]:
                best = (score, mu, beta, L_p, L_w)
    if best is None:
        return np.nan, np.nan, np.nan, np.nan
    return best[1], best[2], best[3], best[4]


# ── Data loaders ──────────────────────────────────────────────────────────
def load_rnd():
    return data_sources.load_rnd()


def load_cwon(code):
    return data_sources.load_cwon(code)


def load_oecd_gfcf():
    df = data_sources.load_oecd_gfcf()
    return df[df["iso3"].isin(ISO3.values())].copy()

def compute_observable_mu(gfcf):
    rows = []
    for iso3 in sorted(gfcf["iso3"].unique()):
        cdf = gfcf[gfcf["iso3"] == iso3]
        for year in sorted(cdf["year"].unique()):
            ydf = cdf[cdf["year"] == year]
            av = dict(zip(ydf["asset"], ydf["value"]))
            detailed = all(a in av and av[a] > 0 for a in ASSET_COMPONENTS)
            comps = ASSET_COMPONENTS if detailed else ASSET_COMPONENTS_FALLBACK
            if not all(a in av and av[a] > 0 for a in comps):
                continue
            total = sum(av[a] for a in comps)
            if total <= 0:
                continue
            mu_obs = sum((av[a] / total) * ASSET_MU[a] for a in comps)
            row = {"iso3": iso3, "year": year, "mu_obs": mu_obs}
            for a in comps:
                row[f"share_{a}"] = av[a] / total
            rows.append(row)
    return pd.DataFrame(rows)


# ── Country dataclass ─────────────────────────────────────────────────────
@dataclass
class Country:
    country: str; iso: str; years: np.ndarray; Y: np.ndarray; I: np.ndarray
    delta: np.ndarray; K0: float; Kpwt: np.ndarray; emp: np.ndarray
    avh: np.ndarray; hc: np.ndarray; labsh: np.ndarray; rnd_share: np.ndarray
    pca: np.ndarray; cwon_years: np.ndarray; mu_obs: np.ndarray

def prepare_countries(mu_df):
    pwt = data_sources.load_pwt()
    pwt = pwt[pwt["country"].isin(COUNTRIES)].sort_values(["country", "year"])
    rnd = load_rnd()
    cwon_pca = load_cwon("NW.PCA.TO")
    out = []
    for country in COUNTRIES:
        iso = ISO3[country]
        g = pwt[pwt["country"] == country].dropna(
            subset=["rgdpna", "rnna", "emp", "csh_i", "delta", "labsh"]
        ).sort_values("year").reset_index(drop=True)
        if len(g) < 30:
            continue
        r = rnd[rnd["iso3"] == iso].set_index("year")["rnd_gdp"]
        if r.empty or r.notna().sum() < 5:
            continue
        years = g["year"].values.astype(int)
        Y = g["rgdpna"].values.astype(float)
        I_v = Y * g["csh_i"].values.astype(float)
        delta = g["delta"].values.astype(float)
        Kpwt = g["rnna"].values.astype(float)
        emp = g["emp"].values.astype(float)
        avh = g["avh"].values.astype(float)
        avh = np.where(np.isnan(avh), np.nanmean(avh), avh)
        hc = g["hc"].values.astype(float)
        hc = np.where(np.isnan(hc), np.nanmean(hc), hc)
        labsh = g["labsh"].values.astype(float)
        rnd_share = np.array([r.get(int(y), np.nan) for y in years], dtype=float)
        cwon_years = np.arange(1995, 2021)
        pca = np.array([cwon_pca.get((iso, int(y)), np.nan) for y in cwon_years])
        mu_c = mu_df[mu_df["iso3"] == iso].set_index("year")["mu_obs"]
        mu_arr = pd.Series(
            [mu_c.get(int(y), np.nan) for y in years], index=years
        ).interpolate().ffill().bfill().values
        if np.isnan(mu_arr).any():
            continue
        out.append(Country(country, iso, years, Y, I_v, delta, float(Kpwt[0]),
                           Kpwt, emp, avh, hc, labsh, rnd_share, pca,
                           cwon_years, mu_arr))
    return out


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 1: Fair evaluation (in-sample) — M0, M1, M2, M3, M4, M_obs
# ══════════════════════════════════════════════════════════════════════════
def run_fair_eval(countries):
    rows = []
    for c in countries:
        alpha = 1 - float(np.clip(np.mean(c.labsh), 0.40, 0.75))
        L = c.emp * c.avh; LH = L * c.hc
        logY = np.log(c.Y); logLH = np.log(LH); logL = np.log(L)
        K_intan = build_intan_stock(c.Y, c.rnd_share)
        if K_intan is None:
            continue

        K_M0 = pim_instant(c.I, c.delta, c.K0)
        mu1 = fit_mu_const(c.I, c.delta, c.K0, logY, logLH, alpha)
        K_M1 = pim_lagged(c.I, c.delta, c.K0, mu1)
        mu0, mu1d = fit_tempo(c.I, c.delta, c.K0, logY, logLH, alpha, c.years)
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1d, c.years)
        beta_M3 = fit_beta_given_K(K_M0, K_intan, logY, logL, alpha)
        idx_map = {int(y): ii for ii, y in enumerate(c.years)}
        ki = [idx_map.get(int(y), None) for y in c.cwon_years]
        mu_j, beta_j, Lp_j, Lw_j = fit_joint(
            c.I, c.delta, c.K0, K_intan, logY, logL, alpha, ki, c.pca)
        K_M4 = pim_lagged(c.I, c.delta, c.K0, float(mu_j)) \
            if np.isfinite(mu_j) else None
        K_Mobs = pim_observable_tempo(c.I, c.delta, c.K0, c.mu_obs)

        out = {"country": c.country, "iso3": c.iso, "alpha": alpha,
               "mu_M1": mu1, "mu_M2_0": mu0, "mu_M2_1": mu1d,
               "beta_M3": beta_M3, "mu_M4": mu_j, "beta_M4": beta_j,
               "mu_obs_mean": float(np.mean(c.mu_obs)),
               "mu_obs_trend": float(np.polyfit(c.years - c.years[0], c.mu_obs, 1)[0])}

        logK_intan = np.log(np.where(K_intan > 0, K_intan, 1e-6))
        for name, Ktang, beta in [
            ("M0", K_M0, 0.0), ("M1", K_M1, 0.0), ("M2", K_M2, 0.0),
            ("M3", K_M0, beta_M3), ("M4", K_M4, beta_j), ("Mobs", K_Mobs, 0.0)
        ]:
            if Ktang is None:
                out[f"{name}_B_rmse"] = np.nan; out[f"{name}_A_mape"] = np.nan
                continue
            Kp = np.where(Ktang > 0, Ktang, 1e-6); logK = np.log(Kp)
            if beta > 0:
                out[f"{name}_B_rmse"] = test_B_growth_intan(
                    logY, logK, logK_intan, logL, alpha, beta)
            else:
                out[f"{name}_B_rmse"] = test_B_growth(logY, logK, logLH, alpha)
            out[f"{name}_A_mape"] = test_A_levels(logY, logK, logLH, alpha)
        rows.append(out)
        print(f"  [fair] {c.country:22s}  M0={out['M0_B_rmse']:.3f}  "
              f"M2={out['M2_B_rmse']:.3f}  Mobs={out['Mobs_B_rmse']:.3f}  "
              f"M4={out.get('M4_B_rmse','nan')}", flush=True)
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 2: Out-of-sample — M0, M1, M2, M3, M4, M_obs
# ══════════════════════════════════════════════════════════════════════════
def run_oos(countries):
    rows = []
    for c in countries:
        mask_train = c.years <= 2014
        mask_test = np.isin(c.years, OOS_TEST_YEARS)
        if mask_test.sum() < 3 or mask_train.sum() < 20:
            continue
        I_tr = c.I[mask_train]; d_tr = c.delta[mask_train]
        yr_tr = c.years[mask_train]; Y_tr = c.Y[mask_train]
        emp_t = c.emp[mask_train]; avh_t = c.avh[mask_train]; hc_t = c.hc[mask_train]
        L_train = emp_t * avh_t * hc_t; L_full = c.emp * c.avh * c.hc
        logY_tr = np.log(Y_tr); logLH_tr = np.log(L_train)
        logL_tr = np.log(emp_t * avh_t)
        alpha = 1 - float(np.clip(np.mean(c.labsh[mask_train]), 0.40, 0.75))
        K0 = c.K0
        K_intan_full = build_intan_stock(c.Y, c.rnd_share)
        if K_intan_full is None:
            continue
        K_intan_tr = K_intan_full[mask_train]

        mu1_tr = fit_mu_const(I_tr, d_tr, K0, logY_tr, logLH_tr, alpha)
        mu0_tr, mu1e_tr = fit_tempo(I_tr, d_tr, K0, logY_tr, logLH_tr, alpha, yr_tr)
        K_M3_tr = pim_instant(I_tr, d_tr, K0)
        beta3_tr = fit_beta_given_K(K_M3_tr, K_intan_tr, logY_tr, logL_tr, alpha)
        idx_map = {int(y): ii for ii, y in enumerate(c.years)}
        ki = [idx_map.get(int(y), None) if int(y) <= 2014 else None
              for y in c.cwon_years]
        mu4_tr, beta4_tr, _, _ = fit_joint(
            I_tr, d_tr, K0, K_intan_tr, logY_tr, logL_tr, alpha,
            ki[:len(np.arange(1995, 2015))], c.pca[c.cwon_years <= 2014])

        K_full = {
            "M0": pim_instant(c.I, c.delta, K0),
            "M1": pim_lagged(c.I, c.delta, K0, mu1_tr),
            "M2": pim_lagged_tempo(c.I, c.delta, K0, mu0_tr, mu1e_tr, c.years),
            "M3": pim_instant(c.I, c.delta, K0),
            "M4": pim_lagged(c.I, c.delta, K0, mu4_tr) if np.isfinite(mu4_tr) else None,
            "Mobs": pim_observable_tempo(c.I, c.delta, K0, c.mu_obs),
        }
        beta_by = {"M0": 0, "M1": 0, "M2": 0, "M3": beta3_tr,
                   "M4": beta4_tr if np.isfinite(beta4_tr) else 0, "Mobs": 0}

        def forecast_level(Ktang, beta):
            logK = np.log(np.where(Ktang > 0, Ktang, 1e-6))
            if beta > 0:
                logI = np.log(np.where(K_intan_full > 0, K_intan_full, 1e-6))
                logLf = np.log(c.emp * c.avh)
                w_L = 1 - alpha - beta
                raw_tfp = np.log(c.Y) - alpha * logK - beta * logI - w_L * logLf
            else:
                logLH = np.log(L_full)
                raw_tfp = np.log(c.Y) - alpha * logK - (1 - alpha) * logLH
            tdm = (c.years >= 2005) & (c.years <= 2014)
            if tdm.sum() == 0:
                return None
            tfp_proj = float(np.mean(raw_tfp[tdm]))
            if beta > 0:
                return alpha * logK + beta * logI + w_L * np.log(c.emp * c.avh) + tfp_proj
            return alpha * logK + (1 - alpha) * np.log(L_full) + tfp_proj

        out = {"country": c.country, "iso3": c.iso}
        for name, K in K_full.items():
            if K is None:
                out[f"{name}_oos_mape"] = np.nan; continue
            pred = forecast_level(K, beta_by[name])
            if pred is None:
                out[f"{name}_oos_mape"] = np.nan; continue
            resid = np.log(c.Y)[mask_test] - pred[mask_test]
            out[f"{name}_oos_mape"] = float(np.mean(np.abs(np.expm1(resid))) * 100)
        rows.append(out)
        print(f"  [oos]  {c.country:22s}  M0={out['M0_oos_mape']:.2f}  "
              f"M2={out['M2_oos_mape']:.2f}  Mobs={out['Mobs_oos_mape']:.2f}  "
              f"M4={out.get('M4_oos_mape', 'nan')}", flush=True)
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 3: Solow decomposition — M0 vs M2 vs M_obs
# ══════════════════════════════════════════════════════════════════════════
def run_solow(countries):
    rows = []
    for c in countries:
        alpha = 1 - float(np.clip(np.mean(c.labsh), 0.40, 0.75))
        LH = c.emp * c.avh * c.hc
        logY = np.log(c.Y); logLH = np.log(LH)
        K_M0 = pim_instant(c.I, c.delta, c.K0)
        mu0, mu1 = fit_tempo(c.I, c.delta, c.K0, logY, logLH, alpha, c.years)
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1, c.years)
        K_Mobs = pim_observable_tempo(c.I, c.delta, c.K0, c.mu_obs)

        def tfp(K):
            logK = np.log(np.where(K > 0, K, 1e-6))
            return logY - alpha * logK - (1 - alpha) * logLH

        tfp_M0 = tfp(K_M0); tfp_M2 = tfp(K_M2); tfp_Mobs = tfp(K_Mobs)
        for t_idx, yr in enumerate(c.years):
            rows.append({"country": c.country, "iso3": c.iso, "year": int(yr),
                         "tfp_M0": float(tfp_M0[t_idx]),
                         "tfp_M2": float(tfp_M2[t_idx]),
                         "tfp_Mobs": float(tfp_Mobs[t_idx]),
                         "alpha": alpha})
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 4: Bootstrap CI on OOS improvement (M0 − M_obs)
# ══════════════════════════════════════════════════════════════════════════
def run_bootstrap_oos(countries, n_boot=500, seed=42):
    """Country-level block bootstrap on OOS MAPE difference."""
    rng = np.random.default_rng(seed)
    # First compute actual per-country OOS MAPEs
    actual_diffs = []
    for c in countries:
        mask_train = c.years <= 2014
        mask_test = np.isin(c.years, OOS_TEST_YEARS)
        if mask_test.sum() < 3 or mask_train.sum() < 20:
            continue
        L_full = c.emp * c.avh * c.hc
        alpha = 1 - float(np.clip(np.mean(c.labsh[mask_train]), 0.40, 0.75))
        K0 = c.K0
        K_M0 = pim_instant(c.I, c.delta, K0)
        K_Mobs = pim_observable_tempo(c.I, c.delta, K0, c.mu_obs)

        def oos_mape(K):
            logK = np.log(np.where(K > 0, K, 1e-6))
            logLH = np.log(L_full)
            raw_tfp = np.log(c.Y) - alpha * logK - (1 - alpha) * logLH
            tdm = (c.years >= 2005) & (c.years <= 2014)
            if tdm.sum() == 0:
                return np.nan
            tfp_proj = float(np.mean(raw_tfp[tdm]))
            pred = alpha * logK + (1 - alpha) * logLH + tfp_proj
            resid = np.log(c.Y)[mask_test] - pred[mask_test]
            return float(np.mean(np.abs(np.expm1(resid))) * 100)

        m0 = oos_mape(K_M0); mobs = oos_mape(K_Mobs)
        if np.isfinite(m0) and np.isfinite(mobs):
            actual_diffs.append(m0 - mobs)

    actual_diffs = np.array(actual_diffs)
    n = len(actual_diffs)
    boot_medians = []
    boot_means = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_medians.append(float(np.median(actual_diffs[idx])))
        boot_means.append(float(np.mean(actual_diffs[idx])))
    return {
        "n_countries": n,
        "actual_median_diff": float(np.median(actual_diffs)),
        "actual_mean_diff": float(np.mean(actual_diffs)),
        "actual_pct_positive": float((actual_diffs > 0).mean() * 100),
        "boot_median_ci_lo": float(np.quantile(boot_medians, 0.025)),
        "boot_median_ci_hi": float(np.quantile(boot_medians, 0.975)),
        "boot_mean_ci_lo": float(np.quantile(boot_means, 0.025)),
        "boot_mean_ci_hi": float(np.quantile(boot_means, 0.975)),
    }


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 5: RPIM (Brass relational model) — M0, M2, M_obs vs CWON
# ══════════════════════════════════════════════════════════════════════════
def fit_rpim(K_pim, K_cwon, cwon_years, pim_years):
    idx_map = {int(y): i for i, y in enumerate(pim_years)}
    lp, lc = [], []
    for i, y in enumerate(cwon_years):
        j = idx_map.get(int(y))
        if j is None: continue
        kp = K_pim[j]; kc = K_cwon[i]
        if np.isfinite(kp) and np.isfinite(kc) and kp > 0 and kc > 0:
            lp.append(np.log(kp)); lc.append(np.log(kc))
    if len(lp) < 6:
        return np.nan, np.nan, np.nan
    lp = np.array(lp); lc = np.array(lc)
    X = np.column_stack([np.ones_like(lc), lc])
    params, _, _, _ = np.linalg.lstsq(X, lp, rcond=None)
    ss_res = float(np.sum((lp - X @ params)**2))
    ss_tot = float(np.sum((lp - lp.mean())**2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return float(params[0]), float(params[1]), float(r2)

def run_rpim(countries, fair):
    rows = []
    for c in countries:
        K_M0 = pim_instant(c.I, c.delta, c.K0)
        mu0 = float(fair.loc[fair["country"] == c.country, "mu_M2_0"].iloc[0]) \
            if c.country in fair["country"].values else np.nan
        mu1 = float(fair.loc[fair["country"] == c.country, "mu_M2_1"].iloc[0]) \
            if c.country in fair["country"].values else np.nan
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1, c.years) \
            if np.isfinite(mu0) else K_M0
        K_Mobs = pim_observable_tempo(c.I, c.delta, c.K0, c.mu_obs)

        rec = {"country": c.country, "iso3": c.iso}
        for label, K in [("M0", K_M0), ("M2", K_M2), ("Mobs", K_Mobs)]:
            rho1, rho2, r2 = fit_rpim(K, c.pca, c.cwon_years, c.years)
            rec[f"{label}_rho1"] = rho1
            rec[f"{label}_rho2"] = rho2
            rec[f"{label}_R2"] = r2
        rows.append(rec)
        print(f"  [rpim] {c.country:22s}  "
              f"M0_R2={rec['M0_R2']:.3f}  M2_R2={rec['M2_R2']:.3f}  "
              f"Mobs_R2={rec['Mobs_R2']:.3f}", flush=True)
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 6: Tempo artifact summary (Table 5 equivalent)
# ══════════════════════════════════════════════════════════════════════════
def summarise_tempo_artifact(solow):
    rows = []
    for country, grp in solow.groupby("country"):
        dtfp_M0 = np.diff(grp["tfp_M0"].values)
        dtfp_M2 = np.diff(grp["tfp_M2"].values)
        dtfp_Mobs = np.diff(grp["tfp_Mobs"].values)
        var_M0 = float(np.var(dtfp_M0))
        var_M2 = float(np.var(dtfp_M2))
        var_Mobs = float(np.var(dtfp_Mobs))
        art_tempo = (var_M0 - var_M2) / var_M0 if var_M0 > 0 else np.nan
        art_obs = (var_M0 - var_Mobs) / var_M0 if var_M0 > 0 else np.nan
        cum_M0 = float(grp["tfp_M0"].iloc[-1] - grp["tfp_M0"].iloc[0])
        cum_Mobs = float(grp["tfp_Mobs"].iloc[-1] - grp["tfp_Mobs"].iloc[0])
        rows.append({
            "Country": country, "ISO3": grp["iso3"].iloc[0],
            "Var(dTFP) M0 (x1e4)": round(var_M0 * 1e4, 2),
            "Var(dTFP) Mobs (x1e4)": round(var_Mobs * 1e4, 2),
            "M2 tempo share %": round(art_tempo * 100, 1) if np.isfinite(art_tempo) else "",
            "Mobs tempo share %": round(art_obs * 100, 1) if np.isfinite(art_obs) else "",
            "Cum TFP M0": round(cum_M0, 3),
            "Cum TFP Mobs": round(cum_Mobs, 3),
        })
    return pd.DataFrame(rows).sort_values("Country")


# ══════════════════════════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════════════════════════
def make_all_figures(mu_df, fair, oos, solow, rpim, countries, lang="en"):
    ISO3_REV = {v: k for k, v in ISO3.items()}

    # ── Fig 1: OOS boxplot M0–M4 + M_obs ─────────────────────────────────
    if not oos.empty:
        cols = ["M0_oos_mape", "M1_oos_mape", "M2_oos_mape",
                "M3_oos_mape", "M4_oos_mape", "Mobs_oos_mape"]
        labels_b = ["M0\n(instant)", "M1\n(const.\nlag)", "M2\n(linear\ndrift)",
                    "M3\n(+intan.)", "M4\n(joint)", "$M_{obs}$\n(asset\ncomp.)"]
        colors = ["#888888", "#4c72b0", "#dd8452", "#55a868", "#c44e52", "#9467bd"]
        fig, ax = plt.subplots(figsize=(10, 5))
        data = [oos[c].dropna().values for c in cols]
        bp = ax.boxplot(data, tick_labels=labels_b, showmeans=True, widths=0.5,
                        patch_artist=True)
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color); patch.set_alpha(0.4)
        for i, col in enumerate(cols):
            med = float(oos[col].dropna().median())
            ax.text(i+1, med+0.3, f"{med:.2f}%", ha="center", fontsize=8,
                    fontweight="bold")
        ax.set_ylabel("Out-of-sample MAPE 2015–19 (%)")
        ax.set_title("Fig. 1  OOS forecast accuracy: M0–M4 vs observable tempo ($M_{obs}$)")
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig1_full_oos_comparison_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig 2: Observable μ(t) time series ────────────────────────────────
    highlight = ["JPN", "USA", "DEU", "KOR", "GBR", "FRA"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for iso in highlight:
        cd = mu_df[mu_df["iso3"] == iso].sort_values("year")
        if cd.empty: continue
        ax.plot(cd["year"], cd["mu_obs"], "o-", ms=2, label=ISO3_REV.get(iso, iso))
    ax.set_xlabel("Year"); ax.set_ylabel("Observable $\\mu_{obs}(t)$ (years)")
    ax.set_title("Fig. 2  Observable investment gestation lag from OECD asset composition")
    ax.legend(fontsize=9); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, f"fig2_mu_obs_timeseries_{lang}.png"), dpi=180)
    plt.close()

    # ── Fig 3: In-sample ranking (M0, M2, M_obs) ─────────────────────────
    if not fair.empty:
        s = fair.sort_values("M0_B_rmse")
        y = np.arange(len(s))
        fig, ax = plt.subplots(figsize=(11, 9))
        bw = 0.25
        for i, (name, color) in enumerate([
            ("M0", "#888888"), ("M2", "#dd8452"), ("Mobs", "#9467bd")
        ]):
            ax.barh(y + (i-1)*bw, s[f"{name}_B_rmse"].values, bw,
                    label=name, color=color)
        ax.set_yticks(y); ax.set_yticklabels(s["country"].values, fontsize=8)
        ax.set_xlabel("Test B: 1-year GDP growth fit RMSE (pp)")
        ax.set_title("Fig. 3  In-sample growth-rate fit: M0 vs M2 vs $M_{obs}$")
        ax.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig3_insample_ranking_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig 4: Country-level OOS gain M0 → M_obs ─────────────────────────
    if not oos.empty:
        oc = oos.dropna(subset=["M0_oos_mape", "Mobs_oos_mape"]).copy()
        oc["gain"] = oc["M0_oos_mape"] - oc["Mobs_oos_mape"]
        oc = oc.sort_values("gain")
        fig, ax = plt.subplots(figsize=(10, 8))
        colors_bar = ["#55a868" if g > 0 else "#c44e52" for g in oc["gain"]]
        ax.barh(range(len(oc)), oc["gain"].values, color=colors_bar, alpha=0.7)
        ax.set_yticks(range(len(oc)))
        ax.set_yticklabels(oc["country"].values, fontsize=8)
        ax.set_xlabel("MAPE reduction (pp): M0 − $M_{obs}$")
        ax.set_title("Fig. 4  Country-level OOS improvement from observable tempo")
        ax.axvline(0, color="k", lw=0.8); ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig4_country_gain_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig 5: Solow decomposition panel ──────────────────────────────────
    if not solow.empty:
        hl = ["Japan", "United States", "Germany",
              "Republic of Korea", "United Kingdom", "France"]
        fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True)
        for ax, country in zip(axes.flat, hl):
            cd = solow[solow["country"] == country]
            if cd.empty: ax.set_visible(False); continue
            yrs = cd["year"].values
            for col, lbl, sty, clr in [
                ("tfp_M0", "M0 (baseline)", "-", "#4c72b0"),
                ("tfp_M2", "M2 (estimated drift)", "--", "#dd8452"),
                ("tfp_Mobs", "$M_{obs}$ (asset comp.)", "-.", "#9467bd"),
            ]:
                vals = cd[col].values - cd[col].values.mean()
                ax.plot(yrs, vals, sty, color=clr, lw=1.5, label=lbl)
            ax.fill_between(yrs,
                            cd["tfp_M0"].values - cd["tfp_M0"].values.mean(),
                            cd["tfp_Mobs"].values - cd["tfp_Mobs"].values.mean(),
                            alpha=0.15, color="#9467bd")
            ax.set_title(country, fontsize=11); ax.grid(alpha=0.3)
        for ax in axes[-1]: ax.set_xlabel("Year")
        for ax in axes[:, 0]: ax.set_ylabel("TFP (demeaned log)")
        h, l = axes[0, 0].get_legend_handles_labels()
        fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
        fig.suptitle("Fig. 5  Solow residual: M0 vs M2 vs $M_{obs}$", y=0.99)
        plt.tight_layout(rect=[0, 0.04, 1, 0.97])
        plt.savefig(os.path.join(FIG, f"fig5_solow_mobs_{lang}.png"), dpi=180,
                    bbox_inches="tight")
        plt.close()

    # ── Fig 6: RPIM R² comparison ─────────────────────────────────────────
    if not rpim.empty:
        fig, ax = plt.subplots(figsize=(10, 7))
        rp = rpim.sort_values("M0_R2")
        y = np.arange(len(rp))
        bw = 0.25
        for i, (name, color) in enumerate([
            ("M0", "#888888"), ("M2", "#dd8452"), ("Mobs", "#9467bd")
        ]):
            ax.barh(y + (i-1)*bw, rp[f"{name}_R2"].values, bw,
                    label=name, color=color, alpha=0.8)
        ax.set_yticks(y); ax.set_yticklabels(rp["country"].values, fontsize=8)
        ax.set_xlabel("$R^2$ (log K_PIM vs log CWON PCA)")
        ax.set_title("Fig. 6  Brass relational PIM: flow-stock coherence")
        ax.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig6_rpim_r2_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig 7: Asset composition panel ────────────────────────────────────
    hl_full = ["Japan", "United States", "Germany", "Republic of Korea"]
    asset_labels = {"N111G": "Dwellings", "N112G": "Other structures",
                    "N1131G": "Transport", "N1132G": "ICT", "N117G": "IP products"}
    asset_colors = {"N111G": "#e41a1c", "N112G": "#377eb8", "N1131G": "#4daf4a",
                    "N1132G": "#984ea3", "N117G": "#ff7f00"}
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    for ax_i, (country, ax) in enumerate(zip(hl_full, axes.flat)):
        iso = ISO3[country]
        cd = mu_df[mu_df["iso3"] == iso].sort_values("year")
        if cd.empty: continue
        yrs = cd["year"].values
        bottom = np.zeros(len(yrs))
        for asset in ASSET_COMPONENTS:
            col = f"share_{asset}"
            if col in cd.columns:
                vals = cd[col].fillna(0).values
                ax.fill_between(yrs, bottom, bottom+vals,
                                color=asset_colors.get(asset, "#999"), alpha=0.7,
                                label=asset_labels.get(asset, asset))
                bottom += vals
        ax.set_title(country); ax.set_ylim(0, 1.05)
        if ax_i >= 2: ax.set_xlabel("Year")
        if ax_i % 2 == 0: ax.set_ylabel("Share of total GFCF")
    h, l = axes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=5, fontsize=9, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Fig. 7  OECD GFCF composition shift by asset type", y=1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, f"fig7_asset_shares_{lang}.png"), dpi=180,
                bbox_inches="tight")
    plt.close()


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("FULL INTEGRATED ANALYSIS: M0–M4 + M_obs")
    print("=" * 60)

    print("\nLoading OECD GFCF...", flush=True)
    gfcf = load_oecd_gfcf()
    mu_df = compute_observable_mu(gfcf)
    mu_df.to_csv(os.path.join(DATA, "observable_mu.csv"), index=False)
    print(f"  {mu_df['iso3'].nunique()} countries, {len(mu_df)} obs", flush=True)

    print("\nPreparing country panel...", flush=True)
    countries = prepare_countries(mu_df)
    print(f"  {len(countries)} countries", flush=True)

    # ── 1. Fair eval ──────────────────────────────────────────────────────
    print("\n--- 1. Fair evaluation (in-sample) ---", flush=True)
    fair = run_fair_eval(countries)
    fair.to_csv(os.path.join(DATA, "full_fair_eval.csv"), index=False)
    fair_summary = {
        name: {"B_rmse_median": float(fair[f"{name}_B_rmse"].median()),
               "A_mape_median": float(fair[f"{name}_A_mape"].median())}
        for name in ("M0", "M1", "M2", "M3", "M4", "Mobs")
        if f"{name}_B_rmse" in fair.columns
    }
    with open(os.path.join(DATA, "full_fair_eval_summary.json"), "w") as fh:
        json.dump(fair_summary, fh, indent=2)

    # ── 2. OOS ────────────────────────────────────────────────────────────
    print("\n--- 2. Out-of-sample prediction ---", flush=True)
    oos = run_oos(countries)
    oos.to_csv(os.path.join(DATA, "full_oos.csv"), index=False)
    oos_summary = {
        name: float(oos[f"{name}_oos_mape"].median())
        for name in ("M0", "M1", "M2", "M3", "M4", "Mobs")
        if f"{name}_oos_mape" in oos.columns
    }
    with open(os.path.join(DATA, "full_oos_summary.json"), "w") as fh:
        json.dump(oos_summary, fh, indent=2)

    # ── 3. Solow decomposition ────────────────────────────────────────────
    print("\n--- 3. Solow residual decomposition ---", flush=True)
    solow = run_solow(countries)
    solow.to_csv(os.path.join(DATA, "full_solow.csv"), index=False)
    table6 = summarise_tempo_artifact(solow)
    table6.to_csv(os.path.join(TAB, "table6_tempo_artifact_mobs.csv"), index=False)

    # ── 4. Bootstrap CI on OOS improvement ────────────────────────────────
    print("\n--- 4. Bootstrap CI on M0 − M_obs OOS ---", flush=True)
    boot = run_bootstrap_oos(countries, n_boot=500)
    with open(os.path.join(DATA, "full_bootstrap_oos.json"), "w") as fh:
        json.dump(boot, fh, indent=2)
    print(f"  Median diff: {boot['actual_median_diff']:.3f} pp  "
          f"95% CI: [{boot['boot_median_ci_lo']:.3f}, {boot['boot_median_ci_hi']:.3f}]",
          flush=True)
    print(f"  M_obs wins in {boot['actual_pct_positive']:.0f}% of countries", flush=True)

    # ── 5. RPIM ───────────────────────────────────────────────────────────
    print("\n--- 5. Brass relational PIM ---", flush=True)
    rpim = run_rpim(countries, fair)
    rpim.to_csv(os.path.join(DATA, "full_rpim.csv"), index=False)
    rpim_summary = {
        name: {"rho2_median": float(rpim[f"{name}_rho2"].median()),
               "R2_median": float(rpim[f"{name}_R2"].median())}
        for name in ("M0", "M2", "Mobs")
    }
    with open(os.path.join(DATA, "full_rpim_summary.json"), "w") as fh:
        json.dump(rpim_summary, fh, indent=2)

    # ── 6. Figures ────────────────────────────────────────────────────────
    print("\n--- 6. Figures ---", flush=True)
    make_all_figures(mu_df, fair, oos, solow, rpim, countries, lang="en")

    # ═══════════════════════════════════════════════════════════════════════
    # COMPREHENSIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("COMPREHENSIVE RESULTS SUMMARY")
    print("=" * 60)

    print(f"\nCountries: {len(countries)}")

    print("\n┌── In-sample (Test B RMSE, median pp) ──────────────────────┐")
    for name in ("M0", "M1", "M2", "M3", "M4", "Mobs"):
        if name in fair_summary:
            print(f"  {name:5s}: {fair_summary[name]['B_rmse_median']:.4f}")

    print("\n┌── Out-of-sample (MAPE 2015-19, median %) ─────────────────┐")
    for name in ("M0", "M1", "M2", "M3", "M4", "Mobs"):
        v = oos_summary.get(name, float("nan"))
        marker = " ◄" if name == "Mobs" else ""
        print(f"  {name:5s}: {v:.3f} %{marker}")

    m0 = oos_summary.get("M0", float("nan"))
    mobs = oos_summary.get("Mobs", float("nan"))
    m2 = oos_summary.get("M2", float("nan"))
    print(f"\n  M_obs improvement over M0: {(m0-mobs)/m0*100:.1f}%  "
          f"(free params: 0 vs 0)")
    print(f"  M2 improvement over M0:    {(m0-m2)/m0*100:.1f}%  "
          f"(free params: 2 vs 0)")

    print(f"\n┌── Bootstrap CI (M0 − M_obs, median) ─────────────────────┐")
    print(f"  {boot['actual_median_diff']:.3f} pp  "
          f"95% CI: [{boot['boot_median_ci_lo']:.3f}, {boot['boot_median_ci_hi']:.3f}]")
    print(f"  M_obs wins in {boot['actual_pct_positive']:.0f}% of countries")

    print(f"\n┌── RPIM R² (median) ────────────────────────────────────────┐")
    for name in ("M0", "M2", "Mobs"):
        if name in rpim_summary:
            print(f"  {name:5s}: rho2={rpim_summary[name]['rho2_median']:.3f}  "
                  f"R²={rpim_summary[name]['R2_median']:.3f}")

    print(f"\n┌── Solow tempo artifact (median share of TFP variance) ───┐")
    m2_shares = table6["M2 tempo share %"].replace("", np.nan).astype(float).dropna()
    mobs_shares = table6["Mobs tempo share %"].replace("", np.nan).astype(float).dropna()
    print(f"  M2:   {m2_shares.median():.1f}%")
    print(f"  Mobs: {mobs_shares.median():.1f}%")

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
