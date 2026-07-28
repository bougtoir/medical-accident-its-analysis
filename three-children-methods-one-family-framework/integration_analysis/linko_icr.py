"""
ICR Calculator: Variance-based Information Contribution Ratio (ICR_v)

Computes the proportion of total information (measured by variance) that
endpoint variables represent within the full dataset of an RCT, using only
summary statistics reported in Table 1 and endpoint results.
"""

import numpy as np
import pandas as pd
from typing import Optional


def reconstruct_pooled_variance(
    n_i: int, n_c: int,
    mean_i: float, mean_c: float,
    sd_i: float, sd_c: float
) -> tuple[float, float]:
    """Reconstruct pooled (total) mean and variance from two-group summary stats.

    Parameters
    ----------
    n_i, n_c : int
        Sample sizes for intervention and control groups.
    mean_i, mean_c : float
        Group means.
    sd_i, sd_c : float
        Group standard deviations.

    Returns
    -------
    mean_all : float
        Pooled mean.
    var_all : float
        Pooled variance (unbiased).
    """
    n = n_i + n_c
    mean_all = (n_i * mean_i + n_c * mean_c) / n
    var_i = sd_i ** 2
    var_c = sd_c ** 2
    numerator = (
        (n_i - 1) * var_i
        + (n_c - 1) * var_c
        + n_i * (mean_i - mean_all) ** 2
        + n_c * (mean_c - mean_all) ** 2
    )
    var_all = numerator / (n - 1) if n > 1 else 0.0
    return mean_all, var_all


def binary_pooled_variance(
    n_i: int, n_c: int,
    prop_i: float, prop_c: float
) -> tuple[float, float]:
    """Reconstruct pooled proportion and variance for a binary variable.

    Parameters
    ----------
    n_i, n_c : int
        Sample sizes for intervention and control groups.
    prop_i, prop_c : float
        Proportions in each group.

    Returns
    -------
    p_all : float
        Pooled proportion.
    var_all : float
        Pooled variance.
    """
    n = n_i + n_c
    p_all = (n_i * prop_i + n_c * prop_c) / n
    var_i = prop_i * (1 - prop_i)
    var_c = prop_c * (1 - prop_c)
    numerator = (
        (n_i - 1) * var_i
        + (n_c - 1) * var_c
        + n_i * (prop_i - p_all) ** 2
        + n_c * (prop_c - p_all) ** 2
    )
    var_all = numerator / (n - 1) if n > 1 else 0.0
    return p_all, var_all


