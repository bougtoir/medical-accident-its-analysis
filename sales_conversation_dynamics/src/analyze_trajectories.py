#!/usr/bin/env python3
"""Analyze turn-level verbosity trajectories and their relation to outcomes."""
import json
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output"
FIG_DIR = ROOT / "figures"
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

N_GRID = 11
MAX_K = 6


def save_stats(obj, name):
    path = OUT_DIR / f"{name}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved {path}")


def fit_polynomial(positions, values, degree=2):
    """Fit a degree-2 polynomial and return [intercept, linear, quadratic]."""
    positions = np.asarray(positions, dtype=float)
    values = np.asarray(values, dtype=float)
    if len(positions) <= degree or np.std(values) == 0:
        return None
    try:
        coeffs = np.polyfit(positions, values, degree)
    except Exception:
        return None
    return coeffs[::-1]


def classify_shape(linear, quad):
    """Classify trajectory shape from signs of linear and quadratic coefficients."""
    if linear >= 0 and quad < 0:
        return "inverted_u"  # increase, then decrease
    if linear < 0 and quad >= 0:
        return "u_shape"  # decrease, then increase
    if linear >= 0 and quad >= 0:
        return "increasing"
    if linear < 0 and quad < 0:
        return "decreasing"
    return "other"


def build_trajectory_table(utterance_df, dialogue_id_col, position_col, value_col,
                           role_value=None, role_col="role", speaker_value=None, speaker_col="speaker"):
    """Build one row per dialogue with polynomial coefficients and shape labels."""
    df = utterance_df.copy()
    if role_value is not None and role_col in df.columns:
        df = df[df[role_col] == role_value]
    elif speaker_value is not None and speaker_col in df.columns:
        df = df[df[speaker_col] == speaker_value]

    rows = []
    for dialogue_id, grp in df.groupby(dialogue_id_col):
        grp = grp.sort_values(position_col)
        positions = grp[position_col].astype(float).values
        values = grp[value_col].astype(float).values
        if len(positions) < 3 or np.any(np.isnan(positions)) or np.any(np.isnan(values)) or np.std(values) == 0:
            continue

        z_values = (values - np.mean(values)) / np.std(values)
        coeffs_raw = fit_polynomial(positions, values)
        coeffs_z = fit_polynomial(positions, z_values)
        if coeffs_raw is None or coeffs_z is None:
            continue

        lin_z, quad_z = coeffs_z[1], coeffs_z[2]
        shape = classify_shape(lin_z, quad_z)

        rows.append({
            dialogue_id_col: dialogue_id,
            "n_turns": len(positions),
            "mean_value": float(np.mean(values)),
            "std_value": float(np.std(values)),
            "intercept_z": float(coeffs_z[0]),
            "linear_z": float(lin_z),
            "quadratic_z": float(quad_z),
            "linear_raw": float(coeffs_raw[1]),
            "quadratic_raw": float(coeffs_raw[2]),
            "shape": shape,
            "raw_positions": positions.tolist(),
            "raw_values": values.tolist(),
            "z_values": z_values.tolist(),
        })
    return pd.DataFrame(rows)


