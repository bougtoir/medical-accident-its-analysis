"""
Sensitivity analysis: Alternative IONV definitions (C–H)

Builds on the primary analysis cohort (df_analysis from analysis.py).
For each definition, performs:
  1. Singleton vs twin rate comparison (chi-square / Fisher)
  2. Multivariable logistic regression (same covariates as primary)
  3. Summary forest plot comparing twin aOR across definitions

Definitions:
  A (primary):  Antiemetic before delivery only            [from analysis.py]
  B (secondary): Any antiemetic (anesthesia→exit)          [from analysis.py]
  C: Post-delivery IONV only (ae_post_delivery=1 AND ae_to_delivery≠1)
  D: Severe IONV (≥2 different antiemetic drugs used)
  E: 5-HT3 antagonist-based (ondansetron or granisetron only)
  F: Excluding dexamethasone-only users from primary
  G: Antiemetic drug count (0,1,2,3+) — ordinal logistic
  H: Hypotension-stratified (primary IONV in hypo+ vs hypo− subgroups)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
from collections import OrderedDict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE = Path(__file__).resolve().parent
FIG = BASE / "figures"
TAB = BASE / "tables"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

# ============================================================
# 1. LOAD DATA (same pipeline as analysis.py)
# ============================================================
print("=" * 60)
print("SENSITIVITY ANALYSIS: Loading data")
print("=" * 60)

import os
single_file = [f for f in os.listdir(BASE) if f.startswith("single") and f.endswith(".xlsm")][0]
twin_file = [f for f in os.listdir(BASE) if f.startswith("twin") and f.endswith(".xlsx")][0]

raw_single = pd.read_excel(BASE / single_file, sheet_name="基本データ", engine="openpyxl")
raw_twin = pd.read_excel(BASE / twin_file, engine="openpyxl")

# --- Harmonize (same as analysis.py) ---
single = raw_single.copy()
single.rename(columns={
    "手術所要": "手術時間_min",
    "麻酔所要": "麻酔時間_min",
    "総出血g(ml) ": "出血量_ml",
    "術中制吐薬投与の有無": "antiemetic_any",
    "制吐薬投与タイミング(入室〜麻酔開始)": "ae_pre_anesthesia",
    "術中制吐薬投与タイミング(麻酔開始〜胎児娩出)": "ae_to_delivery",
    "術中制吐薬投与タイミング(胎児娩出〜退室)": "ae_post_delivery",
    "低血圧回数(回)": "hypotension_count",
    "術中メトクロプラミド投与(mg)": "metoclopramide_mg",
    "術中ドロペリドール投与(mg)": "droperidol_mg",
    "術中オンダンセトロン投与(mg)": "ondansetron_mg",
    "術中グラニセトロン投与(mg)": "granisetron_mg",
    "術中ノバミン投与(mg)": "novamin_mg",
    "術中アタラックスP投与(mg)": "atarax_p_mg",
    "術中デカドロン投与(mg)": "dexamethasone_mg",
    "術前24時間以内の制吐薬投与": "preop_antiemetic",
    "術中輸液量(ml)": "輸液量_ml",
    "術中昇圧薬持続投与の有無": "vasopressor_continuous",
    "術中エフェドリン投与(mg)": "ephedrine_mg",
    "術中フェニレフリン投与(mg)": "phenylephrine_mg",
    "脊髄くも膜下への高比重ブピバカイン投与(mg)": "bupivacaine_mg",
    "脊髄くも膜下へのフェンタニル投与(μg)": "fentanyl_ug",
    "脊髄くも膜下へのモルヒネ投与(mg)": "morphine_mg",
    "術中ディプリバン投与(mg)": "propofol_mg",
    "術中ミダゾラム投与(mg)": "midazolam_mg",
    "術中デクスメデトミジン投与(μg)": "dexmedetomidine_ug",
}, inplace=True)

excl_col = "Unnamed: 66" if "Unnamed: 66" in single.columns else single.columns[66]
single["exclusion_note"] = single[excl_col] if excl_col in single.columns else np.nan

twin = raw_twin.copy()
twin.rename(columns={
    "手術時間(min)": "手術時間_min",
    "麻酔時間(min)": "麻酔時間_min",
    "出血量(ml)": "出血量_ml",
    "輸液量(ml)": "輸液量_ml",
    "制吐薬投与の有無": "antiemetic_any_str",
    "入室〜麻酔開始": "ae_pre_anesthesia_str",
    "麻酔開始〜胎児娩出": "ae_to_delivery_str",
    "胎児娩出〜退室": "ae_post_delivery_str",
    "低血圧(回)": "hypotension_count",
    "メトクロプラミド(mg)": "metoclopramide_mg",
    "ドロペリドール(mg)": "droperidol_mg",
    "オンダンセトロン(mg)": "ondansetron_mg",
    "グラニセトロン(mg)": "granisetron_mg",
    "ノバミン(mg)": "novamin_mg",
    "アタラックスP(mg)": "atarax_p_mg",
    "デカドロン(mg)": "dexamethasone_mg",
    "術前24時間以内の制吐薬投与": "preop_antiemetic",
    "昇圧持続投与": "vasopressor_continuous",
    "エフェドリン(mg)": "ephedrine_mg",
    "フェニレフリン(mg)": "phenylephrine_mg",
    "脊髄くも膜下への高比重ブピバカイン(mg)": "bupivacaine_mg",
    "脊髄くも膜下へのフェンタニル(μg )": "fentanyl_ug",
    "脊髄くも膜下へのモルヒネ(mg)": "morphine_mg",
    "ディプリバン(mg)": "propofol_mg",
    "ミダゾラム(mg)": "midazolam_mg",
    "デクスメデトミジン": "dexmedetomidine_ug",
    "メモ": "exclusion_note",
}, inplace=True)

you_mu_map = {"有": 1, "無": 0}
for src, dst in [("antiemetic_any_str", "antiemetic_any"),
                 ("ae_pre_anesthesia_str", "ae_pre_anesthesia"),
                 ("ae_to_delivery_str", "ae_to_delivery"),
                 ("ae_post_delivery_str", "ae_post_delivery")]:
    if src in twin.columns:
        twin[dst] = twin[src].map(you_mu_map).astype(float)

for col in ["帝王切開の既往", "vasopressor_continuous", "高血圧合併妊娠", "妊娠高血圧症候群",
            "術前24時間以内の降圧薬使用", "preop_antiemetic"]:
    if col in twin.columns and not pd.api.types.is_numeric_dtype(twin[col]):
        twin[col] = twin[col].map(you_mu_map).astype(float)

if "緊急適応疾患" in twin.columns:
    twin["emergency"] = twin["緊急適応疾患"].apply(
        lambda x: 0 if pd.isna(x) or str(x).strip() == "無" else 1
    )
else:
    twin["emergency"] = 0

if "緊急" in single.columns:
    single["emergency"] = single["緊急"].map({"予定": 0, "緊急": 1, "臨時": 1}).astype(float)
else:
    single["emergency"] = 0

single["twin"] = 0
twin["twin"] = 1

import re as re_mod

def parse_ga_weeks(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    m = re_mod.match(r"(\d+)w(\d+)d?", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 7
    try:
        return float(s)
    except ValueError:
        return np.nan

for df in [single, twin]:
    df["GA_weeks"] = df["妊娠週数(週)"].apply(parse_ga_weeks)

def time_to_min(val):
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, pd.Timedelta):
        return val.total_seconds() / 60
    if isinstance(val, str):
        parts = val.split(":")
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        except ValueError:
            return np.nan
    return np.nan

single["手術時間_min"] = single["手術時間_min"].apply(time_to_min)
single["麻酔時間_min"] = single["麻酔時間_min"].apply(time_to_min)
twin["手術時間_min"] = pd.to_numeric(twin["手術時間_min"], errors="coerce")
twin["麻酔時間_min"] = pd.to_numeric(twin["麻酔時間_min"], errors="coerce")

for df in [single, twin]:
    for col in ["年齢(歳)", "身長(cm)", "体重(kg)", "hypotension_count",
                "全身麻酔", "硬膜外麻酔", "脊髄くも膜下麻酔",
                "帝王切開の既往", "高血圧合併妊娠", "妊娠高血圧症候群",
                "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery",
                "preop_antiemetic", "vasopressor_continuous"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

for df in [single, twin]:
    h = pd.to_numeric(df["身長(cm)"], errors="coerce") / 100
    w = pd.to_numeric(df["体重(kg)"], errors="coerce")
    df["BMI"] = w / (h ** 2)

steroid_col_single = "術前1週間以内のステロイド使用" if "術前1週間以内のステロイド使用" in single.columns else "術前1週間以内のステロイド投与"
steroid_col_twin = "術前1週間以内のステロイド投与"
single.rename(columns={steroid_col_single: "preop_steroid"}, inplace=True)
twin.rename(columns={steroid_col_twin: "preop_steroid"}, inplace=True)

merge_cols = [
    "仮ID", "手術日", "年齢(歳)", "身長(cm)", "体重(kg)", "BMI",
    "GA_weeks", "高血圧合併妊娠", "妊娠高血圧症候群",
    "術前24時間以内の降圧薬使用", "preop_steroid", "preop_antiemetic",
    "帝王切開の既往", "子宮脱転", "emergency",
    "全身麻酔", "硬膜外麻酔", "脊髄くも膜下麻酔",
    "手術時間_min", "麻酔時間_min",
    "出血量_ml", "輸液量_ml",
    "hypotension_count",
    "vasopressor_continuous", "ephedrine_mg", "phenylephrine_mg",
    "bupivacaine_mg", "fentanyl_ug", "morphine_mg",
    "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery",
    "metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
    "novamin_mg", "atarax_p_mg", "dexamethasone_mg",
    "exclusion_note", "twin",
]

s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]
df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)

for col in ["全身麻酔", "硬膜外麻酔", "脊髄くも膜下麻酔", "高血圧合併妊娠", "妊娠高血圧症候群",
            "帝王切開の既往", "preop_steroid", "preop_antiemetic",
            "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery"]:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

df_all["出血量_ml"] = pd.to_numeric(df_all["出血量_ml"], errors="coerce")
df_all["hypotension_count"] = pd.to_numeric(df_all["hypotension_count"], errors="coerce")

numeric_cols = [
    "年齢(歳)", "身長(cm)", "体重(kg)", "BMI",
    "手術時間_min", "麻酔時間_min", "出血量_ml", "輸液量_ml",
    "hypotension_count", "vasopressor_continuous",
    "ephedrine_mg", "phenylephrine_mg", "bupivacaine_mg", "fentanyl_ug", "morphine_mg",
    "metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
    "novamin_mg", "atarax_p_mg", "dexamethasone_mg", "emergency", "子宮脱転",
]
for col in numeric_cols:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

# Study period filter (2014-04-01 to 2024-10-24)
df_all["手術日_dt"] = pd.to_datetime(df_all["手術日"], errors="coerce")
STUDY_START = pd.Timestamp("2014-04-01")
df_all = df_all[~(df_all["手術日_dt"] < STUDY_START)].copy()
print(f"After date filter (>={STUDY_START.date()}): {len(df_all)}")

# Exclusions (updated: GA from column OR note)
note = df_all["exclusion_note"].fillna("")
ga_mask = (df_all["全身麻酔"] == 1) | note.str.contains("全身麻酔", na=False) | \
          note.str.contains("全脊髄くも膜下麻酔疑い", na=False)
sbp_mask = note.str.contains(r"SBP\s*90|入室時SBP|入室時.*血圧.*90|入室時.*収縮期.*90|入室児.*収縮期.*90|入室児.*血圧.*90", na=False, regex=True)
iufd_mask = note.str.contains("胎児死亡|子宮内胎児死亡|1児.*死亡|児死亡|死戦期帝王切開", na=False) & \
            ~note.str.contains("全身麻酔", na=False)
vt_mask = note.str.contains("vanishing", case=False, na=False)
triplet_mask = note.str.contains("品胎", na=False)
non_cs_mask = note.str.contains("経膣分娩|鉗子分娩", na=False)
cardiac_mask = note.str.contains("心肺停止|心停止", na=False)
generic_exclude_mask = note.str.contains("除外", na=False)
no_data_mask = df_all["antiemetic_any"].isna()
all_exclude = ga_mask | sbp_mask | iufd_mask | vt_mask | triplet_mask | \
              non_cs_mask | cardiac_mask | no_data_mask | generic_exclude_mask
df = df_all[~all_exclude].copy()

df["ionv_primary"] = (df["ae_to_delivery"] == 1).astype(int)
df["ionv_secondary"] = ((df["ae_to_delivery"] == 1) | (df["ae_post_delivery"] == 1)).astype(int)

df_analysis = df[df["ae_pre_anesthesia"] != 1].copy()
print(f"Analysis cohort: {len(df_analysis)} ({(df_analysis['twin']==0).sum()} single + {(df_analysis['twin']==1).sum()} twin)")

# Derived variables
df_analysis["HDP"] = ((df_analysis["高血圧合併妊娠"] == 1) | (df_analysis["妊娠高血圧症候群"] == 1)).astype(int)
df_analysis["hypotension"] = (df_analysis["hypotension_count"] >= 1).astype(int).where(
    df_analysis["hypotension_count"].notna(), np.nan)
df_analysis["epidural"] = pd.to_numeric(df_analysis["硬膜外麻酔"], errors="coerce")
df_analysis["prior_cs"] = pd.to_numeric(df_analysis["帝王切開の既往"], errors="coerce")

# ============================================================
# 2. DEFINE SENSITIVITY OUTCOMES (C–H)
# ============================================================
print("\n" + "=" * 60)
print("DEFINING SENSITIVITY OUTCOMES")
print("=" * 60)

DRUGS = ["metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
         "novamin_mg", "atarax_p_mg", "dexamethasone_mg"]

for d in DRUGS:
    df_analysis[d] = pd.to_numeric(df_analysis[d], errors="coerce")

# C: Post-delivery IONV only
df_analysis["ionv_C"] = ((df_analysis["ae_post_delivery"] == 1) &
                          (df_analysis["ae_to_delivery"] != 1)).astype(int)

# D: Severe IONV (≥2 different drugs)
df_analysis["drug_count"] = sum(
    (df_analysis[d].fillna(0) > 0).astype(int) for d in DRUGS
)
df_analysis["ionv_D"] = (df_analysis["drug_count"] >= 2).astype(int)

# E: 5-HT3 antagonist-based
df_analysis["ionv_E"] = (
    (df_analysis["ondansetron_mg"].fillna(0) > 0) |
    (df_analysis["granisetron_mg"].fillna(0) > 0)
).astype(int)

# F: Excluding dexamethasone-only
dex_only = (
    (df_analysis["dexamethasone_mg"].fillna(0) > 0) &
    (sum((df_analysis[d].fillna(0) > 0).astype(int)
         for d in DRUGS if d != "dexamethasone_mg") == 0)
)
df_analysis["ionv_F"] = (df_analysis["ionv_primary"] == 1).astype(int)
df_analysis.loc[dex_only & (df_analysis["ionv_primary"] == 1), "ionv_F"] = 0

# G: Drug count as outcome (continuous for Poisson)
# Already have drug_count

# Print summary
s = df_analysis[df_analysis["twin"] == 0]
t = df_analysis[df_analysis["twin"] == 1]

definitions = OrderedDict([
    ("A", ("ionv_primary", "Primary: before delivery")),
    ("B", ("ionv_secondary", "Secondary: any IONV (anesthesia→exit)")),
    ("C", ("ionv_C", "Post-delivery only")),
    ("D", ("ionv_D", "Severe (≥2 drugs)")),
    ("E", ("ionv_E", "5-HT3 antagonist")),
    ("F", ("ionv_F", "Excl. dexamethasone-only")),
])

print(f"\n{'Def':>3} {'Label':<30} {'Single n/N (%)':<22} {'Twin n/N (%)':<22} {'P':>8}")
print("-" * 90)
for key, (col, label) in definitions.items():
    s_n = int(s[col].sum())
    t_n = int(t[col].sum())
    s_pct = 100 * s_n / len(s)
    t_pct = 100 * t_n / len(t)
    table = np.array([[s_n, len(s) - s_n], [t_n, len(t) - t_n]])
    row_totals = table.sum(axis=1)
    col_totals = table.sum(axis=0)
    expected = np.outer(row_totals, col_totals) / table.sum()
    if expected.min() < 5:
        _, p = stats.fisher_exact(table)
    else:
        _, p, _, _ = stats.chi2_contingency(table, correction=False)
    print(f"  {key} {label:<30} {s_n}/{len(s)} ({s_pct:5.1f}%)     "
          f"{t_n}/{len(t)} ({t_pct:5.1f}%)     {p:.4f}")

# G: Drug count summary
print(f"\n  G {'Drug count (mean±SD)':<30} "
      f"{s['drug_count'].mean():.2f}±{s['drug_count'].std():.2f}          "
      f"{t['drug_count'].mean():.2f}±{t['drug_count'].std():.2f}")
stat_g, p_g = stats.mannwhitneyu(s["drug_count"].dropna(), t["drug_count"].dropna(),
                                  alternative="two-sided")
print(f"    Mann-Whitney U P = {p_g:.4f}")

# ============================================================
# 3. MULTIVARIABLE LOGISTIC REGRESSION (C–F)
# ============================================================
print("\n" + "=" * 60)
print("MULTIVARIABLE LOGISTIC REGRESSION — SENSITIVITY")
print("=" * 60)

covariates = [
    "twin", "年齢(歳)", "BMI", "GA_weeks", "emergency",
    "prior_cs", "HDP", "epidural", "手術時間_min", "hypotension",
]

label_map = {
    "twin": "Twin pregnancy",
    "年齢(歳)": "Age (per year)",
    "BMI": "BMI (per kg/m²)",
    "GA_weeks": "GA (per week)",
    "emergency": "Emergency CS",
    "prior_cs": "Prior CS",
    "HDP": "HDP",
    "epidural": "Epidural anesthesia",
    "手術時間_min": "Surgery time (per min)",
    "hypotension": "Hypotension (SBP < 90)",
}

sensitivity_results = []

for key, (col, label) in definitions.items():
    df_model = df_analysis[covariates + [col]].dropna()
    X = sm.add_constant(df_model[covariates].astype(float))
    y = df_model[col].astype(float)

    n_events = int(y.sum())
    if n_events < 5:
        print(f"\n  {key} ({label}): Too few events ({n_events}), skipping regression")
        sensitivity_results.append({
            "Definition": key, "Label": label,
            "n": len(df_model), "Events": n_events,
            "twin_OR": np.nan, "twin_CI_lower": np.nan, "twin_CI_upper": np.nan,
            "twin_P": np.nan, "AIC": np.nan,
        })
        continue

    # Try full model first; if singular, fall back to reduced covariates
    covs_to_use = covariates
    try:
        model = sm.Logit(y, X).fit(disp=0, maxiter=200)
    except Exception:
        # Reduced model: twin + age + BMI + GA + emergency + hypotension
        covs_to_use = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency", "hypotension"]
        df_model_r = df_analysis[covs_to_use + [col]].dropna()
        X = sm.add_constant(df_model_r[covs_to_use].astype(float))
        y = df_model_r[col].astype(float)
        df_model = df_model_r
        n_events = int(y.sum())
        try:
            model = sm.Logit(y, X).fit(disp=0, maxiter=200)
            print(f"    (used reduced model: {len(covs_to_use)} covariates)")
        except Exception as e2:
            print(f"\n  {key} ({label}): Regression failed even with reduced model — {e2}")
            sensitivity_results.append({
                "Definition": key, "Label": label,
                "n": len(df_model), "Events": n_events,
                "twin_OR": np.nan, "twin_CI_lower": np.nan, "twin_CI_upper": np.nan,
                "twin_P": np.nan, "AIC": np.nan,
            })
            continue

    try:
        twin_idx = covs_to_use.index("twin") + 1
        twin_or = np.exp(model.params.iloc[twin_idx])
        ci = model.conf_int().iloc[twin_idx]
        twin_ci_lo = np.exp(ci.iloc[0])
        twin_ci_hi = np.exp(ci.iloc[1])
        twin_p = model.pvalues.iloc[twin_idx]
        aic = model.aic

        reduced_note = " (reduced model)" if len(covs_to_use) < len(covariates) else ""
        print(f"\n  {key} ({label}): n={len(df_model)}, events={n_events}{reduced_note}")
        print(f"     Twin aOR = {twin_or:.2f} (95%CI {twin_ci_lo:.2f}–{twin_ci_hi:.2f}), P = {twin_p:.4f}")

        # Save full OR table
        or_table = pd.DataFrame({
            "Variable": covs_to_use,
            "OR": np.exp(model.params[1:]),
            "95% CI lower": np.exp(model.conf_int().iloc[1:, 0]),
            "95% CI upper": np.exp(model.conf_int().iloc[1:, 1]),
            "P-value": model.pvalues[1:],
        })
        or_table.to_csv(TAB / f"sensitivity_{key}_logistic.csv", index=False)

        sensitivity_results.append({
            "Definition": key, "Label": label,
            "n": len(df_model), "Events": n_events,
            "twin_OR": float(twin_or),
            "twin_CI_lower": float(twin_ci_lo),
            "twin_CI_upper": float(twin_ci_hi),
            "twin_P": float(twin_p),
            "AIC": float(aic),
            "reduced_model": len(covs_to_use) < len(covariates),
        })
    except Exception as e:
        print(f"\n  {key} ({label}): Regression failed — {e}")
        sensitivity_results.append({
            "Definition": key, "Label": label,
            "n": len(df_model), "Events": n_events,
            "twin_OR": np.nan, "twin_CI_lower": np.nan, "twin_CI_upper": np.nan,
            "twin_P": np.nan, "AIC": np.nan,
        })

# ============================================================
# 4. DEFINITION G: POISSON REGRESSION (drug count)
# ============================================================
print("\n" + "=" * 60)
print("DEFINITION G: POISSON REGRESSION — Drug count")
print("=" * 60)

df_model_g = df_analysis[covariates + ["drug_count"]].dropna()
X_g = sm.add_constant(df_model_g[covariates].astype(float))
y_g = df_model_g["drug_count"].astype(float)

try:
    poisson_model = sm.GLM(y_g, X_g, family=sm.families.Poisson()).fit()
    twin_idx_g = covariates.index("twin") + 1
    twin_irr = np.exp(poisson_model.params.iloc[twin_idx_g])
    ci_g = poisson_model.conf_int().iloc[twin_idx_g]
    twin_irr_lo = np.exp(ci_g.iloc[0])
    twin_irr_hi = np.exp(ci_g.iloc[1])
    twin_p_g = poisson_model.pvalues.iloc[twin_idx_g]

    print(f"  n = {len(df_model_g)}")
    print(f"  Twin IRR = {twin_irr:.2f} (95%CI {twin_irr_lo:.2f}–{twin_irr_hi:.2f}), P = {twin_p_g:.4f}")

    or_table_g = pd.DataFrame({
        "Variable": covariates,
        "IRR": np.exp(poisson_model.params[1:]),
        "95% CI lower": np.exp(poisson_model.conf_int().iloc[1:, 0]),
        "95% CI upper": np.exp(poisson_model.conf_int().iloc[1:, 1]),
        "P-value": poisson_model.pvalues[1:],
    })
    or_table_g.to_csv(TAB / "sensitivity_G_poisson.csv", index=False)

    sensitivity_results.append({
        "Definition": "G", "Label": "Drug count (Poisson)",
        "n": len(df_model_g), "Events": int(y_g.sum()),
        "twin_OR": float(twin_irr),
        "twin_CI_lower": float(twin_irr_lo),
        "twin_CI_upper": float(twin_irr_hi),
        "twin_P": float(twin_p_g),
        "AIC": float(poisson_model.aic),
    })
except Exception as e:
    print(f"  Poisson regression failed: {e}")

# ============================================================
# 5. DEFINITION H: HYPOTENSION-STRATIFIED ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("DEFINITION H: HYPOTENSION-STRATIFIED ANALYSIS")
print("=" * 60)

covariates_h = [c for c in covariates if c != "hypotension"]
strata_results = []

for stratum_name, stratum_mask in [("Hypotension (+)", df_analysis["hypotension"] == 1),
                                    ("Hypotension (−)", df_analysis["hypotension"] == 0)]:
    df_stratum = df_analysis[stratum_mask].copy()
    df_model_h = df_stratum[covariates_h + ["ionv_primary"]].dropna()
    n_events_h = int(df_model_h["ionv_primary"].sum())

    s_h = df_stratum[df_stratum["twin"] == 0]
    t_h = df_stratum[df_stratum["twin"] == 1]
    s_rate = 100 * s_h["ionv_primary"].mean() if len(s_h) > 0 else 0
    t_rate = 100 * t_h["ionv_primary"].mean() if len(t_h) > 0 else 0

    print(f"\n  {stratum_name}: n={len(df_model_h)}, events={n_events_h}")
    print(f"    Singleton IONV: {s_h['ionv_primary'].sum()}/{len(s_h)} ({s_rate:.1f}%)")
    print(f"    Twin IONV:      {t_h['ionv_primary'].sum()}/{len(t_h)} ({t_rate:.1f}%)")

    if n_events_h < 5:
        print(f"    Too few events, skipping regression")
        strata_results.append({
            "Stratum": stratum_name, "n": len(df_model_h), "Events": n_events_h,
            "singleton_rate": s_rate, "twin_rate": t_rate,
            "twin_OR": np.nan, "twin_CI_lower": np.nan, "twin_CI_upper": np.nan,
            "twin_P": np.nan,
        })
        continue

    try:
        X_h = sm.add_constant(df_model_h[covariates_h].astype(float))
        y_h = df_model_h["ionv_primary"].astype(float)
        model_h = sm.Logit(y_h, X_h).fit(disp=0, maxiter=200)
        twin_idx_h = covariates_h.index("twin") + 1
        twin_or_h = np.exp(model_h.params.iloc[twin_idx_h])
        ci_h = model_h.conf_int().iloc[twin_idx_h]

        print(f"    Twin aOR = {twin_or_h:.2f} "
              f"(95%CI {np.exp(ci_h.iloc[0]):.2f}–{np.exp(ci_h.iloc[1]):.2f}), "
              f"P = {model_h.pvalues.iloc[twin_idx_h]:.4f}")

        or_table_h = pd.DataFrame({
            "Variable": covariates_h,
            "OR": np.exp(model_h.params[1:]),
            "95% CI lower": np.exp(model_h.conf_int().iloc[1:, 0]),
            "95% CI upper": np.exp(model_h.conf_int().iloc[1:, 1]),
            "P-value": model_h.pvalues[1:],
        })
        or_table_h.to_csv(TAB / f"sensitivity_H_{stratum_name.replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'pos').replace('−', 'neg')}.csv", index=False)

        strata_results.append({
            "Stratum": stratum_name, "n": len(df_model_h), "Events": n_events_h,
            "singleton_rate": s_rate, "twin_rate": t_rate,
            "twin_OR": float(twin_or_h),
            "twin_CI_lower": float(np.exp(ci_h.iloc[0])),
            "twin_CI_upper": float(np.exp(ci_h.iloc[1])),
            "twin_P": float(model_h.pvalues.iloc[twin_idx_h]),
        })
    except Exception as e:
        print(f"    Regression failed: {e}")
        strata_results.append({
            "Stratum": stratum_name, "n": len(df_model_h), "Events": n_events_h,
            "singleton_rate": s_rate, "twin_rate": t_rate,
            "twin_OR": np.nan, "twin_CI_lower": np.nan, "twin_CI_upper": np.nan,
            "twin_P": np.nan,
        })

# ============================================================
# 6. SUMMARY TABLE + FIGURES
# ============================================================
print("\n" + "=" * 60)
print("GENERATING SENSITIVITY ANALYSIS OUTPUTS")
print("=" * 60)

# Save sensitivity summary table
sens_df = pd.DataFrame(sensitivity_results)
sens_df.to_csv(TAB / "sensitivity_summary.csv", index=False)
print("Sensitivity summary table saved")

strata_df = pd.DataFrame(strata_results)
strata_df.to_csv(TAB / "sensitivity_H_stratified.csv", index=False)
print("Stratified analysis table saved")

# --- Fig 7: Forest plot comparing twin aOR across all definitions ---
fig, ax = plt.subplots(figsize=(10, 7))

plot_data = sens_df[sens_df["twin_OR"].notna()].copy()
plot_data = plot_data.sort_values("Definition", ascending=False)

# Add stratified results
for sr in strata_results:
    if not np.isnan(sr["twin_OR"]):
        plot_data = pd.concat([plot_data, pd.DataFrame([{
            "Definition": "H",
            "Label": sr["Stratum"],
            "n": sr["n"], "Events": sr["Events"],
            "twin_OR": sr["twin_OR"],
            "twin_CI_lower": sr["twin_CI_lower"],
            "twin_CI_upper": sr["twin_CI_upper"],
            "twin_P": sr["twin_P"],
        }])], ignore_index=True)

plot_data = plot_data.iloc[::-1].reset_index(drop=True)

y_pos = range(len(plot_data))
colors = []
for _, row in plot_data.iterrows():
    if row["Definition"] in ("A", "B"):
        colors.append("#4C72B0")
    elif row["Definition"] == "H":
        colors.append("#C44E52")
    elif row["Definition"] == "G":
        colors.append("#8172B2")
    else:
        colors.append("#55A868")

for i, (_, row) in enumerate(plot_data.iterrows()):
    ax.errorbar(row["twin_OR"], i,
                xerr=[[row["twin_OR"] - row["twin_CI_lower"]],
                      [row["twin_CI_upper"] - row["twin_OR"]]],
                fmt="o", color=colors[i], capsize=4, markersize=7, linewidth=1.5)

ax.axvline(1, color="red", linestyle="--", linewidth=0.8, alpha=0.7)

labels = []
for _, row in plot_data.iterrows():
    suffix = " (IRR)" if row["Definition"] == "G" else " (aOR)"
    labels.append(f"{row['Definition']}: {row['Label']}")

ax.set_yticks(list(y_pos))
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Odds Ratio / IRR (95% CI)", fontsize=11)
ax.set_title("Effect of twin pregnancy on IONV:\nSensitivity analyses with alternative definitions", fontsize=12)

for i, (_, row) in enumerate(plot_data.iterrows()):
    metric = "IRR" if row["Definition"] == "G" else "aOR"
    p_str = f"P={row['twin_P']:.3f}" if row["twin_P"] >= 0.001 else "P<0.001"
    sig = " *" if row["twin_P"] < 0.05 else ""
    ax.annotate(f"{metric} {row['twin_OR']:.2f} [{row['twin_CI_lower']:.2f}–{row['twin_CI_upper']:.2f}] {p_str}{sig}",
                xy=(max(plot_data["twin_CI_upper"].max() * 1.05, 2.5), i),
                fontsize=8, va="center")

ax.set_xlim(0, max(plot_data["twin_CI_upper"].max() * 1.8, 4))
plt.tight_layout()
plt.savefig(FIG / "fig7_sensitivity_forest.png")
plt.close()
print("Fig 7: Sensitivity forest plot saved")

# --- Fig 8: IONV rates by definition (grouped bar chart) ---
fig, ax = plt.subplots(figsize=(12, 6))

def_labels = []
s_rates = []
t_rates = []
for key, (col, label) in definitions.items():
    def_labels.append(f"{key}: {label}")
    s_rates.append(100 * s[col].mean())
    t_rates.append(100 * t[col].mean())

x = np.arange(len(def_labels))
width = 0.35
bars1 = ax.bar(x - width/2, s_rates, width, label="Singleton", color="#4C72B0",
               edgecolor="black", linewidth=0.5)
bars2 = ax.bar(x + width/2, t_rates, width, label="Twin", color="#DD8452",
               edgecolor="black", linewidth=0.5)

for bars in [bars1, bars2]:
    for bar in bars:
        h = bar.get_height()
        if h > 0.3:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.3,
                    f"{h:.1f}%", ha="center", fontsize=8, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(def_labels, rotation=25, ha="right", fontsize=9)
ax.set_ylabel("Rate (%)")
ax.set_title("IONV rates by definition: Singleton vs Twin")
ax.legend()
plt.tight_layout()
plt.savefig(FIG / "fig8_sensitivity_rates.png")
plt.close()
print("Fig 8: Sensitivity rates comparison saved")

# --- Fig 9: Hypotension-stratified IONV rates ---
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

for ax_i, (stratum_name, stratum_mask) in enumerate([
    ("Hypotension (+)", df_analysis["hypotension"] == 1),
    ("Hypotension (−)", df_analysis["hypotension"] == 0),
]):
    df_str = df_analysis[stratum_mask]
    s_str = df_str[df_str["twin"] == 0]
    t_str = df_str[df_str["twin"] == 1]

    s_rate = 100 * s_str["ionv_primary"].mean()
    t_rate = 100 * t_str["ionv_primary"].mean()

    bars = axes[ax_i].bar(["Singleton", "Twin"], [s_rate, t_rate],
                          color=["#4C72B0", "#DD8452"], width=0.5,
                          edgecolor="black", linewidth=0.5)

    for bar, rate in zip(bars, [s_rate, t_rate]):
        axes[ax_i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f"{rate:.1f}%", ha="center", fontsize=10, fontweight="bold")

    axes[ax_i].set_ylabel("IONV rate (%)")
    axes[ax_i].set_title(f"{stratum_name}\n(n={len(df_str)})")

    # P-value
    table_h = np.array([
        [int(s_str["ionv_primary"].sum()), len(s_str) - int(s_str["ionv_primary"].sum())],
        [int(t_str["ionv_primary"].sum()), len(t_str) - int(t_str["ionv_primary"].sum())]
    ])
    row_totals_h = table_h.sum(axis=1)
    col_totals_h = table_h.sum(axis=0)
    expected_h = np.outer(row_totals_h, col_totals_h) / table_h.sum()
    if expected_h.min() < 5:
        _, p_h = stats.fisher_exact(table_h)
    else:
        _, p_h, _, _ = stats.chi2_contingency(table_h, correction=False)
    p_text = f"P = {p_h:.3f}" if p_h >= 0.001 else "P < 0.001"
    axes[ax_i].text(0.5, max(s_rate, t_rate) + 3, p_text, ha="center", fontsize=9)

fig.suptitle("Definition H: IONV rates stratified by hypotension", fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig(FIG / "fig9_stratified_hypotension.png")
plt.close()
print("Fig 9: Stratified hypotension plot saved")

# ============================================================
# 7. SAVE SUMMARY JSON
# ============================================================
sensitivity_json = {
    "definitions": {
        key: {
            "label": label,
            "col": col,
            "singleton_n": int(s[col].sum()),
            "singleton_pct": float(100 * s[col].mean()),
            "twin_n": int(t[col].sum()),
            "twin_pct": float(100 * t[col].mean()),
        }
        for key, (col, label) in definitions.items()
    },
    "regression": sensitivity_results,
    "stratified": strata_results,
    "drug_count": {
        "singleton_mean": float(s["drug_count"].mean()),
        "singleton_std": float(s["drug_count"].std()),
        "twin_mean": float(t["drug_count"].mean()),
        "twin_std": float(t["drug_count"].std()),
        "p_mannwhitney": float(p_g),
    },
}

with open(BASE / "sensitivity_stats.json", "w") as f:
    json.dump(sensitivity_json, f, indent=2, ensure_ascii=False)

print("\nSensitivity stats JSON saved.")
print("\n" + "=" * 60)
print("SENSITIVITY ANALYSIS COMPLETE")
print("=" * 60)
