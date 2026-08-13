"""
Analyse the simulated datasets and write machine-readable results.

Outputs (all regenerated from data/ on every run):
  results/static_metrics.csv       per-scenario metrics (static)
  results/dynamic_metrics.csv      per-system metrics (dynamic, on PP and SBP)
  results/range_dependence.csv     CCC vs sampling range width
  results/summary.json             every number that appears in the manuscript

Detection rule thresholds (fixed a priori, reported in Methods):
  * mean-bias summary flags an error if |mean bias| > 5 mmHg
  * proportional-bias (BA difference-vs-mean regression) flags if the slope
    95% CI excludes 0
  * Deming / Passing-Bablok flag if the slope 95% CI excludes 1
  * CCC scale shift flags if |v - 1| > 0.05
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

import methods as M
import simulate as SIM

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

BIAS_THRESHOLD = 5.0     # mmHg
V_THRESHOLD = 0.05       # fractional gain deviation


def _ci_excludes(ci, value):
    lo, hi = ci
    return not (lo <= value <= hi)


def analyse_pair(ref, test) -> dict:
    ccc = M.lins_ccc(ref, test)
    ba = M.bland_altman(ref, test)
    dem = M.deming_regression(ref, test)
    pb = M.passing_bablok(ref, test)

    flags = {
        "flag_meanbias": abs(ba["bias"]) > BIAS_THRESHOLD,
        "flag_ba_regression": _ci_excludes(_slope_ci_from_p(ba), 0.0),
        "flag_deming": _ci_excludes(dem["slope_ci"], 1.0),
        "flag_pb": _ci_excludes(pb["slope_ci"], 1.0),
        "flag_ccc_v": abs(ccc["v"] - 1.0) > V_THRESHOLD,
    }
    return {
        "n": ccc["n"],
        "ccc": ccc["ccc"], "r": ccc["r"], "C_b": ccc["C_b"],
        "v": ccc["v"], "u": ccc["u"],
        "bias": ba["bias"], "sd_diff": ba["sd_diff"],
        "loa_lower": ba["loa_lower"], "loa_upper": ba["loa_upper"],
        "pe": ba["pe"],
        "prop_slope": ba["prop_slope"],
        "prop_intercept": ba["prop_intercept"],
        "prop_slope_lo": ba["prop_slope_ci"][0],
        "prop_slope_hi": ba["prop_slope_ci"][1],
        "prop_slope_p": ba["prop_slope_p"],
        "deming_slope": dem["slope"],
        "deming_lo": dem["slope_ci"][0], "deming_hi": dem["slope_ci"][1],
        "pb_slope": pb["slope"],
        "pb_lo": pb["slope_ci"][0], "pb_hi": pb["slope_ci"][1],
        **flags,
    }


def _slope_ci_from_p(ba):
    return (ba["prop_slope_ci"][0], ba["prop_slope_ci"][1])


def analyse_static(df) -> pd.DataFrame:
    rows = []
    for name, g in df.groupby("scenario", sort=False):
        res = analyse_pair(g["reference"].values, g["device"].values)
        res["scenario"] = name
        res["gain_true"] = g["gain_true"].iloc[0]
        res["offset_true"] = g["offset_true"].iloc[0]
        rows.append(res)
    cols = ["scenario", "gain_true", "offset_true"] + \
           [c for c in rows[0] if c not in ("scenario", "gain_true", "offset_true")]
    return pd.DataFrame(rows)[cols]


def analyse_dynamic(df) -> pd.DataFrame:
    rows = []
    for name, g in df.groupby("system", sort=False):
        for measure in ("pp", "sbp"):
            res = analyse_pair(g[f"{measure}_true"].values,
                               g[f"{measure}_dev"].values)
            res["system"] = name
            res["measure"] = measure
            res["fn_hz"] = g["fn_hz"].iloc[0]
            res["zeta"] = g["zeta"].iloc[0]
            # mean fractional PP/SBP change
            res["mean_ratio"] = float(
                np.mean(g[f"{measure}_dev"].values / g[f"{measure}_true"].values))
            rows.append(res)
    lead = ["system", "measure", "fn_hz", "zeta", "mean_ratio"]
    cols = lead + [c for c in rows[0] if c not in lead]
    return pd.DataFrame(rows)[cols]


def analyse_range(df) -> pd.DataFrame:
    rows = []
    for hw, g in df.groupby("half_width", sort=True):
        ccc = M.lins_ccc(g["reference"].values, g["device"].values)
        rows.append({"half_width": hw, "range_width": 2 * hw,
                     "ref_sd": float(np.std(g["reference"].values, ddof=1)),
                     "ccc": ccc["ccc"], "r": ccc["r"],
                     "C_b": ccc["C_b"], "v": ccc["v"], "u": ccc["u"]})
    return pd.DataFrame(rows)


def _round(obj, nd=3):
    if isinstance(obj, dict):
        return {k: _round(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, nd) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return round(float(obj), nd)
    return obj


def build_summary(static_df, dynamic_df, range_df,
                  real_static_df=None, real_stats=None) -> dict:
    summary = {
        "parameters": {
            "n_static": int(static_df["n"].iloc[0]),
            "sbp_low": SIM.SBP_LOW, "sbp_high": SIM.SBP_HIGH,
            "noise_sd": SIM.NOISE_SD, "offset_mmHg": SIM.OFFSET,
            "gain": SIM.GAIN,
            "bias_threshold": BIAS_THRESHOLD, "v_threshold": V_THRESHOLD,
            "seed": SIM.SEED,
            "dyn_systems": {k: {"fn": v[0], "zeta": v[1]}
                            for k, v in SIM.DYN_SYSTEMS.items()},
        },
        "static": {},
        "dynamic": {},
        "range_dependence": {},
        "real_static": {},
    }
    for _, row in static_df.iterrows():
        summary["static"][row["scenario"]] = _round(row.to_dict())
    for _, row in dynamic_df.iterrows():
        summary["dynamic"][f"{row['system']}_{row['measure']}"] = \
            _round(row.to_dict())
    summary["range_dependence"] = {
        "half_widths": _round(range_df["half_width"].tolist()),
        "range_width": _round(range_df["range_width"].tolist()),
        "ccc": _round(range_df["ccc"].tolist()),
        "C_b": _round(range_df["C_b"].tolist()),
        "v": _round(range_df["v"].tolist()),
        "r": _round(range_df["r"].tolist()),
    }
    if real_static_df is not None and not real_static_df.empty:
        for _, row in real_static_df.iterrows():
            summary["real_static"][row["scenario"]] = _round(row.to_dict())
    if real_stats:
        summary["parameters"].update(real_stats)
    return summary


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    static_in = pd.read_csv(os.path.join(DATA_DIR, "static_scenarios.csv"))
    dynamic_in = pd.read_csv(os.path.join(DATA_DIR, "dynamic_scenarios.csv"))
    range_in = pd.read_csv(os.path.join(DATA_DIR, "range_dependence.csv"))

    static_df = analyse_static(static_in)
    dynamic_df = analyse_dynamic(dynamic_in)
    range_df = analyse_range(range_in)

    static_df.to_csv(os.path.join(RESULTS_DIR, "static_metrics.csv"),
                     index=False)
    dynamic_df.to_csv(os.path.join(RESULTS_DIR, "dynamic_metrics.csv"),
                      index=False)
    range_df.to_csv(os.path.join(RESULTS_DIR, "range_dependence.csv"),
                    index=False)

    real_static_path = os.path.join(DATA_DIR, "real_static_scenarios.csv")
    real_static_df = None
    real_stats = None
    if os.path.exists(real_static_path):
        real_static_in = pd.read_csv(real_static_path)
        real_static_df = analyse_static(real_static_in)
        real_static_df.to_csv(os.path.join(RESULTS_DIR, "real_static_metrics.csv"),
                              index=False)
        real_stats = {
            "n_real_cases": int(real_static_in["caseid"].nunique()),
            "n_real_beats_per_scenario": int(
                real_static_in.groupby("scenario").size().iloc[0]),
        }

    summary = build_summary(static_df, dynamic_df, range_df,
                            real_static_df, real_stats)
    with open(os.path.join(RESULTS_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote results/static_metrics.csv, results/dynamic_metrics.csv, "
          "results/range_dependence.csv, results/summary.json")
    if real_static_df is not None:
        print(f"Wrote results/real_static_metrics.csv "
              f"({len(real_static_df)} scenarios)")


if __name__ == "__main__":
    main()
