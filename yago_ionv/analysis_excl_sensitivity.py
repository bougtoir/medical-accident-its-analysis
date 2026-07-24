"""
Exclusion sensitivity analysis:
  Exclude cases with emergency CS, prior CS, HDP, or preoperative steroid,
  then re-run broad/narrow IONV analysis with adjusted covariate models.
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
import json, os, re

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE = Path(__file__).resolve().parent
FIG = BASE / "figures_excl"
TAB = BASE / "tables_excl"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

# ============================================================
# 1. DATA LOADING (same pipeline as analysis_def_e.py)
# ============================================================
print("=" * 60)
print("EXCLUSION SENSITIVITY ANALYSIS: Loading data")
print("=" * 60)

single_file = [f for f in os.listdir(BASE) if f.startswith("single") and f.endswith(".xlsm")][0]
twin_file = [f for f in os.listdir(BASE) if f.startswith("twin") and f.endswith(".xlsx")][0]

raw_single = pd.read_excel(BASE / single_file, sheet_name="基本データ", engine="openpyxl")
raw_twin = pd.read_excel(BASE / twin_file, engine="openpyxl")

single = raw_single.copy()
twin = raw_twin.copy()

single.rename(columns={
    "手術所要": "手術時間_min", "麻酔所要": "麻酔時間_min",
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
    "術中輸液量(ml)": "輸液量_ml",
    "術中昇圧薬持続投与の有無": "vasopressor_continuous",
    "術中エフェドリン投与(mg)": "ephedrine_mg",
    "術中フェニレフリン投与(mg)": "phenylephrine_mg",
    "脊髄くも膜下への高比重ブピバカイン投与(mg)": "bupivacaine_mg",
    "脊髄くも膜下へのフェンタニル投与(μg)": "fentanyl_ug",
    "脊髄くも膜下へのモルヒネ投与(mg)": "morphine_mg",
}, inplace=True)
excl_col = "Unnamed: 66" if "Unnamed: 66" in single.columns else single.columns[66]
single["exclusion_note"] = single[excl_col] if excl_col in single.columns else np.nan

twin.rename(columns={
    "手術時間(min)": "手術時間_min", "麻酔時間(min)": "麻酔時間_min",
    "出血量(ml)": "出血量_ml", "輸液量(ml)": "輸液量_ml",
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
    "昇圧持続投与": "vasopressor_continuous",
    "エフェドリン(mg)": "ephedrine_mg",
    "フェニレフリン(mg)": "phenylephrine_mg",
    "脊髄くも膜下への高比重ブピバカイン(mg)": "bupivacaine_mg",
    "脊髄くも膜下へのフェンタニル(μg )": "fentanyl_ug",
    "脊髄くも膜下へのモルヒネ(mg)": "morphine_mg",
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
            "術前24時間以内の降圧薬使用"]:
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

def parse_ga_weeks(val):
    if pd.isna(val): return np.nan
    s = str(val).strip()
    m = re.match(r"(\d+)w(\d+)d?", s)
    if m: return int(m.group(1)) + int(m.group(2)) / 7
    try: return float(s)
    except ValueError: return np.nan

for df in [single, twin]:
    df["GA_weeks"] = df["妊娠週数(週)"].apply(parse_ga_weeks)

def time_to_min(val):
    if pd.isna(val): return np.nan
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, pd.Timedelta): return val.total_seconds() / 60
    if isinstance(val, str):
        parts = val.split(":")
        try:
            if len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3: return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        except ValueError: return np.nan
    return np.nan

single["手術時間_min"] = single["手術時間_min"].apply(time_to_min)
single["麻酔時間_min"] = single["麻酔時間_min"].apply(time_to_min)
twin["手術時間_min"] = pd.to_numeric(twin["手術時間_min"], errors="coerce")
twin["麻酔時間_min"] = pd.to_numeric(twin["麻酔時間_min"], errors="coerce")

for df in [single, twin]:
    for col in ["年齢(歳)", "hypotension_count", "全身麻酔", "硬膜外麻酔",
                "帝王切開の既往", "高血圧合併妊娠", "妊娠高血圧症候群",
                "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
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
    "preop_steroid", "帝王切開の既往", "子宮脱転", "emergency",
    "全身麻酔", "硬膜外麻酔",
    "手術時間_min", "麻酔時間_min", "出血量_ml", "輸液量_ml",
    "hypotension_count", "vasopressor_continuous",
    "ephedrine_mg", "phenylephrine_mg",
    "bupivacaine_mg", "fentanyl_ug", "morphine_mg",
    "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery",
    "metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
    "novamin_mg", "atarax_p_mg", "dexamethasone_mg",
    "exclusion_note", "twin",
]

s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]
df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)

for col in merge_cols:
    if col in df_all.columns and col not in ["exclusion_note", "仮ID", "手術日"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

# Study period filter (2014-04-01 to 2024-10-24)
df_all["手術日_dt"] = pd.to_datetime(df_all["手術日"], errors="coerce")
STUDY_START = pd.Timestamp("2014-04-01")
df_all = df_all[~(df_all["手術日_dt"] < STUDY_START)].copy()
print(f"After date filter (>={STUDY_START.date()}): {len(df_all)}")

# Standard exclusions (updated: GA from column OR note)
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
generic_mask = note.str.contains("除外", na=False)
no_data = df_all["antiemetic_any"].isna()
all_exclude = ga_mask | sbp_mask | iufd_mask | vt_mask | triplet_mask | \
              non_cs_mask | cardiac_mask | no_data | generic_mask

n_total = len(df_all)
n_single_raw = int((df_all["twin"] == 0).sum())
n_twin_raw = int((df_all["twin"] == 1).sum())
df = df_all[~all_exclude].copy()
df_base = df[df["ae_pre_anesthesia"] != 1].copy()

# Derived variables on base cohort
df_base["HDP"] = ((df_base["高血圧合併妊娠"] == 1) | (df_base["妊娠高血圧症候群"] == 1)).astype(int)
df_base["hypotension"] = (df_base["hypotension_count"] >= 1).astype(int).where(
    df_base["hypotension_count"].notna(), np.nan)
df_base["epidural"] = pd.to_numeric(df_base["硬膜外麻酔"], errors="coerce")
df_base["prior_cs"] = pd.to_numeric(df_base["帝王切開の既往"], errors="coerce")

for d in ["metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
          "novamin_mg", "atarax_p_mg", "dexamethasone_mg"]:
    df_base[d] = pd.to_numeric(df_base[d], errors="coerce")

n_base = len(df_base)
print(f"Base analysis cohort (before additional exclusion): {n_base}")
print(f"  Singleton: {(df_base['twin']==0).sum()}, Twin: {(df_base['twin']==1).sum()}")

# ============================================================
# ADDITIONAL EXCLUSION: Emergency CS, Prior CS, HDP, Preop steroid
# ============================================================
print("\n" + "=" * 60)
print("ADDITIONAL EXCLUSION")
print("=" * 60)

excl_conditions = {
    "Emergency CS": df_base["emergency"] == 1,
    "Prior CS": df_base["prior_cs"] == 1,
    "HDP": df_base["HDP"] == 1,
    "Preoperative steroid": df_base["preop_steroid"] == 1,
}

# Count excluded by each condition
excl_any = pd.Series(False, index=df_base.index)
for name, mask in excl_conditions.items():
    mask_filled = mask.fillna(False)
    n_excl = mask_filled.sum()
    n_excl_s = (mask_filled & (df_base["twin"] == 0)).sum()
    n_excl_t = (mask_filled & (df_base["twin"] == 1)).sum()
    print(f"  {name}: {n_excl} excluded (S={n_excl_s}, T={n_excl_t})")
    excl_any = excl_any | mask_filled

n_excl_total = excl_any.sum()
n_excl_s = (excl_any & (df_base["twin"] == 0)).sum()
n_excl_t = (excl_any & (df_base["twin"] == 1)).sum()
print(f"  Any of above: {n_excl_total} excluded (S={n_excl_s}, T={n_excl_t})")

df_analysis = df_base[~excl_any].copy()
n_analysis = len(df_analysis)
n_single = int((df_analysis["twin"] == 0).sum())
n_twin = int((df_analysis["twin"] == 1).sum())
print(f"\nFinal analysis cohort: {n_analysis} (S={n_single}, T={n_twin})")

s = df_analysis[df_analysis["twin"] == 0]
t = df_analysis[df_analysis["twin"] == 1]

# ============================================================
# 2. OUTCOMES
# ============================================================
print("\n" + "=" * 60)
print("2. OUTCOMES")
print("=" * 60)

_5ht3_any = (
    (df_analysis["ondansetron_mg"].fillna(0) > 0) |
    (df_analysis["granisetron_mg"].fillna(0) > 0)
).astype(int)

df_analysis["ionv_E_primary"] = (
    (_5ht3_any == 1) &
    (df_analysis["ae_to_delivery"] == 1)
).astype(int)

df_analysis["ionv_E_secondary"] = _5ht3_any

df_analysis["ionv_A_primary"] = (df_analysis["ae_to_delivery"] == 1).astype(int)
df_analysis["ionv_A_secondary"] = ((df_analysis["ae_to_delivery"] == 1) | (df_analysis["ae_post_delivery"] == 1)).astype(int)

s = df_analysis[df_analysis["twin"] == 0]
t = df_analysis[df_analysis["twin"] == 1]

outcomes = OrderedDict([
    ("A-Primary", ("ionv_A_primary", "Broad: antiemetic before delivery")),
    ("A-Secondary", ("ionv_A_secondary", "Broad: any antiemetic (any phase)")),
    ("E-Primary", ("ionv_E_primary", "Narrow: 5-HT3 + before delivery")),
    ("E-Secondary", ("ionv_E_secondary", "Narrow: 5-HT3 antagonist (any phase)")),
])

print(f"\n{'Outcome':<15} {'Label':<40} {'Single n/N (%)':<22} {'Twin n/N (%)':<22} {'P':>8}")
print("-" * 110)
outcome_stats = {}
for key, (col, label) in outcomes.items():
    s_n = int(s[col].sum())
    t_n = int(t[col].sum())
    s_pct = 100 * s_n / len(s) if len(s) > 0 else 0
    t_pct = 100 * t_n / len(t) if len(t) > 0 else 0
    table = np.array([[s_n, len(s) - s_n], [t_n, len(t) - t_n]])
    row_t = table.sum(axis=1); col_t = table.sum(axis=0)
    exp = np.outer(row_t, col_t) / table.sum()
    if exp.min() < 5:
        _, p = stats.fisher_exact(table)
    else:
        _, p, _, _ = stats.chi2_contingency(table, correction=False)
    sig = "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"  {key:<13} {label:<40} {s_n}/{len(s)} ({s_pct:5.1f}%)     "
          f"{t_n}/{len(t)} ({t_pct:5.1f}%)     {p:.4f} {sig}")
    outcome_stats[key] = {
        "singleton_n": s_n, "singleton_pct": float(s_pct),
        "twin_n": t_n, "twin_pct": float(t_pct), "p_unadj": float(p),
    }

# ============================================================
# 3. TABLE 1: PATIENT CHARACTERISTICS
# ============================================================
print("\n" + "=" * 60)
print("3. TABLE 1")
print("=" * 60)

def summarize_continuous(s_series, t_series):
    s_val = s_series.dropna()
    t_val = t_series.dropna()
    s_med = s_val.median(); s_q1, s_q3 = s_val.quantile(0.25), s_val.quantile(0.75)
    t_med = t_val.median(); t_q1, t_q3 = t_val.quantile(0.25), t_val.quantile(0.75)
    if len(s_val) > 0 and len(t_val) > 0:
        _, p = stats.mannwhitneyu(s_val, t_val, alternative="two-sided")
    else:
        p = np.nan
    return {
        "Variable": s_series.name, "Type": "continuous",
        "Singleton": f"{s_med:.1f} [{s_q1:.1f}-{s_q3:.1f}]",
        "Twin": f"{t_med:.1f} [{t_q1:.1f}-{t_q3:.1f}]",
        "P-value": p,
    }

def summarize_categorical(s_series, t_series):
    s_val = s_series.dropna()
    t_val = t_series.dropna()
    s_n = int(s_val.sum())
    t_n = int(t_val.sum())
    s_pct = 100 * s_n / len(s_val) if len(s_val) > 0 else 0
    t_pct = 100 * t_n / len(t_val) if len(t_val) > 0 else 0
    table = np.array([[s_n, len(s_val) - s_n], [t_n, len(t_val) - t_n]])
    row_t = table.sum(axis=1); col_t = table.sum(axis=0)
    exp = np.outer(row_t, col_t) / table.sum()
    if exp.min() < 5:
        _, p = stats.fisher_exact(table)
    else:
        _, p, _, _ = stats.chi2_contingency(table, correction=False)
    return {
        "Variable": s_series.name, "Type": "categorical",
        "Singleton": f"{s_n}/{len(s_val)} ({s_pct:.1f}%)",
        "Twin": f"{t_n}/{len(t_val)} ({t_pct:.1f}%)",
        "P-value": p,
    }

table1_rows = []
cont_vars = [("年齢(歳)", "Age (years)"), ("BMI", "BMI (kg/m²)"),
             ("GA_weeks", "Gestational age (weeks)"),
             ("手術時間_min", "Surgery time (min)"),
             ("麻酔時間_min", "Anesthesia time (min)"),
             ("出血量_ml", "Estimated blood loss (mL)"),
             ("輸液量_ml", "Infusion volume (mL)"),
             ("hypotension_count", "Hypotensive episodes (count)")]
for col, label in cont_vars:
    if col in df_analysis.columns:
        row = summarize_continuous(s[col].rename(label), t[col].rename(label))
        row["Variable"] = label
        table1_rows.append(row)

cat_vars = [("epidural", "Epidural anesthesia"),
            ("hypotension", "Hypotension (SBP < 90)")]
for col, label in cat_vars:
    if col in df_analysis.columns:
        row = summarize_categorical(s[col].rename(label), t[col].rename(label))
        row["Variable"] = label
        table1_rows.append(row)

table1_df = pd.DataFrame(table1_rows)
table1_df.to_csv(TAB / "table1_characteristics.csv", index=False)
print("Table 1 saved")

# ============================================================
# 4. MULTIVARIABLE LOGISTIC REGRESSION
# ============================================================
print("\n" + "=" * 60)
print("4. MULTIVARIABLE LOGISTIC REGRESSION")
print("=" * 60)

# Covariates adjusted: emergency, prior_cs, HDP, preop_steroid are excluded from data
# so they cannot be in the model
covariates_full = ["twin", "年齢(歳)", "BMI", "GA_weeks", "epidural", "手術時間_min", "hypotension"]
covariates_reduced = ["twin", "年齢(歳)", "BMI", "GA_weeks", "hypotension"]

label_map = {
    "twin": "Twin pregnancy", "年齢(歳)": "Age (per year)",
    "BMI": "BMI (per kg/m²)", "GA_weeks": "GA (per week)",
    "epidural": "Epidural anesthesia",
    "手術時間_min": "Surgery time (per min)", "hypotension": "Hypotension (SBP < 90)",
}

regression_results = {}

for outcome_key, (col, label) in outcomes.items():
    print(f"\n--- {outcome_key}: {label} ---")

    n_events = int(df_analysis[col].sum())
    covs = covariates_full if n_events >= 50 else covariates_reduced
    df_m = df_analysis[covs + [col]].dropna()
    X = sm.add_constant(df_m[covs].astype(float))
    y = df_m[col].astype(float)

    model_type = "full" if len(covs) == len(covariates_full) else "reduced"
    try:
        model = sm.Logit(y, X).fit(disp=0, maxiter=200)
    except Exception:
        if covs == covariates_full:
            covs = covariates_reduced
            df_m = df_analysis[covs + [col]].dropna()
            X = sm.add_constant(df_m[covs].astype(float))
            y = df_m[col].astype(float)
            model = sm.Logit(y, X).fit(disp=0, maxiter=200)
            model_type = "reduced"
        else:
            raise

    twin_idx = covs.index("twin") + 1
    or_table = pd.DataFrame({
        "Variable": covs,
        "OR": np.exp(model.params[1:]),
        "95% CI lower": np.exp(model.conf_int().iloc[1:, 0]),
        "95% CI upper": np.exp(model.conf_int().iloc[1:, 1]),
        "P-value": model.pvalues[1:],
    })
    or_table.to_csv(TAB / f"logistic_{outcome_key}.csv", index=False)

    twin_or = np.exp(model.params.iloc[twin_idx])
    ci = model.conf_int().iloc[twin_idx]
    twin_ci_lo = np.exp(ci.iloc[0])
    twin_ci_hi = np.exp(ci.iloc[1])
    twin_p = model.pvalues.iloc[twin_idx]

    print(f"  n={len(df_m)}, events={int(y.sum())}, model={model_type}")
    print(f"  Twin aOR = {twin_or:.2f} (95%CI {twin_ci_lo:.2f}-{twin_ci_hi:.2f}), P = {twin_p:.4f}")

    regression_results[outcome_key] = {
        "label": label, "col": col,
        "n": len(df_m), "events": int(y.sum()),
        "twin_OR": float(twin_or),
        "twin_CI_lower": float(twin_ci_lo),
        "twin_CI_upper": float(twin_ci_hi),
        "twin_P": float(twin_p),
        "AIC": float(model.aic),
        "model_type": model_type,
        "covariates": covs,
    }

# ============================================================
# 5. COVARIATE SENSITIVITY ANALYSIS (Narrow primary)
# ============================================================
print("\n" + "=" * 60)
print("5. COVARIATE SENSITIVITY ANALYSIS")
print("=" * 60)

all_covs = ["年齢(歳)", "BMI", "GA_weeks", "epidural", "手術時間_min", "hypotension"]

cov_sensitivity = []

# Crude (twin only)
df_e = df_analysis[["twin", "ionv_E_primary"]].dropna()
X_c = sm.add_constant(df_e[["twin"]].astype(float))
y_c = df_e["ionv_E_primary"].astype(float)
m_c = sm.Logit(y_c, X_c).fit(disp=0)
cov_sensitivity.append({
    "Model": "Crude (twin only)", "n_covariates": 0,
    "aOR": float(np.exp(m_c.params.iloc[1])),
    "CI_lower": float(np.exp(m_c.conf_int().iloc[1, 0])),
    "CI_upper": float(np.exp(m_c.conf_int().iloc[1, 1])),
    "P": float(m_c.pvalues.iloc[1]),
    "AIC": float(m_c.aic),
})

# Twin + each covariate
for cov in all_covs:
    covs = ["twin", cov]
    df_e = df_analysis[covs + ["ionv_E_primary"]].dropna()
    X = sm.add_constant(df_e[covs].astype(float))
    y = df_e["ionv_E_primary"].astype(float)
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=200)
        cov_sensitivity.append({
            "Model": f"Twin + {label_map.get(cov, cov)}",
            "n_covariates": 1,
            "aOR": float(np.exp(m.params.iloc[1])),
            "CI_lower": float(np.exp(m.conf_int().iloc[1, 0])),
            "CI_upper": float(np.exp(m.conf_int().iloc[1, 1])),
            "P": float(m.pvalues.iloc[1]),
            "AIC": float(m.aic),
        })
    except Exception:
        pass

# Full model minus one
for cov_rm in all_covs:
    covs = ["twin"] + [c for c in all_covs if c != cov_rm]
    df_e = df_analysis[covs + ["ionv_E_primary"]].dropna()
    X = sm.add_constant(df_e[covs].astype(float))
    y = df_e["ionv_E_primary"].astype(float)
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=200)
        cov_sensitivity.append({
            "Model": f"Full minus {label_map.get(cov_rm, cov_rm)}",
            "n_covariates": len(covs) - 1,
            "aOR": float(np.exp(m.params.iloc[1])),
            "CI_lower": float(np.exp(m.conf_int().iloc[1, 0])),
            "CI_upper": float(np.exp(m.conf_int().iloc[1, 1])),
            "P": float(m.pvalues.iloc[1]),
            "AIC": float(m.aic),
        })
    except Exception:
        pass

# Reduced model
covs_r = covariates_reduced
df_e = df_analysis[covs_r + ["ionv_E_primary"]].dropna()
X = sm.add_constant(df_e[covs_r].astype(float))
y = df_e["ionv_E_primary"].astype(float)
m = sm.Logit(y, X).fit(disp=0)
cov_sensitivity.append({
    "Model": "Reduced (5 covariates)", "n_covariates": 4,
    "aOR": float(np.exp(m.params.iloc[1])),
    "CI_lower": float(np.exp(m.conf_int().iloc[1, 0])),
    "CI_upper": float(np.exp(m.conf_int().iloc[1, 1])),
    "P": float(m.pvalues.iloc[1]),
    "AIC": float(m.aic),
})

cov_df = pd.DataFrame(cov_sensitivity)
cov_df.to_csv(TAB / "covariate_sensitivity.csv", index=False)

print(f"\n{'Model':<40} {'aOR':>6} {'95% CI':>18} {'P':>8} {'Sig':>4}")
print("-" * 80)
for _, row in cov_df.iterrows():
    sig = "**" if row["P"] < 0.01 else "*" if row["P"] < 0.05 else ""
    print(f"{row['Model']:<40} {row['aOR']:>6.2f} [{row['CI_lower']:.2f}-{row['CI_upper']:.2f}]       {row['P']:>7.4f} {sig}")

# ============================================================
# 6. FIGURES
# ============================================================
print("\n" + "=" * 60)
print("6. GENERATING FIGURES")
print("=" * 60)

# --- Fig 1: IONV rates comparison ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax_i, (title, primary_col, secondary_col, primary_label, secondary_label) in enumerate([
    ("Antiemetic (broad)", "ionv_A_primary", "ionv_A_secondary",
     "Before delivery", "Any antiemetic"),
    ("Antiemetic (narrow: 5-HT3)", "ionv_E_primary", "ionv_E_secondary",
     "5-HT3 + before delivery", "5-HT3 antagonist (any)"),
]):
    s_p = 100 * s[primary_col].mean()
    t_p = 100 * t[primary_col].mean()
    s_s = 100 * s[secondary_col].mean()
    t_s = 100 * t[secondary_col].mean()

    x = np.arange(2)
    width = 0.35
    b1 = axes[ax_i].bar(x - width/2, [s_p, s_s], width, label="Singleton",
                         color="#4C72B0", edgecolor="black", linewidth=0.5)
    b2 = axes[ax_i].bar(x + width/2, [t_p, t_s], width, label="Twin",
                         color="#DD8452", edgecolor="black", linewidth=0.5)

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            if h > 0.1:
                axes[ax_i].text(bar.get_x() + bar.get_width()/2, h + 0.2,
                                f"{h:.1f}%", ha="center", fontsize=9, fontweight="bold")

    axes[ax_i].set_xticks(x)
    axes[ax_i].set_xticklabels([primary_label, secondary_label], fontsize=9)
    axes[ax_i].set_ylabel("Rate (%)")
    axes[ax_i].set_title(title, fontsize=11)
    axes[ax_i].legend(fontsize=9)

plt.suptitle("IONV Rates (Elective, low-risk subgroup)", fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(FIG / "fig1_rates_comparison.png")
plt.close()
print("Fig 1 saved")

# --- Fig 2: Forest plot --- Narrow primary regression ---
or_table_e = pd.read_csv(TAB / "logistic_E-Primary.csv")
or_table_e["label"] = or_table_e["Variable"].map(label_map).fillna(or_table_e["Variable"])
or_table_e = or_table_e.sort_values("P-value", ascending=False)

fig, ax = plt.subplots(figsize=(10, 6))
y_pos = range(len(or_table_e))
colors = ["#C44E52" if v == "twin" else "#4C72B0" for v in or_table_e["Variable"]]

for i, (_, row) in enumerate(or_table_e.iterrows()):
    ax.errorbar(row["OR"], i,
                xerr=[[row["OR"] - row["95% CI lower"]], [row["95% CI upper"] - row["OR"]]],
                fmt="o", color=colors[i], capsize=4, markersize=7, linewidth=1.5)

ax.axvline(1, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(or_table_e["label"], fontsize=9)
ax.set_xlabel("Odds Ratio (95% CI)")
ax.set_title("Logistic regression: 5-HT3 antagonist use\n(elective, low-risk subgroup)")

for i, (_, row) in enumerate(or_table_e.iterrows()):
    sig = "***" if row["P-value"] < 0.001 else "**" if row["P-value"] < 0.01 else "*" if row["P-value"] < 0.05 else ""
    ax.annotate(f"OR {row['OR']:.2f}, P={row['P-value']:.3f}{sig}",
                xy=(or_table_e["95% CI upper"].max() * 1.05, i),
                fontsize=8, va="center")

plt.tight_layout()
plt.savefig(FIG / "fig2_forest_narrow_primary.png")
plt.close()
print("Fig 2 saved")

# --- Fig 3: Covariate sensitivity forest plot ---
fig, ax = plt.subplots(figsize=(12, 8))

plot_cov = cov_df.copy()
plot_cov = plot_cov.iloc[::-1].reset_index(drop=True)
y_pos = range(len(plot_cov))

for i, (_, row) in enumerate(plot_cov.iterrows()):
    color = "#C44E52" if row["P"] < 0.05 else "#8C8C8C"
    marker = "D" if "Crude" in row["Model"] or "Reduced" in row["Model"] else "o"
    ax.errorbar(row["aOR"], i,
                xerr=[[row["aOR"] - row["CI_lower"]], [row["CI_upper"] - row["aOR"]]],
                fmt=marker, color=color, capsize=3, markersize=6, linewidth=1.2)

ax.axvline(1, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(plot_cov["Model"], fontsize=8)
ax.set_xlabel("Adjusted Odds Ratio (95% CI)")
ax.set_title("Covariate Sensitivity: Twin effect on 5-HT3 use\n(elective, low-risk subgroup)")

for i, (_, row) in enumerate(plot_cov.iterrows()):
    sig = "**" if row["P"] < 0.01 else "*" if row["P"] < 0.05 else ""
    ax.annotate(f"aOR {row['aOR']:.2f} [{row['CI_lower']:.2f}-{row['CI_upper']:.2f}] P={row['P']:.3f}{sig}",
                xy=(max(plot_cov["CI_upper"].max() * 1.05, 10), i),
                fontsize=7, va="center")

ax.set_xlim(0, max(plot_cov["CI_upper"].max() * 1.6, 12))
plt.tight_layout()
plt.savefig(FIG / "fig3_covariate_sensitivity.png")
plt.close()
print("Fig 3 saved")

# --- Fig 4: Broad vs Narrow comparison forest ---
fig, ax = plt.subplots(figsize=(10, 4))

compare_data = []
for key in ["A-Primary", "A-Secondary", "E-Primary", "E-Secondary"]:
    r = regression_results[key]
    compare_data.append({
        "Outcome": key, "Label": r["label"],
        "OR": r["twin_OR"], "CI_lo": r["twin_CI_lower"],
        "CI_hi": r["twin_CI_upper"], "P": r["twin_P"],
    })
compare_df = pd.DataFrame(compare_data).iloc[::-1].reset_index(drop=True)

y_pos = range(len(compare_df))
for i, (_, row) in enumerate(compare_df.iterrows()):
    color = "#C44E52" if row["P"] < 0.05 else "#4C72B0"
    ax.errorbar(row["OR"], i,
                xerr=[[row["OR"] - row["CI_lo"]], [row["CI_hi"] - row["OR"]]],
                fmt="o", color=color, capsize=4, markersize=8, linewidth=1.5)

ax.axvline(1, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(compare_df["Label"], fontsize=9)
ax.set_xlabel("Adjusted Odds Ratio (95% CI)")
ax.set_title("Twin effect on IONV: Broad vs Narrow\n(elective, low-risk subgroup)")

for i, (_, row) in enumerate(compare_df.iterrows()):
    sig = "**" if row["P"] < 0.01 else "*" if row["P"] < 0.05 else ""
    p_str = f"P={row['P']:.3f}" if row["P"] >= 0.001 else "P<0.001"
    ax.annotate(f"aOR {row['OR']:.2f} [{row['CI_lo']:.2f}-{row['CI_hi']:.2f}] {p_str}{sig}",
                xy=(max(compare_df["CI_hi"].max() * 1.05, 8), i),
                fontsize=8, va="center")

ax.set_xlim(0, max(compare_df["CI_hi"].max() * 1.6, 10))
plt.tight_layout()
plt.savefig(FIG / "fig4_broad_vs_narrow.png")
plt.close()
print("Fig 4 saved")

# ============================================================
# 7. SAVE SUMMARY JSON
# ============================================================
summary = {
    "n_total": n_total,
    "n_single_raw": n_single_raw,
    "n_twin_raw": n_twin_raw,
    "n_base": n_base,
    "n_base_single": int((df_base["twin"] == 0).sum()),
    "n_base_twin": int((df_base["twin"] == 1).sum()),
    "n_excl_additional": int(n_excl_total),
    "n_excl_additional_single": int(n_excl_s),
    "n_excl_additional_twin": int(n_excl_t),
    "exclusion_counts": {
        name: int(mask.fillna(False).sum()) for name, mask in excl_conditions.items()
    },
    "n_analysis": n_analysis,
    "n_single": n_single,
    "n_twin": n_twin,
    "outcomes": {
        key: {
            "label": label,
            "singleton_n": int(s[col].sum()),
            "singleton_pct": float(100 * s[col].mean()),
            "twin_n": int(t[col].sum()),
            "twin_pct": float(100 * t[col].mean()),
        }
        for key, (col, label) in outcomes.items()
    },
    "regression": regression_results,
    "covariate_sensitivity": cov_sensitivity,
}

with open(BASE / "excl_sensitivity_stats.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("\nSummary JSON saved")
print("\n" + "=" * 60)
print("EXCLUSION SENSITIVITY ANALYSIS COMPLETE")
print("=" * 60)
