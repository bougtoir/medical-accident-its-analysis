"""
Reproducible tempo model selection for the healthcare-capital lag analysis.

Replaces the previously hard-coded AIC/BIC/LOOCV summary values in
analyze_healthcare_economic_effect.py with statistics computed directly from
World Bank public data (39 OECD + BRIC countries, 2000-2019 where available).

Models (health production function LifeExp(t) = a + b*log H(t) + c*log GDPpc(t)):
  M0  flow only       H(t) = E(t)                              k = 3 params
  M1  constant lag    geometric PIM, mean lag mu (grid)        k = 4 params
  M2  tempo lag       mu(t) = mu0 + mu1*(t - t0) (grid)        k = 5 params

Model-selection statistics per country:
  level RMSE, change RMSE
  AIC = n*ln(RSS/n) + 2k
  BIC = n*ln(RSS/n) + k*ln(n)
  LOOCV RMSE via the exact linear leave-one-out formula
    resid_LOO_i = resid_i / (1 - h_ii),  conditioned on the full-sample-optimal mu

Outputs data/tempo_model_selection.json consumed by the manuscript builder.
"""
import os
import json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)

# World Bank raw indicator cache. Portable resolution order:
#   1. $WB_DIR environment variable (if set)
#   2. repository-relative data/wb (committed subset; default)
# A clean clone ships the committed subset in data/wb so the analysis is
# fully reproducible offline. To refresh from the live API, run
# scripts/fetch_wb_health.py (which writes into data/wb).
WB_DIR = os.environ.get("WB_DIR", os.path.join(DATA, "wb"))

COUNTRIES_ISO = [
    ("Australia", "AUS"), ("Austria", "AUT"), ("Belgium", "BEL"),
    ("Canada", "CAN"), ("Chile", "CHL"), ("China", "CHN"),
    ("Colombia", "COL"), ("Costa Rica", "CRI"),
    ("Czech Republic", "CZE"), ("Denmark", "DNK"), ("Estonia", "EST"),
    ("Finland", "FIN"), ("France", "FRA"), ("Germany", "DEU"),
    ("Greece", "GRC"), ("Hungary", "HUN"), ("Iceland", "ISL"),
    ("Ireland", "IRL"), ("Israel", "ISR"), ("Italy", "ITA"),
    ("Japan", "JPN"), ("Korea", "KOR"), ("Latvia", "LVA"),
    ("Lithuania", "LTU"), ("Luxembourg", "LUX"), ("Mexico", "MEX"),
    ("Netherlands", "NLD"), ("New Zealand", "NZL"), ("Norway", "NOR"),
    ("Poland", "POL"), ("Portugal", "PRT"), ("Slovakia", "SVK"),
    ("Slovenia", "SVN"), ("Spain", "ESP"), ("Sweden", "SWE"),
    ("Switzerland", "CHE"), ("Turkey", "TUR"),
    ("United Kingdom", "GBR"), ("United States", "USA"),
]

DELTA_H = 0.10
PERIOD = (2000, 2019)
SEED = 20260718

# Parameter counts (regression coefficients + lag-mean parameters)
K = {"M0": 3, "M1": 4, "M2": 5}


def load_wb(code):
    p = os.path.join(WB_DIR, f"{code}.json")
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"World Bank data file not found: {p}. Run "
            "'python scripts/fetch_wb_health.py' to download the required "
            "indicators (or set the WB_DIR environment variable to an "
            "existing cache)."
        )
    with open(p) as fh:
        rows = json.load(fh)
    df = pd.DataFrame([
        {"iso3": r["countryiso3code"], "year": int(r["date"]), "value": r["value"]}
        for r in rows if r.get("value") is not None
    ])
    return df.set_index(["iso3", "year"])["value"]


def geom_weights(mu, M=40):
    if mu <= 0:
        w = np.zeros(M)
        w[0] = 1.0
        return w
    q = mu / (1.0 + mu)
    s = np.arange(M)
    w = (1.0 - q) * (q ** s)
    w /= w.sum()
    return w


def stock_constant_mu(E, mu, delta=DELTA_H):
    T = len(E)
    E_eff = np.zeros(T)
    for t in range(T):
        w = geom_weights(mu, M=min(40, t + 1))
        for s in range(len(w)):
            E_eff[t] += w[s] * E[t - s]
    H = np.zeros(T)
    H[0] = E_eff[0] / (delta + 0.02)
    for t in range(1, T):
        H[t] = (1 - delta) * H[t - 1] + E_eff[t - 1]
    return H


