#!/usr/bin/env python3
"""
Cesarean Section Bleeding & Transfusion Analysis
=================================================
Retrospective analysis of blood loss and transfusion during singleton
cesarean sections (2014-2024).

Outputs
-------
- figures/  : PNG figures for the manuscript
- tables/   : CSV tables
- manuscript_methods_results.docx : Methods + Results draft
- figures.pptx : Editable figures (1 per slide)
"""

import os, re, warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import mannwhitneyu, chi2_contingency, kruskal, spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score, roc_curve

warnings.filterwarnings("ignore")

# Japanese font
plt.rcParams["font.family"] = "DejaVu Sans"
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)

BASE = Path(__file__).resolve().parent
FIG_DIR = BASE / "figures"
TBL_DIR = BASE / "tables"
FIG_DIR.mkdir(exist_ok=True)
TBL_DIR.mkdir(exist_ok=True)

# ============================================================
# 1. DATA LOADING & CLEANING
# ============================================================
print("=" * 60)
print("1. DATA LOADING & CLEANING")
print("=" * 60)

filepath = BASE / "data.xlsm"
raw = pd.read_excel(filepath, sheet_name="基本データ", engine="openpyxl")
print(f"Raw data: {raw.shape[0]} rows, {raw.shape[1]} columns")

# --- Exclusions ---
# Cases marked for exclusion in the notes column
excluded_mask = raw["Unnamed: 66"].str.contains("除外", na=False)
n_excluded = excluded_mask.sum()
print(f"Excluded (notes): {n_excluded}")

# Apply exclusions
df = raw[~excluded_mask].copy()
print(f"After exclusion: {df.shape[0]} rows")

# Drop the notes column
df.drop(columns=["Unnamed: 66"], inplace=True)

# --- Type conversions ---
# Date
df["手術日"] = pd.to_datetime(df["手術日"], format="mixed", errors="coerce")
df["year"] = df["手術日"].dt.year

# Body weight: convert to numeric
df["体重(kg)"] = pd.to_numeric(df["体重(kg)"], errors="coerce")

# Blood loss
df["総出血量"] = pd.to_numeric(df["総出血g(ml) "], errors="coerce")

# Gestational age: parse "38w2d" format → weeks as float
def parse_ga(val):
    if pd.isna(val):
        return np.nan
    m = re.match(r"(\d+)w(\d+)d", str(val))
    if m:
        return int(m.group(1)) + int(m.group(2)) / 7
    try:
        return float(val)
    except (ValueError, TypeError):
        return np.nan

df["GA_weeks"] = df["妊娠週数(週)"].apply(parse_ga)

# Surgery / anesthesia duration: parse "HH:MM" → minutes
def parse_duration(val):
    if pd.isna(val):
        return np.nan
    m = re.match(r"(\d+):(\d+)", str(val))
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    return np.nan

df["手術時間_min"] = df["手術所要"].apply(parse_duration)
df["麻酔時間_min"] = df["麻酔所要"].apply(parse_duration)

# BMI
df["BMI"] = df["体重(kg)"] / (df["身長(cm)"] / 100) ** 2

# Transfusion binary
df["transfusion"] = (df["輸血有無"] == "有").astype(int)

# Emergency binary: 予定=0, 緊急/臨時=1
df["emergency"] = df["緊急"].map({"予定": 0, "緊急": 1, "臨時": 1})

# Prior cesarean binary
df["prior_cs"] = df["帝王切開の既往"].apply(lambda x: 1 if x >= 1 else 0 if x == 0 else np.nan)

# Preeclampsia / HDP
df["HDP"] = df["妊娠高血圧症候群"].apply(lambda x: 1 if x == 1 else 0 if x == 0 else np.nan)

# Placenta previa from comorbidity text
df["placenta_previa"] = df["術前合併症"].str.contains("前置胎盤|低置胎盤", na=False).astype(int)

# Epidural use
df["epidural"] = df["硬膜外麻酔"]

# Vasopressor continuous infusion
df["vasopressor_infusion"] = df["術中昇圧薬持続投与の有無"]