def compute_icr_v(
    table1_data: list[dict],
    endpoints: list[str],
    n_i: int,
    n_c: int,
) -> dict:
    """Compute Variance-based ICR from Table 1 summary statistics.

    Returns both:
    - icr_std (standardized): d/D, treating each variable as equal after Z-scoring.
      This is the PRIMARY measure representing the "dimensional weight" of the
      endpoint in the data space.
    - icr_raw: ratio of actual endpoint variance to total variance.
      This captures scale-dependent information contribution.

    Parameters
    ----------
    table1_data : list of dict
        Each dict describes one variable with keys:
        - "variable": str (variable name)
        - "type": "continuous" or "binary"
        - For continuous: "mean_I", "std_I", "mean_C", "std_C"
        - For binary: "prop_I", "prop_C"
    endpoints : list of str
        Names of endpoint variables.
    n_i, n_c : int
        Sample sizes for intervention and control groups.

    Returns
    -------
    dict with keys:
        - "icr_std": float (standardized ICR = d/D, primary measure)
        - "icr_raw": float (raw variance-ratio ICR)
        - "icr_raw_intervention": float
        - "icr_raw_control": float
        - "unusable_variables": list of str
        - "variable_details": dict mapping variable name to variance info
        - "n_variables_used": int (D)
        - "n_endpoint_variables": int (d)
        - "group_icr_difference": float (|ICR_I - ICR_C|)
    """
    unusable = []
    var_details = {}

    for var_info in table1_data:
        var_name = var_info["variable"]
        var_type = var_info.get("type", "continuous")

        if var_type == "continuous":
            required = ["mean_I", "std_I", "mean_C", "std_C"]
            if not all(k in var_info and var_info[k] is not None for k in required):
                unusable.append(var_name)
                continue

            mean_i_val = var_info["mean_I"]
            sd_i_val = var_info["std_I"]
            mean_c_val = var_info["mean_C"]
            sd_c_val = var_info["std_C"]

            var_i = sd_i_val ** 2
            var_c = sd_c_val ** 2
            _, var_all = reconstruct_pooled_variance(
                n_i, n_c, mean_i_val, mean_c_val, sd_i_val, sd_c_val
            )

        elif var_type == "binary":
            if not all(k in var_info and var_info[k] is not None
                       for k in ["prop_I", "prop_C"]):
                unusable.append(var_name)
                continue

            prop_i_val = var_info["prop_I"]
            prop_c_val = var_info["prop_C"]

            var_i = prop_i_val * (1 - prop_i_val)
            var_c = prop_c_val * (1 - prop_c_val)
            _, var_all = binary_pooled_variance(
                n_i, n_c, prop_i_val, prop_c_val
            )
        else:
            unusable.append(var_name)
            continue

        var_details[var_name] = {
            "var_intervention": var_i,
            "var_control": var_c,
            "var_all": var_all,
            "is_endpoint": var_name in endpoints,
        }

    # Counts
    n_used = len(var_details)
    n_ep = sum(1 for v in var_details.values() if v["is_endpoint"])

    # Standardized ICR: d/D (each variable equal weight after Z-scoring)
    icr_std = n_ep / n_used if n_used > 0 else 0.0

    # Raw ICR: actual variance magnitudes
    sum_var_all = sum(v["var_all"] for v in var_details.values())
    sum_var_i = sum(v["var_intervention"] for v in var_details.values())
    sum_var_c = sum(v["var_control"] for v in var_details.values())

    sum_ep_var_all = sum(v["var_all"] for v in var_details.values() if v["is_endpoint"])
    sum_ep_var_i = sum(v["var_intervention"] for v in var_details.values() if v["is_endpoint"])
    sum_ep_var_c = sum(v["var_control"] for v in var_details.values() if v["is_endpoint"])

    icr_raw = sum_ep_var_all / sum_var_all if sum_var_all > 0 else 0.0
    icr_raw_i = sum_ep_var_i / sum_var_i if sum_var_i > 0 else 0.0
    icr_raw_c = sum_ep_var_c / sum_var_c if sum_var_c > 0 else 0.0

    return {
        "icr_std": icr_std,
        "icr_raw": icr_raw,
        "icr_raw_intervention": icr_raw_i,
        "icr_raw_control": icr_raw_c,
        "unusable_variables": unusable,
        "variable_details": var_details,
        "n_variables_used": n_used,
        "n_endpoint_variables": n_ep,
        "group_icr_difference": abs(icr_raw_i - icr_raw_c),
    }


def compute_icr_v_from_dataframe(
    df: pd.DataFrame,
    endpoint_cols: list[str],
    group_col: Optional[str] = None,
    intervention_label: Optional[str] = None,
    control_label: Optional[str] = None,
) -> dict:
    """Compute ICR_v directly from a raw data DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw data with one row per subject.
    endpoint_cols : list of str
        Column names for endpoint variables.
    group_col : str, optional
        Column indicating group assignment. If None, treats all data as one group.
    intervention_label, control_label : str, optional
        Labels for intervention and control groups in group_col.

    Returns
    -------
    dict with ICR values.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if group_col and group_col in numeric_cols:
        numeric_cols.remove(group_col)

    variances = {}
    for col in numeric_cols:
        variances[col] = df[col].var(ddof=1)

    total_var = sum(variances.values())
    endpoint_var = sum(variances.get(c, 0) for c in endpoint_cols if c in variances)

    n_used = len(variances)
    n_ep = sum(1 for c in endpoint_cols if c in variances)

    result = {
        "icr_std": n_ep / n_used if n_used > 0 else 0.0,
        "icr_raw": endpoint_var / total_var if total_var > 0 else 0.0,
        "n_variables_used": n_used,
        "n_endpoint_variables": n_ep,
        "variable_variances": variances,
    }

    if group_col and intervention_label and control_label:
        for label, key in [(intervention_label, "intervention"), (control_label, "control")]:
            sub = df[df[group_col] == label]
            sub_vars = {col: sub[col].var(ddof=1) for col in numeric_cols}
            total_sub = sum(sub_vars.values())
            ep_sub = sum(sub_vars.get(c, 0) for c in endpoint_cols if c in sub_vars)
            result[f"icr_raw_{key}"] = ep_sub / total_sub if total_sub > 0 else 0.0

    return result
