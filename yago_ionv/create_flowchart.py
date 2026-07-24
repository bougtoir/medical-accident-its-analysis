"""
STROBE-compliant participant selection flowchart.
Generates:
  - fig_flowchart.png (English, publication-quality)
  - flowchart_counts.json (all numbers for manuscript)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json, os, re

BASE = Path(__file__).resolve().parent
FIG = BASE / "figures_strobe"
FIG.mkdir(exist_ok=True)

# ============================================================
# 1. DATA LOADING (replicate from analysis pipeline)
# ============================================================
single_file = [f for f in os.listdir(BASE) if f.startswith("single") and f.endswith(".xlsm")][0]
twin_file = [f for f in os.listdir(BASE) if f.startswith("twin") and f.endswith(".xlsx")][0]

raw_single = pd.read_excel(BASE / single_file, sheet_name="基本データ", engine="openpyxl")
raw_twin = pd.read_excel(BASE / twin_file, engine="openpyxl")

single = raw_single.copy()
twin = raw_twin.copy()

single.rename(columns={
    "術中制吐薬投与の有無": "antiemetic_any",
    "制吐薬投与タイミング(入室〜麻酔開始)": "ae_pre_anesthesia",
}, inplace=True)
excl_col = "Unnamed: 66" if "Unnamed: 66" in single.columns else single.columns[66]
single["exclusion_note"] = single[excl_col] if excl_col in single.columns else np.nan

twin.rename(columns={
    "制吐薬投与の有無": "antiemetic_any_str",
    "入室〜麻酔開始": "ae_pre_anesthesia_str",
    "メモ": "exclusion_note",
}, inplace=True)

you_mu_map = {"有": 1, "無": 0}
for src, dst in [("antiemetic_any_str", "antiemetic_any"),
                 ("ae_pre_anesthesia_str", "ae_pre_anesthesia")]:
    if src in twin.columns:
        twin[dst] = twin[src].map(you_mu_map).astype(float)

for col in ["帝王切開の既往", "高血圧合併妊娠", "妊娠高血圧症候群"]:
    if col in twin.columns and not pd.api.types.is_numeric_dtype(twin[col]):
        twin[col] = twin[col].map(you_mu_map).astype(float)

if "緊急適応疾患" in twin.columns:
    twin["emergency"] = twin["緊急適応疾患"].apply(
        lambda x: 0 if pd.isna(x) or str(x).strip() == "無" else 1)
else:
    twin["emergency"] = 0

if "緊急" in single.columns:
    single["emergency"] = single["緊急"].map({"予定": 0, "緊急": 1, "臨時": 1}).astype(float)
else:
    single["emergency"] = 0

single["twin"] = 0
twin["twin"] = 1

# Steroid
steroid_col_single = "術前1週間以内のステロイド使用" if "術前1週間以内のステロイド使用" in single.columns else "術前1週間以内のステロイド投与"
steroid_col_twin = "術前1週間以内のステロイド投与"
single.rename(columns={steroid_col_single: "preop_steroid"}, inplace=True)
twin.rename(columns={steroid_col_twin: "preop_steroid"}, inplace=True)

# Prior CS
single["prior_cs"] = pd.to_numeric(single.get("帝王切開の既往", 0), errors="coerce")
twin["prior_cs"] = pd.to_numeric(twin.get("帝王切開の既往", 0), errors="coerce")

for df in [single, twin]:
    df["antiemetic_any"] = pd.to_numeric(df["antiemetic_any"], errors="coerce")
    df["ae_pre_anesthesia"] = pd.to_numeric(df["ae_pre_anesthesia"], errors="coerce")
    df["全身麻酔"] = pd.to_numeric(df.get("全身麻酔", 0), errors="coerce")

merge_cols = ["仮ID", "手術日", "twin", "antiemetic_any", "ae_pre_anesthesia",
              "exclusion_note", "全身麻酔", "emergency", "prior_cs",
              "preop_steroid", "高血圧合併妊娠", "妊娠高血圧症候群"]
s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]
df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)

for col in merge_cols:
    if col in df_all.columns and col not in ["exclusion_note", "仮ID", "手術日"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

# ============================================================
# 2. EXCLUSION FLOW (step-by-step, mutually exclusive)
# ============================================================
n_total_raw = len(df_all)
n_single_raw = int((df_all["twin"] == 0).sum())
n_twin_raw = int((df_all["twin"] == 1).sum())

# --- Step 0: Study period filter (2014-04-01 to 2024-10-24) ---
df_all["手術日_dt"] = pd.to_datetime(df_all.get("手術日", pd.NaT), errors="coerce")
STUDY_START = pd.Timestamp("2014-04-01")
out_mask = df_all["手術日_dt"] < STUDY_START
n_out = int(out_mask.sum())
n_out_s = int((out_mask & (df_all["twin"] == 0)).sum())
n_out_t = int((out_mask & (df_all["twin"] == 1)).sum())
df_all = df_all[~out_mask].copy()

n_total = len(df_all)
n_single_total = int((df_all["twin"] == 0).sum())
n_twin_total = int((df_all["twin"] == 1).sum())

# Step-by-step exclusions applied sequentially
remaining = df_all.copy()
remaining["included"] = True
note = remaining["exclusion_note"].fillna("")

exclusion_steps = []

# 1. General anesthesia (column-based OR note-based)
mask = (remaining["全身麻酔"] == 1) | note.str.contains("全身麻酔", na=False) | \
       note.str.contains("全脊髄くも膜下麻酔疑い", na=False)
n_excl = mask.sum()
n_s = (mask & (remaining["twin"] == 0)).sum()
n_t = (mask & (remaining["twin"] == 1)).sum()
exclusion_steps.append({"reason": "General anesthesia", "reason_ja": "全身麻酔",
                        "n": int(n_excl), "n_s": int(n_s), "n_t": int(n_t)})
remaining.loc[mask, "included"] = False

# 2. SBP < 90 at admission
r = remaining[remaining["included"]]
r_note = r["exclusion_note"].fillna("")
mask_sbp = r_note.str.contains(r"SBP\s*90|入室時SBP|入室時.*血圧.*90|入室時.*収縮期.*90|入室児.*収縮期.*90|入室児.*血圧.*90", na=False, regex=True)
idx_sbp = r[mask_sbp].index
n_excl = len(idx_sbp)
n_s = int((remaining.loc[idx_sbp, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_sbp, "twin"] == 1).sum())
exclusion_steps.append({"reason": "SBP < 90 mmHg at admission", "reason_ja": "入室時SBP 90 mmHg未満",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_sbp, "included"] = False

# 3. IUFD
r = remaining[remaining["included"]]
r_note = r["exclusion_note"].fillna("")
mask_iufd = r_note.str.contains("胎児死亡|子宮内胎児死亡|1児.*死亡|児死亡|死戦期帝王切開", na=False) & \
            ~r_note.str.contains("全身麻酔", na=False)
idx_iufd = r[mask_iufd].index
n_excl = len(idx_iufd)
n_s = int((remaining.loc[idx_iufd, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_iufd, "twin"] == 1).sum())
exclusion_steps.append({"reason": "Intrauterine fetal death (IUFD)", "reason_ja": "子宮内胎児死亡（IUFD）",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_iufd, "included"] = False

# 4. Vanishing twin
r = remaining[remaining["included"]]
mask_vt = r["exclusion_note"].str.contains("vanishing", case=False, na=False)
idx_vt = r[mask_vt].index
n_excl = len(idx_vt)
n_s = int((remaining.loc[idx_vt, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_vt, "twin"] == 1).sum())
exclusion_steps.append({"reason": "Vanishing twin", "reason_ja": "Vanishing twin",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_vt, "included"] = False

# 5. Triplet
r = remaining[remaining["included"]]
mask_trip = r["exclusion_note"].str.contains("品胎", na=False)
idx_trip = r[mask_trip].index
n_excl = len(idx_trip)
n_s = int((remaining.loc[idx_trip, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_trip, "twin"] == 1).sum())
exclusion_steps.append({"reason": "Triplet pregnancy", "reason_ja": "品胎",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_trip, "included"] = False

# 6. Non-cesarean delivery
r = remaining[remaining["included"]]
mask_ncs = r["exclusion_note"].str.contains("経膣分娩|鉗子分娩", na=False)
idx_ncs = r[mask_ncs].index
n_excl = len(idx_ncs)
if n_excl > 0:
    n_s = int((remaining.loc[idx_ncs, "twin"] == 0).sum())
    n_t = int((remaining.loc[idx_ncs, "twin"] == 1).sum())
    exclusion_steps.append({"reason": "Non-cesarean delivery", "reason_ja": "帝王切開以外の分娩",
                            "n": int(n_excl), "n_s": n_s, "n_t": n_t})
    remaining.loc[idx_ncs, "included"] = False

# 7. Cardiac arrest
r = remaining[remaining["included"]]
mask_ca = r["exclusion_note"].str.contains("心肺停止|心停止", na=False)
idx_ca = r[mask_ca].index
n_excl = len(idx_ca)
if n_excl > 0:
    n_s = int((remaining.loc[idx_ca, "twin"] == 0).sum())
    n_t = int((remaining.loc[idx_ca, "twin"] == 1).sum())
    exclusion_steps.append({"reason": "Cardiac arrest", "reason_ja": "心肺停止",
                            "n": int(n_excl), "n_s": n_s, "n_t": n_t})
    remaining.loc[idx_ca, "included"] = False

# 8. Missing anesthesia data
r = remaining[remaining["included"]]
mask_nodata = r["antiemetic_any"].isna()
idx_nodata = r[mask_nodata].index
n_excl = len(idx_nodata)
n_s = int((remaining.loc[idx_nodata, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_nodata, "twin"] == 1).sum())
exclusion_steps.append({"reason": "Missing anesthesia data", "reason_ja": "麻酔データ欠損",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_nodata, "included"] = False

# After standard exclusions
df_eligible = remaining[remaining["included"]].copy()
n_eligible = len(df_eligible)
n_eligible_s = int((df_eligible["twin"] == 0).sum())
n_eligible_t = int((df_eligible["twin"] == 1).sum())

# 8. Preoperative antiemetic (prophylactic)
mask_preop_ae = df_eligible["ae_pre_anesthesia"] == 1
n_preop_ae = int(mask_preop_ae.sum())
n_preop_ae_s = int((mask_preop_ae & (df_eligible["twin"] == 0)).sum())
n_preop_ae_t = int((mask_preop_ae & (df_eligible["twin"] == 1)).sum())

df_analysis = df_eligible[~mask_preop_ae].copy()
n_analysis = len(df_analysis)
n_analysis_s = int((df_analysis["twin"] == 0).sum())
n_analysis_t = int((df_analysis["twin"] == 1).sum())

# Derive HDP
df_analysis["HDP"] = ((df_analysis["高血圧合併妊娠"] == 1) | (df_analysis["妊娠高血圧症候群"] == 1)).astype(int)

# Exclusion sensitivity subgroup
excl_sens = {}
excl_sens_mask = pd.Series(False, index=df_analysis.index)
for name, col in [("Emergency CS", "emergency"), ("Prior CS", "prior_cs"),
                  ("HDP", "HDP"), ("Preoperative steroid", "preop_steroid")]:
    m = (df_analysis[col] == 1).fillna(False)
    excl_sens[name] = {
        "n": int(m.sum()),
        "n_s": int((m & (df_analysis["twin"] == 0)).sum()),
        "n_t": int((m & (df_analysis["twin"] == 1)).sum()),
    }
    excl_sens_mask = excl_sens_mask | m

n_excl_sens = int(excl_sens_mask.sum())
n_excl_sens_s = int((excl_sens_mask & (df_analysis["twin"] == 0)).sum())
n_excl_sens_t = int((excl_sens_mask & (df_analysis["twin"] == 1)).sum())

df_subgroup = df_analysis[~excl_sens_mask].copy()
n_subgroup = len(df_subgroup)
n_subgroup_s = int((df_subgroup["twin"] == 0).sum())
n_subgroup_t = int((df_subgroup["twin"] == 1).sum())

# Total standard exclusions
n_std_excl = sum(s["n"] for s in exclusion_steps)
n_std_excl_s = sum(s["n_s"] for s in exclusion_steps)
n_std_excl_t = sum(s["n_t"] for s in exclusion_steps)

# Save all counts
flow = {
    "total_raw": {"n": n_total_raw, "n_s": n_single_raw, "n_t": n_twin_raw},
    "out_of_period": {"n": n_out, "n_s": n_out_s, "n_t": n_out_t},
    "total": {"n": n_total, "n_s": n_single_total, "n_t": n_twin_total},
    "exclusion_steps": exclusion_steps,
    "total_excluded": {"n": n_std_excl, "n_s": n_std_excl_s, "n_t": n_std_excl_t},
    "eligible": {"n": n_eligible, "n_s": n_eligible_s, "n_t": n_eligible_t},
    "preop_antiemetic": {"n": n_preop_ae, "n_s": n_preop_ae_s, "n_t": n_preop_ae_t},
    "primary_analysis": {"n": n_analysis, "n_s": n_analysis_s, "n_t": n_analysis_t},
    "exclusion_sensitivity": excl_sens,
    "exclusion_sensitivity_total": {"n": n_excl_sens, "n_s": n_excl_sens_s, "n_t": n_excl_sens_t},
    "subgroup_analysis": {"n": n_subgroup, "n_s": n_subgroup_s, "n_t": n_subgroup_t},
}

with open(BASE / "flowchart_counts.json", "w") as f:
    json.dump(flow, f, indent=2, ensure_ascii=False)

# Print summary
print("=" * 60)
print("PARTICIPANT FLOW")
print("=" * 60)
print(f"Total raw: {n_total_raw} (S={n_single_raw}, T={n_twin_raw})")
print(f"  Outside study period (<2014-04-01): {n_out} (S={n_out_s}, T={n_out_t})")
print(f"Within study period: {n_total} (S={n_single_total}, T={n_twin_total})")
for step in exclusion_steps:
    print(f"  Excluded - {step['reason']}: {step['n']} (S={step['n_s']}, T={step['n_t']})")
print(f"Eligible: {n_eligible} (S={n_eligible_s}, T={n_eligible_t})")
print(f"  Preop antiemetic: {n_preop_ae} (S={n_preop_ae_s}, T={n_preop_ae_t})")
print(f"Primary analysis: {n_analysis} (S={n_analysis_s}, T={n_analysis_t})")
print(f"  Additional exclusion: {n_excl_sens} (S={n_excl_sens_s}, T={n_excl_sens_t})")
for name, counts in excl_sens.items():
    print(f"    {name}: {counts['n']} (S={counts['n_s']}, T={counts['n_t']})")
print(f"Subgroup analysis: {n_subgroup} (S={n_subgroup_s}, T={n_subgroup_t})")

# ============================================================
# 3. STROBE FLOWCHART FIGURE (matplotlib)
# ============================================================
print("\nGenerating flowchart...")

fig, ax = plt.subplots(1, 1, figsize=(16, 26))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# Colors
BOX_MAIN = "#E8F0FE"
BOX_EXCL = "#FFF3E0"
BOX_FINAL = "#E8F5E9"
BOX_SUB = "#F3E5F5"
EDGE_MAIN = "#1565C0"
EDGE_EXCL = "#E65100"
EDGE_FINAL = "#2E7D32"
EDGE_SUB = "#6A1B9A"

def draw_box(ax, x, y, w, h, text, facecolor, edgecolor, fontsize=9, bold_first=False):
    rect = mpatches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                    boxstyle="round,pad=0.3",
                                    facecolor=facecolor, edgecolor=edgecolor,
                                    linewidth=1.8)
    ax.add_patch(rect)
    lines = text.split("\n")
    line_h = fontsize * 0.13
    total_h = (len(lines) - 1) * line_h
    for i, line in enumerate(lines):
        yy = y + total_h / 2 - i * line_h
        weight = "bold" if (i == 0 and bold_first) else "normal"
        ax.text(x, yy, line, ha="center", va="center", fontsize=fontsize, fontweight=weight)

def draw_arrow(ax, x1, y1, x2, y2, color="black"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5))

cx = 42
ex = 80

# --- Row 0: Total records in database ---
y0 = 97
draw_box(ax, cx, y0, 40, 3.5,
         f"Cesarean deliveries in database\n"
         f"(Jan 2014 – Oct 2024)\n"
         f"N = {n_total_raw:,}  (Singleton {n_single_raw:,}  /  Twin {n_twin_raw:,})",
         BOX_MAIN, EDGE_MAIN, fontsize=9, bold_first=True)

# Arrow down + date filter exclusion (right)
y_branch0 = y0 - 3.5
draw_arrow(ax, cx, y0 - 1.75, cx, y_branch0)

y_date_excl = y_branch0 - 1.5
draw_box(ax, ex, y_date_excl, 36, 3,
         f"Outside study period\n"
         f"(before Apr 2014): n = {n_out}\n"
         f"(S {n_out_s}, T {n_out_t})",
         BOX_EXCL, EDGE_EXCL, fontsize=7.5)
draw_arrow(ax, cx + 20, y_branch0, ex - 18, y_date_excl, color=EDGE_EXCL)

# --- Row 1: Within study period ---
y1 = y_branch0 - 5
draw_arrow(ax, cx, y_branch0, cx, y1 + 1.75)
draw_box(ax, cx, y1, 40, 3.5,
         f"Within study period\n"
         f"(Apr 2014 – Oct 2024)\n"
         f"N = {n_total:,}  (Singleton {n_single_total:,}  /  Twin {n_twin_total:,})",
         BOX_MAIN, EDGE_MAIN, fontsize=9, bold_first=True)

# Arrow down to exclusion branch point
y_branch1 = y1 - 3.5
draw_arrow(ax, cx, y1 - 1.75, cx, y_branch1)

# Exclusion box (right)
excl_lines = []
for step in exclusion_steps:
    excl_lines.append(f"{step['reason']}: n = {step['n']}  (S {step['n_s']}, T {step['n_t']})")
excl_text = (f"Excluded  (n = {n_std_excl})\n" +
             "\n".join(excl_lines))
excl_h = 1.5 + len(exclusion_steps) * 1.5
y_excl = y_branch1 - excl_h / 2
draw_box(ax, ex, y_excl, 36, excl_h, excl_text,
         BOX_EXCL, EDGE_EXCL, fontsize=7.5)
draw_arrow(ax, cx + 20, y_branch1, ex - 18, y_excl + excl_h/4, color=EDGE_EXCL)

# Arrow down
y2 = y_branch1 - excl_h - 2.5
draw_arrow(ax, cx, y_branch1, cx, y2 + 2.25)

# --- Row 2: Eligible ---
draw_box(ax, cx, y2, 40, 4,
         f"Eligible for analysis\n"
         f"N = {n_eligible:,}  (Singleton {n_eligible_s:,}  /  Twin {n_eligible_t:,})",
         BOX_MAIN, EDGE_MAIN, fontsize=9, bold_first=True)

# Preop antiemetic exclusion (right)
y_branch2 = y2 - 4
draw_arrow(ax, cx, y2 - 2, cx, y_branch2)
y_preop = y_branch2 - 1.5
draw_box(ax, ex, y_preop, 36, 3.5,
         f"Prophylactic antiemetic\nbefore anesthesia: n = {n_preop_ae}\n"
         f"(S {n_preop_ae_s}, T {n_preop_ae_t})",
         BOX_EXCL, EDGE_EXCL, fontsize=7.5)
draw_arrow(ax, cx + 20, y_branch2, ex - 18, y_preop, color=EDGE_EXCL)

# Arrow down
y3 = y_branch2 - 6
draw_arrow(ax, cx, y_branch2, cx, y3 + 2.25)

# --- Row 3: Primary analysis cohort ---
draw_box(ax, cx, y3, 40, 4.5,
         f"Primary analysis cohort\n"
         f"N = {n_analysis:,}  (Singleton {n_analysis_s:,}  /  Twin {n_analysis_t:,})",
         BOX_FINAL, EDGE_FINAL, fontsize=9, bold_first=True)

# --- Split: Singleton / Twin ---
y4 = y3 - 7
draw_box(ax, 22, y4, 20, 4,
         f"Singleton\nn = {n_analysis_s:,}",
         BOX_FINAL, EDGE_FINAL, fontsize=9, bold_first=True)
draw_arrow(ax, cx - 12, y3 - 2.25, 22, y4 + 2)

draw_box(ax, 62, y4, 20, 4,
         f"Twin\nn = {n_analysis_t:,}",
         BOX_FINAL, EDGE_FINAL, fontsize=9, bold_first=True)
draw_arrow(ax, cx + 12, y3 - 2.25, 62, y4 + 2)

# --- Row 4: Sensitivity subgroup ---
y_branch3 = y4 - 5.5
draw_arrow(ax, cx, y4 - 2, cx, y_branch3)

# Additional exclusion box (right)
sens_lines = []
for name, counts in excl_sens.items():
    sens_lines.append(f"{name}: n = {counts['n']}")
sens_text = (f"Additional exclusion for\nsensitivity analysis\n"
             f"(n = {n_excl_sens}, with overlap)\n" +
             "\n".join(sens_lines))
y_sens = y_branch3 - 3
draw_box(ax, ex, y_sens, 36, 6.5,
         sens_text, BOX_EXCL, EDGE_EXCL, fontsize=7.5)
draw_arrow(ax, cx + 20, y_branch3, ex - 18, y_sens + 2, color=EDGE_EXCL)

# Arrow down
y5 = y_branch3 - 8
draw_arrow(ax, cx, y_branch3, cx, y5 + 2.5)

# Subgroup box
draw_box(ax, cx, y5, 40, 5,
         f"Sensitivity analysis subgroup\n"
         f"(Elective, low-risk)\n"
         f"N = {n_subgroup:,}  (Singleton {n_subgroup_s:,}  /  Twin {n_subgroup_t:,})",
         BOX_SUB, EDGE_SUB, fontsize=9, bold_first=True)

# --- Split sensitivity: Singleton / Twin ---
y6 = y5 - 6.5
draw_box(ax, 22, y6, 20, 4,
         f"Singleton\nn = {n_subgroup_s:,}",
         BOX_SUB, EDGE_SUB, fontsize=9, bold_first=True)
draw_arrow(ax, cx - 12, y5 - 2.5, 22, y6 + 2)

draw_box(ax, 62, y6, 20, 4,
         f"Twin\nn = {n_subgroup_t:,}",
         BOX_SUB, EDGE_SUB, fontsize=9, bold_first=True)
draw_arrow(ax, cx + 12, y5 - 2.5, 62, y6 + 2)

# Title
ax.text(50, 99, "Figure 1.  STROBE Flow Diagram — Participant Selection",
        ha="center", va="center", fontsize=14, fontweight="bold")

plt.savefig(FIG / "fig_flowchart.png", dpi=300, bbox_inches="tight",
            facecolor="white", edgecolor="none")
plt.close()
print(f"Flowchart saved to {FIG / 'fig_flowchart.png'}")

print("\nDone.")