# Uterine exteriorization
df["uterine_ext"] = df["子宮脱転"]

# Antiemetic use
df["antiemetic"] = df["術中制吐薬投与の有無"]

# Hypotension count
df["hypotension_count"] = pd.to_numeric(df["低血圧回数(回)"], errors="coerce")

# Oxytocin
df["oxytocin"] = pd.to_numeric(df["術中オキシトシン投与(U)"], errors="coerce")

# Fluid volume
df["fluid_ml"] = pd.to_numeric(df["術中輸液量(ml)"], errors="coerce")

# Define massive hemorrhage (≥1500 mL, a commonly used threshold for PPH)
df["massive_hemorrhage"] = df["総出血量"].apply(lambda x: int(x >= 1500) if pd.notna(x) else np.nan)

# Phenylephrine total dose
df["phenylephrine_mg"] = pd.to_numeric(df["術中フェニレフリン投与(mg)"], errors="coerce")
# Ephedrine total dose
df["ephedrine_mg"] = pd.to_numeric(df["術中エフェドリン投与(mg)"], errors="coerce")

# Period: early (2014-2018) vs late (2019-2024) for trend analysis
df["period"] = df["year"].apply(lambda y: "2014-2018" if y <= 2018 else "2019-2024")

print(f"\nFinal analysis cohort: n = {df.shape[0]}")
print(f"Blood loss available: {df['総出血量'].notna().sum()}")
print(f"Transfusion cases: {df['transfusion'].sum()} ({100*df['transfusion'].mean():.1f}%)")
print(f"Massive hemorrhage (>=1500 mL): {df['massive_hemorrhage'].sum()} "
      f"({100*df['massive_hemorrhage'].mean():.1f}%)")

# ============================================================
# 2. DESCRIPTIVE STATISTICS
# ============================================================
print("\n" + "=" * 60)
print("2. DESCRIPTIVE STATISTICS")
print("=" * 60)

def describe_continuous(series, name):
    s = series.dropna()
    return {
        "Variable": name,
        "n": len(s),
        "Mean": f"{s.mean():.1f}",
        "SD": f"{s.std():.1f}",
        "Median": f"{s.median():.1f}",
        "IQR": f"{s.quantile(0.25):.1f}-{s.quantile(0.75):.1f}",
        "Min": f"{s.min():.1f}",
        "Max": f"{s.max():.1f}",
    }

def describe_categorical(series, name, categories=None):
    s = series.dropna()
    total = len(s)
    if categories is None:
        categories = sorted(s.unique())
    rows = []
    for cat in categories:
        n = (s == cat).sum()
        rows.append({
            "Variable": f"{name}: {cat}",
            "n": n,
            "Percentage": f"{100*n/total:.1f}%",
        })
    return rows

# --- Table 1: Patient characteristics ---
table1_rows = []
cont_vars = [
    ("年齢(歳)", "Age (years)"),
    ("BMI", "BMI (kg/m\u00b2)"),
    ("GA_weeks", "Gestational age (weeks)"),
    ("手術時間_min", "Surgical duration (min)"),
    ("麻酔時間_min", "Anesthesia duration (min)"),
    ("総出血量", "Estimated blood loss (mL)"),
    ("fluid_ml", "Intravenous fluid (mL)"),
    ("hypotension_count", "Hypotension episodes"),
    ("oxytocin", "Oxytocin (U)"),
]

for col, name in cont_vars:
    table1_rows.append(describe_continuous(df[col], name))

table1_cont = pd.DataFrame(table1_rows)
print("\nContinuous variables:")
print(table1_cont.to_string(index=False))

