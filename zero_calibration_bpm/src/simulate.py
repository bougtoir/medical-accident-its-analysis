"""
Generate the (synthetic) paired measurement datasets used in the paper.

IMPORTANT — these are *simulated* data, not measurements from patients or a
published dataset. Every parameter (operating pressures, offset magnitude,
gain error, measurement noise, catheter-transducer natural frequency and
damping) is stated explicitly here and justified from the cited literature in
the manuscript. The simulations are seeded so that a third party re-running
this script obtains byte-identical CSVs.

Two families of scenarios are produced:

Static method-comparison scenarios (systolic pressure, device vs reference):
    S1  offset_only         b0 = +12 mmHg,   gain = 1.00   (pre-zeroing)
    S2  zeroed_ideal         b0 = 0,          gain = 1.00   (offset removed)
    S3  gain_uncompensated   b0 = 0,          gain = 1.10   (gain error, visible)
    S4  gain_masked          gain = 1.10 with a compensating negative offset
                             chosen so the *mean* difference is ~0 mmHg
                             (gain error hidden from the mean-bias summary)

Dynamic-response scenarios (waveform level, per-beat SBP/DBP/MAP/PP):
    optimal / underdamped / overdamped second-order catheter-transducer
    systems applied to synthetic arterial waveforms.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

import methods as M

SEED = 20260716
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ---- static scenario parameters ----
N_STATIC = 150
SBP_LOW, SBP_HIGH = 80.0, 180.0     # physiological systolic range
NOISE_SD = 3.0                       # random measurement noise (mmHg)
OFFSET = 12.0                        # DC offset before zeroing (mmHg)
GAIN = 1.10                          # 10% sensitivity (gain) error

# ---- dynamic scenario parameters (Gardner 1981; Romagnoli et al 2014) ----
N_BEATS = 120
DYN_NOISE_SD = 1.5     # beat-to-beat measurement noise on extracted SBP/DBP (mmHg)
DYN_SYSTEMS = {
    # name: (natural_frequency_Hz, damping_coefficient)
    "optimal": (25.0, 0.65),
    "underdamped": (10.0, 0.15),
    "overdamped": (8.0, 0.80),
}


def _rng():
    return np.random.RandomState(SEED)


def simulate_static() -> pd.DataFrame:
    rng = _rng()
    ref = rng.uniform(SBP_LOW, SBP_HIGH, N_STATIC)
    ref = np.sort(ref)
    mean_ref = ref.mean()

    rows = []
    scenarios = {
        "S1_offset_only": dict(gain=1.0, offset=OFFSET),
        "S2_zeroed_ideal": dict(gain=1.0, offset=0.0),
        "S3_gain_uncompensated": dict(gain=GAIN, offset=0.0),
        # compensating offset makes the mean difference ~0
        "S4_gain_masked": dict(gain=GAIN, offset=-(GAIN - 1.0) * mean_ref),
    }
    for name, p in scenarios.items():
        noise = rng.normal(0.0, NOISE_SD, N_STATIC)
        device = p["gain"] * ref + p["offset"] + noise
        for r, d in zip(ref, device):
            rows.append({"scenario": name, "reference": r, "device": d,
                         "gain_true": p["gain"], "offset_true": p["offset"]})
    return pd.DataFrame(rows)


def simulate_dynamic() -> pd.DataFrame:
    rng = _rng()
    # draw physiologically plausible beats
    maps = rng.uniform(70.0, 110.0, N_BEATS)
    pps = rng.uniform(30.0, 60.0, N_BEATS)
    hrs = rng.uniform(55.0, 95.0, N_BEATS)

    rows = []
    for i in range(N_BEATS):
        t, wave, freqs, amps, phases, f1 = M.synth_arterial_wave(
            hr=hrs[i], map_mmHg=maps[i], pp_mmHg=pps[i])
        true = M.wave_features(wave)
        for name, (fn, zeta) in DYN_SYSTEMS.items():
            _, dwave = M.apply_dynamic_response(
                freqs, amps, phases, f1, fn, zeta, maps[i])
            dev = M.wave_features(dwave)
            # beat-to-beat measurement noise on the extracted pressures
            sbp_dev = dev["sbp"] + rng.normal(0.0, DYN_NOISE_SD)
            dbp_dev = dev["dbp"] + rng.normal(0.0, DYN_NOISE_SD)
            rows.append({
                "system": name, "fn_hz": fn, "zeta": zeta,
                "hr": hrs[i],
                "sbp_true": true["sbp"], "sbp_dev": sbp_dev,
                "dbp_true": true["dbp"], "dbp_dev": dbp_dev,
                "map_true": true["map"], "map_dev": dev["map"],
                "pp_true": true["pp"], "pp_dev": sbp_dev - dbp_dev,
            })
    return pd.DataFrame(rows)


def simulate_range_dependence() -> pd.DataFrame:
    """One device with a fixed small gain error, sampled over BP ranges of
    increasing width, to demonstrate the range-dependence of the CCC."""
    rng = _rng()
    gain = 1.05
    noise_sd = 3.0
    centre = 130.0
    half_widths = [10.0, 20.0, 30.0, 40.0, 50.0]   # narrow -> wide
    n = 150

    rows = []
    for hw in half_widths:
        ref = rng.uniform(centre - hw, centre + hw, n)
        device = gain * ref + rng.normal(0.0, noise_sd, n)
        for r, d in zip(ref, device):
            rows.append({"half_width": hw, "reference": r, "device": d})
    return pd.DataFrame(rows)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    simulate_static().to_csv(os.path.join(DATA_DIR, "static_scenarios.csv"),
                             index=False)
    simulate_dynamic().to_csv(os.path.join(DATA_DIR, "dynamic_scenarios.csv"),
                              index=False)
    simulate_range_dependence().to_csv(
        os.path.join(DATA_DIR, "range_dependence.csv"), index=False)
    print("Wrote data/static_scenarios.csv, data/dynamic_scenarios.csv, "
          "data/range_dependence.csv")


if __name__ == "__main__":
    main()