def stock_tempo_mu(E, mu0, mu1, delta=DELTA_H):
    T = len(E)
    E_eff = np.zeros(T)
    for t in range(T):
        mu_t = max(0.01, mu0 + mu1 * t)
        w = geom_weights(mu_t, M=min(40, t + 1))
        for s in range(len(w)):
            E_eff[t] += w[s] * E[t - s]
    H = np.zeros(T)
    if E_eff[0] <= 0:
        return None
    H[0] = E_eff[0] / (delta + 0.02)
    for t in range(1, T):
        H[t] = (1 - delta) * H[t - 1] + E_eff[t - 1]
    if np.any(H <= 0):
        return None
    return H


def ols_fit(X, y):
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    resid = y - pred
    return coef, pred, resid


def rmse(resid):
    return float(np.sqrt(np.mean(resid ** 2)))


def change_rmse(y, pred):
    return float(np.sqrt(np.mean((np.diff(y) - np.diff(pred)) ** 2)))


def aic_bic(resid, k):
    n = len(resid)
    rss = float(np.sum(resid ** 2))
    rss = max(rss, 1e-9)
    ll_term = n * np.log(rss / n)
    return ll_term + 2 * k, ll_term + k * np.log(n)


def loocv_rmse(X, y):
    """Exact leave-one-out RMSE for a linear model via the hat matrix."""
    XtX_inv = np.linalg.pinv(X.T @ X)
    H = X @ XtX_inv @ X.T
    h = np.clip(np.diag(H), 0.0, 1.0 - 1e-8)
    coef, pred, resid = ols_fit(X, y)
    loo = resid / (1.0 - h)
    return float(np.sqrt(np.mean(loo ** 2)))


def fit_M0(E, gdp_pc, y):
    X = np.column_stack([np.ones(len(y)), np.log(E), np.log(gdp_pc)])
    _, pred, resid = ols_fit(X, y)
    return {"X": X, "pred": pred, "resid": resid}


def fit_M1(E, gdp_pc, y):
    best = None
    for mu in np.arange(0.0, 20.0, 1.0):
        H = stock_constant_mu(E, mu)
        if np.any(H <= 0):
            continue
        X = np.column_stack([np.ones(len(y)), np.log(H), np.log(gdp_pc)])
        _, pred, resid = ols_fit(X, y)
        r = rmse(resid)
        if best is None or r < best["rmse"]:
            best = {"rmse": r, "mu": float(mu), "X": X, "pred": pred, "resid": resid}
    return best


def fit_M2(E, gdp_pc, y):
    best = None
    for mu0 in np.arange(0.0, 20.0, 2.0):
        for mu1 in np.arange(-0.10, 0.35, 0.05):
            H = stock_tempo_mu(E, mu0, mu1)
            if H is None:
                continue
            X = np.column_stack([np.ones(len(y)), np.log(H), np.log(gdp_pc)])
            _, pred, resid = ols_fit(X, y)
            r = rmse(resid)
            if best is None or r < best["rmse"]:
                best = {"rmse": r, "mu0": float(mu0), "mu1": float(mu1),
                        "X": X, "pred": pred, "resid": resid}
    return best