# Categorical
cat_rows = []
cat_rows += describe_categorical(df["emergency"], "Emergency CS", [0, 1])
cat_rows += describe_categorical(df["ASA-PS"], "ASA-PS", [1.0, 2.0, 3.0])
cat_rows += describe_categorical(df["prior_cs"], "Prior cesarean", [0, 1])
cat_rows += describe_categorical(df["HDP"], "Hypertensive disorders of pregnancy", [0, 1])
cat_rows += describe_categorical(df["placenta_previa"], "Placenta previa/low-lying placenta", [0, 1])
cat_rows += describe_categorical(df["epidural"], "Epidural anesthesia", [0.0, 1.0])
cat_rows += describe_categorical(df["vasopressor_infusion"], "Continuous vasopressor infusion", [0.0, 1.0])
cat_rows += describe_categorical(df["antiemetic"], "Intraoperative antiemetic", [0.0, 1.0])
cat_rows += describe_categorical(df["transfusion"], "Transfusion", [0, 1])
cat_rows += describe_categorical(df["massive_hemorrhage"], "Massive hemorrhage (>=1500 mL)", [0, 1])

table1_cat = pd.DataFrame(cat_rows)
print("\nCategorical variables:")
print(table1_cat.to_string(index=False))

table1_cont.to_csv(TBL_DIR / "table1_continuous.csv", index=False)
table1_cat.to_csv(TBL_DIR / "table1_categorical.csv", index=False)

# ============================================================
# 3. TABLE 1 BY TRANSFUSION GROUP
# ============================================================
print("\n" + "=" * 60)
print("3. TABLE 1 BY TRANSFUSION GROUP")
print("=" * 60)

def compare_continuous_by_group(data, col, group_col):
    g0 = data.loc[data[group_col] == 0, col].dropna()
    g1 = data.loc[data[group_col] == 1, col].dropna()
    try:
        stat, p = mannwhitneyu(g0, g1, alternative="two-sided")
    except Exception:
        p = np.nan
    return {
        "Variable": col,
        "No transfusion median [IQR]": f"{g0.median():.1f} [{g0.quantile(0.25):.1f}-{g0.quantile(0.75):.1f}]",
        "No transfusion n": len(g0),
        "Transfusion median [IQR]": f"{g1.median():.1f} [{g1.quantile(0.25):.1f}-{g1.quantile(0.75):.1f}]",
        "Transfusion n": len(g1),
        "P-value": p,
    }

def compare_categorical_by_group(data, col, group_col):
    ct = pd.crosstab(data[col].dropna(), data[group_col])
    try:
        chi2, p, dof, expected = chi2_contingency(ct)
    except Exception:
        p = np.nan
    return {"Variable": col, "P-value": p, "Crosstab": ct.to_dict()}

t1_grp_rows = []
for col, name in cont_vars:
    if col == "総出血量":
        continue  # outcome variable
    row = compare_continuous_by_group(df, col, "transfusion")
    row["Variable"] = name
    t1_grp_rows.append(row)

table1_grouped = pd.DataFrame(t1_grp_rows)
print(table1_grouped.to_string(index=False))
table1_grouped.to_csv(TBL_DIR / "table1_by_transfusion.csv", index=False)

# ============================================================
# 4. BLOOD LOSS ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("4. BLOOD LOSS ANALYSIS")
print("=" * 60)

bl = df["総出血量"].dropna()
print(f"\nBlood loss (n={len(bl)}):")
print(f"  Mean ± SD: {bl.mean():.1f} ± {bl.std():.1f} mL")
print(f"  Median [IQR]: {bl.median():.1f} [{bl.quantile(0.25):.1f}-{bl.quantile(0.75):.1f}] mL")
print(f"  Range: {bl.min():.0f}-{bl.max():.0f} mL")

# By year
yearly = df.groupby("year")["総出血量"].agg(["median", "mean", "std", "count"])
yearly.columns = ["Median", "Mean", "SD", "n"]
print("\nBlood loss by year:")
print(yearly.to_string())
yearly.to_csv(TBL_DIR / "blood_loss_by_year.csv")

