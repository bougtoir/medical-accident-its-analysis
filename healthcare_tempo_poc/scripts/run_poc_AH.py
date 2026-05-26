"""
Candidate A-H PoC -- spending-to-outcome tempo in healthcare.

Hypothesis: life expectancy at time t reflects a STOCK of health capital
accumulated from past health spending. The standard mistake is to compare
period health outcomes to period spending, which biases cross-country
efficiency rankings. This PoC tests whether adding a spending-to-outcome
lag (with a time-varying mean, the tempo analog) improves the fit of a
simple health production function:

   LifeExp(t) = a + b * log H(t) + c * log(GDPpc(t)) + u(t)

where H(t) is a perpetual-inventory stock of health expenditure.

Three specifications:

  M0 (flow, baseline):    H(t) = E(t)                               (current spending only)
  M1 (constant lag):      H(t+1) = (1-delta_H) H(t) + sum w_s(mu*) E(t-s)
                          geometric lag weights, mu* fit per country
  M2 (tempo lag):         mu(t) = mu_H0 + mu_H1 * (year - t0)
                          mu_H1 > 0 -> spending-to-outcome lag lengthens over time

Evaluation (mirrors GDP PoC):
  Test A: levels RMSE of life expectancy (years)
  Test B: year-on-year change in life expectancy
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
os.makedirs(DATA, exist_ok=True); os.makedirs(FIG, exist_ok=True)

WB_DIR = "/home/ubuntu/healthcare_tempo_data/wb"

# Focus on OECD + BRIC countries with long WB data coverage.
COUNTRIES_ISO = [
    ("Australia","AUS"), ("Austria","AUT"), ("Belgium","BEL"),
    ("Canada","CAN"), ("Chile","CHL"), ("China","CHN"),
    ("Colombia","COL"), ("Costa Rica","CRI"),
    ("Czech Republic","CZE"), ("Denmark","DNK"), ("Estonia","EST"),
    ("Finland","FIN"), ("France","FRA"), ("Germany","DEU"),
    ("Greece","GRC"), ("Hungary","HUN"), ("Iceland","ISL"),
    ("Ireland","IRL"), ("Israel","ISR"), ("Italy","ITA"),
    ("Japan","JPN"), ("Korea","KOR"), ("Latvia","LVA"),
    ("Lithuania","LTU"), ("Luxembourg","LUX"), ("Mexico","MEX"),
    ("Netherlands","NLD"), ("New Zealand","NZL"), ("Norway","NOR"),
    ("Poland","POL"), ("Portugal","PRT"), ("Slovakia","SVK"),
    ("Slovenia","SVN"), ("Spain","ESP"), ("Sweden","SWE"),
    ("Switzerland","CHE"), ("Turkey","TUR"),
    ("United Kingdom","GBR"), ("United States","USA"),
]

DELTA_H = 0.10  # placeholder; OECD health-capital literature suggests 0.05-0.15


def load_wb(code):
    p = os.path.join(WB_DIR, f"{code}.json")
    with open(p) as fh:
        rows = json.load(fh)
    df = pd.DataFrame([
        {"iso3": r["countryiso3code"], "year": int(r["date"]),
         "value": r["value"]}
        for r in rows if r.get("value") is not None
    ])
    return df.set_index(["iso3","year"])["value"]


def geom_weights(mu, M=40):
    """Geometric distribution on 0..M-1 with mean mu.  p(s) = (1-q) q^s where E[s]=q/(1-q)."""
    if mu <= 0:
        w = np.zeros(M); w[0] = 1.0; return w
    q = mu / (1.0 + mu)
    s = np.arange(M)
    w = (1.0 - q) * (q ** s)
    w /= w.sum()
    return w


def stock_constant_mu(E, mu, delta=DELTA_H):
    """PIM with constant lag mean mu. Weights are renormalized at each t so that
    early-period effective flow is not biased low by lag-window truncation
    (matches the renormalization convention used inside fit_mu_tempo)."""
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


def stock_tempo_mu(E, mu0, mu1, t0, delta=DELTA_H):
    T = len(E)
    E_eff = np.zeros(T)
    for t in range(T):
        mu_t = max(0.0, mu0 + mu1 * (t0 + t - t0))  # year-index form; t0 is origin
        # correction: mu depends on calendar year; pass in via outer
        pass
    return None  # implemented inline in main


def test_A_levels(LE, LE_pred):
    resid = LE - LE_pred
    return float(np.sqrt(np.mean(resid**2)))  # RMSE in years


def test_B_changes(LE, LE_pred):
    d = np.diff(LE); dp = np.diff(LE_pred)
    resid = d - dp
    return float(np.sqrt(np.mean(resid**2)))


def fit_mu_const(E, gdp_pc, LE, t0):
    best = None
    for mu in np.arange(0.0, 20.0, 1.0):
        H = stock_constant_mu(E, mu)
        X = np.column_stack([np.ones(len(LE)), np.log(H + 1e-6), np.log(gdp_pc + 1e-6)])
        coef, *_ = np.linalg.lstsq(X, LE, rcond=None)
        pred = X @ coef
        rmse = test_A_levels(LE, pred)
        if best is None or rmse < best[0]:
            best = (rmse, mu, coef, pred)
    return best


def fit_mu_tempo(E, gdp_pc, LE, t0):
    """Grid search over mu_H0, mu_H1."""
    best = None
    for mu0 in np.arange(0.0, 20.0, 2.0):
        for mu1 in np.arange(-0.10, 0.35, 0.05):
            T = len(E)
            # Time-varying weights: compute E_eff[t] using mu(t) = mu0 + mu1 * t
            E_eff = np.zeros(T)
            for t in range(T):
                mu_t = max(0.01, mu0 + mu1 * t)
                w = geom_weights(mu_t, M=min(40, t+1))
                for s in range(len(w)):
                    E_eff[t] += w[s] * E[t-s]
            H = np.zeros(T)
            if E_eff[0] <= 0: continue
            H[0] = E_eff[0] / (DELTA_H + 0.02)
            for t in range(1, T):
                H[t] = (1 - DELTA_H) * H[t-1] + E_eff[t-1]
            if np.any(H <= 0): continue
            X = np.column_stack([np.ones(T), np.log(H), np.log(gdp_pc + 1e-6)])
            coef, *_ = np.linalg.lstsq(X, LE, rcond=None)
            pred = X @ coef
            rmse = test_A_levels(LE, pred)
            if best is None or rmse < best[0]:
                best = (rmse, mu0, mu1, coef, pred)
    return best


def main():
    print("Loading WB indicators...", flush=True)
    E_share = load_wb("SH.XPD.CHEX.GD.ZS")        # current health exp % GDP
    E_pc    = load_wb("SH.XPD.CHEX.PP.CD")        # per capita PPP USD
    LE      = load_wb("SP.DYN.LE00.IN")           # life expectancy

    # GDP per capita from PWT (use PPP gdp / population). For this PoC we reuse
    # E_pc / (E_share/100) ~ GDP per capita PPP USD.
    rows = []
    for name, iso in COUNTRIES_ISO:
        try:
            e_sh = E_share.loc[iso].sort_index()
            e_pc = E_pc.loc[iso].sort_index()
            le   = LE.loc[iso].sort_index()
        except KeyError:
            continue
        common = e_sh.index.intersection(e_pc.index).intersection(le.index)
        if len(common) < 15:
            print(f"  skip {name} ({len(common)} obs)"); continue
        common = common.sort_values()
        years = np.array(common)
        gdp_pc = (e_pc.loc[common].values / (e_sh.loc[common].values / 100.0))
        E = e_pc.loc[common].values                 # per-capita PPP health exp
        y = le.loc[common].values
        if np.any(E <= 0) or np.any(gdp_pc <= 0) or np.any(y <= 0):
            print(f"  skip {name} (non-positive)"); continue

        t0 = int(years[0])

        # M0 flow only
        X0 = np.column_stack([np.ones(len(y)), np.log(E), np.log(gdp_pc)])
        c0, *_ = np.linalg.lstsq(X0, y, rcond=None)
        pred0 = X0 @ c0
        rmse0 = test_A_levels(y, pred0)
        b0 = test_B_changes(y, pred0)

        # M1 constant lag
        m1 = fit_mu_const(E, gdp_pc, y, t0)
        rmse1, mu_const, c1, pred1 = m1
        b1 = test_B_changes(y, pred1)

        # M2 tempo lag
        m2 = fit_mu_tempo(E, gdp_pc, y, t0)
        if m2 is None:
            rmse2, mu0, mu1, pred2 = rmse1, mu_const, 0.0, pred1
        else:
            rmse2, mu0, mu1, c2, pred2 = m2
        b2 = test_B_changes(y, pred2)

        rows.append({
            "country": name, "iso3": iso, "n": len(years),
            "y_start": t0, "y_end": int(years[-1]),
            "mu_const": float(mu_const), "mu_H0": float(mu0), "mu_H1": float(mu1),
            "M0_level_rmse": rmse0, "M1_level_rmse": rmse1, "M2_level_rmse": rmse2,
            "M0_change_rmse": b0,   "M1_change_rmse": b1,   "M2_change_rmse": b2,
        })
        print(f"  {name:20s}  mu1={mu1:+.2f}/yr  level RMSE M0={rmse0:.2f} "
              f"M1={rmse1:.2f} M2={rmse2:.2f}", flush=True)

    rdf = pd.DataFrame(rows).sort_values("country").reset_index(drop=True)
    rdf.to_csv(os.path.join(DATA, "poc_AH_results.csv"), index=False)

    # ---- Figures ----
    s = rdf.sort_values("M0_level_rmse")
    y = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(11, 9))
    bw = 0.28
    ax.barh(y - bw, s["M0_level_rmse"], bw, label="M0 flow-only", color="#888")
    ax.barh(y,       s["M1_level_rmse"], bw, label="M1 constant lag", color="#4c72b0")
    ax.barh(y + bw, s["M2_level_rmse"], bw, label="M2 tempo lag", color="#dd8452")
    ax.set_yticks(y); ax.set_yticklabels(s["country"], fontsize=8)
    ax.set_xlabel("Life expectancy RMSE (years)")
    ax.set_title(f"Candidate A-H: spending-to-outcome tempo ({len(rdf)} countries)")
    ax.legend(loc="lower right"); ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figAH1_level_rmse.png"), dpi=140)
    plt.close(fig)

    d10 = rdf["M0_level_rmse"] - rdf["M1_level_rmse"]
    d20 = rdf["M0_level_rmse"] - rdf["M2_level_rmse"]
    d21 = rdf["M1_level_rmse"] - rdf["M2_level_rmse"]
    fig, ax = plt.subplots(figsize=(8,5))
    ax.boxplot([d10, d20, d21], tick_labels=["M0-M1","M0-M2","M1-M2"])
    ax.axhline(0, color="red", lw=1)
    ax.set_ylabel("Level RMSE reduction (years)")
    ax.set_title(f"Candidate A-H: pairwise RMSE improvements ({len(rdf)} countries)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figAH2_improvements.png"), dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8,6))
    sc = ax.scatter(rdf["mu_H1"], rdf["M1_level_rmse"] - rdf["M2_level_rmse"],
                    c=rdf["mu_H0"], cmap="viridis", s=50, edgecolor="k")
    for _, row in rdf.iterrows():
        ax.annotate(row["country"][:8],
                    (row["mu_H1"], row["M1_level_rmse"] - row["M2_level_rmse"]),
                    fontsize=7, alpha=0.7)
    ax.axhline(0, color="gray", lw=1); ax.axvline(0, color="red", lw=1)
    ax.set_xlabel("Tempo drift in spending-outcome lag (years of lag per year)")
    ax.set_ylabel("Level RMSE reduction M1 -> M2 (years)")
    ax.set_title("Where does the tempo effect in health spending show up?")
    plt.colorbar(sc, ax=ax, label="Base lag mu_H0 (years)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "figAH3_tempo_scatter.png"), dpi=140)
    plt.close(fig)

    summary = {
        "n_countries": int(len(rdf)),
        "level_rmse_median_years": {
            "M0": float(rdf["M0_level_rmse"].median()),
            "M1": float(rdf["M1_level_rmse"].median()),
            "M2": float(rdf["M2_level_rmse"].median()),
        },
        "change_rmse_median_years": {
            "M0": float(rdf["M0_change_rmse"].median()),
            "M1": float(rdf["M1_change_rmse"].median()),
            "M2": float(rdf["M2_change_rmse"].median()),
        },
        "share_M1_beats_M0": float((rdf["M1_level_rmse"] < rdf["M0_level_rmse"]).mean()),
        "share_M2_beats_M0": float((rdf["M2_level_rmse"] < rdf["M0_level_rmse"]).mean()),
        "share_M2_beats_M1": float((rdf["M2_level_rmse"] < rdf["M1_level_rmse"]).mean()),
        "mu_H1_median_per_year": float(rdf["mu_H1"].median()),
        "mu_const_median": float(rdf["mu_const"].median()),
    }
    with open(os.path.join(DATA, "poc_AH_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\n=== A-H SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
