"""
Asset-specific tempo analysis — observable μ(t) from OECD GFCF composition.

Constructs μ(t) from asset-specific service lives and age-efficiency profiles
rather than treating the PIM as if its only parameter of interest were a single
aggregate mean lag.

Instead of estimating μ as a free parameter (M1/M2), we CONSTRUCT it from
observable investment composition:

    μ_obs(t) = Σ_a [GFCF_a(t) / GFCF_total(t)] × μ_a

where μ_a is a literature-based gestation period per asset type.

Key test: does M_obs (zero free parameters) improve OOS prediction over M0?

Reads the frozen public inputs under source_data/:
  - pwt1001_selected.csv
  - world_bank_indicators.csv
  - oecd/gfcf_by_asset_full.csv

Writes (under gdp_tempo_paper/data/ and gdp_tempo_paper/figures/):
  - asset_composition.csv
  - observable_mu.csv
  - asset_oos.csv, asset_oos_summary.json
  - asset_fair_eval.csv, asset_fair_eval_summary.json
  - figures: fig_observable_mu_timeseries.png, fig_asset_oos_comparison.png,
             fig_mu_obs_vs_estimated.png, fig_asset_shares_panel.png
"""
from __future__ import annotations

import json
import os

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
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

DELTA_I = 0.15

# Literature-based gestation periods (years) by OECD SNA asset code.
# Sources:
#   Structures: Kydland & Prescott (1982) time-to-build = 4 quarters for structures;
#               Mayer (1960) avg construction period ~2 years
#   Transport:  BEA fixed-asset tables; typical delivery+installation ~6 months
#   ICT:        Dell/HP delivery to deployment ~3–4 months
#   Other M&E:  Industrial equipment installation ~1 year (Koeva 2000)
#   IP (R&D):   DiMasi et al. (2003) pharma R&D 3-5 yr; Hall et al. (2010)
#               general R&D lag ~3 yr to productivity impact
ASSET_MU = {
    "N111G": 2.0,    # Dwellings
    "N112G": 2.0,    # Other buildings & structures
    "N1131G": 0.5,   # Transport equipment
    "N1132G": 0.3,   # ICT equipment
    "N11MG": 0.8,    # Machinery & equipment (total, fallback)
    "N117G": 3.0,    # Intellectual property products (R&D, software, etc.)
}

# The asset categories we use for decomposition (excluding totals)
ASSET_COMPONENTS = ["N111G", "N112G", "N1131G", "N1132G", "N117G"]
# Fallback: if detailed equipment breakdown unavailable, use N11MG
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
ISO3_REV = {v: k for k, v in ISO3.items()}


# ── PIM helpers (from run_paper_analyses.py) ──────────────────────────────
def geom_weights(mu: float, S: int = 12) -> np.ndarray:
    mu = max(mu, 0.01)
    theta = mu / (1.0 + mu)
    s = np.arange(S + 1)
    w = (1 - theta) * theta ** s
    return w / w.sum()


def pim_instant(I: np.ndarray, delta: np.ndarray, K0: float) -> np.ndarray:
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        K[t] = (1 - delta[t - 1]) * K[t - 1] + I[t - 1]
    return K


def pim_lagged(I: np.ndarray, delta: np.ndarray, K0: float, mu: float,
               S: int = 12) -> np.ndarray:
    w = geom_weights(mu, S)
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        inv = 0.0
        top = min(S + 1, t)
        for s in range(top):
            inv += w[s] * I[t - 1 - s]
        K[t] = (1 - delta[t - 1]) * K[t - 1] + inv
    return K


def pim_lagged_tempo(I: np.ndarray, delta: np.ndarray, K0: float,
                     mu0: float, mu1: float, years: np.ndarray,
                     S: int = 12) -> np.ndarray:
    t0 = years[0]
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        mu_t = max(0.01, mu0 + mu1 * (years[t] - t0))
        w = geom_weights(mu_t, S)
        inv = 0.0
        top = min(S + 1, t)
        for s in range(top):
            inv += w[s] * I[t - 1 - s]
        K[t] = (1 - delta[t - 1]) * K[t - 1] + inv
    return K