# By emergency
for grp_name, grp_col in [("Emergency", "emergency"), ("Prior CS", "prior_cs"),
                           ("HDP", "HDP"), ("Placenta previa", "placenta_previa"),
                           ("Epidural", "epidural")]:
    g0 = df.loc[df[grp_col] == 0, "総出血量"].dropna()
    g1 = df.loc[df[grp_col] == 1, "総出血量"].dropna()
    stat, p = mannwhitneyu(g0, g1, alternative="two-sided")
    print(f"\n{grp_name}: No={g0.median():.0f} mL (n={len(g0)}) vs Yes={g1.median():.0f} mL (n={len(g1)}), p={p:.4f}")

# Kruskal-Wallis by ASA-PS
groups_asa = [df.loc[df["ASA-PS"] == i, "総出血量"].dropna() for i in [1, 2, 3]]
stat, p_asa = kruskal(*[g for g in groups_asa if len(g) > 0])
print(f"\nASA-PS Kruskal-Wallis: p={p_asa:.4f}")

# Spearman correlations
for var, name in [("年齢(歳)", "Age"), ("BMI", "BMI"), ("GA_weeks", "GA"),
                  ("手術時間_min", "Surg duration"), ("hypotension_count", "Hypotension")]:
    tmp = df[[var, "総出血量"]].dropna()
    r, p = spearmanr(tmp[var], tmp["総出血量"])
    print(f"  Spearman {name} vs blood loss: r={r:.3f}, p={p:.4f}")

# ============================================================
# 5. MULTIVARIABLE ANALYSIS - BLOOD LOSS
# ============================================================
print("\n" + "=" * 60)
print("5. MULTIVARIABLE ANALYSIS - BLOOD LOSS (Log-transformed)")
print("=" * 60)

# Log-transform blood loss for normality
df["log_bl"] = np.log(df["総出血量"])

model_vars_bl = ["年齢(歳)", "BMI", "GA_weeks", "emergency", "prior_cs",
                 "HDP", "placenta_previa", "epidural", "手術時間_min",
                 "hypotension_count"]

df_model = df[model_vars_bl + ["log_bl"]].dropna()
print(f"Complete cases for regression: {len(df_model)}")

X = sm.add_constant(df_model[model_vars_bl])
y = df_model["log_bl"]
ols_model = sm.OLS(y, X).fit()
print(ols_model.summary())

# Back-transform coefficients to percent change
bl_results = pd.DataFrame({
    "Variable": model_vars_bl,
    "Coefficient": ols_model.params[1:],
    "95% CI lower": ols_model.conf_int().iloc[1:, 0],
    "95% CI upper": ols_model.conf_int().iloc[1:, 1],
    "% change": (np.exp(ols_model.params[1:]) - 1) * 100,
    "P-value": ols_model.pvalues[1:],
})
bl_results = bl_results.sort_values("P-value")
print("\nMultivariable linear regression (log-EBL):")
print(bl_results.to_string(index=False))
bl_results.to_csv(TBL_DIR / "regression_blood_loss.csv", index=False)

# ============================================================
# 6. LOGISTIC REGRESSION - TRANSFUSION
# ============================================================
print("\n" + "=" * 60)
print("6. LOGISTIC REGRESSION - TRANSFUSION")
print("=" * 60)

model_vars_tx = ["年齢(歳)", "BMI", "GA_weeks", "emergency", "prior_cs",
                 "HDP", "placenta_previa", "epidural", "手術時間_min"]

df_model_tx = df[model_vars_tx + ["transfusion"]].dropna()
print(f"Complete cases: {len(df_model_tx)}")
print(f"Events: {df_model_tx['transfusion'].sum()}")

X_tx = sm.add_constant(df_model_tx[model_vars_tx])
y_tx = df_model_tx["transfusion"]
logit_model = sm.Logit(y_tx, X_tx).fit(disp=0)
print(logit_model.summary())

# Odds ratios
or_results = pd.DataFrame({
    "Variable": model_vars_tx,
    "OR": np.exp(logit_model.params[1:]),
    "95% CI lower": np.exp(logit_model.conf_int().iloc[1:, 0]),
    "95% CI upper": np.exp(logit_model.conf_int().iloc[1:, 1]),
    "P-value": logit_model.pvalues[1:],
})
or_results = or_results.sort_values("P-value")
print("\nLogistic regression - Odds Ratios:")
print(or_results.to_string(index=False))
or_results.to_csv(TBL_DIR / "logistic_regression_transfusion.csv", index=False)