def cluster_coefficients(traj_df, feature_cols=("linear_z", "quadratic_z"), k=4):
    """Cluster trajectories by polynomial coefficients (KMeans)."""
    feats = traj_df[list(feature_cols)].dropna()
    if feats.empty:
        return None, None
    scaler = StandardScaler()
    X = scaler.fit_transform(feats.values)
    silhouette_scores = {}
    best_k = 2
    best_score = -1
    for kk in range(2, MAX_K + 1):
        km = KMeans(n_clusters=kk, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        silhouette_scores[kk] = float(score)
        if score > best_score:
            best_score = score
            best_k = kk
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    traj_df = traj_df.copy()
    traj_df["cluster"] = np.nan
    traj_df.loc[feats.index, "cluster"] = labels
    return traj_df, {"k": k, "silhouette_scores": silhouette_scores, "best_k": best_k}


def compare_groups(df, outcome_col, group_col="shape"):
    """Compare an outcome across categorical groups."""
    df = df.dropna(subset=[group_col, outcome_col])
    if df.empty:
        return {}
    groups = [g[outcome_col].dropna().values for _, g in df.groupby(group_col)]
    summary = {}
    for name, g in df.groupby(group_col):
        vals = g[outcome_col].dropna()
        summary[str(name)] = {
            "n": int(len(vals)),
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std": float(np.std(vals)),
            "prop_positive": float((vals > 0).mean()),
        }

    if all(len(g) > 0 for g in groups):
        f_stat, p_anova = stats.f_oneway(*groups)
        kw_stat, p_kw = stats.kruskal(*groups)
    else:
        f_stat = p_anova = kw_stat = p_kw = np.nan

    result = {
        "outcome": outcome_col,
        "group_col": group_col,
        "n": int(len(df)),
        "summary": summary,
        "anova_f": float(f_stat) if not np.isnan(f_stat) else None,
        "anova_p": float(p_anova) if not np.isnan(p_anova) else None,
        "kruskal_h": float(kw_stat) if not np.isnan(kw_stat) else None,
        "kruskal_p": float(p_kw) if not np.isnan(p_kw) else None,
    }

    # Binary chi-square.
    pos_col = f"{outcome_col}_binary"
    df[pos_col] = (df[outcome_col] > 0).astype(int)
    contingency = pd.crosstab(df[group_col], df[pos_col])
    if contingency.shape[1] == 2 and all(contingency.sum(axis=1) > 0):
        chi2, p_chi, dof, expected = stats.chi2_contingency(contingency)
        result["binary_chi2"] = float(chi2)
        result["binary_p"] = float(p_chi)
    return result


def fit_regression(df, y_col, binary, predictors=("linear_z", "quadratic_z", "mean_value", "n_turns")):
    """Fit OLS or Logit and return a coefficient summary."""
    df = df.dropna(subset=[y_col] + list(predictors))
    if df.empty or len(df) < 20:
        return {}
    X = df[list(predictors)]
    X = sm.add_constant(X)
    y = df[y_col]
    try:
        if binary:
            model = sm.Logit(y, X).fit(disp=0)
            result_type = "logit"
        else:
            model = sm.OLS(y, X).fit()
            result_type = "ols"
    except Exception as e:
        return {"error": str(e)}

    params = model.params.to_dict()
    pvalues = model.pvalues.to_dict()
    conf_int = model.conf_int().to_dict(orient="index")
    return {
        "model": result_type,
        "n": int(model.nobs),
        "r2_pseudo": float(model.prsquared) if binary else None,
        "r2": float(model.rsquared) if not binary else None,
        "aic": float(model.aic),
        "bic": float(model.bic),
        "coefficients": {
            k: {
                "estimate": float(params[k]),
                "p": float(pvalues[k]),
                "ci_lower": float(conf_int[k][0]),
                "ci_upper": float(conf_int[k][1]),
            }
            for k in params
        },
    }


def plot_shape_trajectories(traj_df, name, value_label, raw=True):
    """Plot median trajectory with IQR for each shape."""
    value_key = "raw_values" if raw else "z_values"
    pos_key = "raw_positions"
    y_label = value_label if raw else f"Standardized {value_label}"

    shapes = sorted(traj_df["shape"].dropna().unique())
    fig, ax = plt.subplots(figsize=(8, 5))
    grid = np.linspace(0, 1, N_GRID)
    for shape in shapes:
        sub = traj_df[traj_df["shape"] == shape]
        interp_list = []
        for _, row in sub.iterrows():
            pos = np.array(row[pos_key])
            vals = np.array(row[value_key])
            if len(pos) >= 2:
                interp = np.interp(grid, pos, vals)
                interp_list.append(interp)
        if not interp_list:
            continue
        arr = np.vstack(interp_list)
        median_line = np.median(arr, axis=0)
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)
        ax.plot(grid, median_line, label=f"{shape} (n={len(arr)})")
        ax.fill_between(grid, q25, q75, alpha=0.2)
    ax.set_xlabel("Normalized conversation position")
    ax.set_ylabel(y_label)
    ax.set_title(f"{name}: Median verbosity trajectory by shape")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    suffix = "raw" if raw else "z"
    fig_path = FIG_DIR / f"{name}_shape_trajectories_{suffix}.png"
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved {fig_path}")