def pim_observable_tempo(I: np.ndarray, delta: np.ndarray, K0: float,
                         mu_series: np.ndarray, S: int = 12) -> np.ndarray:
    """PIM with time-varying μ(t) from observable asset composition."""
    K = np.zeros_like(I, dtype=float)
    K[0] = K0
    for t in range(1, len(I)):
        mu_t = max(0.01, float(mu_series[t]))
        w = geom_weights(mu_t, S)
        inv = 0.0
        top = min(S + 1, t)
        for s in range(top):
            inv += w[s] * I[t - 1 - s]
        K[t] = (1 - delta[t - 1]) * K[t - 1] + inv
    return K


def build_intan_stock(Y: np.ndarray, rnd_share: np.ndarray,
                      g: float = 0.03) -> np.ndarray | None:
    s = pd.Series(rnd_share).ffill().bfill()
    if s.isna().all():
        return None
    s = s.fillna(s.median()).values
    I_R = Y * s / 100.0
    K = np.zeros_like(I_R, dtype=float)
    K[0] = I_R[0] / (DELTA_I + g)
    for t in range(1, len(K)):
        K[t] = (1 - DELTA_I) * K[t - 1] + I_R[t - 1]
    return K


# ── Test metrics ──────────────────────────────────────────────────────────
def test_B_growth(logY, logK, logLH, alpha):
    dY = np.diff(logY); dK = np.diff(logK); dLH = np.diff(logLH)
    pred = alpha * dK + (1 - alpha) * dLH
    g = np.mean(dY - pred)
    resid = dY - (g + pred)
    return float(np.sqrt(np.mean(resid ** 2)) * 100)


def test_A_levels(logY, logK, logLH, alpha):
    raw_tfp = logY - alpha * logK - (1 - alpha) * logLH
    decades = np.arange(len(logY)) // 10
    tfp_smooth = np.zeros_like(raw_tfp)
    for d in np.unique(decades):
        m = decades == d
        tfp_smooth[m] = raw_tfp[m].mean()
    resid = logY - (alpha * logK + (1 - alpha) * logLH + tfp_smooth)
    return float(np.mean(np.abs(np.expm1(resid))) * 100)


# ── Fitting helpers (from run_paper_analyses.py) ──────────────────────────
def fit_mu_const(I, delta, K0, logY, logLH, alpha) -> float:
    best = (np.inf, 0.4)
    for mu in np.linspace(0.01, 6.0, 25):
        K = pim_lagged(I, delta, K0, mu)
        K = np.where(K > 0, K, 1e-6)
        r = test_B_growth(logY, np.log(K), logLH, alpha)
        if r < best[0]:
            best = (r, mu)
    return best[1]


def fit_tempo(I, delta, K0, logY, logLH, alpha, years) -> tuple[float, float]:
    best = (np.inf, 0.4, 0.0)
    for mu0 in np.linspace(0.05, 5.0, 10):
        for mu1 in np.linspace(-0.08, 0.12, 11):
            K = pim_lagged_tempo(I, delta, K0, mu0, mu1, years)
            K = np.where(K > 0, K, 1e-6)
            r = test_B_growth(logY, np.log(K), logLH, alpha)
            if r < best[0]:
                best = (r, mu0, mu1)
    return best[1], best[2]


# ── OECD asset composition loader ────────────────────────────────────────
def load_oecd_gfcf() -> pd.DataFrame:
    """Load OECD GFCF by asset type, return tidy DataFrame."""
    df = data_sources.load_oecd_gfcf()
    return df[df["iso3"].isin(ISO3.values())].copy()