# ROC-AUC
y_pred = logit_model.predict(X_tx)
auc = roc_auc_score(y_tx, y_pred)
print(f"\nROC-AUC: {auc:.3f}")

# ============================================================
# 7. LOGISTIC REGRESSION - MASSIVE HEMORRHAGE (>=1500 mL)
# ============================================================
print("\n" + "=" * 60)
print("7. LOGISTIC REGRESSION - MASSIVE HEMORRHAGE (>=1500 mL)")
print("=" * 60)

df_model_mh = df[model_vars_tx + ["massive_hemorrhage"]].dropna()
print(f"Complete cases: {len(df_model_mh)}")
print(f"Events: {df_model_mh['massive_hemorrhage'].sum()}")

X_mh = sm.add_constant(df_model_mh[model_vars_tx])
y_mh = df_model_mh["massive_hemorrhage"]
logit_mh = sm.Logit(y_mh, X_mh).fit(disp=0)

or_mh = pd.DataFrame({
    "Variable": model_vars_tx,
    "OR": np.exp(logit_mh.params[1:]),
    "95% CI lower": np.exp(logit_mh.conf_int().iloc[1:, 0]),
    "95% CI upper": np.exp(logit_mh.conf_int().iloc[1:, 1]),
    "P-value": logit_mh.pvalues[1:],
})
or_mh = or_mh.sort_values("P-value")
print("\nLogistic regression - Massive hemorrhage OR:")
print(or_mh.to_string(index=False))
or_mh.to_csv(TBL_DIR / "logistic_regression_massive_hemorrhage.csv", index=False)

auc_mh = roc_auc_score(y_mh, logit_mh.predict(X_mh))
print(f"ROC-AUC: {auc_mh:.3f}")

# ============================================================
# 8. TEMPORAL TREND ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("8. TEMPORAL TREND ANALYSIS")
print("=" * 60)

yearly_stats = df.groupby("year").agg(
    n=("仮ID", "count"),
    blood_loss_median=("総出血量", "median"),
    blood_loss_mean=("総出血量", "mean"),
    transfusion_rate=("transfusion", "mean"),
    massive_hemorrhage_rate=("massive_hemorrhage", "mean"),
    emergency_rate=("emergency", "mean"),
).reset_index()

print(yearly_stats.to_string(index=False))
yearly_stats.to_csv(TBL_DIR / "yearly_trends.csv", index=False)

# Cochran-Armitage trend test for transfusion
from scipy.stats import pearsonr
r_tx, p_tx = pearsonr(yearly_stats["year"], yearly_stats["transfusion_rate"])
print(f"\nTrend - transfusion rate vs year: r={r_tx:.3f}, p={p_tx:.4f}")
r_mh, p_mh = pearsonr(yearly_stats["year"], yearly_stats["massive_hemorrhage_rate"])
print(f"Trend - massive hemorrhage rate vs year: r={r_mh:.3f}, p={p_mh:.4f}")
r_bl, p_bl = pearsonr(yearly_stats["year"], yearly_stats["blood_loss_median"])
print(f"Trend - median blood loss vs year: r={r_bl:.3f}, p={p_bl:.4f}")

# Period comparison
for var_name, var_col in [("Blood loss", "総出血量"), ("Transfusion", "transfusion"),
                          ("Massive hemorrhage", "massive_hemorrhage")]:
    g_early = df.loc[df["period"] == "2014-2018", var_col].dropna()
    g_late = df.loc[df["period"] == "2019-2024", var_col].dropna()
    if var_col == "総出血量":
        stat, p = mannwhitneyu(g_early, g_late, alternative="two-sided")
        print(f"\n{var_name}: Early median={g_early.median():.0f} vs Late median={g_late.median():.0f}, p={p:.4f}")
    else:
        ct = pd.crosstab(df["period"], df[var_col])
        chi2, p, dof, exp = chi2_contingency(ct)
        print(f"\n{var_name}: Early={g_early.mean()*100:.1f}% vs Late={g_late.mean()*100:.1f}%, p={p:.4f}")