def main():
    np.random.seed(SEED)
    print("Loading WB indicators...", flush=True)
    E_share = load_wb("SH.XPD.CHEX.GD.ZS")
    E_pc = load_wb("SH.XPD.CHEX.PP.CD")
    LE = load_wb("SP.DYN.LE00.IN")

    rows = []
    for name, iso in COUNTRIES_ISO:
        try:
            e_sh = E_share.loc[iso].sort_index()
            e_pc = E_pc.loc[iso].sort_index()
            le = LE.loc[iso].sort_index()
        except KeyError:
            continue
        common = e_sh.index.intersection(e_pc.index).intersection(le.index)
        common = [yr for yr in common if PERIOD[0] <= yr <= PERIOD[1]]
        common = pd.Index(sorted(common))
        if len(common) < 15:
            continue
        gdp_pc = e_pc.loc[common].values / (e_sh.loc[common].values / 100.0)
        E = e_pc.loc[common].values
        y = le.loc[common].values
        if np.any(E <= 0) or np.any(gdp_pc <= 0) or np.any(y <= 0):
            continue

        m0 = fit_M0(E, gdp_pc, y)
        m1 = fit_M1(E, gdp_pc, y)
        m2 = fit_M2(E, gdp_pc, y)
        if m1 is None or m2 is None:
            continue

        rec = {"country": name, "iso3": iso, "n": len(y),
               "mu_const": m1["mu"], "mu_H0": m2["mu0"], "mu_H1": m2["mu1"]}
        for tag, m in [("M0", m0), ("M1", m1), ("M2", m2)]:
            aic, bic = aic_bic(m["resid"], K[tag])
            rec[f"{tag}_level_rmse"] = rmse(m["resid"])
            rec[f"{tag}_change_rmse"] = change_rmse(y, m["pred"])
            rec[f"{tag}_aic"] = aic
            rec[f"{tag}_bic"] = bic
            rec[f"{tag}_loocv"] = loocv_rmse(m["X"], y)
        rows.append(rec)
        print(f"  {name:18s} mu1={m2['mu1']:+.2f} "
              f"RMSE M0={rec['M0_level_rmse']:.3f} M1={rec['M1_level_rmse']:.3f} "
              f"M2={rec['M2_level_rmse']:.3f}", flush=True)

    rdf = pd.DataFrame(rows).sort_values("country").reset_index(drop=True)
    rdf.to_csv(os.path.join(DATA, "tempo_model_selection_bycountry.csv"), index=False)

    def med(col):
        return float(rdf[col].median())

    def share_better(a, b):
        # fraction of countries where model a has LOWER (better) value than b
        return float((rdf[a] < rdf[b]).mean())

    summary = {
        "n_countries": int(len(rdf)),
        "data_source": "World Bank WDI (SH.XPD.CHEX.PP.CD, SH.XPD.CHEX.GD.ZS, SP.DYN.LE00.IN)",
        "period": f"{PERIOD[0]}-{PERIOD[1]}",
        "delta_H": DELTA_H,
        "n_params": K,
        "models": {
            "M0_flow": {
                "level_rmse_median": med("M0_level_rmse"),
                "change_rmse_median": med("M0_change_rmse"),
                "loocv_rmse_median": med("M0_loocv"),
                "aic_median": med("M0_aic"),
                "bic_median": med("M0_bic"),
            },
            "M1_constant_lag": {
                "level_rmse_median": med("M1_level_rmse"),
                "change_rmse_median": med("M1_change_rmse"),
                "loocv_rmse_median": med("M1_loocv"),
                "aic_median": med("M1_aic"),
                "bic_median": med("M1_bic"),
                "mu_const_median_yr": med("mu_const"),
            },
            "M2_tempo_lag": {
                "level_rmse_median": med("M2_level_rmse"),
                "change_rmse_median": med("M2_change_rmse"),
                "loocv_rmse_median": med("M2_loocv"),
                "aic_median": med("M2_aic"),
                "bic_median": med("M2_bic"),
                "mu_H0_median_yr": med("mu_H0"),
                "mu_H1_median_yr_per_yr": med("mu_H1"),
            },
        },
        "key_findings": {
            "M1_beats_M0_level_pct": round(100 * share_better("M1_level_rmse", "M0_level_rmse")),
            "M2_beats_M0_level_pct": round(100 * share_better("M2_level_rmse", "M0_level_rmse")),
            "M2_beats_M0_change_pct": round(100 * share_better("M2_change_rmse", "M0_change_rmse")),
            "M2_beats_M1_level_pct": round(100 * share_better("M2_level_rmse", "M1_level_rmse")),
            "M1_beats_M0_aic_pct": round(100 * share_better("M1_aic", "M0_aic")),
            "M1_beats_M0_bic_pct": round(100 * share_better("M1_bic", "M0_bic")),
            "M1_beats_M0_loocv_pct": round(100 * share_better("M1_loocv", "M0_loocv")),
            "M2_beats_M1_aic_pct": round(100 * share_better("M2_aic", "M1_aic")),
            "M2_beats_M1_bic_pct": round(100 * share_better("M2_bic", "M1_bic")),
            "M2_beats_M1_loocv_pct": round(100 * share_better("M2_loocv", "M1_loocv")),
        },
    }
    with open(os.path.join(DATA, "tempo_model_selection.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n=== TEMPO MODEL SELECTION SUMMARY (computed) ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