def compute_observable_mu(gfcf: pd.DataFrame) -> pd.DataFrame:
    """Compute observable μ(t) = Σ_a [share_a(t) × μ_a] for each country-year.

    Uses detailed asset breakdown where available; falls back to aggregate
    machinery when ICT/transport detail is missing.
    """
    rows = []
    for iso3 in sorted(gfcf["iso3"].unique()):
        cdf = gfcf[gfcf["iso3"] == iso3]
        years = sorted(cdf["year"].unique())
        for year in years:
            ydf = cdf[cdf["year"] == year]
            asset_vals = dict(zip(ydf["asset"], ydf["value"]))

            # Try detailed breakdown first
            detailed_ok = all(
                a in asset_vals and asset_vals[a] > 0
                for a in ASSET_COMPONENTS
            )
            if detailed_ok:
                components = ASSET_COMPONENTS
                mu_map = ASSET_MU
            else:
                fallback_ok = all(
                    a in asset_vals and asset_vals[a] > 0
                    for a in ASSET_COMPONENTS_FALLBACK
                )
                if not fallback_ok:
                    continue
                components = ASSET_COMPONENTS_FALLBACK
                mu_map = ASSET_MU

            total = sum(asset_vals[a] for a in components)
            if total <= 0:
                continue

            mu_obs = sum(
                (asset_vals[a] / total) * mu_map[a]
                for a in components
            )
            shares = {a: asset_vals[a] / total for a in components}
            row = {"iso3": iso3, "year": year, "mu_obs": mu_obs, "total_gfcf": total}
            for a in components:
                row[f"share_{a}"] = shares.get(a, 0.0)
            rows.append(row)

    return pd.DataFrame(rows)


# ── PWT + WB loaders (from run_paper_analyses.py) ────────────────────────
def load_rnd() -> pd.DataFrame:
    return data_sources.load_rnd()


def load_cwon(code: str) -> dict[tuple[str, int], float]:
    return data_sources.load_cwon(code)


# ── Country data structure ────────────────────────────────────────────────
from dataclasses import dataclass

@dataclass
class Country:
    country: str
    iso: str
    years: np.ndarray
    Y: np.ndarray
    I: np.ndarray
    delta: np.ndarray
    K0: float
    Kpwt: np.ndarray
    emp: np.ndarray
    avh: np.ndarray
    hc: np.ndarray
    labsh: np.ndarray
    rnd_share: np.ndarray
    pca: np.ndarray
    cwon_years: np.ndarray
    mu_obs: np.ndarray  # observable μ(t) from asset composition


def prepare_countries(mu_df: pd.DataFrame) -> list[Country]:
    pwt = data_sources.load_pwt()
    pwt = pwt[pwt["country"].isin(COUNTRIES)].sort_values(["country", "year"])
    rnd = load_rnd()
    cwon_pca = load_cwon("NW.PCA.TO")
    out: list[Country] = []
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
        I = Y * g["csh_i"].values.astype(float)
        delta = g["delta"].values.astype(float)
        Kpwt = g["rnna"].values.astype(float)
        emp = g["emp"].values.astype(float)
        avh = g["avh"].values.astype(float)
        if np.isnan(avh).any():
            avh = np.where(np.isnan(avh), np.nanmean(avh), avh)
        hc = g["hc"].values.astype(float)
        if np.isnan(hc).any():
            hc = np.where(np.isnan(hc), np.nanmean(hc), hc)
        labsh = g["labsh"].values.astype(float)
        rnd_share = np.array([r.get(int(y), np.nan) for y in years], dtype=float)
        cwon_years = np.arange(1995, 2021)
        pca = np.array([cwon_pca.get((iso, int(y)), np.nan) for y in cwon_years])

        # Map observable μ onto PWT years
        mu_c = mu_df[mu_df["iso3"] == iso].set_index("year")["mu_obs"]
        mu_obs = np.array([mu_c.get(int(y), np.nan) for y in years], dtype=float)
        # Interpolate gaps
        mu_series = pd.Series(mu_obs, index=years)
        mu_series = mu_series.interpolate(method="linear").ffill().bfill()
        mu_obs_filled = mu_series.values

        if np.isnan(mu_obs_filled).any():
            # Not enough OECD data for this country
            continue

        out.append(Country(country, iso, years, Y, I, delta, float(Kpwt[0]),
                           Kpwt, emp, avh, hc, labsh, rnd_share,
                           pca, cwon_years, mu_obs_filled))
    return out


