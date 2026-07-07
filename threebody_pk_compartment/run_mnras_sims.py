#!/usr/bin/env python3
"""
Generate the additional scattering datasets needed for the MNRAS extensions:

  * 3D Newtonian baseline recording final-binary eccentricity + ejection
    velocity        -> A-4 (eccentricity / kick population)
  * 3D + 1PN precession                                     -> B-5
  * 3D + phenomenological tidal drag                        -> B-6

for the three mass configurations (equal 1:1:1, unequal 1:2:0.5, democratic).

Uses the numba-accelerated core in ``simulations/threebody_fast.py``.
Outputs JSON records compatible with the existing analysis code
(``data/<name>.json``) plus the new ``ecc`` field.
"""

import argparse
import json
import os
import time

import numpy as np

from simulations.threebody_fast import simulate
from simulations.threebody_scattering import (
    generate_binary_single_ic, generate_democratic_ic,
)

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(BASEDIR, "data")

COMP_TO_PAIR = {0: [1, 2], 1: [1, 3], 2: [2, 3]}

MODE_CODE = {"newton": 0, "pn1": 1, "tidal": 2, "pn1_tidal": 3}

# Simulation parameters (match the existing 3D runs)
SIM = dict(c_light=100.0, k_tidal=0.05, r_tidal=0.05, dt_initial=1e-3,
           t_max=1e5, escape_radius=100.0, collision_radius=1e-4,
           softening=0.0, eta=0.01)

# Match the Julia scattering ICs used for the existing datasets.
BS_IC = dict(v_inf=0.8, b_max=4.0)


def run_config(name, masses, ic_mode, mode, n_runs, seed):
    rng = np.random.default_rng(seed)
    mcode = MODE_CODE[mode]
    m = np.asarray(masses, dtype=np.float64)
    records = []
    t0 = time.time()
    for i in range(n_runs):
        if ic_mode == "binary_single":
            ic = generate_binary_single_ic(*masses, rng=rng, **BS_IC)
        else:
            ic = generate_democratic_ic(*masses, rng=rng)
        pos = np.ascontiguousarray(ic.positions, dtype=np.float64)
        vel = np.ascontiguousarray(ic.velocities, dtype=np.float64)
        # to COM frame
        M = m.sum()
        rcom = (m[:, None] * pos).sum(0) / M
        vcom = (m[:, None] * vel).sum(0) / M
        pos = np.ascontiguousarray(pos - rcom)
        vel = np.ascontiguousarray(vel - vcom)

        (status, escaper, bpi, bpj, sma, ecc, E_bin, v_esc, life, E0, Ef,
         ncfg, comp_seq, t_seq) = simulate(
            m, pos, vel, mcode, SIM["c_light"], SIM["k_tidal"], SIM["r_tidal"],
            SIM["dt_initial"], SIM["t_max"], SIM["escape_radius"],
            SIM["collision_radius"], SIM["softening"], SIM["eta"])

        status_str = {0: "escape", 1: "collision", 2: "timeout"}[status]
        seq = [{"pair": COMP_TO_PAIR[int(comp_seq[k])], "t": float(t_seq[k])}
               for k in range(ncfg)]
        rec = {
            "status": status_str,
            "escaper": (int(escaper) + 1) if escaper >= 0 else 0,
            "binary_pair": ([int(bpi) + 1, int(bpj) + 1] if bpi >= 0 else None),
            "E_bin": (float(E_bin) if status == 0 else None),
            "sma": (float(sma) if status == 0 else None),
            "ecc": (float(ecc) if (status == 0 and ecc == ecc) else None),
            "v_esc": (float(v_esc) if status == 0 else None),
            "n_excursions": int(ncfg),
            "lifetime": float(life),
            "E_initial": float(E0),
            "E_final": float(Ef),
            "config_sequence": seq,
        }
        records.append(rec)
        if (i + 1) % max(1, n_runs // 10) == 0:
            n_esc = sum(1 for r in records if r["status"] == "escape")
            print(f"    [{name}/{mode}] {i+1}/{n_runs} esc={n_esc} "
                  f"({time.time()-t0:.0f}s)", flush=True)

    out = os.path.join(DATADIR, f"{name}.json")
    with open(out, "w") as f:
        json.dump(records, f)
    n_esc = sum(1 for r in records if r["status"] == "escape")
    print(f"  wrote {out}: {len(records)} runs, {n_esc} escapes, "
          f"{time.time()-t0:.0f}s", flush=True)
    return records


CONFIGS = [
    ("equal_mass", (1.0, 1.0, 1.0), "binary_single"),
    ("unequal_mass", (1.0, 2.0, 0.5), "binary_single"),
    ("democratic", (1.0, 1.0, 1.0), "democratic"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--modes", nargs="+",
                    default=["newton", "pn1", "tidal"])
    ap.add_argument("--only", nargs="+", default=None,
                    help="restrict to config names")
    args = ap.parse_args()

    suffix = {"newton": "3d_newton_ecc", "pn1": "3d_pn1",
              "tidal": "3d_tidal", "pn1_tidal": "3d_pn1_tidal"}

    seed = 20260706
    for mode in args.modes:
        for cname, masses, ic_mode in CONFIGS:
            if args.only and cname not in args.only:
                continue
            seed += 1
            name = f"{cname}_{suffix[mode]}"
            run_config(name, masses, ic_mode, mode, args.n, seed)


if __name__ == "__main__":
    main()
