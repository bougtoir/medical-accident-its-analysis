"""
IONV (Intraoperative Nausea and Vomiting) during Cesarean Section:
Effect of Twin Pregnancy

Retrospective single-center observational study
Period: 2014-04-01 to 2024-10-23
Primary outcome: antiemetic use (anesthesia start→delivery OR delivery→exit)
Secondary outcome: antiemetic use (anesthesia start→delivery only)
Comparison: singleton vs twin pregnancy
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

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
# 1. LOAD DATA
# ============================================================
print("=" * 60)
print("1. LOADING DATA")
print("=" * 60)

import os
single_file = [f for f in os.listdir(BASE) if f.startswith("single") and f.endswith(".xlsm")][0]
twin_file = [f for f in os.listdir(BASE) if f.startswith("twin") and f.endswith(".xlsx")][0]

raw_single = pd.read_excel(BASE / single_file, sheet_name="基本データ", engine="openpyxl")
raw_twin = pd.read_excel(BASE / twin_file, engine="openpyxl")

print(f"Single raw: {len(raw_single)} rows, {len(raw_single.columns)} columns")
print(f"Twin raw:   {len(raw_twin)} rows, {len(raw_twin.columns)} columns")

# ============================================================
# 2. HARMONIZE COLUMNS
# ============================================================
print("\n" + "=" * 60)
print("2. HARMONIZING COLUMNS")
print("=" * 60)

# Rename single columns for consistency
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

# Determine exclusion for single
excl_col = "Unnamed: 66" if "Unnamed: 66" in single.columns else single.columns[66]
single["exclusion_note"] = single[excl_col] if excl_col in single.columns else np.nan

# Twin rename
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

# Convert twin text-based columns to numeric (有=1, 無=0)
you_mu_map = {"有": 1, "無": 0}
for src, dst in [("antiemetic_any_str", "antiemetic_any"),
                 ("ae_pre_anesthesia_str", "ae_pre_anesthesia"),
                 ("ae_to_delivery_str", "ae_to_delivery"),
                 ("ae_post_delivery_str", "ae_post_delivery")]:
    if src in twin.columns:
        twin[dst] = twin[src].map(you_mu_map).astype(float)

# Convert other 有/無 columns in twin
for col in ["帝王切開の既往", "vasopressor_continuous", "高血圧合併妊娠", "妊娠高血圧症候群",
            "術前24時間以内の降圧薬使用", "preop_antiemetic"]:
    if col in twin.columns and not pd.api.types.is_numeric_dtype(twin[col]):
        twin[col] = twin[col].map(you_mu_map).astype(float)

# Twin: derive emergency from 緊急適応疾患 (non-"無" = emergency)
if "緊急適応疾患" in twin.columns:
    twin["emergency"] = twin["緊急適応疾患"].apply(
        lambda x: 0 if pd.isna(x) or str(x).strip() == "無" else 1
    )
else:
    twin["emergency"] = 0

# Single: derive emergency from 緊急 column (予定=0, 緊急/臨時=1)
if "緊急" in single.columns:
    single["emergency"] = single["緊急"].map({"予定": 0, "緊急": 1, "臨時": 1}).astype(float)
else:
    single["emergency"] = 0

# Add group indicator
single["twin"] = 0
twin["twin"] = 1

# Parse GA weeks from "36w2d" format to numeric weeks
def parse_ga_weeks(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    import re
    m = re.match(r"(\d+)w(\d+)d?", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 7
    try:
        return float(s)
    except ValueError:
        return np.nan

for df in [single, twin]:
    df["GA_weeks"] = df["妊娠週数(週)"].apply(parse_ga_weeks)

# Convert single surgery/anesthesia time to minutes if needed
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

# Numeric conversions
for df in [single, twin]:
    for col in ["年齢(歳)", "身長(cm)", "体重(kg)", "hypotension_count",
                "全身麻酔", "硬膜外麻酔", "脊髄くも膜下麻酔",
                "帝王切開の既往", "高血圧合併妊娠", "妊娠高血圧症候群",
                "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery",
                "preop_antiemetic", "vasopressor_continuous"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

# Compute BMI
for df in [single, twin]:
    h = pd.to_numeric(df["身長(cm)"], errors="coerce") / 100
    w = pd.to_numeric(df["体重(kg)"], errors="coerce")
    df["BMI"] = w / (h ** 2)

# Handle column name differences between single and twin
steroid_col_single = "術前1週間以内のステロイド使用" if "術前1週間以内のステロイド使用" in single.columns else "術前1週間以内のステロイド投与"
steroid_col_twin = "術前1週間以内のステロイド投与"
single.rename(columns={steroid_col_single: "preop_steroid"}, inplace=True)
twin.rename(columns={steroid_col_twin: "preop_steroid"}, inplace=True)

# Merge columns
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

# Filter to existing columns
s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]

df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)
print(f"Merged dataset: {len(df_all)} rows ({(df_all['twin']==0).sum()} single + {(df_all['twin']==1).sum()} twin)")

# Numeric conversions
for col in ["全身麻酔", "硬膜外麻酔", "脊髄くも膜下麻酔", "高血圧合併妊娠", "妊娠高血圧症候群",
            "帝王切開の既往", "preop_steroid", "preop_antiemetic",
            "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery"]:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

df_all["出血量_ml"] = pd.to_numeric(df_all["出血量_ml"], errors="coerce")
df_all["hypotension_count"] = pd.to_numeric(df_all["hypotension_count"], errors="coerce")

# Coerce all remaining numeric columns
numeric_cols = [
    "年齢(歳)", "身長(cm)", "体重(kg)", "BMI", "妊娠週数(週)",
    "手術時間_min", "麻酔時間_min", "出血量_ml", "輸液量_ml",
    "hypotension_count", "vasopressor_continuous",
    "ephedrine_mg", "phenylephrine_mg", "bupivacaine_mg", "fentanyl_ug", "morphine_mg",
    "metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
    "novamin_mg", "atarax_p_mg", "dexamethasone_mg", "emergency",
    "子宮脱転",
]
for col in numeric_cols:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

# ============================================================
# 3. APPLY EXCLUSION CRITERIA
# ============================================================
print("\n" + "=" * 60)
print("3. APPLYING EXCLUSION CRITERIA")
print("=" * 60)

n_total = len(df_all)

# Exclusion list
exclusions = []

# 3a. General anesthesia
ga_mask = df_all["全身麻酔"] == 1
exclusions.append(("General anesthesia", ga_mask.sum()))

# 3b. Pre-anesthesia SBP < 90 mmHg (from exclusion notes)
sbp_mask = df_all["exclusion_note"].str.contains("SBP90", na=False) | \
           df_all["exclusion_note"].str.contains("入室時SBP", na=False)
exclusions.append(("Pre-anesthesia SBP < 90 mmHg", sbp_mask.sum()))

# 3c. Intrauterine fetal death
iufd_mask = df_all["exclusion_note"].str.contains("胎児死亡|死亡", na=False) & \
            ~df_all["exclusion_note"].str.contains("全身麻酔", na=False)
exclusions.append(("Intrauterine fetal death", iufd_mask.sum()))

# 3d. Vanishing twin
vt_mask = df_all["exclusion_note"].str.contains("vanishing", case=False, na=False)
exclusions.append(("Vanishing twin", vt_mask.sum()))

# 3e. Triplet (品胎)
triplet_mask = df_all["exclusion_note"].str.contains("品胎", na=False)
exclusions.append(("Triplet pregnancy", triplet_mask.sum()))

# Combined exclusion mask (any marked for exclusion in note)
# Also include any generic "除外" in exclusion note
generic_exclude_mask = df_all["exclusion_note"].str.contains("除外", na=False)
all_exclude = generic_exclude_mask | ga_mask | sbp_mask | iufd_mask | vt_mask | triplet_mask

# Additionally exclude rows with NaN in key IONV columns (no anesthesia data available)
no_data_mask = df_all["antiemetic_any"].isna() & ~all_exclude
exclusions.append(("No anesthesia data available", no_data_mask.sum()))

all_exclude = all_exclude | no_data_mask

print(f"Total before exclusion: {n_total}")
for reason, n in exclusions:
    print(f"  {reason}: {n}")

# Apply exclusions
df = df_all[~all_exclude].copy()
print(f"\nAfter exclusion: {len(df)} ({(df['twin']==0).sum()} single + {(df['twin']==1).sum()} twin)")

# ============================================================
# 4. DEFINE OUTCOMES
# ============================================================
print("\n" + "=" * 60)
print("4. DEFINING OUTCOMES")
print("=" * 60)

# Primary outcome: antiemetic use at any time during surgery
# (麻酔開始〜胎児娩出 OR 胎児娩出〜退室)
# Per protocol: exclude patients who received pre-anesthesia antiemetic (入室〜麻酔開始=1)
# from outcome count, as these are likely prophylactic

df["ionv_primary"] = ((df["ae_to_delivery"] == 1) | (df["ae_post_delivery"] == 1)).astype(int)
df["ionv_secondary"] = (df["ae_to_delivery"] == 1).astype(int)

# Per protocol note: patients with pre-anesthesia antiemetic use
pre_ae_count = (df["ae_pre_anesthesia"] == 1).sum()
print(f"Patients with pre-anesthesia antiemetic: {pre_ae_count}")
print(f"  (per protocol, excluding from outcome analysis)")

# Exclude pre-anesthesia antiemetic users from primary analysis
df_analysis = df[df["ae_pre_anesthesia"] != 1].copy()
print(f"Analysis cohort (excluding pre-anesthesia antiemetic): {len(df_analysis)}")
print(f"  Singleton: {(df_analysis['twin']==0).sum()}")
print(f"  Twin: {(df_analysis['twin']==1).sum()}")

# Primary outcome rates
for grp_name, grp in [("Overall", df_analysis), 
                       ("Singleton", df_analysis[df_analysis["twin"]==0]),
                       ("Twin", df_analysis[df_analysis["twin"]==1])]:
    n = len(grp)
    p1 = grp["ionv_primary"].sum()
    p2 = grp["ionv_secondary"].sum()
    print(f"\n{grp_name} (n={n}):")
    print(f"  Primary IONV: {p1} ({100*p1/n:.1f}%)")
    print(f"  Secondary IONV (before delivery): {p2} ({100*p2/n:.1f}%)")

# HDP: merge 高血圧合併妊娠 and 妊娠高血圧症候群
df_analysis["HDP"] = ((df_analysis["高血圧合併妊娠"] == 1) | (df_analysis["妊娠高血圧症候群"] == 1)).astype(int)

# Hypotension binary (≥1 episode)
df_analysis["hypotension"] = (df_analysis["hypotension_count"] >= 1).astype(int).where(
    df_analysis["hypotension_count"].notna(), np.nan
)

# Uterine exteriorization: 子宮脱転 (0, 1, 2=unknown → treat 2 as missing)
df_analysis["uterine_exteriorization"] = df_analysis["子宮脱転"].replace(2, np.nan)

# Epidural
df_analysis["epidural"] = pd.to_numeric(df_analysis["硬膜外麻酔"], errors="coerce")

# Prior CS
df_analysis["prior_cs"] = pd.to_numeric(df_analysis["帝王切開の既往"], errors="coerce")

# BMI ≥ 35
df_analysis["bmi_ge35"] = (df_analysis["BMI"] >= 35).astype(int).where(df_analysis["BMI"].notna(), np.nan)

# ============================================================
# 5. TABLE 1: PATIENT CHARACTERISTICS
# ============================================================
print("\n" + "=" * 60)
print("5. TABLE 1: PATIENT CHARACTERISTICS (singleton vs twin)")
print("=" * 60)

def summarize_continuous(s_series, t_series, test="mannwhitneyu"):
    """Compare continuous variable between groups."""
    s = s_series.dropna()
    t = t_series.dropna()
    s_med = s.median()
    s_q1, s_q3 = s.quantile(0.25), s.quantile(0.75)
    t_med = t.median()
    t_q1, t_q3 = t.quantile(0.25), t.quantile(0.75)
    if test == "mannwhitneyu" and len(s) > 0 and len(t) > 0:
        stat, p = stats.mannwhitneyu(s, t, alternative="two-sided")
    else:
        p = np.nan
    return {
        "Singleton": f"{s_med:.1f} [{s_q1:.1f}–{s_q3:.1f}]",
        "Twin": f"{t_med:.1f} [{t_q1:.1f}–{t_q3:.1f}]",
        "Singleton_n": len(s),
        "Twin_n": len(t),
        "P-value": p,
    }

def summarize_categorical(s_series, t_series, test="chi2"):
    """Compare binary variable between groups."""
    s = s_series.dropna()
    t = t_series.dropna()
    s_n = int(s.sum())
    t_n = int(t.sum())
    s_pct = 100 * s_n / len(s) if len(s) > 0 else 0
    t_pct = 100 * t_n / len(t) if len(t) > 0 else 0
    # Chi-square or Fisher
    table = np.array([
        [s_n, len(s) - s_n],
        [t_n, len(t) - t_n]
    ])
    row_totals = table.sum(axis=1)
    col_totals = table.sum(axis=0)
    grand_total = table.sum()
    expected = np.outer(row_totals, col_totals) / grand_total
    if expected.min() < 5:
        _, p = stats.fisher_exact(table)
    else:
        _, p, _, _ = stats.chi2_contingency(table, correction=False)
    return {
        "Singleton": f"{s_n}/{len(s)} ({s_pct:.1f}%)",
        "Twin": f"{t_n}/{len(t)} ({t_pct:.1f}%)",
        "Singleton_n": len(s),
        "Twin_n": len(t),
        "P-value": p,
    }

s = df_analysis[df_analysis["twin"] == 0]
t = df_analysis[df_analysis["twin"] == 1]

table1_rows = []
# Continuous
for var, label in [("年齢(歳)", "Age (years)"),
                   ("BMI", "BMI (kg/m²)"),
                   ("GA_weeks", "Gestational age (weeks)"),
                   ("手術時間_min", "Surgery time (min)"),
                   ("麻酔時間_min", "Anesthesia time (min)"),
                   ("出血量_ml", "Estimated blood loss (mL)"),
                   ("輸液量_ml", "Infusion volume (mL)"),
                   ("hypotension_count", "Hypotensive episodes (count)"),
                   ("bupivacaine_mg", "Intrathecal bupivacaine (mg)"),
                   ("fentanyl_ug", "Intrathecal fentanyl (μg)"),
                   ]:
    if var in df_analysis.columns:
        row = summarize_continuous(s[var], t[var])
        row["Variable"] = label
        row["Type"] = "continuous"
        table1_rows.append(row)

# Categorical
for var, label in [("emergency", "Emergency CS"),
                   ("prior_cs", "Prior CS"),
                   ("HDP", "Hypertensive disorders of pregnancy"),
                   ("preop_steroid", "Preoperative steroid (≤1 week)"),
                   ("epidural", "Epidural anesthesia"),
                   ("vasopressor_continuous", "Continuous vasopressor infusion"),
                   ("hypotension", "Hypotension (SBP < 90 mmHg)"),
                   ("uterine_exteriorization", "Uterine exteriorization"),
                   ("bmi_ge35", "BMI ≥ 35 kg/m²"),
                   ]:
    if var in df_analysis.columns:
        row = summarize_categorical(s[var], t[var])
        row["Variable"] = label
        row["Type"] = "categorical"
        table1_rows.append(row)

table1 = pd.DataFrame(table1_rows)
table1 = table1[["Variable", "Type", "Singleton", "Twin", "P-value"]]
table1.to_csv(TAB / "table1_characteristics.csv", index=False)
print(table1.to_string(index=False))

# ============================================================
# 6. IONV OUTCOME TABLE
# ============================================================
print("\n" + "=" * 60)
print("6. IONV OUTCOME COMPARISON")
print("=" * 60)

ionv_rows = []
for outcome, label in [("ionv_primary", "Primary: any IONV (anesthesia→exit)"),
                        ("ionv_secondary", "Secondary: IONV before delivery"),
                        ("ae_post_delivery", "Post-delivery IONV only")]:
    row = summarize_categorical(s[outcome], t[outcome])
    row["Outcome"] = label
    ionv_rows.append(row)

ionv_table = pd.DataFrame(ionv_rows)[["Outcome", "Singleton", "Twin", "P-value"]]
ionv_table.to_csv(TAB / "table2_ionv_outcomes.csv", index=False)
print(ionv_table.to_string(index=False))

# ============================================================
# 7. ANTIEMETIC DRUG DETAILS
# ============================================================
print("\n" + "=" * 60)
print("7. ANTIEMETIC DRUG USAGE DETAILS")
print("=" * 60)

drug_rows = []
for var, label in [("metoclopramide_mg", "Metoclopramide"),
                   ("droperidol_mg", "Droperidol"),
                   ("ondansetron_mg", "Ondansetron"),
                   ("granisetron_mg", "Granisetron"),
                   ("novamin_mg", "Prochlorperazine (Novamin)"),
                   ("atarax_p_mg", "Hydroxyzine (Atarax-P)"),
                   ("dexamethasone_mg", "Dexamethasone")]:
    if var in df_analysis.columns:
        s_any = (pd.to_numeric(s[var], errors="coerce") > 0).sum()
        t_any = (pd.to_numeric(t[var], errors="coerce") > 0).sum()
        s_pct = 100 * s_any / len(s)
        t_pct = 100 * t_any / len(t)
        table = np.array([[s_any, len(s) - s_any], [t_any, len(t) - t_any]])
        row_totals = table.sum(axis=1)
        col_totals = table.sum(axis=0)
        grand_total = table.sum()
        expected = np.outer(row_totals, col_totals) / grand_total
        if expected.min() < 5:
            _, p = stats.fisher_exact(table)
        else:
            _, p, _, _ = stats.chi2_contingency(table, correction=False)
        drug_rows.append({
            "Drug": label,
            "Singleton": f"{s_any} ({s_pct:.1f}%)",
            "Twin": f"{t_any} ({t_pct:.1f}%)",
            "P-value": p,
        })

drug_table = pd.DataFrame(drug_rows)
drug_table.to_csv(TAB / "table3_antiemetic_drugs.csv", index=False)
print(drug_table.to_string(index=False))

# ============================================================
# 8. MULTIVARIABLE LOGISTIC REGRESSION
# ============================================================
print("\n" + "=" * 60)
print("8. MULTIVARIABLE LOGISTIC REGRESSION")
print("=" * 60)

# Covariates based on known IONV risk factors from literature
covariates = [
    "twin",           # exposure of interest
    "年齢(歳)",
    "BMI",
    "GA_weeks",
    "emergency",
    "prior_cs",
    "HDP",
    "epidural",
    "手術時間_min",
    "hypotension",
]

# Note: uterine_exteriorization excluded from model due to excessive missing data
# (available in only ~20% of the cohort → would reduce model n drastically)

# --- 8a. Primary outcome ---
df_model_p = df_analysis[covariates + ["ionv_primary"]].dropna()
print(f"Primary model: n={len(df_model_p)} complete cases")

X_p = sm.add_constant(df_model_p[covariates].astype(float))
y_p = df_model_p["ionv_primary"].astype(float)

try:
    logit_primary = sm.Logit(y_p, X_p).fit(disp=0, maxiter=200)
    print(logit_primary.summary2())

    # OR table
    or_p = pd.DataFrame({
        "Variable": covariates,
        "OR": np.exp(logit_primary.params[1:]),
        "95% CI lower": np.exp(logit_primary.conf_int().iloc[1:, 0]),
        "95% CI upper": np.exp(logit_primary.conf_int().iloc[1:, 1]),
        "P-value": logit_primary.pvalues[1:],
    })
    or_p.to_csv(TAB / "table4_logistic_primary.csv", index=False)
    print("\nOdds ratios (primary outcome):")
    print(or_p.to_string(index=False))
except Exception as e:
    print(f"Primary logistic regression error: {e}")
    logit_primary = None
    or_p = None

# --- 8b. Secondary outcome ---
df_model_s = df_analysis[covariates + ["ionv_secondary"]].dropna()
print(f"\nSecondary model: n={len(df_model_s)} complete cases")

X_s = sm.add_constant(df_model_s[covariates].astype(float))
y_s = df_model_s["ionv_secondary"].astype(float)

try:
    logit_secondary = sm.Logit(y_s, X_s).fit(disp=0, maxiter=200)

    or_s = pd.DataFrame({
        "Variable": covariates,
        "OR": np.exp(logit_secondary.params[1:]),
        "95% CI lower": np.exp(logit_secondary.conf_int().iloc[1:, 0]),
        "95% CI upper": np.exp(logit_secondary.conf_int().iloc[1:, 1]),
        "P-value": logit_secondary.pvalues[1:],
    })
    or_s.to_csv(TAB / "table5_logistic_secondary.csv", index=False)
    print("\nOdds ratios (secondary outcome):")
    print(or_s.to_string(index=False))
except Exception as e:
    print(f"Secondary logistic regression error: {e}")
    logit_secondary = None
    or_s = None

# ============================================================
# 9. FIGURES
# ============================================================
print("\n" + "=" * 60)
print("9. GENERATING FIGURES")
print("=" * 60)

# --- Fig 1: IONV rates by group (bar chart) ---
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

for ax, outcome, title in [
    (axes[0], "ionv_primary", "Primary outcome:\nAny intraoperative IONV"),
    (axes[1], "ionv_secondary", "Secondary outcome:\nIONV before delivery"),
]:
    s_rate = 100 * s[outcome].mean()
    t_rate = 100 * t[outcome].mean()
    
    # Confidence intervals (Wilson)
    from statsmodels.stats.proportion import proportion_confint
    s_ci = proportion_confint(s[outcome].sum(), len(s), method="wilson")
    t_ci = proportion_confint(t[outcome].sum(), len(t), method="wilson")
    
    bars = ax.bar(["Singleton", "Twin"], [s_rate, t_rate],
                  color=["#4C72B0", "#DD8452"], width=0.5,
                  yerr=[[s_rate - 100*s_ci[0], t_rate - 100*t_ci[0]], 
                        [100*s_ci[1] - s_rate, 100*t_ci[1] - t_rate]],
                  capsize=5, edgecolor="black", linewidth=0.5)
    
    ax.set_ylabel("IONV rate (%)")
    ax.set_title(title)
    
    for bar, rate in zip(bars, [s_rate, t_rate]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f"{rate:.1f}%", ha="center", fontsize=10, fontweight="bold")
    
    # P-value annotation
    row = [r for r in ionv_rows if outcome in r.get("Outcome", "")]
    if not row:
        row = ionv_rows[0] if outcome == "ionv_primary" else ionv_rows[1]
    else:
        row = row[0]
    p = row["P-value"]
    p_text = f"P = {p:.3f}" if p >= 0.001 else "P < 0.001"
    ax.text(0.5, max(s_rate, t_rate) + 5, p_text, ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(FIG / "fig1_ionv_rates.png")
plt.close()
print("Fig 1: IONV rates saved")

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

# --- Fig 2: Forest plot (primary outcome) ---
if or_p is not None:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    or_plot = or_p.copy()
    or_plot["label"] = or_plot["Variable"].map(label_map).fillna(or_plot["Variable"])
    or_plot = or_plot.sort_values("P-value", ascending=False)

    y_pos = range(len(or_plot))
    ax.errorbar(or_plot["OR"], y_pos,
                xerr=[or_plot["OR"] - or_plot["95% CI lower"],
                      or_plot["95% CI upper"] - or_plot["OR"]],
                fmt="o", color="#4C72B0", capsize=4, markersize=6)
    ax.axvline(1, color="red", linestyle="--", linewidth=0.8)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(or_plot["label"])
    ax.set_xlabel("Odds Ratio (95% CI)")
    ax.set_title("Multivariable logistic regression: Factors associated with IONV\n(Primary outcome)")
    
    for i, row in enumerate(or_plot.itertuples()):
        sig = "***" if row._5 < 0.001 else "**" if row._5 < 0.01 else "*" if row._5 < 0.05 else ""
        ax.annotate(f"OR {row.OR:.2f}, p={row._5:.3f}{sig}",
                    xy=(or_plot["95% CI upper"].max() * 1.05, i),
                    fontsize=8, va="center")
    
    plt.tight_layout()
    plt.savefig(FIG / "fig2_forest_primary.png")
    plt.close()
    print("Fig 2: Forest plot (primary) saved")

# --- Fig 3: Forest plot (secondary outcome) ---
if or_s is not None:
    fig, ax = plt.subplots(figsize=(10, 6))
    
    or_plot_s = or_s.copy()
    or_plot_s["label"] = or_plot_s["Variable"].map(label_map).fillna(or_plot_s["Variable"])
    or_plot_s = or_plot_s.sort_values("P-value", ascending=False)

    y_pos = range(len(or_plot_s))
    ax.errorbar(or_plot_s["OR"], y_pos,
                xerr=[or_plot_s["OR"] - or_plot_s["95% CI lower"],
                      or_plot_s["95% CI upper"] - or_plot_s["OR"]],
                fmt="o", color="#DD8452", capsize=4, markersize=6)
    ax.axvline(1, color="red", linestyle="--", linewidth=0.8)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(or_plot_s["label"])
    ax.set_xlabel("Odds Ratio (95% CI)")
    ax.set_title("Multivariable logistic regression: Factors associated with IONV\n(Secondary outcome: before delivery)")
    
    for i, row in enumerate(or_plot_s.itertuples()):
        sig = "***" if row._5 < 0.001 else "**" if row._5 < 0.01 else "*" if row._5 < 0.05 else ""
        ax.annotate(f"OR {row.OR:.2f}, p={row._5:.3f}{sig}",
                    xy=(or_plot_s["95% CI upper"].max() * 1.05, i),
                    fontsize=8, va="center")
    
    plt.tight_layout()
    plt.savefig(FIG / "fig3_forest_secondary.png")
    plt.close()
    print("Fig 3: Forest plot (secondary) saved")

# --- Fig 4: IONV timing breakdown ---
fig, ax = plt.subplots(figsize=(8, 5))

timing_data = {
    "Before delivery\n(anesthesia→delivery)": [100 * s["ae_to_delivery"].mean(), 100 * t["ae_to_delivery"].mean()],
    "After delivery\n(delivery→exit)": [100 * s["ae_post_delivery"].mean(), 100 * t["ae_post_delivery"].mean()],
}

x = np.arange(len(timing_data))
width = 0.3
bars1 = ax.bar(x - width/2, [v[0] for v in timing_data.values()], width, label="Singleton", color="#4C72B0", edgecolor="black", linewidth=0.5)
bars2 = ax.bar(x + width/2, [v[1] for v in timing_data.values()], width, label="Twin", color="#DD8452", edgecolor="black", linewidth=0.5)

ax.set_xticks(x)
ax.set_xticklabels(timing_data.keys())
ax.set_ylabel("IONV rate (%)")
ax.set_title("IONV rates by timing phase")
ax.legend()

for bars in [bars1, bars2]:
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.1f}%", ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(FIG / "fig4_ionv_timing.png")
plt.close()
print("Fig 4: IONV timing breakdown saved")

# --- Fig 5: Temporal trend ---
df_analysis["year"] = pd.to_datetime(df_analysis["手術日"], errors="coerce").dt.year
yearly = df_analysis.groupby(["year", "twin"]).agg(
    n=("ionv_primary", "count"),
    ionv_n=("ionv_primary", "sum"),
).reset_index()
yearly["ionv_rate"] = 100 * yearly["ionv_n"] / yearly["n"]

fig, ax = plt.subplots(figsize=(10, 5))
for grp, label, color in [(0, "Singleton", "#4C72B0"), (1, "Twin", "#DD8452")]:
    sub = yearly[yearly["twin"] == grp]
    ax.plot(sub["year"], sub["ionv_rate"], "o-", label=label, color=color, linewidth=2, markersize=6)
    for _, row in sub.iterrows():
        ax.annotate(f"n={int(row['n'])}", (row["year"], row["ionv_rate"]),
                    textcoords="offset points", xytext=(0, 10), fontsize=7, ha="center")

ax.set_xlabel("Year")
ax.set_ylabel("IONV rate (%)")
ax.set_title("Temporal trend of IONV rates")
ax.legend()
ax.set_xticks(sorted(yearly["year"].unique()))
plt.tight_layout()
plt.savefig(FIG / "fig5_temporal_trend.png")
plt.close()
print("Fig 5: Temporal trend saved")

# --- Fig 6: Antiemetic drug usage comparison ---
fig, ax = plt.subplots(figsize=(10, 5))

drugs = ["metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
         "novamin_mg", "atarax_p_mg", "dexamethasone_mg"]
drug_labels = ["Metoclopramide", "Droperidol", "Ondansetron", "Granisetron",
               "Prochlorperazine", "Hydroxyzine", "Dexamethasone"]

s_rates = []
t_rates = []
for drug in drugs:
    if drug in df_analysis.columns:
        s_rates.append(100 * (pd.to_numeric(s[drug], errors="coerce") > 0).mean())
        t_rates.append(100 * (pd.to_numeric(t[drug], errors="coerce") > 0).mean())
    else:
        s_rates.append(0)
        t_rates.append(0)

x = np.arange(len(drug_labels))
width = 0.35
ax.bar(x - width/2, s_rates, width, label="Singleton", color="#4C72B0", edgecolor="black", linewidth=0.5)
ax.bar(x + width/2, t_rates, width, label="Twin", color="#DD8452", edgecolor="black", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(drug_labels, rotation=30, ha="right")
ax.set_ylabel("Usage rate (%)")
ax.set_title("Antiemetic drug usage: Singleton vs Twin")
ax.legend()
plt.tight_layout()
plt.savefig(FIG / "fig6_antiemetic_drugs.png")
plt.close()
print("Fig 6: Antiemetic drug comparison saved")

# ============================================================
# 10. SAVE SUMMARY STATS FOR MANUSCRIPT
# ============================================================
print("\n" + "=" * 60)
print("10. SAVING SUMMARY FOR MANUSCRIPT")
print("=" * 60)

summary = {
    "n_total_before_exclusion": n_total,
    "n_single_raw": int((df_all["twin"] == 0).sum()),
    "n_twin_raw": int((df_all["twin"] == 1).sum()),
    "n_excluded": n_total - len(df),
    "n_after_exclusion": len(df),
    "n_pre_anesthesia_antiemetic_excluded": int(pre_ae_count),
    "n_analysis": len(df_analysis),
    "n_single": int((df_analysis["twin"] == 0).sum()),
    "n_twin": int((df_analysis["twin"] == 1).sum()),
    "ionv_primary_single_n": int(s["ionv_primary"].sum()),
    "ionv_primary_single_pct": float(100 * s["ionv_primary"].mean()),
    "ionv_primary_twin_n": int(t["ionv_primary"].sum()),
    "ionv_primary_twin_pct": float(100 * t["ionv_primary"].mean()),
    "ionv_secondary_single_n": int(s["ionv_secondary"].sum()),
    "ionv_secondary_single_pct": float(100 * s["ionv_secondary"].mean()),
    "ionv_secondary_twin_n": int(t["ionv_secondary"].sum()),
    "ionv_secondary_twin_pct": float(100 * t["ionv_secondary"].mean()),
}

# Add exclusion details
for reason, n in exclusions:
    key = reason.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("<", "lt").replace("≥", "ge")
    summary[f"excl_{key}"] = int(n)

# Add regression results
if logit_primary is not None:
    twin_idx = covariates.index("twin") + 1
    summary["primary_or_twin"] = float(np.exp(logit_primary.params.iloc[twin_idx]))
    ci = logit_primary.conf_int().iloc[twin_idx]
    summary["primary_or_twin_ci_lower"] = float(np.exp(ci.iloc[0]))
    summary["primary_or_twin_ci_upper"] = float(np.exp(ci.iloc[1]))
    summary["primary_or_twin_p"] = float(logit_primary.pvalues.iloc[twin_idx])
    summary["primary_model_n"] = len(df_model_p)
    summary["primary_model_events"] = int(df_model_p["ionv_primary"].sum())
    summary["primary_aic"] = float(logit_primary.aic)

if logit_secondary is not None:
    twin_idx = covariates.index("twin") + 1
    summary["secondary_or_twin"] = float(np.exp(logit_secondary.params.iloc[twin_idx]))
    ci = logit_secondary.conf_int().iloc[twin_idx]
    summary["secondary_or_twin_ci_lower"] = float(np.exp(ci.iloc[0]))
    summary["secondary_or_twin_ci_upper"] = float(np.exp(ci.iloc[1]))
    summary["secondary_or_twin_p"] = float(logit_secondary.pvalues.iloc[twin_idx])
    summary["secondary_model_n"] = len(df_model_s)
    summary["secondary_model_events"] = int(df_model_s["ionv_secondary"].sum())

import json
with open(BASE / "summary_stats.json", "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("Summary stats saved.")
print(json.dumps(summary, indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
print("Done! All tables in tables/, all figures in figures/")
print("=" * 60)