# ── Analysis: Fair evaluation M0 / M1 / M2 / M_obs ─────────────────────
def run_fair_eval(countries: list[Country]) -> pd.DataFrame:
    rows = []
    for c in countries:
        alpha = 1 - float(np.clip(np.mean(c.labsh), 0.40, 0.75))
        L = c.emp * c.avh
        LH = L * c.hc
        logY = np.log(c.Y)
        logLH = np.log(LH)

        # M0: instant PIM
        K_M0 = pim_instant(c.I, c.delta, c.K0)
        # M1: constant estimated lag
        mu1 = fit_mu_const(c.I, c.delta, c.K0, logY, logLH, alpha)
        K_M1 = pim_lagged(c.I, c.delta, c.K0, mu1)
        # M2: linear-drift estimated lag
        mu0, mu1_drift = fit_tempo(c.I, c.delta, c.K0, logY, logLH, alpha, c.years)
        K_M2 = pim_lagged_tempo(c.I, c.delta, c.K0, mu0, mu1_drift, c.years)
        # M_obs: observable μ(t) from OECD asset composition (zero free params)
        K_Mobs = pim_observable_tempo(c.I, c.delta, c.K0, c.mu_obs)

        out = {
            "country": c.country, "iso3": c.iso, "alpha": alpha,
            "mu_M1": mu1, "mu_M2_0": mu0, "mu_M2_1": mu1_drift,
            "mu_obs_mean": float(np.mean(c.mu_obs)),
            "mu_obs_std": float(np.std(c.mu_obs)),
            "mu_obs_trend": float(np.polyfit(c.years - c.years[0], c.mu_obs, 1)[0]),
        }

        for name, K in [("M0", K_M0), ("M1", K_M1), ("M2", K_M2), ("Mobs", K_Mobs)]:
            Kp = np.where(K > 0, K, 1e-6)
            logK = np.log(Kp)
            out[f"{name}_B_rmse"] = test_B_growth(logY, logK, logLH, alpha)
            out[f"{name}_A_mape"] = test_A_levels(logY, logK, logLH, alpha)

        rows.append(out)
        print(f"  [fair] {c.country:22s}  "
              f"M0={out['M0_B_rmse']:.3f}  M1={out['M1_B_rmse']:.3f}  "
              f"M2={out['M2_B_rmse']:.3f}  Mobs={out['Mobs_B_rmse']:.3f}  "
              f"(mu_obs_mean={out['mu_obs_mean']:.2f})", flush=True)
    return pd.DataFrame(rows)


# ── Analysis: Out-of-sample comparison ────────────────────────────────────
OOS_TEST_YEARS = (2015, 2016, 2017, 2018, 2019)


def run_oos(countries: list[Country]) -> pd.DataFrame:
    rows = []
    for c in countries:
        mask_train = c.years <= 2014
        mask_test = np.isin(c.years, OOS_TEST_YEARS)
        if mask_test.sum() < 3 or mask_train.sum() < 20:
            continue

        I_train = c.I[mask_train]
        delta_train = c.delta[mask_train]
        years_train = c.years[mask_train]
        Y_train = c.Y[mask_train]
        emp_t = c.emp[mask_train]; avh_t = c.avh[mask_train]; hc_t = c.hc[mask_train]
        L_train = emp_t * avh_t * hc_t
        L_full = c.emp * c.avh * c.hc
        logY_train = np.log(Y_train); logLH_train = np.log(L_train)
        alpha = 1 - float(np.clip(np.mean(c.labsh[mask_train]), 0.40, 0.75))
        K0 = c.K0

        # Fit M1, M2 on training data only
        mu1_tr = fit_mu_const(I_train, delta_train, K0, logY_train, logLH_train, alpha)
        mu0_tr, mu1e_tr = fit_tempo(I_train, delta_train, K0, logY_train,
                                    logLH_train, alpha, years_train)

        # M_obs uses NO training data — μ(t) is fully observable
        K_full = {
            "M0": pim_instant(c.I, c.delta, K0),
            "M1": pim_lagged(c.I, c.delta, K0, mu1_tr),
            "M2": pim_lagged_tempo(c.I, c.delta, K0, mu0_tr, mu1e_tr, c.years),
            "Mobs": pim_observable_tempo(c.I, c.delta, K0, c.mu_obs),
        }

        def forecast_level(Ktang_full):
            logK = np.log(np.where(Ktang_full > 0, Ktang_full, 1e-6))
            logLH = np.log(L_full)
            raw_tfp = np.log(c.Y) - alpha * logK - (1 - alpha) * logLH
            train_dec_mask = (c.years >= 2005) & (c.years <= 2014)
            if train_dec_mask.sum() == 0:
                return None
            tfp_proj = float(np.mean(raw_tfp[train_dec_mask]))
            return alpha * logK + (1 - alpha) * logLH + tfp_proj

        out = {"country": c.country, "iso3": c.iso}
        for name, K in K_full.items():
            pred_logY = forecast_level(K)
            if pred_logY is None:
                out[f"{name}_oos_mape"] = np.nan
                continue
            resid = np.log(c.Y)[mask_test] - pred_logY[mask_test]
            out[f"{name}_oos_mape"] = float(np.mean(np.abs(np.expm1(resid))) * 100)

        rows.append(out)
        print(f"  [oos]  {c.country:22s}  "
              f"M0={out['M0_oos_mape']:.2f}  M1={out['M1_oos_mape']:.2f}  "
              f"M2={out['M2_oos_mape']:.2f}  Mobs={out['Mobs_oos_mape']:.2f}",
              flush=True)
    return pd.DataFrame(rows)


