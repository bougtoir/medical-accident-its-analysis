"""
LINKO PCA-based ICR + IST loader (vendored from bougtoir icr-paper).

Information Contribution Ratio via PCA. Loader and per-group ICR_pca copied
from ist_pca_analysis.py and generalised to accept an arbitrary grouping
column (country or IONE stratum).
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def load_and_encode_ist(data_path):
    """Load IST data and encode categoricals for PCA/ICR.

    Returns (encoded_df, all_analysis_vars, endpoint_col).
    """
    df = pd.read_csv(data_path, encoding="latin-1", low_memory=False)

    binary_maps = {
        "SEX": {"M": 1, "F": 0},
        "RSLEEP": {"Y": 1, "N": 0},
        "RATRIAL": {"Y": 1, "N": 0},
        "RCT": {"Y": 1, "N": 0},
        "RVISINF": {"Y": 1, "N": 0},
        "RHEP24": {"Y": 1, "N": 0},
        "RASP3": {"Y": 1, "N": 0},
        "RXASP": {"Y": 1, "N": 0},
    }
    for col, mapping in binary_maps.items():
        df[col + "_num"] = df[col].map(mapping)

    df["RCONSC_num"] = df["RCONSC"].map({"F": 0, "D": 1, "U": 2})
    df["RXHEP_num"] = df["RXHEP"].map({"N": 0, "L": 1, "M": 2, "H": 3})

    for i in range(1, 9):
        df[f"RDEF{i}_num"] = (df[f"RDEF{i}"] == "Y").astype(int)

    for stype in ["TACS", "PACS", "POCS", "LACS"]:
        df[f"STYPE_{stype}"] = (df["STYPE"] == stype).astype(int)

    # DIED: derive 14-day death from FDEAD (Y/N) if DIED not present numeric
    if "DIED" not in df.columns:
        df["DIED"] = (df["FDEAD"] == "Y").astype(int)
    else:
        df["DIED"] = pd.to_numeric(df["DIED"], errors="coerce")

    all_vars = (
        ["RDELAY", "AGE", "RSBP"]
        + [c + "_num" for c in [
            "SEX", "RSLEEP", "RATRIAL", "RCT", "RVISINF",
            "RHEP24", "RASP3", "RCONSC", "RXHEP",
        ]]
        + [f"RDEF{i}_num" for i in range(1, 9)]
        + [f"STYPE_{s}" for s in ["TACS", "PACS", "POCS", "LACS"]]
        + ["DIED"]
    )
    endpoint_col = "DIED"
    return df, all_vars, endpoint_col


def icr_pca_for_subset(sub, all_vars, endpoint_col, threshold=0.3):
    """Compute ICR_pca (loading-based and regression-based) for one subset.

    Returns dict: icr_std, icr_pca_loading, icr_pca_reg, n_endpoint_pcs.
    """
    D = len(all_vars)
    X_sub = sub[all_vars].values.astype(float)
    X_scaled = StandardScaler().fit_transform(X_sub)

    pca_sub = PCA()
    pca_sub.fit(X_scaled)
    loadings = pca_sub.components_.T
    evr = pca_sub.explained_variance_ratio_
    ep_idx = all_vars.index(endpoint_col)
    ep_pcs = [i for i in range(D) if abs(loadings[ep_idx, i]) >= threshold]
    icr_pca_loading = sum(evr[i] for i in ep_pcs)

    pred_vars = [v for v in all_vars if v != endpoint_col]
    X_pred = sub[pred_vars].values.astype(float)
    y = sub[endpoint_col].values.astype(float)
    X_pred_scaled = StandardScaler().fit_transform(X_pred)
    pca_pred = PCA()
    pc_scores = pca_pred.fit_transform(X_pred_scaled)
    eigenvalues = pca_pred.explained_variance_
    var_y = np.var(y, ddof=1)
    betas = np.array([
        (np.cov(y, pc_scores[:, k])[0, 1] / np.var(pc_scores[:, k], ddof=1))
        if np.var(pc_scores[:, k], ddof=1) > 1e-10 else 0.0
        for k in range(pc_scores.shape[1])
    ])
    contributions = betas ** 2 * eigenvalues
    total_info = np.sum(eigenvalues) + var_y
    icr_pca_reg = np.sum(contributions) / total_info if total_info > 0 else 0.0

    return {
        "icr_std": 1.0 / D,
        "icr_pca_loading": float(icr_pca_loading),
        "icr_pca_reg": float(icr_pca_reg),
        "n_endpoint_pcs": len(ep_pcs),
    }


def icr_pca_by_group(df, all_vars, endpoint_col, group_col, min_n=50, threshold=0.3):
    """Compute ICR_pca for each group (country or stratum)."""
    analysis_df = df[all_vars + [group_col]].dropna()
    rows = []
    for g, sub in analysis_df.groupby(group_col):
        if len(sub) < min_n:
            continue
        res = icr_pca_for_subset(sub, all_vars, endpoint_col, threshold)
        res.update({
            "group": g,
            "n": len(sub),
            "mortality_rate": float(sub[endpoint_col].mean()),
        })
        rows.append(res)
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)