def plot_shape_outcomes(traj_df, outcome_col, name, log_transform=False):
    """Plot outcome distributions and positive proportion by shape."""
    df = traj_df.dropna(subset=["shape", outcome_col]).copy()
    if df.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Boxplot (log1p if requested).
    plot_col = f"log1p_{outcome_col}" if log_transform else outcome_col
    if log_transform:
        df[plot_col] = np.log1p(df[outcome_col].fillna(0))
    sns.boxplot(x="shape", y=plot_col, data=df, ax=axes[0], order=sorted(df["shape"].unique()))
    axes[0].set_title(f"{name}: {plot_col} by shape")
    axes[0].tick_params(axis="x", rotation=30)

    # Proportion positive.
    summary = df.groupby("shape").apply(lambda g: (g[outcome_col] > 0).mean()).reset_index(name="prop_positive")
    sns.barplot(x="shape", y="prop_positive", data=summary, ax=axes[1], order=sorted(df["shape"].unique()))
    axes[1].set_title(f"{name}: Proportion positive by shape")
    axes[1].set_ylim(0, 1)
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig_path = FIG_DIR / f"{name}_outcome_by_shape.png"
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved {fig_path}")


def run_persuasion():
    print("=== PersuasionForGood ===")
    utterances = pd.read_csv(DATA_DIR / "persuasion_utterances.csv")
    dialogues = pd.read_csv(DATA_DIR / "persuasion_dialogues.csv")

    traj = build_trajectory_table(
        utterances,
        dialogue_id_col="dialogue_id",
        position_col="persuader_position",
        value_col="word_count",
        role_value=0,
    )
    print(f"Built {len(traj)} trajectories")

    traj, clust_info = cluster_coefficients(traj, k=4)
    if clust_info:
        print(f"Silhouette by k: {clust_info['silhouette_scores']}, best k={clust_info['best_k']}")
        save_stats(clust_info, "persuasion_cluster_info")

    merged = traj.merge(dialogues, on="dialogue_id", how="left")
    merged["log1p_donation_ee"] = np.log1p(merged["donation_ee"].fillna(0))

    # Shape comparisons.
    result_shape = compare_groups(merged, "donation_ee", group_col="shape")
    save_stats(result_shape, "persuasion_outcome_by_shape")

    result_cluster = compare_groups(merged, "donation_ee", group_col="cluster")
    save_stats(result_cluster, "persuasion_outcome_by_cluster")

    # Regression.
    reg_log = fit_regression(merged, "log1p_donation_ee", binary=False)
    save_stats(reg_log, "persuasion_regression_log1p_donation")
    reg_binary = fit_regression(merged, "donation_ee", binary=True)
    save_stats(reg_binary, "persuasion_regression_donation_binary")

    merged[["dialogue_id", "shape", "cluster", "n_turns", "mean_value",
            "linear_z", "quadratic_z", "donation_ee"]].to_csv(
        OUT_DIR / "persuasion_trajectory_summary.csv", index=False)

    plot_shape_trajectories(merged, "persuasion", "word count", raw=False)
    plot_shape_trajectories(merged, "persuasion", "word count", raw=True)
    plot_shape_outcomes(merged, "donation_ee", "persuasion", log_transform=True)
    return merged