# ============================================================
# 9. FIGURES
# ============================================================
print("\n" + "=" * 60)
print("9. GENERATING FIGURES")
print("=" * 60)

# --- Figure 1: Blood loss distribution ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Histogram
axes[0].hist(bl, bins=50, color="#4C72B0", edgecolor="white", alpha=0.8)
axes[0].axvline(bl.median(), color="red", linestyle="--", linewidth=2, label=f"Median: {bl.median():.0f} mL")
axes[0].axvline(1500, color="orange", linestyle=":", linewidth=2, label="Massive hemorrhage (1500 mL)")
axes[0].set_xlabel("Estimated blood loss (mL)")
axes[0].set_ylabel("Frequency")
axes[0].set_title("A) Distribution of estimated blood loss")
axes[0].legend(fontsize=9)

# Box plot by emergency
box_data = [df.loc[df["emergency"] == 0, "総出血量"].dropna(),
            df.loc[df["emergency"] == 1, "総出血量"].dropna()]
bp = axes[1].boxplot(box_data, labels=["Elective", "Emergency"],
                     patch_artist=True, widths=0.6,
                     showfliers=True, flierprops=dict(marker="o", markersize=3, alpha=0.3))
bp["boxes"][0].set_facecolor("#4C72B0")
bp["boxes"][1].set_facecolor("#DD8452")
axes[1].set_ylabel("Estimated blood loss (mL)")
axes[1].set_title("B) Blood loss by surgical urgency")

plt.tight_layout()
fig.savefig(FIG_DIR / "fig1_blood_loss_distribution.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 1: Blood loss distribution")

# --- Figure 2: Temporal trends ---
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 2a: Median blood loss
axes[0, 0].plot(yearly_stats["year"], yearly_stats["blood_loss_median"], "o-", color="#4C72B0", linewidth=2)
axes[0, 0].fill_between(yearly_stats["year"],
                         df.groupby("year")["総出血量"].quantile(0.25).values,
                         df.groupby("year")["総出血量"].quantile(0.75).values,
                         alpha=0.2, color="#4C72B0")
axes[0, 0].set_ylabel("Median EBL (mL)")
axes[0, 0].set_title("A) Median estimated blood loss")
axes[0, 0].set_xlabel("Year")

# 2b: Transfusion rate
axes[0, 1].bar(yearly_stats["year"], yearly_stats["transfusion_rate"] * 100,
               color="#DD8452", edgecolor="white")
axes[0, 1].set_ylabel("Transfusion rate (%)")
axes[0, 1].set_title("B) Transfusion rate")
axes[0, 1].set_xlabel("Year")

# 2c: Massive hemorrhage rate
axes[1, 0].bar(yearly_stats["year"], yearly_stats["massive_hemorrhage_rate"] * 100,
               color="#C44E52", edgecolor="white")
axes[1, 0].set_ylabel("Massive hemorrhage rate (%)")
axes[1, 0].set_title("C) Massive hemorrhage rate (EBL >= 1500 mL)")
axes[1, 0].set_xlabel("Year")

# 2d: Case volume
axes[1, 1].bar(yearly_stats["year"], yearly_stats["n"],
               color="#55A868", edgecolor="white")
axes[1, 1].set_ylabel("Number of cases")
axes[1, 1].set_title("D) Annual case volume")
axes[1, 1].set_xlabel("Year")

for ax in axes.flat:
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

plt.tight_layout()
fig.savefig(FIG_DIR / "fig2_temporal_trends.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 2: Temporal trends")

