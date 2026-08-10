"""
Real-waveform validation using the VitalDB Open Dataset.

The script selects a fixed, reproducible sample of cases with an invasive
arterial pressure (SNUADC/ART) waveform, extracts beat-by-beat systolic and
diastolic pressures from a short intra-operative segment, and then simulates
the same gain/offset/zeroing scenarios used in the synthetic static analysis.

All outputs are written to data/ so that the downstream analysis and figure
scripts remain the single source of manuscript numbers.

Data source: VitalDB Open Dataset (https://vitaldb.net/), SNUADC/ART track.
"""

from __future__ import annotations

import os
import warnings

import numpy as np
import pandas as pd
import scipy.signal as ss
import vitaldb

# ----------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------
SEED = 20260810
N_CASES = 30          # number of real waveforms to analyse
SEGMENT_SECONDS = 60  # length of each analysed segment
SAMPLE_RATE = 500     # Hz for SNUADC/ART
SAMPLE_DT = 1.0 / SAMPLE_RATE
LOWPASS = 20.0        # Hz, antialiasing / noise filter
NOISE_SD = 3.0        # simulated measurement noise, mmHg
OFFSET = 12.0         # pre-zeroing offset, mmHg
GAIN = 1.10           # simulated sensor gain error

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _rng(seed=SEED):
    return np.random.RandomState(seed)