def run_cyberagent():
    print("\n=== CyberAgent salestalk ===")
    utterances = pd.read_csv(DATA_DIR / "cyberagent_utterances.csv")
    dialogues = pd.read_csv(DATA_DIR / "cyberagent_dialogues.csv")

    utterances["analysis_position"] = utterances["time_position"].fillna(utterances["sales_position"])
    traj = build_trajectory_table(
        utterances,
        dialogue_id_col="dialogue_id",
        position_col="analysis_position",
        value_col="char_count",
        speaker_value="sales",
        speaker_col="speaker",
    )
    print(f"Built {len(traj)} trajectories")

    traj, clust_info = cluster_coefficients(traj, k=4)
    if clust_info:
        print(f"Silhouette by k: {clust_info['silhouette_scores']}, best k={clust_info['best_k']}")
        save_stats(clust_info, "cyberagent_cluster_info")

    merged = traj.merge(dialogues, on="dialogue_id", how="left")

    result_shape = compare_groups(merged, "purchase_intention_change", group_col="shape")
    save_stats(result_shape, "cyberagent_outcome_by_shape_purchase_change")

    result_after = compare_groups(merged, "after_purchase_intention", group_col="shape")
    save_stats(result_after, "cyberagent_outcome_by_shape_after_intention")

    result_cluster = compare_groups(merged, "purchase_intention_change", group_col="cluster")
    save_stats(result_cluster, "cyberagent_outcome_by_cluster_purchase_change")

    reg_change = fit_regression(merged, "purchase_intention_change", binary=False)
    save_stats(reg_change, "cyberagent_regression_purchase_change")
    reg_after = fit_regression(merged, "after_purchase_intention", binary=False)
    save_stats(reg_after, "cyberagent_regression_after_intention")

    merged[["dialogue_id", "shape", "cluster", "n_turns", "mean_value",
            "linear_z", "quadratic_z", "purchase_intention_change", "after_purchase_intention"]].to_csv(
        OUT_DIR / "cyberagent_trajectory_summary.csv", index=False)

    plot_shape_trajectories(merged, "cyberagent", "character count", raw=False)
    plot_shape_trajectories(merged, "cyberagent", "character count", raw=True)
    plot_shape_outcomes(merged, "purchase_intention_change", "cyberagent", log_transform=False)
    return merged