# --- Figure 3: Forest plot - Multivariable regression (blood loss) ---
var_labels = {
    "年齢(歳)": "Age (per year)",
    "BMI": "BMI (per kg/m\u00b2)",
    "GA_weeks": "Gestational age (per week)",
    "emergency": "Emergency (vs elective)",
    "prior_cs": "Prior cesarean (vs none)",
    "HDP": "HDP (vs none)",
    "placenta_previa": "Placenta previa (vs none)",
    "epidural": "Epidural (vs none)",
    "手術時間_min": "Surgical duration (per min)",
    "hypotension_count": "Hypotension episodes (per episode)",
}

fig, ax = plt.subplots(figsize=(8, 6))
bl_plot = bl_results.sort_values("P-value", ascending=False).copy()
bl_plot["label"] = bl_plot["Variable"].map(var_labels)
y_pos = range(len(bl_plot))

ax.errorbar(bl_plot["% change"], y_pos,
            xerr=[bl_plot["% change"] - (np.exp(bl_plot["95% CI lower"]) - 1) * 100,
                  (np.exp(bl_plot["95% CI upper"]) - 1) * 100 - bl_plot["% change"]],
            fmt="o", color="#4C72B0", capsize=4, markersize=8)
ax.axvline(0, color="grey", linestyle="--", linewidth=1)
ax.set_yticks(list(y_pos))
ax.set_yticklabels(bl_plot["label"])
ax.set_xlabel("% change in estimated blood loss (95% CI)")
ax.set_title("Multivariable linear regression: Factors associated with EBL")

for i, row in enumerate(bl_plot.itertuples()):
    sig = "***" if row._6 < 0.001 else "**" if row._6 < 0.01 else "*" if row._6 < 0.05 else ""
    ax.annotate(f"p={row._6:.3f}{sig}",
                xy=(max(bl_plot["% change"].max() * 0.6, 5), i),
                fontsize=8, va="center")

plt.tight_layout()
fig.savefig(FIG_DIR / "fig3_forest_blood_loss.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 3: Forest plot - blood loss")

# --- Figure 4: Forest plot - Logistic regression (transfusion) ---
fig, ax = plt.subplots(figsize=(8, 6))
or_plot = or_results.sort_values("P-value", ascending=False).copy()
or_plot["label"] = or_plot["Variable"].map(var_labels)
y_pos = range(len(or_plot))

ax.errorbar(or_plot["OR"], y_pos,
            xerr=[or_plot["OR"] - or_plot["95% CI lower"],
                  or_plot["95% CI upper"] - or_plot["OR"]],
            fmt="o", color="#C44E52", capsize=4, markersize=8)
ax.axvline(1, color="grey", linestyle="--", linewidth=1)
ax.set_xscale("log")
ax.set_yticks(list(y_pos))
ax.set_yticklabels(or_plot["label"])
ax.set_xlabel("Odds ratio (95% CI) — log scale")
ax.set_title("Multivariable logistic regression: Factors associated with transfusion")

for i, row in enumerate(or_plot.itertuples()):
    sig = "***" if row._5 < 0.001 else "**" if row._5 < 0.01 else "*" if row._5 < 0.05 else ""
    ax.annotate(f"OR {row.OR:.2f}, p={row._5:.3f}{sig}",
                xy=(or_plot["95% CI upper"].max() * 1.1, i),
                fontsize=8, va="center")

plt.tight_layout()
fig.savefig(FIG_DIR / "fig4_forest_transfusion.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 4: Forest plot - transfusion")

# --- Figure 5: Blood loss by key subgroups (violin plots) ---
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

subgroup_vars = [
    ("emergency", "Emergency CS", {0: "Elective", 1: "Emergency"}),
    ("prior_cs", "Prior cesarean", {0: "No", 1: "Yes"}),
    ("HDP", "HDP", {0: "No", 1: "Yes"}),
    ("placenta_previa", "Placenta previa", {0: "No", 1: "Yes"}),
    ("epidural", "Epidural", {0.0: "No", 1.0: "Yes"}),
    ("vasopressor_infusion", "Continuous vasopressor", {0.0: "No", 1.0: "Yes"}),
]

