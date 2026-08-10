"""
Generate all manuscript figures from the analysed results.

Every figure is rebuilt from data/ and results/ so the numbers shown in the
figures are always consistent with the tables and text. Pass ``lang="en"``
or ``lang="ja"`` to control the language of all labels (per the repository's
figure-language-consistency rule).
"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

import methods as M
import real_waveforms as RW

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "..", "data")
RESULTS_DIR = os.path.join(HERE, "..", "results")

# Mapping from generation stems to the submission figure numbering.
# Blood Pressure Monitoring allows six figures/tables in total; two figures
# are provided as Supplemental Digital Content and are numbered separately.
SUBMISSION_MAP = {
    "figure1_signal_decomposition": "Figure1",
    "figure2_scenarios_concordance": "Figure2",
    "figure3_detection_panel": "Figure3",
    "figure4_ba_masked_gain": "Figure4",
    "figure5_dynamic_response": "Figure5",
    "figure6_range_dependence": "Figure6",
    "figure7_real_validation": "Figure7",
}


def _savefig(fig, outdir, stem):
    """Save a PNG always; for the English figures also save a vector PDF.

    Graphs are line-art, for which Blood Pressure Monitoring requires a vector
    format (or >=1200 dpi). The vector PDF copies live in figures/pdf/.
    """
    fig.savefig(os.path.join(outdir, stem + ".png"))
    if os.path.basename(os.path.normpath(outdir)) != "ja":
        pdf_dir = os.path.join(outdir, "pdf")
        os.makedirs(pdf_dir, exist_ok=True)
        fig.savefig(os.path.join(pdf_dir, stem + ".pdf"))

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "font.family": "DejaVu Sans",
})

# ---------------------------------------------------------------- labels
L = {
    "en": {
        "pressure": "Pressure (mmHg)", "time": "Time (s)",
        "true_arterial": "True arterial waveform",
        "with_offset": "With +12 mmHg DC offset", "ac_pp": "Pulse pressure (AC)",
        "reference": "Reference pressure (mmHg)",
        "device": "Device pressure (mmHg)",
        "mean_pair": "Mean of device and reference (mmHg)",
        "difference": "Device − reference (mmHg)",
        "freq": "Frequency (Hz)", "gain": "Dynamic gain",
        "sys_optimal": "Optimal (fn=25 Hz, ζ=0.65)",
        "sys_under": "Underdamped (fn=10 Hz, ζ=0.15)",
        "sys_over": "Overdamped (fn=8 Hz, ζ=0.80)",
        "pp_true": "True pulse pressure (mmHg)",
        "pp_dev": "Measured pulse pressure (mmHg)",
        "range_width": "Sampling range width (mmHg)",
        "value": "Value", "detected": "Detected", "missed": "Missed",
        "method": "Analysis reported", "scenario": "Scenario",
        "harmonics": "Arterial harmonics",
        "fig1_title": "Decomposition of the arterial pressure signal",
        "fig1a": "A  Offset shifts the DC level; pulse pressure is unchanged",
        "fig1b": "B  Gain error scales the whole waveform (pulse pressure changes)",
        "fig2_title": "Concordance of device vs reference across four scenarios",
        "fig3_title": "Which reported analysis detects the error?",
        "fig4_title": "Bland–Altman difference-vs-mean plots: hidden gain error",
        "fig5_title": "Dynamic response of the catheter–transducer system",
        "fig5a": "A  System frequency response and arterial harmonics",
        "fig5b": "B  Example waveforms (MAP 90, true PP 40 mmHg)",
        "fig5c": "C  Measured vs true pulse pressure",
        "fig6_title": "Range-dependence of the concordance correlation coefficient",
        "fig7_title": "Real-waveform validation from the VitalDB open dataset",
        "fig7a": "A  10-s arterial pressure waveform (SNUADC/ART) with detected beats",
        "fig7b": "B  Real-data Bland–Altman plot for R4 (gain error masked by offset)",
        "identity": "identity", "mean_bias": "mean bias",
        "gain_x": "gain ×", "s2_label": "S2 zeroed (no gain error)",
        "s4_label": "S4 gain error masked by offset",
        "slope": "slope", "scale_shift": "scale shift",
    },
    "ja": {
        "pressure": "圧 (mmHg)", "time": "時間 (s)",
        "true_arterial": "真の動脈圧波形",
        "with_offset": "+12 mmHg のDCオフセット付与", "ac_pp": "脈圧 (AC成分)",
        "reference": "基準圧 (mmHg)",
        "device": "機器計測圧 (mmHg)",
        "mean_pair": "機器と基準の平均 (mmHg)",
        "difference": "機器 − 基準 (mmHg)",
        "freq": "周波数 (Hz)", "gain": "動的ゲイン",
        "sys_optimal": "最適 (fn=25 Hz, ζ=0.65)",
        "sys_under": "低制動 (fn=10 Hz, ζ=0.15)",
        "sys_over": "過制動 (fn=8 Hz, ζ=0.80)",
        "pp_true": "真の脈圧 (mmHg)",
        "pp_dev": "計測脈圧 (mmHg)",
        "range_width": "標本圧の範囲幅 (mmHg)",
        "value": "値", "detected": "検出", "missed": "見逃し",
        "method": "報告する解析", "scenario": "シナリオ",
        "harmonics": "動脈圧の高調波",
        "fig1_title": "動脈圧信号の分解",
        "fig1a": "A  オフセットはDC水準を移動；脈圧は不変",
        "fig1b": "B  ゲイン誤差は波形全体をスケール（脈圧が変化）",
        "fig2_title": "4シナリオにおける機器対基準の一致度",
        "fig3_title": "どの報告解析が誤差を検出するか",
        "fig4_title": "Bland–Altman 差対平均プロット：隠れたゲイン誤差",
        "fig5_title": "カテーテル–トランスデューサ系の動的応答",
        "fig5a": "A  系の周波数応答と動脈圧高調波",
        "fig5b": "B  波形例 (MAP 90, 真の脈圧 40 mmHg)",
        "fig5c": "C  計測脈圧 対 真の脈圧",
        "fig6_title": "一致相関係数の範囲依存性",
        "fig7_title": "VitalDB公開データセットからの実波形検証",
        "fig7a": "A  10秒間の動脈圧波形（SNUADC/ART）と検出ビート",
        "fig7b": "B  R4（オフセットで隠れたゲイン誤差）の実データBland–Altmanプロット",
        "identity": "同一線", "mean_bias": "平均バイアス",
        "gain_x": "ゲイン ×", "s2_label": "S2 ゼロ校正後（ゲイン誤差なし）",
        "s4_label": "S4 オフセットで隠れたゲイン誤差",
        "slope": "傾き", "scale_shift": "スケールシフト",
    },
}

SCEN_LABELS = {
    "en": {"S1_offset_only": "S1: offset only (pre-zeroing)",
           "S2_zeroed_ideal": "S2: zeroed, no gain error",
           "S3_gain_uncompensated": "S3: gain error (uncompensated)",
           "S4_gain_masked": "S4: gain error masked by offset",
           "R1_offset_only": "R1: offset only",
           "R2_zeroed_ideal": "R2: zeroed, no gain error",
           "R3_gain_uncompensated": "R3: gain error (uncompensated)",
           "R4_gain_masked": "R4: gain error masked by offset"},
    "ja": {"S1_offset_only": "S1: オフセットのみ（ゼロ校正前）",
           "S2_zeroed_ideal": "S2: ゼロ校正後・ゲイン誤差なし",
           "S3_gain_uncompensated": "S3: ゲイン誤差（未補正）",
           "S4_gain_masked": "S4: オフセットで隠れたゲイン誤差",
           "R1_offset_only": "R1: オフセットのみ",
           "R2_zeroed_ideal": "R2: ゼロ校正後・ゲイン誤差なし",
           "R3_gain_uncompensated": "R3: ゲイン誤差（未補正）",
           "R4_gain_masked": "R4: オフセットで隠れたゲイン誤差"},
}

METHOD_LABELS = {
    "en": ["Mean bias\n±LoA", "BA regression\nslope", "Deming\nslope",
           "Passing–Bablok\nslope", "CCC scale\nshift v"],
    "ja": ["平均バイアス\n±LoA", "BA回帰\n傾き", "Deming\n傾き",
           "Passing–Bablok\n傾き", "CCC scale\nshift v"],
}
FLAG_KEYS = ["flag_meanbias", "flag_ba_regression", "flag_deming",
             "flag_pb", "flag_ccc_v"]


def _load():
    with open(os.path.join(RESULTS_DIR, "summary.json")) as f:
        summary = json.load(f)
    static = pd.read_csv(os.path.join(DATA_DIR, "static_scenarios.csv"))
    dynamic = pd.read_csv(os.path.join(DATA_DIR, "dynamic_scenarios.csv"))
    real_static = None
    real_path = os.path.join(DATA_DIR, "real_static_scenarios.csv")
    if os.path.exists(real_path):
        real_static = pd.read_csv(real_path)
    return summary, static, dynamic, real_static


def fig1_signal(lang, outdir):
    t = L[lang]
    _, _, freqs, amps, phases, f1 = M.synth_arterial_wave(
        hr=75, map_mmHg=90, pp_mmHg=40)
    tt, wave, _, _, _, _ = M.synth_arterial_wave(hr=75, map_mmHg=90, pp_mmHg=40)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(tt, wave, color="#1f77b4", lw=2, label=t["true_arterial"])
    ax1.plot(tt, wave + 12, color="#d62728", lw=2, ls="--",
             label=t["with_offset"])
    ax1.annotate("", xy=(tt[-1] * 0.9, wave.max()),
                 xytext=(tt[-1] * 0.9, wave.min()),
                 arrowprops=dict(arrowstyle="<->", color="green"))
    ax1.text(tt[-1] * 0.92, 90, t["ac_pp"], color="green", rotation=90,
             va="center")
    ax1.set_xlabel(t["time"]); ax1.set_ylabel(t["pressure"])
    ax1.set_title(t["fig1a"], fontsize=10, loc="left")
    ax1.legend(fontsize=8, loc="upper right")

    ax2.plot(tt, wave, color="#1f77b4", lw=2, label=t["gain"] + " = 1.00")
    ax2.plot(tt, (wave - 90) * 1.15 + 90, color="#ff7f0e", lw=2, ls="--",
             label=t["gain"] + " = 1.15")
    ax2.set_xlabel(t["time"]); ax2.set_ylabel(t["pressure"])
    ax2.set_title(t["fig1b"], fontsize=10, loc="left")
    ax2.legend(fontsize=8, loc="upper right")

    fig.suptitle(t["fig1_title"], fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _savefig(fig, outdir, "figure1_signal_decomposition")
    plt.close(fig)


def fig2_scenarios(lang, outdir):
    t = L[lang]
    summary, static, _, _ = _load()
    order = ["S1_offset_only", "S2_zeroed_ideal",
             "S3_gain_uncompensated", "S4_gain_masked"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    for ax, name in zip(axes.ravel(), order):
        g = static[static["scenario"] == name]
        s = summary["static"][name]
        ax.scatter(g["reference"], g["device"], s=12, alpha=0.5,
                   color="#1f77b4")
        lim = [70, 200]
        ax.plot(lim, lim, "k--", lw=1, label=t["identity"])
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_aspect("equal")
        ax.set_xlabel(t["reference"]); ax.set_ylabel(t["device"])
        ax.set_title(SCEN_LABELS[lang][name], fontsize=9.5)
        txt = (f"CCC={s['ccc']:.3f}\nv={s['v']:.3f}\n"
               f"{t['mean_bias']}={s['bias']:.1f}")
        ax.text(0.05, 0.95, txt, transform=ax.transAxes, va="top",
                fontsize=9, bbox=dict(boxstyle="round", fc="white", alpha=0.8))
        ax.legend(fontsize=8, loc="lower right")
    fig.suptitle(t["fig2_title"], fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    _savefig(fig, outdir, "figure2_scenarios_concordance")
    plt.close(fig)


def fig3_detection(lang, outdir):
    t = L[lang]
    summary, _, _, _ = _load()
    order = ["S1_offset_only", "S2_zeroed_ideal",
             "S3_gain_uncompensated", "S4_gain_masked"]
    mat = np.array([[1 if summary["static"][s][k] else 0 for k in FLAG_KEYS]
                    for s in order])
    fig, ax = plt.subplots(figsize=(8.5, 5))
    cmap = matplotlib.colors.ListedColormap(["#e0e0e0", "#2ca02c"])
    ax.imshow(mat, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(FLAG_KEYS)))
    ax.set_xticklabels(METHOD_LABELS[lang], fontsize=9)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([SCEN_LABELS[lang][s] for s in order], fontsize=9)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, t["detected"] if mat[i, j] else t["missed"],
                    ha="center", va="center", fontsize=8,
                    color="white" if mat[i, j] else "#555555")
    ax.set_xlabel(t["method"]); ax.set_ylabel(t["scenario"])
    ax.set_title(t["fig3_title"], fontsize=12, fontweight="bold")
    fig.tight_layout()
    _savefig(fig, outdir, "figure3_detection_panel")
    plt.close(fig)


def fig4_ba(lang, outdir):
    t = L[lang]
    summary, static, _, _ = _load()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, name, lab in zip(
            axes, ["S2_zeroed_ideal", "S4_gain_masked"],
            [t["s2_label"], t["s4_label"]]):
        g = static[static["scenario"] == name]
        s = summary["static"][name]
        mean = (g["reference"].values + g["device"].values) / 2
        diff = g["device"].values - g["reference"].values
        ax.scatter(mean, diff, s=12, alpha=0.5, color="#1f77b4")
        ax.axhline(s["bias"], color="k", lw=1.2,
                   label=f"{t['mean_bias']}={s['bias']:.1f}")
        ax.axhline(s["loa_upper"], color="grey", ls="--", lw=1)
        ax.axhline(s["loa_lower"], color="grey", ls="--", lw=1)
        xs = np.linspace(mean.min(), mean.max(), 50)
        ax.plot(xs, s["prop_slope"] * xs + s["prop_intercept"],
                color="#d62728", lw=1.8,
                label=f"{t['slope']}={s['prop_slope']:.3f}")
        ax.set_xlabel(t["mean_pair"]); ax.set_ylabel(t["difference"])
        ax.set_title(lab, fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(t["fig4_title"], fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _savefig(fig, outdir, "figure4_ba_masked_gain")
    plt.close(fig)


def fig5_dynamic(lang, outdir):
    t = L[lang]
    summary, _, dynamic, _ = _load()
    systems = [("optimal", "#2ca02c", t["sys_optimal"]),
               ("underdamped", "#d62728", t["sys_under"]),
               ("overdamped", "#1f77b4", t["sys_over"])]

    fig = plt.figure(figsize=(13, 4.6))
    ax1 = fig.add_subplot(1, 3, 1)
    freq = np.linspace(0.1, 40, 500)
    from simulate import DYN_SYSTEMS
    for name, color, lab in systems:
        fn, zeta = DYN_SYSTEMS[name]
        mag, _ = M.second_order_gain_phase(freq, fn, zeta)
        ax1.plot(freq, mag, color=color, lw=2, label=lab)
    # arterial harmonics (HR 75)
    f1 = 75 / 60.0
    for k in range(1, 11):
        ax1.axvline(k * f1, color="grey", lw=0.5, alpha=0.4)
    ax1.axhline(1.0, color="k", lw=0.8, ls=":")
    ax1.set_xlim(0, 40); ax1.set_ylim(0, 3)
    ax1.set_xlabel(t["freq"]); ax1.set_ylabel(t["gain"])
    ax1.set_title(t["fig5a"], fontsize=10, loc="left")
    ax1.legend(fontsize=7.5, loc="upper right")

    # example waveforms
    ax2 = fig.add_subplot(1, 3, 2)
    tt, wave, freqs, amps, phases, f1w = M.synth_arterial_wave(
        hr=75, map_mmHg=90, pp_mmHg=40)
    ax2.plot(tt, wave, color="k", lw=2, label=t["true_arterial"])
    for name, color, lab in systems:
        fn, zeta = DYN_SYSTEMS[name]
        _, dwave = M.apply_dynamic_response(freqs, amps, phases, f1w,
                                            fn, zeta, 90)
        ax2.plot(tt, dwave, color=color, lw=1.6, ls="--")
    ax2.set_xlabel(t["time"]); ax2.set_ylabel(t["pressure"])
    ax2.set_title(t["fig5b"], fontsize=10, loc="left")
    ax2.legend(fontsize=7.5, loc="upper right")

    # measured vs true PP
    ax3 = fig.add_subplot(1, 3, 3)
    for name, color, lab in systems:
        g = dynamic[dynamic["system"] == name]
        ax3.scatter(g["pp_true"], g["pp_dev"], s=10, alpha=0.5, color=color)
    lim = [20, 70]
    ax3.plot(lim, lim, "k--", lw=1)
    for name, color, lab in systems:
        s = summary["dynamic"][f"{name}_pp"]
        ax3.scatter([], [], color=color,
                    label=f"{lab.split('(')[0].strip()} "
                          f"(PP ratio={s['mean_ratio']:.2f})")
    ax3.set_xlim(lim); ax3.set_ylim(lim); ax3.set_aspect("equal")
    ax3.set_xlabel(t["pp_true"]); ax3.set_ylabel(t["pp_dev"])
    ax3.set_title(t["fig5c"], fontsize=10, loc="left")
    ax3.legend(fontsize=7.5, loc="upper left")

    fig.suptitle(t["fig5_title"], fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    _savefig(fig, outdir, "figure5_dynamic_response")
    plt.close(fig)


def fig6_range(lang, outdir):
    t = L[lang]
    summary, _, _, _ = _load()
    rd = summary["range_dependence"]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(rd["range_width"], rd["ccc"], "o-", color="#1f77b4",
            lw=2, label="CCC (ρc)")
    ax.plot(rd["range_width"], rd["C_b"], "s-", color="#2ca02c",
            lw=2, label="C_b")
    ax.plot(rd["range_width"], rd["v"], "^-", color="#d62728",
            lw=2, label=f"v ({t['scale_shift']})")
    ax.axhline(1.05, color="grey", ls=":", lw=1)
    ax.set_xlabel(t["range_width"]); ax.set_ylabel(t["value"])
    ax.set_ylim(0.5, 1.3)
    ax.set_title(t["fig6_title"], fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    fig.tight_layout()
    _savefig(fig, outdir, "figure6_range_dependence")
    plt.close(fig)


def fig7_real_validation(lang, outdir):
    t = L[lang]
    summary, _, _, real_static = _load()
    if real_static is None or real_static.empty:
        return

    # Example waveform (first 10 s)
    example = pd.read_csv(os.path.join(DATA_DIR, "real_example_waveform.csv"))
    t_vals = example["time"].values[: int(10 / RW.SAMPLE_DT)]
    p_vals = example["pressure"].values[: len(t_vals)]
    sbp_ex, dbp_ex, _, sbp_idx_ex, dbp_idx_ex = RW._extract_beats(
        p_vals, fs=RW.SAMPLE_RATE)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    ax1.plot(t_vals, p_vals, color="#1f77b4", lw=1.2, label=t["true_arterial"])
    ax1.scatter(t_vals[sbp_idx_ex], p_vals[sbp_idx_ex],
                color="k", s=12, zorder=3, label=t["detected"])
    ax1.set_xlabel(t["time"])
    ax1.set_ylabel(t["pressure"])
    ax1.set_title(t["fig7a"], fontsize=10, loc="left")
    ax1.legend(fontsize=8, loc="upper right")

    # Real R4 Bland-Altman plot
    r4 = real_static[real_static["scenario"] == "R4_gain_masked"]
    s = summary["real_static"]["R4_gain_masked"]
    mean = (r4["reference"].values + r4["device"].values) / 2.0
    diff = r4["device"].values - r4["reference"].values
    ax2.scatter(mean, diff, s=6, alpha=0.3, color="#1f77b4")
    ax2.axhline(s["bias"], color="k", lw=1.2,
                 label=f"{t['mean_bias']}={s['bias']:.1f}")
    ax2.axhline(s["loa_upper"], color="grey", ls="--", lw=1)
    ax2.axhline(s["loa_lower"], color="grey", ls="--", lw=1)
    xs = np.linspace(np.percentile(mean, 1), np.percentile(mean, 99), 50)
    ax2.plot(xs, s["prop_slope"] * xs + s["prop_intercept"],
             color="#d62728", lw=1.8,
             label=f"{t['slope']}={s['prop_slope']:.3f}")
    ax2.set_xlabel(t["mean_pair"])
    ax2.set_ylabel(t["difference"])
    ax2.set_title(t["fig7b"], fontsize=10, loc="left")
    ax2.legend(fontsize=8, loc="upper left")

    fig.suptitle(t["fig7_title"], fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _savefig(fig, outdir, "figure7_real_validation")
    plt.close(fig)


def _set_font(lang):
    if lang == "ja":
        for cand in ("IPAGothic", "IPAPGothic", "Noto Sans CJK JP",
                     "WenQuanYi Zen Hei"):
            try:
                matplotlib.font_manager.findfont(cand, fallback_to_default=False)
                plt.rcParams["font.family"] = cand
                break
            except Exception:
                continue
    else:
        chosen = "DejaVu Sans"
        for cand in ("Arial", "Helvetica", "Liberation Sans", "Nimbus Sans"):
            try:
                matplotlib.font_manager.findfont(cand, fallback_to_default=False)
                chosen = cand
                break
            except Exception:
                continue
        plt.rcParams["font.family"] = chosen
    plt.rcParams["axes.unicode_minus"] = False


def generate(lang="en", outdir=None):
    _set_font(lang)
    if outdir is None:
        outdir = os.path.join(HERE, "..", "figures")
        if lang == "ja":
            outdir = os.path.join(outdir, "ja")
    os.makedirs(outdir, exist_ok=True)
    fig1_signal(lang, outdir)
    fig2_scenarios(lang, outdir)
    fig3_detection(lang, outdir)
    fig4_ba(lang, outdir)
    fig5_dynamic(lang, outdir)
    fig6_range(lang, outdir)
    fig7_real_validation(lang, outdir)
    print(f"[{lang}] wrote 7 figures to {outdir}")


def export_tiff(src_dir=None, dst_dir=None, dpi=300):
    """Write submission-ready TIFF copies of the English figures.

    Blood Pressure Monitoring (Editorial Manager) requires each figure as a
    separate file, preferably TIFF, not embedded in the manuscript. The PNGs
    are kept for the inline reading copy of the manuscript.
    """
    if src_dir is None:
        src_dir = os.path.join(HERE, "..", "figures")
    if dst_dir is None:
        dst_dir = os.path.join(src_dir, "tiff")
    os.makedirs(dst_dir, exist_ok=True)
    names = [f for f in sorted(os.listdir(src_dir)) if f.endswith(".png")]
    for name in names:
        img = Image.open(os.path.join(src_dir, name)).convert("RGB")
        out = os.path.join(dst_dir, name[:-4] + ".tif")
        img.save(out, format="TIFF", compression="tiff_lzw",
                 dpi=(dpi, dpi))
    print(f"[en] wrote {len(names)} TIFF figures to {dst_dir}")


def export_submission(src_dir=None, dst_dir=None, dpi=600):
    """Assemble separately-numbered submission figures.

    Each English figure is copied to a file named for its submission number
    (Figure1..Figure4 and SupplementalDigitalContent1..2), both as a
    high-resolution TIFF and as the vector PDF, so that figure numbers and
    file names correspond one-to-one for the Editorial Manager upload.
    """
    if src_dir is None:
        src_dir = os.path.join(HERE, "..", "figures")
    if dst_dir is None:
        dst_dir = os.path.join(src_dir, "submission")
    os.makedirs(dst_dir, exist_ok=True)
    n = 0
    for stem, target in SUBMISSION_MAP.items():
        png = os.path.join(src_dir, stem + ".png")
        if os.path.exists(png):
            img = Image.open(png).convert("RGB")
            img.save(os.path.join(dst_dir, target + ".tif"),
                     format="TIFF", compression="tiff_lzw", dpi=(dpi, dpi))
            n += 1
        pdf = os.path.join(src_dir, "pdf", stem + ".pdf")
        if os.path.exists(pdf):
            with open(pdf, "rb") as fsrc:
                data = fsrc.read()
            with open(os.path.join(dst_dir, target + ".pdf"), "wb") as fdst:
                fdst.write(data)
    print(f"[en] wrote {n} submission figures to {dst_dir}")


def main():
    generate("en")
    generate("ja")
    export_tiff()
    export_submission()


if __name__ == "__main__":
    main()