# ── Robustness: sensitivity of M_obs to μ_a assignments ──────────────────
def run_mu_sensitivity(countries: list[Country],
                       gfcf: pd.DataFrame,
                       mu_scales: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
                       ) -> pd.DataFrame:
    """Scale individual μ_a by a factor and re-evaluate OOS.

    Tests whether the result is robust to ±50% uncertainty in assigned lags.
    """
    rows = []
    for scale in mu_scales:
        scaled_mu = {k: v * scale for k, v in ASSET_MU.items()}

        # Recompute observable μ with scaled lags
        mu_rows = []
        for iso3 in sorted(gfcf["iso3"].unique()):
            cdf = gfcf[gfcf["iso3"] == iso3]
            for year in sorted(cdf["year"].unique()):
                ydf = cdf[cdf["year"] == year]
                asset_vals = dict(zip(ydf["asset"], ydf["value"]))
                detailed_ok = all(
                    a in asset_vals and asset_vals[a] > 0
                    for a in ASSET_COMPONENTS
                )
                if detailed_ok:
                    components = ASSET_COMPONENTS
                else:
                    fallback_ok = all(
                        a in asset_vals and asset_vals[a] > 0
                        for a in ASSET_COMPONENTS_FALLBACK
                    )
                    if not fallback_ok:
                        continue
                    components = ASSET_COMPONENTS_FALLBACK
                total = sum(asset_vals[a] for a in components)
                if total <= 0:
                    continue
                mu_obs = sum((asset_vals[a] / total) * scaled_mu[a]
                             for a in components)
                mu_rows.append({"iso3": iso3, "year": year, "mu_obs": mu_obs})
        mu_scaled = pd.DataFrame(mu_rows)

        oos_mapes = []
        for c in countries:
            mask_train = c.years <= 2014
            mask_test = np.isin(c.years, OOS_TEST_YEARS)
            if mask_test.sum() < 3 or mask_train.sum() < 20:
                continue
            # Map scaled μ
            mu_c = mu_scaled[mu_scaled["iso3"] == c.iso].set_index("year")["mu_obs"]
            mu_arr = np.array([mu_c.get(int(y), np.nan) for y in c.years])
            mu_s = pd.Series(mu_arr, index=c.years).interpolate().ffill().bfill()
            if mu_s.isna().any():
                continue

            K0 = c.K0
            K = pim_observable_tempo(c.I, c.delta, K0, mu_s.values)
            L_full = c.emp * c.avh * c.hc
            alpha = 1 - float(np.clip(np.mean(c.labsh[mask_train]), 0.40, 0.75))
            logK = np.log(np.where(K > 0, K, 1e-6))
            logLH = np.log(L_full)
            raw_tfp = np.log(c.Y) - alpha * logK - (1 - alpha) * logLH
            train_dec_mask = (c.years >= 2005) & (c.years <= 2014)
            if train_dec_mask.sum() == 0:
                continue
            tfp_proj = float(np.mean(raw_tfp[train_dec_mask]))
            pred_logY = alpha * logK + (1 - alpha) * logLH + tfp_proj
            resid = np.log(c.Y)[mask_test] - pred_logY[mask_test]
            mape = float(np.mean(np.abs(np.expm1(resid))) * 100)
            oos_mapes.append(mape)

        if oos_mapes:
            rows.append({
                "scale": scale,
                "median_oos_mape": float(np.median(oos_mapes)),
                "mean_oos_mape": float(np.mean(oos_mapes)),
                "n_countries": len(oos_mapes),
            })
            print(f"  [sens] scale={scale:.2f}  "
                  f"median_mape={rows[-1]['median_oos_mape']:.3f}  "
                  f"n={len(oos_mapes)}", flush=True)
    return pd.DataFrame(rows)