for idx, (var, title, labels) in enumerate(subgroup_vars):
    ax = axes[idx // 3, idx % 3]
    plot_df = df[["総出血量", var]].dropna()
    plot_df["group"] = plot_df[var].map(labels)
    
    sns.violinplot(x="group", y="総出血量", data=plot_df, ax=ax, 
                   palette=["#4C72B0", "#DD8452"], cut=0, inner="quartile")
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel("EBL (mL)")
    ax.axhline(1500, color="red", linestyle=":", alpha=0.5)

plt.suptitle("Estimated blood loss by clinical subgroups", fontsize=14, y=1.01)
plt.tight_layout()
fig.savefig(FIG_DIR / "fig5_subgroup_violins.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 5: Subgroup violin plots")

# --- Figure 6: ROC curves ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Transfusion ROC
fpr, tpr, _ = roc_curve(y_tx, y_pred)
axes[0].plot(fpr, tpr, color="#4C72B0", linewidth=2, label=f"AUC = {auc:.3f}")
axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5)
axes[0].set_xlabel("False positive rate")
axes[0].set_ylabel("True positive rate")
axes[0].set_title("A) ROC curve: Transfusion prediction")
axes[0].legend()

# Massive hemorrhage ROC
y_pred_mh = logit_mh.predict(X_mh)
fpr_mh, tpr_mh, _ = roc_curve(y_mh, y_pred_mh)
axes[1].plot(fpr_mh, tpr_mh, color="#C44E52", linewidth=2, label=f"AUC = {auc_mh:.3f}")
axes[1].plot([0, 1], [0, 1], "k--", alpha=0.5)
axes[1].set_xlabel("False positive rate")
axes[1].set_ylabel("True positive rate")
axes[1].set_title("B) ROC curve: Massive hemorrhage prediction")
axes[1].legend()

plt.tight_layout()
fig.savefig(FIG_DIR / "fig6_roc_curves.png", dpi=300, bbox_inches="tight")
plt.close()
print("  Fig 6: ROC curves")

# ============================================================
# 10. SAVE SUMMARY STATS FOR MANUSCRIPT
# ============================================================
print("\n" + "=" * 60)
print("10. SAVING SUMMARY FOR MANUSCRIPT")
print("=" * 60)

summary = {
    "total_raw": raw.shape[0],
    "n_excluded": n_excluded,
    "n_final": df.shape[0],
    "n_bl_available": df["総出血量"].notna().sum(),
    "bl_mean": bl.mean(),
    "bl_sd": bl.std(),
    "bl_median": bl.median(),
    "bl_iqr_low": bl.quantile(0.25),
    "bl_iqr_high": bl.quantile(0.75),
    "bl_range_min": bl.min(),
    "bl_range_max": bl.max(),
    "n_transfusion": df["transfusion"].sum(),
    "pct_transfusion": df["transfusion"].mean() * 100,
    "n_massive": df["massive_hemorrhage"].sum(),
    "pct_massive": df["massive_hemorrhage"].mean() * 100,
    "n_emergency": df["emergency"].sum(),
    "pct_emergency": df["emergency"].mean() * 100,
    "age_mean": df["年齢(歳)"].mean(),
    "age_sd": df["年齢(歳)"].std(),
    "ga_median": df["GA_weeks"].median(),
    "ga_iqr_low": df["GA_weeks"].quantile(0.25),
    "ga_iqr_high": df["GA_weeks"].quantile(0.75),
    "ols_r2": ols_model.rsquared,
    "ols_adj_r2": ols_model.rsquared_adj,
    "auc_transfusion": auc,
    "auc_massive": auc_mh,
    "year_range": f"{df['year'].min()}-{df['year'].max()}",
    "logit_tx_n": len(df_model_tx),
    "logit_tx_events": df_model_tx["transfusion"].sum(),
    "logit_mh_n": len(df_model_mh),
    "logit_mh_events": df_model_mh["massive_hemorrhage"].sum(),
    "ols_n": len(df_model),
}

# Save as JSON for manuscript generation
import json
with open(BASE / "summary_stats.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)

print("Summary stats saved.")
print("\nDone! All tables in tables/, all figures in figures/")
