"""
Stratified Bootstrap Analysis for IONV Logistic Regression.

Addresses the ~8:1 singleton-to-twin ratio by using stratified resampling
to maintain group proportions in each bootstrap sample.

Outputs:
  - bootstrap_results.json: Bootstrap CIs for all outcomes (main + subgroup)
  - tables_bootstrap/bootstrap_summary.csv: Summary table
  - figures_bootstrap/fig_bootstrap_comparison.png: Wald vs Bootstrap CI comparison
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats as scipy_stats
import statsmodels.api as sm
import json, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

np.random.seed(42)

plt.rcParams.update({
    "font.size": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE = Path(__file__).resolve().parent
FIG = BASE / "figures_bootstrap"
TAB = BASE / "tables_bootstrap"
FIG.mkdir(exist_ok=True)
TAB.mkdir(exist_ok=True)

N_BOOT = 10000

# ============================================================
# 1. DATA LOADING (reuse pipeline from analysis_def_e.py)
# ============================================================
print("=" * 60)
print("BOOTSTRAP ANALYSIS: Loading data")
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

for d in ["metoclopramide_mg", "droperidol_mg", "ondansetron_mg", "granisetron_mg",
          "novamin_mg", "atarax_p_mg", "dexamethasone_mg"]:
    df_analysis[d] = pd.to_numeric(df_analysis[d], errors="coerce")

# IONV outcomes
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

# Subgroup: exclude emergency, prior CS, HDP, preop steroid
df_analysis["preop_steroid"] = pd.to_numeric(df_analysis["preop_steroid"], errors="coerce").fillna(0)
sub_mask = (
    (df_analysis["emergency"] != 1) &
    (df_analysis["prior_cs"] != 1) &
    (df_analysis["HDP"] != 1) &
    (df_analysis["preop_steroid"] != 1)
)
df_subgroup = df_analysis[sub_mask].copy()

print(f"Primary analysis cohort: N={len(df_analysis)} "
      f"(Singleton {(df_analysis['twin']==0).sum()}, Twin {(df_analysis['twin']==1).sum()})")
print(f"Sensitivity subgroup: N={len(df_subgroup)} "
      f"(Singleton {(df_subgroup['twin']==0).sum()}, Twin {(df_subgroup['twin']==1).sum()})")

# ============================================================
# 2. BOOTSTRAP FUNCTIONS
# ============================================================
covariates_full = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency",
                   "prior_cs", "HDP", "epidural", "手術時間_min", "hypotension"]
covariates_reduced = ["twin", "年齢(歳)", "BMI", "GA_weeks", "emergency", "hypotension"]

# For subgroup (no emergency, prior_cs, HDP in data), further reduce covariates
covariates_subgroup_full = ["twin", "年齢(歳)", "BMI", "GA_weeks",
                            "epidural", "手術時間_min", "hypotension"]
covariates_subgroup_reduced = ["twin", "年齢(歳)", "BMI", "GA_weeks", "hypotension"]


def stratified_resample(data, rng):
    """Stratified bootstrap: resample within each twin group separately."""
    s = data[data["twin"] == 0]
    t = data[data["twin"] == 1]
    s_boot = s.sample(n=len(s), replace=True, random_state=rng.integers(1e9))
    t_boot = t.sample(n=len(t), replace=True, random_state=rng.integers(1e9))
    return pd.concat([s_boot, t_boot], ignore_index=True)


def fit_logit_or(data, outcome_col, covs):
    """Fit logistic regression and return twin aOR. Returns NaN on failure."""
    df_m = data[covs + [outcome_col]].dropna()
    if df_m[outcome_col].sum() < 2 or (df_m[outcome_col] == 0).sum() < 2:
        return np.nan
    X = sm.add_constant(df_m[covs].astype(float))
    y = df_m[outcome_col].astype(float)
    try:
        model = sm.Logit(y, X).fit(disp=0, maxiter=200, method="bfgs")
        return float(np.exp(model.params["twin"]))
    except Exception:
        try:
            model = sm.Logit(y, X).fit(disp=0, maxiter=200)
            return float(np.exp(model.params["twin"]))
        except Exception:
            return np.nan


def run_bootstrap(data, outcome_col, covs, n_boot=N_BOOT, label=""):
    """Run stratified bootstrap and return percentile + BCa CIs."""
    rng = np.random.default_rng(42)

    # Point estimate
    point_or = fit_logit_or(data, outcome_col, covs)
    print(f"  {label}: Point aOR = {point_or:.3f}")

    # Bootstrap
    boot_ors = np.empty(n_boot)
    n_fail = 0
    for i in range(n_boot):
        boot_data = stratified_resample(data, rng)
        boot_ors[i] = fit_logit_or(boot_data, outcome_col, covs)
        if np.isnan(boot_ors[i]):
            n_fail += 1

    valid = boot_ors[~np.isnan(boot_ors)]
    n_valid = len(valid)
    pct_fail = n_fail / n_boot * 100
    print(f"    Convergence: {n_valid}/{n_boot} ({100-pct_fail:.1f}%)")

    if n_valid < n_boot * 0.5:
        print(f"    WARNING: <50% convergence, CI unreliable")
        return {
            "point_aOR": round(point_or, 4) if not np.isnan(point_or) else None,
            "boot_median": None,
            "pct_CI_lower": None, "pct_CI_upper": None,
            "bca_CI_lower": None, "bca_CI_upper": None,
            "n_boot": n_boot, "n_valid": n_valid,
            "convergence_pct": round(100 - pct_fail, 1),
        }

    # Percentile CI
    pct_lo, pct_hi = np.percentile(valid, [2.5, 97.5])

    # BCa CI
    # Bias correction factor z0
    z0 = scipy_stats.norm.ppf(np.mean(valid < point_or))

    # Acceleration factor (jackknife)
    n = len(data)
    jack_ors = np.empty(n)
    # For speed, subsample jackknife if large
    if n > 500:
        jack_idx = np.random.default_rng(123).choice(n, size=500, replace=False)
    else:
        jack_idx = np.arange(n)
    jack_vals = []
    for idx in jack_idx:
        jack_data = data.drop(data.index[idx])
        val = fit_logit_or(jack_data, outcome_col, covs)
        if not np.isnan(val):
            jack_vals.append(val)
    jack_vals = np.array(jack_vals)

    if len(jack_vals) > 10:
        jack_mean = jack_vals.mean()
        num = np.sum((jack_mean - jack_vals) ** 3)
        den = 6 * (np.sum((jack_mean - jack_vals) ** 2)) ** 1.5
        a = num / den if den > 0 else 0

        alpha = np.array([0.025, 0.975])
        z_alpha = scipy_stats.norm.ppf(alpha)
        adj = z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha))
        bca_quantiles = scipy_stats.norm.cdf(adj)
        bca_quantiles = np.clip(bca_quantiles, 0.001, 0.999)
        bca_lo, bca_hi = np.percentile(valid, bca_quantiles * 100)
    else:
        bca_lo, bca_hi = pct_lo, pct_hi
        a = 0

    print(f"    Percentile 95% CI: [{pct_lo:.3f}, {pct_hi:.3f}]")
    print(f"    BCa 95% CI:        [{bca_lo:.3f}, {bca_hi:.3f}]")

    return {
        "point_aOR": round(point_or, 4),
        "boot_median": round(float(np.median(valid)), 4),
        "boot_mean": round(float(np.mean(valid)), 4),
        "pct_CI_lower": round(float(pct_lo), 4),
        "pct_CI_upper": round(float(pct_hi), 4),
        "bca_CI_lower": round(float(bca_lo), 4),
        "bca_CI_upper": round(float(bca_hi), 4),
        "n_boot": n_boot,
        "n_valid": n_valid,
        "convergence_pct": round(100 - pct_fail, 1),
        "bias_correction_z0": round(float(z0), 4) if not np.isnan(z0) else None,
        "acceleration_a": round(float(a), 6),
    }


# ============================================================
# 3. RUN BOOTSTRAP — MAIN COHORT
# ============================================================
print("\n" + "=" * 60)
print("3. BOOTSTRAP: MAIN COHORT (N={})".format(len(df_analysis)))
print("=" * 60)

outcomes_main = {
    "A-Primary":   ("ionv_A_primary",   covariates_full),
    "A-Secondary": ("ionv_A_secondary", covariates_full),
    "E-Primary":   ("ionv_E_primary",   covariates_reduced),
    "E-Secondary": ("ionv_E_secondary", covariates_reduced),
}

results = {"main_cohort": {}, "subgroup": {}}

for key, (col, covs) in outcomes_main.items():
    n_events = int(df_analysis[col].sum())
    actual_covs = covs if n_events >= 50 else covariates_reduced
    label = f"Main {key} (events={n_events})"
    results["main_cohort"][key] = run_bootstrap(
        df_analysis, col, actual_covs, label=label)
    results["main_cohort"][key]["events"] = n_events
    results["main_cohort"][key]["model_covariates"] = actual_covs

# ============================================================
# 4. RUN BOOTSTRAP — SUBGROUP
# ============================================================
print("\n" + "=" * 60)
print("4. BOOTSTRAP: SUBGROUP (N={})".format(len(df_subgroup)))
print("=" * 60)

outcomes_sub = {
    "A-Primary":   ("ionv_A_primary",   covariates_subgroup_full),
    "A-Secondary": ("ionv_A_secondary", covariates_subgroup_reduced),
    "E-Primary":   ("ionv_E_primary",   covariates_subgroup_reduced),
    "E-Secondary": ("ionv_E_secondary", covariates_subgroup_reduced),
}

for key, (col, covs) in outcomes_sub.items():
    n_events = int(df_subgroup[col].sum())
    actual_covs = covs if n_events >= 50 else covariates_subgroup_reduced
    label = f"Subgroup {key} (events={n_events})"
    results["subgroup"][key] = run_bootstrap(
        df_subgroup, col, actual_covs, label=label)
    results["subgroup"][key]["events"] = n_events

# ============================================================
# 5. LOAD WALD CIs FOR COMPARISON
# ============================================================
with open(BASE / "def_e_stats.json") as f:
    M = json.load(f)
with open(BASE / "excl_sensitivity_stats.json") as f:
    E_stats = json.load(f)

# Add Wald CIs to results
for key in ["A-Primary", "A-Secondary", "E-Primary", "E-Secondary"]:
    wald = M["regression"][key]
    results["main_cohort"][key]["wald_CI_lower"] = wald["twin_CI_lower"]
    results["main_cohort"][key]["wald_CI_upper"] = wald["twin_CI_upper"]
    results["main_cohort"][key]["wald_P"] = wald["twin_P"]

    wald_sub = E_stats["regression"][key]
    results["subgroup"][key]["wald_CI_lower"] = wald_sub["twin_CI_lower"]
    results["subgroup"][key]["wald_CI_upper"] = wald_sub["twin_CI_upper"]
    results["subgroup"][key]["wald_P"] = wald_sub["twin_P"]

# ============================================================
# 6. SAVE RESULTS
# ============================================================
with open(BASE / "bootstrap_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nResults saved to {BASE / 'bootstrap_results.json'}")

# Summary CSV
rows = []
for cohort, label in [("main_cohort", "Full cohort"), ("subgroup", "Low-risk subgroup")]:
    for key in ["A-Primary", "A-Secondary", "E-Primary", "E-Secondary"]:
        r = results[cohort][key]
        rows.append({
            "Cohort": label,
            "Outcome": key,
            "Events": r["events"],
            "aOR": r["point_aOR"],
            "Wald_CI": f"{r.get('wald_CI_lower',''):.2f}\u2013{r.get('wald_CI_upper',''):.2f}" if r.get("wald_CI_lower") else "",
            "Wald_P": f"{r.get('wald_P',''):.4f}" if r.get("wald_P") else "",
            "Boot_Pct_CI": f"{r['pct_CI_lower']:.2f}\u2013{r['pct_CI_upper']:.2f}" if r.get("pct_CI_lower") else "N/A",
            "Boot_BCa_CI": f"{r['bca_CI_lower']:.2f}\u2013{r['bca_CI_upper']:.2f}" if r.get("bca_CI_lower") else "N/A",
            "Boot_Median": r.get("boot_median"),
            "Convergence": f"{r['convergence_pct']}%",
        })
summary_df = pd.DataFrame(rows)
summary_df.to_csv(TAB / "bootstrap_summary.csv", index=False)
print(f"Summary saved to {TAB / 'bootstrap_summary.csv'}")

# ============================================================
# 7. FIGURE: Wald vs Bootstrap CI comparison
# ============================================================
print("\n" + "=" * 60)
print("7. FIGURE: Wald vs Bootstrap CI Comparison")
print("=" * 60)

fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax_idx, (cohort, cohort_label) in enumerate([
        ("main_cohort", f"Full Cohort (N = {len(df_analysis):,})"),
        ("subgroup", f"Low-Risk Subgroup (N = {len(df_subgroup):,})")]):
    ax = axes[ax_idx]

    outcome_labels = {
        "A-Primary": "Broad, Primary (before delivery)",
        "A-Secondary": "Broad, Secondary (any phase)",
        "E-Primary": "Narrow, Primary (5-HT3, before delivery)",
        "E-Secondary": "Narrow, Secondary (5-HT3, any phase)",
    }
    y_pos = list(range(len(outcome_labels)))
    y_labels = list(outcome_labels.values())

    for i, key in enumerate(outcome_labels.keys()):
        r = results[cohort][key]
        if r["point_aOR"] is None:
            continue

        or_val = r["point_aOR"]

        # Wald CI (blue)
        wald_lo = r.get("wald_CI_lower")
        wald_hi = r.get("wald_CI_upper")
        if wald_lo and wald_hi:
            ax.plot([wald_lo, wald_hi], [i + 0.1, i + 0.1],
                    color="steelblue", linewidth=2, label="Wald CI" if i == 0 else "")
            ax.plot(or_val, i + 0.1, "o", color="steelblue", markersize=8)

        # Bootstrap BCa CI (red)
        bca_lo = r.get("bca_CI_lower")
        bca_hi = r.get("bca_CI_upper")
        if bca_lo and bca_hi:
            ax.plot([bca_lo, bca_hi], [i - 0.1, i - 0.1],
                    color="firebrick", linewidth=2, label="Bootstrap BCa CI" if i == 0 else "")
            boot_med = r.get("boot_median", or_val)
            ax.plot(boot_med, i - 0.1, "D", color="firebrick", markersize=7)

    ax.axvline(x=1, color="gray", linestyle="--", linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Adjusted Odds Ratio (aOR)")
    ax.set_title(cohort_label, fontweight="bold")
    ax.set_xscale("log")
    ax.legend(loc="upper right", fontsize=8)

plt.suptitle("Wald vs Stratified Bootstrap Confidence Intervals for Twin Effect on IONV",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(FIG / "fig_bootstrap_comparison.png")
plt.close()
print(f"Figure saved to {FIG / 'fig_bootstrap_comparison.png'}")

# ============================================================
# 8. PRINT SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("SUMMARY: KEY FINDINGS")
print("=" * 60)
for cohort, label in [("main_cohort", "Full cohort"), ("subgroup", "Low-risk subgroup")]:
    print(f"\n--- {label} ---")
    for key in ["A-Primary", "A-Secondary", "E-Primary", "E-Secondary"]:
        r = results[cohort][key]
        if r["point_aOR"] is None:
            print(f"  {key}: Insufficient convergence")
            continue
        wald_str = f"Wald [{r.get('wald_CI_lower','?'):.2f}\u2013{r.get('wald_CI_upper','?'):.2f}]" if r.get("wald_CI_lower") else ""
        bca_str = f"BCa [{r.get('bca_CI_lower','?'):.2f}\u2013{r.get('bca_CI_upper','?'):.2f}]" if r.get("bca_CI_lower") else ""
        print(f"  {key}: aOR={r['point_aOR']:.2f}  {wald_str}  {bca_str}  "
              f"(events={r['events']}, conv={r['convergence_pct']}%)")

print("\nDone.")
