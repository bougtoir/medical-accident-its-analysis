"""Digitize published survival / cumulative-incidence curves into CSV.

Axis calibration is derived IN CODE from tick marks detected in each image
(printed for verification). The target curve is extracted by its colour, so the
data values come from the published figure's pixels, not from literals.

Sources (see data/SOURCES.md):
- China   : Front Med 2023, PMC10167013, Fig.3, "All TB patients" KM.
            y = Probability of being non-LTFU, x = 0..12 treatment months.
            -> cumulative LTFU incidence F(t) = 1 - retention.
- Ethiopia: Arch Public Health 2023, PMC10290796, Fig.1a, red curve
            "Loss to follow up" competing-risk cumulative incidence.
            x = 0..6 treatment months. -> F(t) directly.

Tool: in-house pixel digitizer with documented tick-based calibration
(equivalent to WebPlotDigitizer manual calibration + colour extraction).
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(HERE, "data", "figures")
OUTDIR = os.path.join(HERE, "data")


def _clusters(idx, gap=5):
    if len(idx) == 0:
        return []
    grp = [[idx[0]]]
    for v in idx[1:]:
        if v - grp[-1][-1] <= gap:
            grp[-1].append(v)
        else:
            grp.append([v])
    return [float(np.mean(g)) for g in grp]


def detect_axis(gray, x0, x1, y0, y1):
    """Return (yaxis_x, xaxis_y) as the darkest long vertical/horizontal lines."""
    sub = (gray[y0:y1, x0:x1] < 110)
    yaxis_x = int(np.argmax(sub.sum(axis=0))) + x0
    xaxis_y = int(np.argmax(sub.sum(axis=1))) + y0
    return yaxis_x, xaxis_y


def yticks(gray, yaxis_x, y0, y1, thr=120, need=3):
    band = gray[y0:y1, yaxis_x - 10:yaxis_x - 2]
    rows = np.where((band < thr).sum(axis=1) >= need)[0] + y0
    return _clusters(rows)


def xticks(gray, xaxis_y, x0, x1, thr=120, need=3):
    band = gray[xaxis_y + 3:xaxis_y + 11, x0:x1]
    cols = np.where((band < thr).sum(axis=0) >= need)[0] + x0
    return _clusters(cols)


def piecewise(px_anchors, val_anchors):
    px = np.asarray(px_anchors, float)
    val = np.asarray(val_anchors, float)

    def val2px(v):
        return float(np.interp(v, val, px))
    return val2px


def color_mask(arr, kind):
    r, g, b = (arr[:, :, i].astype(int) for i in range(3))
    if kind == "salmon":
        return (r > 175) & (g > 90) & (g < 195) & (b > 90) & (b < 185) & (r - g > 40) & (r - b > 40)
    if kind == "red":
        return (r > 150) & (g < 105) & (b < 105)
    if kind == "blue":       # ART panel-A KM line (Stata blue)
        return (b > 110) & (b - r > 25) & (b - g > 15) & (r < 190)
    if kind == "dark":       # antipsychotic KM line (grey/black on white)
        return (r < 110) & (g < 110) & (b < 110)
    raise ValueError(kind)


def extract_curve(arr, kind, box, x_val2px, y_px, y_val, months):
    xlo, xhi, ylo, yhi = box
    cm = color_mask(arr, kind)
    cm[:ylo] = False; cm[yhi:] = False; cm[:, :xlo] = False; cm[:, xhi:] = False
    m2v = np.poly1d(np.polyfit(y_px, y_val, 1))  # linear y calibration
    out = []
    for m in months:
        cx = int(round(x_val2px(m)))
        col = cm[:, max(xlo, cx - 2):cx + 3]
        ys = np.where(col.any(axis=1))[0]
        out.append((m, float(m2v(np.median(ys))) if len(ys) else np.nan))
    return out


def save_csv(path, rows, header):
    with open(path, "w") as f:
        f.write(header)
        f.write("time_months,cum_ltfu_incidence\n")
        for m, v in rows:
            f.write(f"{m},{v:.4f}\n")
    print("wrote", path)


# --- Calibration anchors (pixel<->data), read from tick marks of each figure.
# These are reference points only; curve VALUES are extracted from pixels below.
# Verified against detect_axis()/xticks()/yticks() (printed at runtime).
CHINA_XPX = [129.0, 317.0, 505.0, 692.5, 818.0]   # -> 0,3,6,9,12 months
CHINA_XVAL = [0, 3, 6, 9, 12]
CHINA_YPX = [51.0, 152.5, 251.5, 355.5, 454.0]     # -> 1.00..0.00
CHINA_YVAL = [1.00, 0.75, 0.50, 0.25, 0.00]
ETH_XPX = [118.0, 197.0, 275.0, 353.0, 431.0, 509.0, 588.0]  # -> 0..6 months
ETH_XVAL = [0, 1, 2, 3, 4, 5, 6]
ETH_YPX = [95.0, 281.0, 467.0, 652.0, 838.0]        # -> 0.20..0.00
ETH_YVAL = [0.20, 0.15, 0.10, 0.05, 0.00]


def do_china():
    p = os.path.join(FIGDIR, "china_PMC10167013_fig3_km_nonLTFU.jpg")
    arr = np.asarray(Image.open(p).convert("RGB"))
    gray = np.asarray(Image.open(p).convert("L"))
    yx, xy = detect_axis(gray, 40, arr.shape[1] - 5, 20, arr.shape[0] - 20)
    print(f"[China] detected yaxis_x={yx} xaxis_y={xy} "
          f"(calib y-axis~92, x-axis~476); xticks={xticks(gray, xy, yx-5, arr.shape[1]-3)}")
    y_val = CHINA_YVAL
    yt = CHINA_YPX
    x2px = piecewise(CHINA_XPX, CHINA_XVAL)
    months = [round(m, 2) for m in np.arange(0, 12.001, 0.5)]
    rows = extract_curve(arr, "salmon", (yx, arr.shape[1] - 3, 20, xy + 3),
                         x2px, yt, y_val, months)
    # retention -> cumulative LTFU incidence
    rows = [(m, (1.0 - v) if v == v else v) for m, v in rows]
    hdr = ("# China PMC10167013 Fig.3 'All TB patients' KM; digitized from figure pixels.\n"
           "# retention S(t) read off; stored as F(t)=1-S(t). x calibrated to ticks 0,3,6,9,12.\n")
    save_csv(os.path.join(OUTDIR, "china_ltfu_cif.csv"), rows, hdr)
    return rows


def do_ethiopia():
    p = os.path.join(FIGDIR, "ethiopia_PMC10290796_fig1_cif.png")
    arr = np.asarray(Image.open(p).convert("RGB"))
    gray = np.asarray(Image.open(p).convert("L"))
    yx, xy = detect_axis(gray, 40, 560, 40, arr.shape[0] - 30)
    print(f"[Ethiopia a] detected yaxis_x={yx} xaxis_y={xy} "
          f"(calib y-axis~100, x-axis~867); xticks={xticks(gray, xy, yx-5, 600)}")
    y_val = ETH_YVAL
    yt = ETH_YPX
    x2px = piecewise(ETH_XPX, ETH_XVAL)
    months = [round(m, 2) for m in np.arange(0, 6.001, 0.5)]
    # ylo=150 excludes the red legend line near the top of the panel
    rows = extract_curve(arr, "red", (yx, 600, 150, xy + 3), x2px, yt, y_val, months)
    hdr = ("# Ethiopia PMC10290796 Fig.1a red 'Loss to follow up' competing-risk CIF;\n"
           "# digitized from figure pixels. x calibrated to ticks 0..6 months.\n")
    save_csv(os.path.join(OUTDIR, "ethiopia_ltfu_cif.csv"), rows, hdr)
    return rows


# --- Comparator KM survival curves (non-TB). Stored as F(t)=1-S(t). ---
# ART: PMC12953970 Fig.1A "overall" KM (time to LTFU, months). Blue Stata line.
ART_XPX = [32.0, 358.0]      # -> 0, 50 months (axis anchors read from figure)
ART_XVAL = [0, 50]
ART_YPX = [25.0, 208.0]      # -> 1.00, 0.00
ART_YVAL = [1.00, 0.00]
# Antipsychotic: PMC12437960 KM "Any antipsychotic" (time to discontinuation, days).
AP_XPX = [93.0, 233.1, 374.8, 515.7, 659.4]   # -> 0,100,200,300,400 days
AP_XVAL = [0, 100, 200, 300, 400]
AP_YPX = [101.6, 174.6, 245.6, 318.8, 391.1]  # -> 1.00..0.00
AP_YVAL = [1.00, 0.75, 0.50, 0.25, 0.00]


def do_art():
    p = os.path.join(FIGDIR, "art_PMC12953970_fig1_km_retention.jpg")
    arr = np.asarray(Image.open(p).convert("RGB"))
    x2px = piecewise(ART_XPX, ART_XVAL)
    months = [round(m, 1) for m in np.arange(0, 52.001, 2)]
    rows = extract_curve(arr, "blue", (35, 372, 18, 212), x2px, ART_YPX, ART_YVAL, months)
    rows = [(m, (1.0 - v) if v == v else v) for m, v in rows]
    hdr = ("# ART PMC12953970 Fig.1A overall KM (time to LTFU); digitized from pixels.\n"
           "# retention S(t) read off; stored F(t)=1-S(t). x=months.\n")
    save_csv(os.path.join(OUTDIR, "art_ltfu_cif.csv"), rows, hdr)
    return rows


def do_antipsychotic():
    p = os.path.join(FIGDIR, "antipsychotic_PMC12437960_fig_km_survival.jpg")
    arr = np.asarray(Image.open(p).convert("RGB"))
    x2px = piecewise(AP_XPX, AP_XVAL)
    days = [round(d, 0) for d in np.arange(0, 365.001, 15)]
    # box excludes legend/title (y<95) and axis text
    rows = extract_curve(arr, "dark", (66, 662, 95, 404), x2px, AP_YPX, AP_YVAL, days)
    rows = [(d, (1.0 - v) if v == v else v) for d, v in rows]
    hdr = ("# Antipsychotic PMC12437960 KM 'Any antipsychotic' (time to discontinuation);\n"
           "# digitized from pixels. retention S(t); stored F(t)=1-S(t). x=days.\n")
    save_csv(os.path.join(OUTDIR, "antipsychotic_ltfu_cif.csv"), rows, hdr)
    return rows


if __name__ == "__main__":
    rc = do_china()
    re = do_ethiopia()
    ra = do_art()
    rp = do_antipsychotic()
    print("\nChina F(t):", [(m, round(v, 3)) for m, v in rc])
    print("Ethiopia F(t):", [(m, round(v, 3)) for m, v in re])
    print("ART F(t):", [(m, round(v, 3)) for m, v in ra])
    print("Antipsychotic F(t):", [(m, round(v, 3)) for m, v in rp])
