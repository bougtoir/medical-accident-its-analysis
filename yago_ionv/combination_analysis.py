"""
Exhaustive combination analysis:
Test ALL combinations of IONV definitions (C–H elements)
as covariates/outcomes to find which produce significant
singleton vs twin differences.

Two approaches:
1. Outcome combinations: OR definitions together (e.g., C|D, C|E, C|D|E, ...)
   and test twin effect on combined outcome
2. Covariate combinations: Use different covariate sets with each definition
   to see which adjustments flip significance
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
from itertools import combinations
import os, re, json

BASE = Path(__file__).resolve().parent

# ============================================================
# DATA LOADING (same pipeline as sensitivity_analysis.py)
# ============================================================
print("Loading data...")

single_file = [f for f in os.listdir(BASE) if f.startswith("single") and f.endswith(".xlsm")][0]
twin_file = [f for f in os.listdir(BASE) if f.startswith("twin") and f.endswith(".xlsx")][0]

raw_single = pd.read_excel(BASE / single_file, sheet_name="基本データ", engine="openpyxl")
raw_twin = pd.read_excel(BASE / twin_file, engine="openpyxl")

single = raw_single.copy()
twin = raw_twin.copy()

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
}, inplace=True)
excl_col = "Unnamed: 66" if "Unnamed: 66" in single.columns else single.columns[66]
single["exclusion_note"] = single[excl_col] if excl_col in single.columns else np.nan

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
    "メモ": "exclusion_note",
}, inplace=True)

you_mu_map = {"有": 1, "無": 0}
for src, dst in [("antiemetic_any_str", "antiemetic_any"),
                 ("ae_pre_anesthesia_str", "ae_pre_anesthesia"),
                 ("ae_to_delivery_str", "ae_to_delivery"),
                 ("ae_post_delivery_str", "ae_post_delivery")]:
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
twin["手術時間_min"] = pd.to_numeric(twin["手術時間_min"], errors="coerce")

for df in [single, twin]:
    for col in ["年齢(歳)", "hypotension_count", "全身麻酔", "硬膜外麻酔",
                "帝王切開の既往", "高血圧合併妊娠", "妊娠高血圧症候群",
                "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    h = pd.to_numeric(df["身長(cm)"], errors="coerce") / 100
    w = pd.to_numeric(df["体重(kg)"], errors="coerce")
    df["BMI"] = w / (h ** 2)

merge_cols = [
    "手術日", "年齢(歳)", "BMI", "GA_weeks", "emergency", "帝王切開の既往",
    "高血圧合併妊娠", "妊娠高血圧症候群", "硬膜外麻酔", "手術時間_min",
    "hypotension_count", "全身麻酔",
    "antiemetic_any", "ae_pre_anesthesia", "ae_to_delivery", "ae_post_delivery",
    "metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
    "novamin_mg", "atarax_p_mg", "dexamethasone_mg",
    "exclusion_note", "twin",
]

s_cols = [c for c in merge_cols if c in single.columns]
t_cols = [c for c in merge_cols if c in twin.columns]
df_all = pd.concat([single[s_cols], twin[t_cols]], ignore_index=True)

for col in merge_cols:
    if col in df_all.columns and col not in ["exclusion_note", "手術日"]:
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
generic_mask = note.str.contains("除外", na=False)
no_data = df_all["antiemetic_any"].isna()
all_exclude = ga_mask | sbp_mask | iufd_mask | vt_mask | triplet_mask | \
              non_cs_mask | cardiac_mask | no_data | generic_mask
df = df_all[~all_exclude].copy()
df_analysis = df[df["ae_pre_anesthesia"] != 1].copy()

# Derived variables
df_analysis["HDP"] = ((df_analysis["高血圧合併妊娠"] == 1) | (df_analysis["妊娠高血圧症候群"] == 1)).astype(int)
df_analysis["hypotension"] = (df_analysis["hypotension_count"] >= 1).astype(int).where(
    df_analysis["hypotension_count"].notna(), np.nan)
df_analysis["epidural"] = pd.to_numeric(df_analysis["硬膜外麻酔"], errors="coerce")
df_analysis["prior_cs"] = pd.to_numeric(df_analysis["帝王切開の既往"], errors="coerce")

DRUGS = ["metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
         "novamin_mg", "atarax_p_mg", "dexamethasone_mg"]
for d in DRUGS:
    df_analysis[d] = pd.to_numeric(df_analysis[d], errors="coerce")

# Define all outcomes
df_analysis["ionv_A"] = ((df_analysis["ae_to_delivery"] == 1) | (df_analysis["ae_post_delivery"] == 1)).astype(int)
df_analysis["ionv_B"] = (df_analysis["ae_to_delivery"] == 1).astype(int)
df_analysis["ionv_C"] = ((df_analysis["ae_post_delivery"] == 1) & (df_analysis["ae_to_delivery"] != 1)).astype(int)
df_analysis["drug_count"] = sum((df_analysis[d].fillna(0) > 0).astype(int) for d in DRUGS)
df_analysis["ionv_D"] = (df_analysis["drug_count"] >= 2).astype(int)
df_analysis["ionv_E"] = ((df_analysis["ondansetron_mg"].fillna(0) > 0) | (df_analysis["granisetron_mg"].fillna(0) > 0)).astype(int)
dex_only = ((df_analysis["dexamethasone_mg"].fillna(0) > 0) &
            (sum((df_analysis[d].fillna(0) > 0).astype(int) for d in DRUGS if d != "dexamethasone_mg") == 0))
df_analysis["ionv_F"] = df_analysis["ionv_A"].copy()
df_analysis.loc[dex_only & (df_analysis["ionv_A"] == 1), "ionv_F"] = 0

print(f"Analysis cohort: {len(df_analysis)} (Singleton {(df_analysis['twin']==0).sum()}, Twin {(df_analysis['twin']==1).sum()})")

# ============================================================
# APPROACH 1: OUTCOME COMBINATIONS (OR of definitions)
# ============================================================
covariates_full = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency",
                   "prior_cs", "HDP", "epidural", "手術時間_min", "hypotension"]
covariates_reduced = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency", "hypotension"]

binary_defs = {
    "A": "ionv_A", "B": "ionv_B", "C": "ionv_C",
    "D": "ionv_D", "E": "ionv_E", "F": "ionv_F",
}

s = df_analysis[df_analysis["twin"] == 0]
t = df_analysis[df_analysis["twin"] == 1]

print("\n" + "=" * 100)
print("APPROACH 1: OUTCOME COMBINATIONS — OR of definitions as single outcome")
print("  For each combination, outcome = 1 if ANY included definition is 1")
print("=" * 100)

results = []

# Single definitions + all combinations of 2, 3, 4, 5, 6
all_def_keys = ["A", "B", "C", "D", "E", "F"]

for r in range(1, len(all_def_keys) + 1):
    for combo in combinations(all_def_keys, r):
        combo_name = "+".join(combo)
        # Create combined outcome
        combined = df_analysis[[binary_defs[k] for k in combo]].max(axis=1).astype(int)

        s_n = int(combined[df_analysis["twin"] == 0].sum())
        t_n = int(combined[df_analysis["twin"] == 1].sum())
        s_pct = 100 * s_n / len(s)
        t_pct = 100 * t_n / len(t)

        # Univariable P
        table = np.array([[s_n, len(s) - s_n], [t_n, len(t) - t_n]])
        row_t = table.sum(axis=1); col_t = table.sum(axis=0)
        exp = np.outer(row_t, col_t) / table.sum()
        if exp.min() < 5:
            _, p_uni = stats.fisher_exact(table)
        else:
            _, p_uni, _, _ = stats.chi2_contingency(table, correction=False)

        # Multivariable
        n_events = s_n + t_n
        if n_events < 5:
            results.append({
                "Combo": combo_name, "Size": len(combo),
                "S_n": s_n, "T_n": t_n, "S_pct": s_pct, "T_pct": t_pct,
                "P_uni": p_uni, "aOR": np.nan, "CI_lo": np.nan, "CI_hi": np.nan,
                "P_adj": np.nan, "Model": "skip",
            })
            continue

        covs = covariates_full if n_events >= 50 else covariates_reduced
        df_m = df_analysis[covs].copy()
        df_m["outcome"] = combined
        df_m = df_m.dropna()
        X = sm.add_constant(df_m[covs].astype(float))
        y = df_m["outcome"].astype(float)

        try:
            model = sm.Logit(y, X).fit(disp=0, maxiter=200)
            twin_idx = covs.index("twin") + 1
            aor = np.exp(model.params.iloc[twin_idx])
            ci = model.conf_int().iloc[twin_idx]
            ci_lo = np.exp(ci.iloc[0])
            ci_hi = np.exp(ci.iloc[1])
            p_adj = model.pvalues.iloc[twin_idx]
            model_type = "full" if len(covs) == len(covariates_full) else "reduced"
        except Exception:
            # Try reduced
            if covs == covariates_full:
                covs = covariates_reduced
                df_m = df_analysis[covs].copy()
                df_m["outcome"] = combined
                df_m = df_m.dropna()
                X = sm.add_constant(df_m[covs].astype(float))
                y = df_m["outcome"].astype(float)
                try:
                    model = sm.Logit(y, X).fit(disp=0, maxiter=200)
                    twin_idx = covs.index("twin") + 1
                    aor = np.exp(model.params.iloc[twin_idx])
                    ci = model.conf_int().iloc[twin_idx]
                    ci_lo = np.exp(ci.iloc[0])
                    ci_hi = np.exp(ci.iloc[1])
                    p_adj = model.pvalues.iloc[twin_idx]
                    model_type = "reduced"
                except Exception:
                    aor = ci_lo = ci_hi = p_adj = np.nan
                    model_type = "failed"
            else:
                aor = ci_lo = ci_hi = p_adj = np.nan
                model_type = "failed"

        results.append({
            "Combo": combo_name, "Size": len(combo),
            "S_n": s_n, "T_n": t_n, "S_pct": s_pct, "T_pct": t_pct,
            "P_uni": p_uni, "aOR": aor, "CI_lo": ci_lo, "CI_hi": ci_hi,
            "P_adj": p_adj, "Model": model_type,
        })

results_df = pd.DataFrame(results)

# Show significant results first
print("\n--- SIGNIFICANT COMBINATIONS (P < 0.05 in either univariable or adjusted) ---\n")
sig = results_df[(results_df["P_uni"] < 0.05) | (results_df["P_adj"] < 0.05)].copy()
sig = sig.sort_values("P_adj")

if len(sig) == 0:
    print("  No significant combinations found.")
else:
    print(f"{'Combination':<25} {'S%':>6} {'T%':>6} {'P(uni)':>8} {'aOR':>6} {'95% CI':>16} {'P(adj)':>8} {'Model':>8}")
    print("-" * 95)
    for _, row in sig.iterrows():
        ci_str = f"[{row['CI_lo']:.2f}–{row['CI_hi']:.2f}]" if pd.notna(row['CI_lo']) else "—"
        aor_str = f"{row['aOR']:.2f}" if pd.notna(row['aOR']) else "—"
        p_adj_str = f"{row['P_adj']:.4f}" if pd.notna(row['P_adj']) else "—"
        sig_uni = "*" if row["P_uni"] < 0.05 else ""
        sig_adj = "**" if pd.notna(row["P_adj"]) and row["P_adj"] < 0.01 else "*" if pd.notna(row["P_adj"]) and row["P_adj"] < 0.05 else ""
        print(f"{row['Combo']:<25} {row['S_pct']:>5.1f}% {row['T_pct']:>5.1f}% {row['P_uni']:>7.4f}{sig_uni} {aor_str:>6} {ci_str:>16} {p_adj_str:>8}{sig_adj} {row['Model']:>8}")

print(f"\n--- ALL COMBINATIONS SUMMARY ({len(results_df)} total) ---\n")
print(f"  Total combinations tested: {len(results_df)}")
print(f"  Significant univariable (P<0.05): {(results_df['P_uni'] < 0.05).sum()}")
print(f"  Significant adjusted (P<0.05): {(results_df['P_adj'].dropna() < 0.05).sum()}")

# ============================================================
# APPROACH 2: COVARIATE COMBINATIONS (which covariates flip E?)
# ============================================================
print("\n" + "=" * 100)
print("APPROACH 2: COVARIATE SENSITIVITY — Definition E with different covariate sets")
print("  Which covariates are essential for Definition E significance?")
print("=" * 100)

all_covs = ["年齢(歳)", "BMI", "GA_weeks", "emergency", "prior_cs", "HDP",
            "epidural", "手術時間_min", "hypotension"]

cov_results = []

# Twin only (crude)
df_e = df_analysis[["twin", "ionv_E"]].dropna()
X_crude = sm.add_constant(df_e[["twin"]].astype(float))
y_crude = df_e["ionv_E"].astype(float)
try:
    m_crude = sm.Logit(y_crude, X_crude).fit(disp=0)
    or_crude = np.exp(m_crude.params.iloc[1])
    ci_crude = m_crude.conf_int().iloc[1]
    p_crude = m_crude.pvalues.iloc[1]
    cov_results.append({"Covariates": "twin only (crude)", "aOR": or_crude,
                        "CI_lo": np.exp(ci_crude.iloc[0]), "CI_hi": np.exp(ci_crude.iloc[1]),
                        "P": p_crude, "n_covs": 0})
except Exception:
    pass

# Each covariate added one at a time
for cov in all_covs:
    covs = ["twin", cov]
    df_e = df_analysis[covs + ["ionv_E"]].dropna()
    X = sm.add_constant(df_e[covs].astype(float))
    y = df_e["ionv_E"].astype(float)
    try:
        m = sm.Logit(y, X).fit(disp=0)
        twin_idx = 1
        aor = np.exp(m.params.iloc[twin_idx])
        ci = m.conf_int().iloc[twin_idx]
        p = m.pvalues.iloc[twin_idx]
        cov_results.append({"Covariates": f"twin + {cov}", "aOR": aor,
                            "CI_lo": np.exp(ci.iloc[0]), "CI_hi": np.exp(ci.iloc[1]),
                            "P": p, "n_covs": 1})
    except Exception:
        pass

# Full model minus one covariate at a time
for cov_to_remove in all_covs:
    covs = ["twin"] + [c for c in all_covs if c != cov_to_remove]
    df_e = df_analysis[covs + ["ionv_E"]].dropna()
    X = sm.add_constant(df_e[covs].astype(float))
    y = df_e["ionv_E"].astype(float)
    try:
        m = sm.Logit(y, X).fit(disp=0)
        twin_idx = 1
        aor = np.exp(m.params.iloc[twin_idx])
        ci = m.conf_int().iloc[twin_idx]
        p = m.pvalues.iloc[twin_idx]
        cov_results.append({"Covariates": f"all MINUS {cov_to_remove}", "aOR": aor,
                            "CI_lo": np.exp(ci.iloc[0]), "CI_hi": np.exp(ci.iloc[1]),
                            "P": p, "n_covs": len(covs) - 1})
    except Exception:
        pass

# Reduced model (6 covs — what we used)
covs_reduced = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency", "hypotension"]
df_e = df_analysis[covs_reduced + ["ionv_E"]].dropna()
X = sm.add_constant(df_e[covs_reduced].astype(float))
y = df_e["ionv_E"].astype(float)
try:
    m = sm.Logit(y, X).fit(disp=0)
    aor = np.exp(m.params.iloc[1])
    ci = m.conf_int().iloc[1]
    p = m.pvalues.iloc[1]
    cov_results.append({"Covariates": "reduced (6 covs)", "aOR": aor,
                        "CI_lo": np.exp(ci.iloc[0]), "CI_hi": np.exp(ci.iloc[1]),
                        "P": p, "n_covs": 5})
except Exception:
    pass

cov_df = pd.DataFrame(cov_results)
print(f"\n{'Covariates':<35} {'aOR':>6} {'95% CI':>16} {'P':>8} {'Sig?':>5}")
print("-" * 75)
for _, row in cov_df.iterrows():
    sig = "**" if row["P"] < 0.01 else "*" if row["P"] < 0.05 else ""
    print(f"{row['Covariates']:<35} {row['aOR']:>6.2f} [{row['CI_lo']:.2f}–{row['CI_hi']:.2f}]     {row['P']:>7.4f} {sig}")

# ============================================================
# APPROACH 3: NON-SIGNIFICANT → check what makes them NOT significant
# ============================================================
print("\n" + "=" * 100)
print("APPROACH 3: ALL NON-SIGNIFICANT COMBOS — Why no significance?")
print("  Show the range of aOR and P-values for non-significant combinations")
print("=" * 100)

non_sig = results_df[(results_df["P_uni"] >= 0.05) & ((results_df["P_adj"] >= 0.05) | results_df["P_adj"].isna())].copy()
print(f"\n  Non-significant combinations: {len(non_sig)} / {len(results_df)}")
if len(non_sig) > 0:
    valid = non_sig[non_sig["aOR"].notna()]
    print(f"  aOR range: {valid['aOR'].min():.2f} – {valid['aOR'].max():.2f}")
    print(f"  P (adj) range: {valid['P_adj'].min():.4f} – {valid['P_adj'].max():.4f}")
    # Show borderline ones (P 0.05-0.10)
    borderline = valid[(valid["P_adj"] >= 0.05) & (valid["P_adj"] < 0.10)]
    if len(borderline) > 0:
        print(f"\n  Borderline (0.05 ≤ P < 0.10): {len(borderline)}")
        for _, row in borderline.sort_values("P_adj").iterrows():
            print(f"    {row['Combo']:<25} aOR={row['aOR']:.2f} P={row['P_adj']:.4f}")

# Save results
results_df.to_csv(BASE / "tables" / "combination_analysis.csv", index=False)
cov_df.to_csv(BASE / "tables" / "covariate_sensitivity_E.csv", index=False)
print(f"\nResults saved to tables/combination_analysis.csv and tables/covariate_sensitivity_E.csv")