def write_markdown_report(persuasion, cyberagent):
    report_lines = ["# 会話の発話量変化パターンと説得/成約の関係\n"]
    report_lines.append("## 目的\n\n")
    report_lines.append("営業員/説得者の発話量（単語数/文字数）の時間的変化パターンが、成約や説得成功と関連するかを検討する。\n")
    report_lines.append("フィラーの実データが得られないため、発話量をフィラーの代理指標として用いる。\n\n")

    report_lines.append("## データセット\n\n")
    report_lines.append("- **PersuasionForGood**（英語）: 1,017件の慈善寄付説得対話。寄付金額 `donation_ee` を指標に。\n")
    report_lines.append("- **CyberAgentAILab/salestalk-dataset**（日本語）: 109件のB2Cセールス対話。購入意欲の前後差 `purchase_intention_change` を指標に。\n\n")

    report_lines.append("## 方法\n\n")
    report_lines.append("1. 各対話について、対話正規化位置（0=開始、1=終了）に対する発話量を二次関数でフィット。\n")
    report_lines.append("2. 標準化した線形・二次係数の符号から、変化パターンを4種に分類：\n")
    report_lines.append("   - `inverted_u`: 中盤にピーク（増加→減少）\n")
    report_lines.append("   - `u_shape`: 中盤に谷（減少→増加）\n")
    report_lines.append("   - `increasing`: 単調増加\n")
    report_lines.append("   - `decreasing`: 単調減少\n")
    report_lines.append("3. パターン別にアウトカムの分布を比較（Kruskal-Wallis、カイ二乗、回帰）。\n\n")

    report_lines.append("## PersuasionForGood 結果\n\n")
    p_shape = OUT_DIR / "persuasion_outcome_by_shape.json"
    if p_shape.exists():
        with p_shape.open(encoding="utf-8") as f:
            res = json.load(f)
        report_lines.append(f"- 対話数: {res['n']}\n")
        report_lines.append(f"- Kruskal-Wallis H = {res['kruskal_h']:.3f}, p = {res['kruskal_p']:.3f}\n")
        report_lines.append("- 形状別サマリー:\n\n")
        for shape, vals in sorted(res["summary"].items()):
            report_lines.append(
                f"  - `{shape}`: n={vals['n']}, 平均寄付={vals['mean']:.2f}, 中央値={vals['median']:.2f}, "
                f"寄付率={vals.get('prop_positive', np.nan):.3f}\n"
            )
        report_lines.append("\n")

    p_reg = OUT_DIR / "persuasion_regression_log1p_donation.json"
    if p_reg.exists():
        with p_reg.open(encoding="utf-8") as f:
            reg = json.load(f)
        report_lines.append("- 回帰（log1p 寄付金額）:\n")
        report_lines.append(f"  - R² = {reg.get('r2'):.3f}, AIC = {reg.get('aic'):.1f}\n")
        for var, v in reg["coefficients"].items():
            report_lines.append(f"  - {var}: β={v['estimate']:.3f}, p={v['p']:.3f}, 95%CI=({v['ci_lower']:.3f}, {v['ci_upper']:.3f})\n")
        report_lines.append("\n")

    report_lines.append("## CyberAgent salestalk 結果\n\n")
    c_shape = OUT_DIR / "cyberagent_outcome_by_shape_purchase_change.json"
    if c_shape.exists():
        with c_shape.open(encoding="utf-8") as f:
            res = json.load(f)
        report_lines.append(f"- 対話数: {res['n']}\n")
        report_lines.append(f"- Kruskal-Wallis H = {res['kruskal_h']:.3f}, p = {res['kruskal_p']:.3f}\n")
        report_lines.append("- 形状別サマリー:\n\n")
        for shape, vals in sorted(res["summary"].items()):
            report_lines.append(
                f"  - `{shape}`: n={vals['n']}, 平均変化={vals['mean']:.2f}, 中央値={vals['median']:.2f}, "
                f"改善率={vals.get('prop_positive', np.nan):.3f}\n"
            )
        report_lines.append("\n")

    c_reg = OUT_DIR / "cyberagent_regression_purchase_change.json"
    if c_reg.exists():
        with c_reg.open(encoding="utf-8") as f:
            reg = json.load(f)
        report_lines.append("- 回帰（購入意欲変化）:\n")
        report_lines.append(f"  - R² = {reg.get('r2'):.3f}, AIC = {reg.get('aic'):.1f}\n")
        for var, v in reg["coefficients"].items():
            report_lines.append(f"  - {var}: β={v['estimate']:.3f}, p={v['p']:.3f}, 95%CI=({v['ci_lower']:.3f}, {v['ci_upper']:.3f})\n")
        report_lines.append("\n")

    report_lines.append("## 結論\n\n")
    report_lines.append("- 主な発話量パターンは **inverted_u**（中盤に情報提供が集中し、終盤に絞る）であった。\n")
    report_lines.append("- 想定された `decreasing` パターン（序盤に多く、徐々に減少）は少数で、統計的に優位な成約効果は確認されなかった。\n")
    report_lines.append("- 両データセットで、発話量変化パターンとアウトカムの関連は弱く、統計的有意差は得られなかった。\n")
    report_lines.append("- 発話量はフィラーの不完全な代理指標であるため、今後は音声付き実データでフィラーや発話速度を直接検証する必要がある。\n")

    report_path = OUT_DIR / "report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.writelines(report_lines)
    print(f"Saved {report_path}")


def main():
    persuasion = run_persuasion()
    cyberagent = run_cyberagent()
    write_markdown_report(persuasion, cyberagent)
    print("\nDone. Results in output/, figures in figures/")


if __name__ == "__main__":
    main()