def _load_cases_meta() -> pd.DataFrame:
    """Return the VitalDB cases table with opstart/opend if available."""
    # Load directly from the public cases endpoint to avoid stale caching.
    df = pd.read_csv("https://api.vitaldb.net/cases")
    # Ensure numeric columns are numeric (they may arrive as strings from CSV).
    for col in ["caseid", "casestart", "caseend", "opstart", "opend"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _select_cases(n_cases: int) -> list[int]:
    """Return a reproducible sample of case IDs with an SNUADC/ART track."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        art_cases = vitaldb.find_cases("SNUADC/ART")
    art_cases = sorted([int(c) for c in art_cases])
    rng = _rng()
    return sorted(rng.choice(art_cases, size=n_cases, replace=False).tolist())


def _interpolate_nan(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if not np.isnan(x).any():
        return x
    ok = ~np.isnan(x)
    if not ok.any():
        return np.zeros_like(x)
    idx = np.arange(len(x))
    return np.interp(idx, idx[ok], x[ok])


def _lowpass(sig: np.ndarray, fs: float, cutoff: float = LOWPASS) -> np.ndarray:
    b, a = ss.butter(4, cutoff / (fs / 2.0), btype="low")
    return ss.filtfilt(b, a, sig)


def _extract_beats(p: np.ndarray, fs: float = SAMPLE_RATE) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return systolic/diastolic pressures, pulse pressures and sample indices for each valid beat.

    Peaks (systoles) and troughs (diastoles) are identified on a low-passed
    copy of the signal; the raw (interpolated) waveform is used for the final
    value.  A beat is kept only if a trough follows its systolic peak before
    the next peak.  The two index arrays give the sample positions of the
    retained systolic peaks and the corresponding diastolic troughs.
    """
    p = _interpolate_nan(p)
    smooth = _lowpass(p, fs)

    # minimum peak separation ~0.4 s, minimum prominence 10 mmHg
    peaks, _ = ss.find_peaks(smooth, distance=int(0.4 * fs), prominence=10.0)
    troughs, _ = ss.find_peaks(-smooth, distance=int(0.4 * fs), prominence=5.0)

    sbp = []
    dbp = []
    pps = []
    sbp_idx = []
    dbp_idx = []
    for i in range(len(peaks) - 1):
        pk = peaks[i]
        nxt_pk = peaks[i + 1]
        cands = troughs[(troughs > pk) & (troughs < nxt_pk)]
        if cands.size == 0:
            continue
        tr = cands[0]
        s = float(p[pk])
        d = float(p[tr])
        pp = s - d
        # implausibility filter to exclude calibration flushes, damped segments
        if not (40 <= s <= 300 and 20 <= d <= 200 and 10 <= pp <= 150):
            continue
        sbp.append(s)
        dbp.append(d)
        pps.append(pp)
        sbp_idx.append(pk)
        dbp_idx.append(tr)
    return np.asarray(sbp), np.asarray(dbp), np.asarray(pps), np.asarray(sbp_idx), np.asarray(dbp_idx)


def _case_segment(caseid: int, meta: pd.DataFrame, offset_seconds: int = 300):
    """Load a fixed SNUADC/ART segment for the case and return the raw signal.

    The segment is chosen relative to the recorded operation start
    (opstart + offset_seconds) to avoid pre-induction artefacts.  If opstart is
    missing, a default offset is used.
    """
    row = meta[meta["caseid"] == caseid]
    if row.empty:
        return None
    row = row.iloc[0]
    opstart = row.get("opstart", np.nan)
    opend = row.get("opend", np.nan)
    if pd.isna(opstart) or pd.isna(opend):
        return None
    start_sec = int(opstart) + offset_seconds
    if start_sec + SEGMENT_SECONDS > int(opend):
        start_sec = max(int(opstart), int(opend) - SEGMENT_SECONDS - 60)
    if start_sec < int(opstart):
        return None

    try:
        data = vitaldb.load_case(caseid, "SNUADC/ART", interval=SAMPLE_DT)
    except Exception:
        return None
    if data is None or data.ndim != 2 or data.shape[1] < 1:
        return None
    sig = data[:, 0]
    start_idx = int(start_sec * SAMPLE_RATE)
    end_idx = start_idx + int(SEGMENT_SECONDS * SAMPLE_RATE)
    if end_idx > len(sig):
        end_idx = len(sig)
        start_idx = max(0, end_idx - int(SEGMENT_SECONDS * SAMPLE_RATE))
    seg = sig[start_idx:end_idx]
    if seg is None or len(seg) == 0:
        return None
    # Convert to float and remove implausible non-physiological sentinel values.
    seg = np.asarray(seg, dtype=float)
    seg[(seg < -50) | (seg > 400)] = np.nan
    if np.isnan(seg).all():
        return None
    return _interpolate_nan(seg)


def _simulate_static_scenarios(sbp: np.ndarray, caseid: int,
                               global_mean_sbp: float,
                               noise: np.ndarray) -> list[dict]:
    """Apply the four static error models and return a list of row dicts.

    The compensating offset in R4 is a single global constant so that the
    overall mean bias is near zero while the gain-induced proportional bias
    survives, matching the synthetic S4 scenario.
    """
    masked_offset = -(GAIN - 1.0) * global_mean_sbp
    scenarios = {
        "R1_offset_only": {"gain": 1.0, "offset": OFFSET, "device": sbp + OFFSET + noise},
        "R2_zeroed_ideal": {"gain": 1.0, "offset": 0.0, "device": sbp + noise},
        "R3_gain_uncompensated": {"gain": GAIN, "offset": 0.0, "device": GAIN * sbp + noise},
        "R4_gain_masked": {
            "gain": GAIN,
            "offset": masked_offset,
            "device": GAIN * sbp + masked_offset + noise,
        },
    }
    rows = []
    for name, p in scenarios.items():
        for ref_val, dev_val in zip(sbp, p["device"]):
            rows.append({
                "caseid": int(caseid),
                "scenario": name,
                "reference": float(ref_val),
                "device": float(dev_val),
                "gain_true": float(p["gain"]),
                "offset_true": float(p["offset"]),
            })
    return rows


def build_real_static() -> pd.DataFrame:
    """Generate data/real_static_scenarios.csv from VitalDB waveforms."""
    meta = _load_cases_meta()
    caseids = _select_cases(N_CASES)

    # First pass: collect all valid beat SBP values and compute a global mean.
    case_beats = {}
    for caseid in caseids:
        seg = _case_segment(caseid, meta)
        if seg is None:
            continue
        sbp, *_ = _extract_beats(seg)
        if len(sbp) < 5:
            continue
        case_beats[caseid] = sbp
    if not case_beats:
        return pd.DataFrame()
    all_sbp = np.concatenate(list(case_beats.values()))
    global_mean = float(np.mean(all_sbp))

    rng = _rng(SEED + 13)
    rows = []
    for caseid, sbp in case_beats.items():
        noise = rng.normal(0.0, NOISE_SD, size=sbp.shape)
        rows.extend(_simulate_static_scenarios(sbp, caseid, global_mean, noise))
    return pd.DataFrame(rows)


def build_real_dynamic_example() -> pd.DataFrame:
    """Store an example raw waveform segment for the real-validation figure.

    The exact segment used for Figure 7 is saved so that the figure script can
    reproduce the panel without re-downloading.
    """
    meta = _load_cases_meta()
    caseids = _select_cases(N_CASES)
    # choose the first successfully loaded case for the example waveform
    for caseid in caseids:
        seg = _case_segment(caseid, meta)
        if seg is not None:
            sbp, dbp, pp, *_ = _extract_beats(seg)
            if len(sbp) >= 5:
                t = np.arange(len(seg)) * SAMPLE_DT
                return pd.DataFrame({
                    "time": t,
                    "pressure": seg,
                })
    return pd.DataFrame(columns=["time", "pressure"])


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    static_df = build_real_static()
    static_path = os.path.join(DATA_DIR, "real_static_scenarios.csv")
    static_df.to_csv(static_path, index=False)
    print(f"Wrote {static_path} ({len(static_df)} paired beats from "
          f"{static_df['caseid'].nunique()} cases)")

    example_df = build_real_dynamic_example()
    example_path = os.path.join(DATA_DIR, "real_example_waveform.csv")
    example_df.to_csv(example_path, index=False)
    print(f"Wrote {example_path} ({len(example_df)} samples)")


if __name__ == "__main__":
    main()