# ── Figures ───────────────────────────────────────────────────────────────
def make_figures(mu_df: pd.DataFrame, fair: pd.DataFrame, oos: pd.DataFrame,
                 countries: list[Country], sensitivity: pd.DataFrame,
                 lang: str = "en"):
    # ── Fig A: Observable μ(t) time series for selected countries ─────────
    highlight = ["JPN", "USA", "DEU", "KOR", "GBR", "FRA"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for iso in highlight:
        cdata = mu_df[mu_df["iso3"] == iso].sort_values("year")
        if cdata.empty:
            continue
        label = ISO3_REV.get(iso, iso)
        ax.plot(cdata["year"], cdata["mu_obs"], "o-", ms=2, label=label)
    ax.set_xlabel("Year")
    ax.set_ylabel("Observable $\\mu_{obs}(t)$ (years)")
    ax.set_title("Observable investment gestation lag from OECD asset composition")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, f"fig_observable_mu_timeseries_{lang}.png"), dpi=180)
    plt.close()

    # ── Fig B: OOS comparison boxplot M0 / M1 / M2 / M_obs ──────────────
    if not oos.empty:
        cols = ["M0_oos_mape", "M1_oos_mape", "M2_oos_mape", "Mobs_oos_mape"]
        labels = ["M0\n(instant)", "M1\n(const. lag)", "M2\n(linear drift)",
                  "$M_{obs}$\n(asset comp.)"]
        fig, ax = plt.subplots(figsize=(8, 5))
        data = [oos[col].dropna().values for col in cols]
        bp = ax.boxplot(data, tick_labels=labels, showmeans=True, widths=0.5,
                        patch_artist=True)
        colors = ["#888888", "#4c72b0", "#dd8452", "#55a868"]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.4)
        ax.set_ylabel("Out-of-sample MAPE 2015–19 (%)")
        ax.set_title("OOS forecast accuracy: estimated vs observable tempo")
        ax.grid(axis="y", alpha=0.3)
        # Add median annotations
        for i, col in enumerate(cols):
            med = float(oos[col].dropna().median())
            ax.text(i + 1, med + 0.2, f"{med:.2f}%", ha="center", fontsize=9,
                    fontweight="bold")
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig_asset_oos_comparison_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig C: μ_obs(mean) vs estimated μ_M1 scatter ─────────────────────
    if not fair.empty:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.scatter(fair["mu_obs_mean"], fair["mu_M1"], s=30, alpha=0.7, c="#4c72b0")
        for _, row in fair.iterrows():
            ax.annotate(row["iso3"], (row["mu_obs_mean"], row["mu_M1"]),
                        fontsize=6, alpha=0.7)
        lim = max(fair["mu_obs_mean"].max(), fair["mu_M1"].max()) * 1.1
        ax.plot([0, lim], [0, lim], "k--", lw=0.8, alpha=0.5, label="45° line")
        ax.set_xlabel("Observable $\\mu_{obs}$ (OECD composition mean)")
        ax.set_ylabel("Estimated $\\hat{\\mu}_{M1}$ (fitted constant lag)")
        ax.set_title("Observable vs estimated gestation lag")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig_mu_obs_vs_estimated_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig D: Asset composition shares panel (selected countries) ────────
    highlight_full = ["Japan", "United States", "Germany", "Republic of Korea"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    asset_labels = {
        "N111G": "Dwellings", "N112G": "Other structures",
        "N1131G": "Transport", "N1132G": "ICT equipment",
        "N117G": "IP products",
    }
    asset_colors = {
        "N111G": "#e41a1c", "N112G": "#377eb8",
        "N1131G": "#4daf4a", "N1132G": "#984ea3",
        "N117G": "#ff7f00",
    }
    for ax_i, (country, ax) in enumerate(zip(highlight_full, axes.flat)):
        iso = ISO3[country]
        cdata = mu_df[mu_df["iso3"] == iso].sort_values("year")
        if cdata.empty:
            continue
        years = cdata["year"].values
        bottom = np.zeros(len(years))
        for asset in ASSET_COMPONENTS:
            col = f"share_{asset}"
            if col in cdata.columns:
                vals = cdata[col].fillna(0).values
                ax.fill_between(years, bottom, bottom + vals,
                                color=asset_colors.get(asset, "#999"),
                                alpha=0.7,
                                label=asset_labels.get(asset, asset))
                bottom += vals
        ax.set_title(country)
        ax.set_ylim(0, 1.05)
        if ax_i >= 2:
            ax.set_xlabel("Year")
        if ax_i % 2 == 0:
            ax.set_ylabel("Share of total GFCF")
    handles, lbls = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center", ncol=5, fontsize=9,
               bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Investment composition shift: OECD GFCF by asset type", y=1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, f"fig_asset_shares_panel_{lang}.png"),
                dpi=180, bbox_inches="tight")
    plt.close()

    # ── Fig E: Sensitivity of M_obs OOS to μ_a scaling ────────────────────
    if not sensitivity.empty:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(sensitivity["scale"], sensitivity["median_oos_mape"],
                "o-", color="#55a868", lw=2, ms=8, label="$M_{obs}$ (median OOS MAPE)")
        # Add M0 baseline
        if not oos.empty:
            m0_med = float(oos["M0_oos_mape"].dropna().median())
            ax.axhline(m0_med, color="#888888", ls="--", lw=1.5,
                       label=f"M0 baseline ({m0_med:.2f}%)")
            m2_med = float(oos["M2_oos_mape"].dropna().median())
            ax.axhline(m2_med, color="#dd8452", ls="--", lw=1.5,
                       label=f"M2 baseline ({m2_med:.2f}%)")
        ax.set_xlabel("Scale factor on literature $\\mu_a$ values")
        ax.set_ylabel("Median OOS MAPE 2015–19 (%)")
        ax.set_title("Robustness: $M_{obs}$ performance under $\\mu_a$ uncertainty")
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig_mu_sensitivity_{lang}.png"), dpi=180)
        plt.close()

    # ── Fig F: Country-level M_obs gain over M0 ──────────────────────────
    if not oos.empty and "Mobs_oos_mape" in oos.columns:
        oos_c = oos.dropna(subset=["M0_oos_mape", "Mobs_oos_mape"]).copy()
        oos_c["gain"] = oos_c["M0_oos_mape"] - oos_c["Mobs_oos_mape"]
        oos_c = oos_c.sort_values("gain")
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = ["#55a868" if g > 0 else "#c44e52" for g in oos_c["gain"]]
        ax.barh(range(len(oos_c)), oos_c["gain"].values, color=colors, alpha=0.7)
        ax.set_yticks(range(len(oos_c)))
        ax.set_yticklabels(oos_c["country"].values, fontsize=8)
        ax.set_xlabel("MAPE reduction (pp): M0 − $M_{obs}$")
        ax.set_title("Country-level OOS improvement from observable tempo correction")
        ax.axvline(0, color="k", lw=0.8)
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(FIG, f"fig_country_gain_{lang}.png"), dpi=180)
        plt.close()


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print("Loading OECD GFCF by asset type...", flush=True)
    gfcf = load_oecd_gfcf()
    print(f"  {len(gfcf)} records, {gfcf['iso3'].nunique()} countries", flush=True)

    print("\nComputing observable μ(t)...", flush=True)
    mu_df = compute_observable_mu(gfcf)
    print(f"  {len(mu_df)} country-year observations", flush=True)
    mu_df.to_csv(os.path.join(DATA, "observable_mu.csv"), index=False)
    gfcf.to_csv(os.path.join(DATA, "asset_composition.csv"), index=False)

    # Summary statistics
    print("\nObservable μ summary by country:", flush=True)
    for iso in sorted(mu_df["iso3"].unique()):
        cd = mu_df[mu_df["iso3"] == iso]["mu_obs"]
        if len(cd) > 5:
            trend = np.polyfit(range(len(cd)), cd.values, 1)[0]
            print(f"  {iso}: mean={cd.mean():.3f}  std={cd.std():.3f}  "
                  f"trend={trend:.4f}/yr  n={len(cd)}", flush=True)

    print("\nPreparing country panel...", flush=True)
    countries = prepare_countries(mu_df)
    print(f"  {len(countries)} countries with complete PWT + OECD coverage", flush=True)

    print("\n--- Fair evaluation: M0 / M1 / M2 / M_obs ---", flush=True)
    fair = run_fair_eval(countries)
    fair.to_csv(os.path.join(DATA, "asset_fair_eval.csv"), index=False)
    fair_summary = {
        name: {
            "B_rmse_median": float(fair[f"{name}_B_rmse"].median()),
            "A_mape_median": float(fair[f"{name}_A_mape"].median()),
        } for name in ("M0", "M1", "M2", "Mobs")
    }
    with open(os.path.join(DATA, "asset_fair_eval_summary.json"), "w") as fh:
        json.dump(fair_summary, fh, indent=2)

    print("\n--- Out-of-sample: M0 / M1 / M2 / M_obs ---", flush=True)
    oos = run_oos(countries)
    oos.to_csv(os.path.join(DATA, "asset_oos.csv"), index=False)
    oos_summary = {
        name: float(oos[f"{name}_oos_mape"].median())
        for name in ("M0", "M1", "M2", "Mobs")
        if f"{name}_oos_mape" in oos.columns
    }
    with open(os.path.join(DATA, "asset_oos_summary.json"), "w") as fh:
        json.dump(oos_summary, fh, indent=2)

    print("\n--- Robustness: μ_a scaling sensitivity ---", flush=True)
    sensitivity = run_mu_sensitivity(countries, gfcf)
    sensitivity.to_csv(os.path.join(DATA, "mu_sensitivity.csv"), index=False)

    print("\n--- Figures ---", flush=True)
    make_figures(mu_df, fair, oos, countries, sensitivity, lang="en")

    # ── Print summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 60, flush=True)
    print("ASSET-SPECIFIC TEMPO ANALYSIS — RESULTS SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"\nCountries analyzed: {len(countries)}", flush=True)
    print(f"\nIn-sample (Test B RMSE, median):", flush=True)
    for name in ("M0", "M1", "M2", "Mobs"):
        med = fair_summary[name]["B_rmse_median"]
        print(f"  {name:5s}: {med:.4f}", flush=True)
    print(f"\nOut-of-sample (MAPE 2015-19, median):", flush=True)
    for name in ("M0", "M1", "M2", "Mobs"):
        med = oos_summary.get(name, float("nan"))
        print(f"  {name:5s}: {med:.4f} %", flush=True)

    m0_oos = oos_summary.get("M0", float("nan"))
    mobs_oos = oos_summary.get("Mobs", float("nan"))
    improvement = (m0_oos - mobs_oos) / m0_oos * 100
    print(f"\nM_obs relative improvement over M0: {improvement:.1f} %", flush=True)
    print(f"  (M0={m0_oos:.3f}% → M_obs={mobs_oos:.3f}%)", flush=True)

    # Count how many countries M_obs beats M0
    if "Mobs_oos_mape" in oos.columns and "M0_oos_mape" in oos.columns:
        wins = (oos["Mobs_oos_mape"] < oos["M0_oos_mape"]).sum()
        total = oos[["M0_oos_mape", "Mobs_oos_mape"]].dropna().shape[0]
        print(f"\nM_obs beats M0 in {wins}/{total} countries "
              f"({wins/total*100:.0f}%)", flush=True)

    if not sensitivity.empty:
        print(f"\nSensitivity (median OOS MAPE under different μ_a scales):", flush=True)
        for _, row in sensitivity.iterrows():
            print(f"  scale={row['scale']:.2f}: {row['median_oos_mape']:.3f}%",
                  flush=True)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
