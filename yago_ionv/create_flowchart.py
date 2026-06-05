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

merge_cols = ["仮ID", "twin", "antiemetic_any", "ae_pre_anesthesia",
              "exclusion_note", "全身麻酔", "emergency", "prior_cs",
              "preop_steroid", "高血圧合併妊娠", "妊娠高血圧症候群"]
s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]
df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)

for col in merge_cols:
    if col in df_all.columns and col not in ["exclusion_note", "仮ID"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

# ============================================================
# 2. EXCLUSION FLOW (step-by-step, mutually exclusive)
# ============================================================
n_total = len(df_all)
n_single_total = int((df_all["twin"] == 0).sum())
n_twin_total = int((df_all["twin"] == 1).sum())

# Step-by-step exclusions applied sequentially
remaining = df_all.copy()
remaining["included"] = True

exclusion_steps = []

# 1. General anesthesia
mask = remaining["全身麻酔"] == 1
n_excl = mask.sum()
n_s = (mask & (remaining["twin"] == 0)).sum()
n_t = (mask & (remaining["twin"] == 1)).sum()
exclusion_steps.append({"reason": "General anesthesia", "reason_ja": "全身麻酔",
                        "n": int(n_excl), "n_s": int(n_s), "n_t": int(n_t)})
remaining.loc[mask, "included"] = False

# 2. SBP < 90 at admission
r = remaining[remaining["included"]]
mask_sbp = r["exclusion_note"].str.contains("SBP90|入室時SBP", na=False)
idx_sbp = r[mask_sbp].index
n_excl = len(idx_sbp)
n_s = int((remaining.loc[idx_sbp, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_sbp, "twin"] == 1).sum())
exclusion_steps.append({"reason": "SBP < 90 mmHg at admission", "reason_ja": "入室時SBP 90 mmHg未満",
                        "n": int(n_excl), "n_s": n_s, "n_t": n_t})
remaining.loc[idx_sbp, "included"] = False

# 3. IUFD
r = remaining[remaining["included"]]
mask_iufd = r["exclusion_note"].str.contains("胎児死亡|死亡", na=False) & ~r["exclusion_note"].str.contains("全身麻酔", na=False)
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

# 6. Other exclusion (generic)
r = remaining[remaining["included"]]
mask_gen = r["exclusion_note"].str.contains("除外", na=False)
idx_gen = r[mask_gen].index
n_excl = len(idx_gen)
n_s = int((remaining.loc[idx_gen, "twin"] == 0).sum())
n_t = int((remaining.loc[idx_gen, "twin"] == 1).sum())
if n_excl > 0:
    exclusion_steps.append({"reason": "Other exclusion criteria", "reason_ja": "その他の除外基準",
                            "n": int(n_excl), "n_s": n_s, "n_t": n_t})
    remaining.loc[idx_gen, "included"] = False

# 7. Missing anesthesia data
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
print(f"Total: {n_total} (S={n_single_total}, T={n_twin_total})")
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

fig, ax = plt.subplots(1, 1, figsize=(16, 22))
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

# --- Row 1: Total assessed ---
y1 = 95
draw_box(ax, cx, y1, 40, 4.5,
         f"Cesarean deliveries assessed for eligibility\n"
         f"(Apr 2014 – Oct 2024)\n"
         f"N = {n_total:,}  (Singleton {n_single_total:,}  /  Twin {n_twin_total:,})",
         BOX_MAIN, EDGE_MAIN, fontsize=9, bold_first=True)

# Arrow down to exclusion branch point
y_branch1 = y1 - 5
draw_arrow(ax, cx, y1 - 2.25, cx, y_branch1)

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
