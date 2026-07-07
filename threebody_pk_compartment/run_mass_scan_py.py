#!/usr/bin/env python3
"""
Python re-implementation of the population mass-ratio scan (direction C).

The original ``simulations/mass_scan.jl`` requires Julia, which is not
available in this environment.  This runner reproduces the same aggregate
per-configuration statistics using the Numba-accelerated 3D core in
``simulations/threebody_fast.py`` so the population-PK analysis can be run on
an expanded grid with more runs per configuration (to reduce the estimation
noise on the mean-residence-time / median-lifetime scaling).

Output: ``data/mass_scan_3d.json`` — a list of dicts with the same keys the
existing analysis (`analysis.advanced_pk_analysis.population_pk_analysis`)
consumes: masses, rates (row convention rates[i][j] = i->j), ke,
total_dwell_time, lifetimes_mean/median, mean_excursions, escaper_probs,
n_escape, lifetime_percentiles.
"""

import argparse
import json
import os
import time

import numpy as np

from simulations.threebody_fast import simulate
from simulations.threebody_scattering import generate_binary_single_ic

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")

COMP_TO_PAIR = {0: (1, 2), 1: (1, 3), 2: (2, 3)}
PAIR_TO_COMP = {(1, 2): 0, (2, 1): 0, (1, 3): 1, (3, 1): 1, (2, 3): 2, (3, 2): 2}

SIM = dict(c_light=100.0, k_tidal=0.05, r_tidal=0.05, dt_initial=1e-3,
           t_max=1e5, escape_radius=100.0, collision_radius=1e-4,
           softening=0.0, eta=0.01)
BS_IC = dict(v_inf=0.8, b_max=4.0)


def run_config(masses, n_runs, seed):
    rng = np.random.default_rng(seed)
    m = np.asarray(masses, dtype=np.float64)
    M = m.sum()

    trans = np.zeros((3, 3))
    dwell = np.zeros(3)
    esc = np.zeros(3)
    lifetimes = []
    n_exc = []
    escaper_body = []

    for _ in range(n_runs):
        ic = generate_binary_single_ic(*masses, rng=rng, **BS_IC)
        pos = np.ascontiguousarray(ic.positions, dtype=np.float64)
        vel = np.ascontiguousarray(ic.velocities, dtype=np.float64)
        rcom = (m[:, None] * pos).sum(0) / M
        vcom = (m[:, None] * vel).sum(0) / M
        pos = np.ascontiguousarray(pos - rcom)
        vel = np.ascontiguousarray(vel - vcom)

        (status, escaper, bpi, bpj, sma, ecc, E_bin, v_esc, life, E0, Ef,
         ncfg, comp_seq, t_seq) = simulate(
            m, pos, vel, 0, SIM["c_light"], SIM["k_tidal"], SIM["r_tidal"],
            SIM["dt_initial"], SIM["t_max"], SIM["escape_radius"],
            SIM["collision_radius"], SIM["softening"], SIM["eta"])

        if status != 0 or ncfg == 0:
            continue
        lifetimes.append(float(life))
        n_exc.append(int(ncfg))
        if escaper >= 0:
            escaper_body.append(int(escaper) + 1)

        comps = [int(comp_seq[k]) for k in range(ncfg)]
        times = [float(t_seq[k]) for k in range(ncfg)]
        for k in range(ncfg - 1):
            cf, ct = comps[k], comps[k + 1]
            if cf != ct:
                trans[cf, ct] += 1
        for k in range(ncfg):
            t_s = times[k]
            t_e = times[k + 1] if k + 1 < ncfg else life
            if t_e > t_s:
                dwell[comps[k]] += (t_e - t_s)
        esc[comps[-1]] += 1

    T = np.maximum(dwell, 1e-10)
    rates = np.zeros((3, 3))
    ke = np.zeros(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                rates[i, j] = trans[i, j] / T[i]
        ke[i] = esc[i] / T[i]

    lt = np.array(lifetimes)
    n = len(escaper_body)
    return {
        "masses": [float(x) for x in masses],
        "trans": trans.tolist(),
        "esc_counts": esc.tolist(),
        "total_dwell_time": T.tolist(),
        "rates": rates.tolist(),
        "ke": ke.tolist(),
        "n_escape": int(len(lt)),
        "lifetimes_mean": float(lt.mean()) if len(lt) else 0.0,
        "lifetimes_median": float(np.median(lt)) if len(lt) else 0.0,
        "lifetimes_std": float(lt.std()) if len(lt) else 0.0,
        "mean_excursions": float(np.mean(n_exc)) if n_exc else 0.0,
        "escaper_probs": ([escaper_body.count(b) / n for b in (1, 2, 3)]
                          if n else [0.0, 0.0, 0.0]),
        "lifetime_percentiles": (np.quantile(lt, np.arange(0, 1.01, 0.1)).tolist()
                                 if len(lt) else [0.0] * 11),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2500,
                    help="runs per configuration")
    ap.add_argument("--out", default="mass_scan_3d.json")
    args = ap.parse_args()

    grid = [0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
    total = len(grid) ** 2
    print(f"3D population mass scan: {total} configs x {args.n} runs")
    results = []
    seed = 424242
    idx = 0
    t0 = time.time()
    for m2 in grid:
        for m3 in grid:
            idx += 1
            seed += 1
            r = run_config((1.0, m2, m3), args.n, seed)
            results.append(r)
            print(f"  [{idx}/{total}] m=(1,{m2},{m3}) esc={r['n_escape']} "
                  f"med={r['lifetimes_median']:.1f} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    out = os.path.join(DATADIR, args.out)
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} configs -> {out} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
