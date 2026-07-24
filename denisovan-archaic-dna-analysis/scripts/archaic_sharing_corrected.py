"""Dependence-aware regression, outlier testing, and sensitivity analyses."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from archaic_sharing_common import ADMIXED_EUR_FRAC, build_symmetric_matrix


FULL_PREDICTORS = [
    "geo_dist_1000km",
    "any_admixed",
    "same_continent",
    "same_dataset",
]
NONADMIXED_PREDICTORS = [
    "geo_dist_1000km",
    "same_continent",
    "same_dataset",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairwise-input", type=Path, default=Path("data/pairwise_sharing.csv")
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--permutations", type=int, default=9_999)
    parser.add_argument("--sensitivity-permutations", type=int, default=999)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def fit_linear_model(
    response: np.ndarray, predictors: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    design = np.column_stack([np.ones(len(response)), predictors])
    coefficients = np.linalg.lstsq(design, response, rcond=None)[0]
    predicted = design @ coefficients
    residuals = response - predicted
    total_sum_squares = float(np.sum((response - response.mean()) ** 2))
    residual_sum_squares = float(np.sum(residuals**2))
    r_squared = (
        1 - residual_sum_squares / total_sum_squares
        if total_sum_squares
        else np.nan
    )
    return coefficients, predicted, residuals, r_squared


def matrix_vectors(
    pairs: pd.DataFrame,
    populations: list[str],
    response_column: str,
    predictor_columns: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    triangle = np.triu_indices(len(populations), k=1)
    response_matrix = build_symmetric_matrix(pairs, populations, response_column)
    response = response_matrix[triangle]
    predictors = np.column_stack(
        [
            build_symmetric_matrix(pairs, populations, column)[triangle]
            for column in predictor_columns
        ]
    )
    if np.isnan(response).any() or np.isnan(predictors).any():
        raise ValueError(
            f"{response_column} analysis requires a complete population-pair matrix"
        )
    return response_matrix, response, predictors, triangle


def qap_regression(
    pairs: pd.DataFrame,
    populations: list[str],
    response_column: str,
    predictor_columns: list[str],
    permutations: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    response_matrix, response, predictors, triangle = matrix_vectors(
        pairs, populations, response_column, predictor_columns
    )
    coefficients, predicted, residuals, r_squared = fit_linear_model(
        response, predictors
    )
    exceedances = np.zeros(len(coefficients), dtype=np.int64)
    for _ in range(permutations):
        permutation = rng.permutation(len(populations))
        permuted_response = response_matrix[np.ix_(permutation, permutation)][triangle]
        permuted_coefficients = fit_linear_model(permuted_response, predictors)[0]
        exceedances += np.abs(permuted_coefficients) >= np.abs(coefficients)
    p_values = (exceedances + 1) / (permutations + 1)
    return {
        "coefficients": coefficients,
        "p_values": p_values,
        "predicted": predicted,
        "residuals": residuals,
        "r_squared": r_squared,
        "response": response,
        "predictors": predictors,
        "triangle": triangle,
    }


def partial_correlation(
    response: np.ndarray, predictors: np.ndarray, distance_index: int = 0
) -> float:
    distance = predictors[:, distance_index]
    covariates = np.delete(predictors, distance_index, axis=1)
    if covariates.shape[1]:
        response_residuals = fit_linear_model(response, covariates)[2]
        distance_residuals = fit_linear_model(distance, covariates)[2]
    else:
        response_residuals = response
        distance_residuals = distance
    return float(stats.pearsonr(distance_residuals, response_residuals).statistic)


def leave_one_population_out(
    pairs: pd.DataFrame,
    populations: list[str],
    response_column: str,
    predictor_columns: list[str],
) -> np.ndarray:
    estimates = []
    for omitted in populations:
        retained = [population for population in populations if population != omitted]
        _, response, predictors, _ = matrix_vectors(
            pairs[
                (pairs["pop1"] != omitted) & (pairs["pop2"] != omitted)
            ],
            retained,
            response_column,
            predictor_columns,
        )
        estimates.append(fit_linear_model(response, predictors)[0])
    return np.asarray(estimates)


def pair_order(populations: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        combinations(populations, 2), columns=["pop1", "pop2"]
    )


def outlier_qap(
    pairs: pd.DataFrame,
    response_column: str,
    prefix: str,
    permutations: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    nonadmixed_populations = sorted(
        (set(pairs["pop1"]) | set(pairs["pop2"])) - set(ADMIXED_EUR_FRAC)
    )
    nonadmixed_pairs = pairs[
        pairs["pop1"].isin(nonadmixed_populations)
        & pairs["pop2"].isin(nonadmixed_populations)
    ].copy()
    response_matrix, response, predictors, triangle = matrix_vectors(
        nonadmixed_pairs,
        nonadmixed_populations,
        response_column,
        NONADMIXED_PREDICTORS,
    )
    coefficients, predicted, residuals, _ = fit_linear_model(response, predictors)
    residual_standard_deviation = residuals.std(ddof=len(coefficients))
    z_scores = residuals / residual_standard_deviation
    exceedances = np.zeros(len(residuals), dtype=np.int64)
    for _ in range(permutations):
        permutation = rng.permutation(len(nonadmixed_populations))
        permuted_response = response_matrix[np.ix_(permutation, permutation)][triangle]
        permuted_residuals = fit_linear_model(permuted_response, predictors)[2]
        exceedances += permuted_residuals >= residuals
    p_values = (exceedances + 1) / (permutations + 1)
    q_values = multipletests(p_values, method="fdr_bh")[1]
    ordered = pair_order(nonadmixed_populations)
    ordered[f"{prefix}_predicted"] = predicted
    ordered[f"{prefix}_resid_corrected"] = residuals
    ordered[f"{prefix}_resid_z"] = z_scores
    ordered[f"{prefix}_perm_pval"] = p_values
    ordered[f"{prefix}_fdr_pval"] = q_values
    return ordered


def qap_summary_rows(
    pairs: pd.DataFrame,
    response_column: str,
    ancestry: str,
    permutations: int,
    rng: np.random.Generator,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    populations = sorted(set(pairs["pop1"]) | set(pairs["pop2"]))
    full = qap_regression(
        pairs,
        populations,
        response_column,
        FULL_PREDICTORS,
        permutations,
        rng,
    )
    simple = qap_regression(
        pairs,
        populations,
        response_column,
        ["geo_dist_1000km"],
        permutations,
        rng,
    )
    jackknife = leave_one_population_out(
        pairs, populations, response_column, FULL_PREDICTORS
    )
    names = ["intercept", *FULL_PREDICTORS]
    rows = []
    for index, name in enumerate(names):
        rows.append(
            {
                "ancestry": ancestry,
                "model": "expanded QAP",
                "term": name,
                "estimate": full["coefficients"][index],
                "qap_p_two_sided": full["p_values"][index],
                "leave_one_population_out_2.5pct": np.percentile(
                    jackknife[:, index], 2.5
                ),
                "leave_one_population_out_97.5pct": np.percentile(
                    jackknife[:, index], 97.5
                ),
                "r_squared": full["r_squared"],
                "permutations": permutations,
            }
        )
    rows.append(
        {
            "ancestry": ancestry,
            "model": "distance-only QAP",
            "term": "geo_dist_1000km",
            "estimate": simple["coefficients"][1],
            "qap_p_two_sided": simple["p_values"][1],
            "leave_one_population_out_2.5pct": np.nan,
            "leave_one_population_out_97.5pct": np.nan,
            "r_squared": simple["r_squared"],
            "permutations": permutations,
        }
    )
    statistics = {
        "raw_r": float(
            stats.pearsonr(
                pairs["geo_dist_1000km"], pairs[response_column]
            ).statistic
        ),
        "partial_r": partial_correlation(
            full["response"], full["predictors"]
        ),
        "distance_only_r_squared": simple["r_squared"],
        "expanded_r_squared": full["r_squared"],
        "distance_qap_beta": full["coefficients"][1],
        "distance_qap_p": full["p_values"][1],
    }
    return rows, statistics


def is_complete_population_subset(frame: pd.DataFrame) -> bool:
    populations = set(frame["pop1"]) | set(frame["pop2"])
    return len(frame) == len(populations) * (len(populations) - 1) // 2


def sensitivity_subsets(pairs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    subsets = {
        "all": pairs,
        "nonadmixed": pairs[pairs["any_admixed"] == 0],
        "zero_distance_excluded": pairs[pairs["geo_dist_km"] > 0],
        "1000_genomes_only": pairs[
            (pairs["dataset1"] == "1000 Genomes")
            & (pairs["dataset2"] == "1000 Genomes")
        ],
        "hgdp_only": pairs[
            (pairs["dataset1"] == "HGDP") & (pairs["dataset2"] == "HGDP")
        ],
    }
    for minimum in [10, 15, 20]:
        subsets[f"minimum_n_{minimum}"] = pairs[
            (pairs["n1"] >= minimum) & (pairs["n2"] >= minimum)
        ]
    continents = sorted(set(pairs["continent1"]) | set(pairs["continent2"]))
    for continent in continents:
        subsets[f"leave_out_{continent}"] = pairs[
            (pairs["continent1"] != continent)
            & (pairs["continent2"] != continent)
        ]
    return subsets


def sensitivity_analysis(
    pairs: pd.DataFrame,
    permutations: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    response_columns = {
        "nean_corr": ("Neanderthal", "Pearson"),
        "deni_corr": ("Denisovan", "Pearson"),
        "nean_spearman": ("Neanderthal", "Spearman"),
        "deni_spearman": ("Denisovan", "Spearman"),
        "nean_cosine": ("Neanderthal", "Cosine"),
        "deni_cosine": ("Denisovan", "Cosine"),
        "nean_full_corr": ("Neanderthal", "Full-window Pearson"),
        "deni_full_corr": ("Denisovan", "Full-window Pearson"),
        "nean_jaccard": ("Neanderthal", "Presence Jaccard"),
        "deni_jaccard": ("Denisovan", "Presence Jaccard"),
    }
    records = []
    for subset_name, subset in sensitivity_subsets(pairs).items():
        for response_column, (ancestry, metric) in response_columns.items():
            valid = subset.dropna(subset=[response_column])
            raw_r = float(
                stats.pearsonr(valid["geo_dist_1000km"], valid[response_column]).statistic
            )
            record = {
                "subset": subset_name,
                "ancestry": ancestry,
                "metric": metric,
                "populations": len(set(valid["pop1"]) | set(valid["pop2"])),
                "pairs": len(valid),
                "raw_distance_r": raw_r,
                "distance_qap_beta": np.nan,
                "distance_qap_p_two_sided": np.nan,
                "qap_permutations": 0,
            }
            if is_complete_population_subset(valid):
                populations = sorted(set(valid["pop1"]) | set(valid["pop2"]))
                result = qap_regression(
                    valid,
                    populations,
                    response_column,
                    ["geo_dist_1000km"],
                    permutations,
                    rng,
                )
                record["distance_qap_beta"] = result["coefficients"][1]
                record["distance_qap_p_two_sided"] = result["p_values"][1]
                record["qap_permutations"] = permutations
            records.append(record)
    return pd.DataFrame(records)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_csv(args.pairwise_input)
    pairs["geo_dist_1000km"] = pairs["geo_dist_km"] / 1000
    required = set(FULL_PREDICTORS) | {
        "nean_corr",
        "deni_corr",
        "nean_spearman",
        "deni_spearman",
        "nean_cosine",
        "deni_cosine",
        "nean_full_corr",
        "deni_full_corr",
        "nean_jaccard",
        "deni_jaccard",
    }
    missing = required - set(pairs.columns)
    if missing:
        raise ValueError(f"Missing required pairwise columns: {sorted(missing)}")
    rng = np.random.default_rng(args.seed)
    summary_rows = []
    statistics = {}
    for response_column, ancestry, prefix in [
        ("nean_corr", "Neanderthal", "nean"),
        ("deni_corr", "Denisovan", "deni"),
    ]:
        rows, ancestry_statistics = qap_summary_rows(
            pairs,
            response_column,
            ancestry,
            args.permutations,
            rng,
        )
        summary_rows.extend(rows)
        statistics[prefix] = ancestry_statistics
    neanderthal_outliers = outlier_qap(
        pairs, "nean_corr", "nean", args.permutations, rng
    )
    denisovan_outliers = outlier_qap(
        pairs, "deni_corr", "deni", args.permutations, rng
    )
    outlier_results = neanderthal_outliers.merge(
        denisovan_outliers, on=["pop1", "pop2"], how="outer"
    )
    corrected = pairs.merge(outlier_results, on=["pop1", "pop2"], how="left")
    corrected.to_csv(
        args.output_dir / "pairwise_sharing_corrected.csv", index=False
    )
    model_summary = pd.DataFrame(summary_rows)
    model_summary.to_csv(args.output_dir / "model_summary.csv", index=False)
    sensitivity = sensitivity_analysis(
        pairs, args.sensitivity_permutations, rng
    )
    sensitivity.to_csv(
        args.output_dir / "sensitivity_analysis.csv", index=False
    )
    significant = corrected[
        ((corrected["nean_resid_z"] > 2) & (corrected["nean_fdr_pval"] < 0.10))
        | ((corrected["deni_resid_z"] > 2) & (corrected["deni_fdr_pval"] < 0.10))
    ].copy()
    significant.to_csv(args.output_dir / "outlier_summary.csv", index=False)
    statistics["nonadmixed_pairs_tested"] = len(neanderthal_outliers)
    statistics["nean"]["fdr_q_lt_0.10_positive_z_gt_2"] = int(
        (
            (corrected["nean_resid_z"] > 2)
            & (corrected["nean_fdr_pval"] < 0.10)
        ).sum()
    )
    statistics["deni"]["fdr_q_lt_0.10_positive_z_gt_2"] = int(
        (
            (corrected["deni_resid_z"] > 2)
            & (corrected["deni_fdr_pval"] < 0.10)
        ).sum()
    )
    statistics["permutations"] = args.permutations
    statistics["sensitivity_permutations"] = args.sensitivity_permutations
    (args.output_dir / "correction_stats.json").write_text(
        json.dumps(statistics, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "Dependence-aware QAP analysis",
        f"Population-label permutations: {args.permutations}",
        f"Sensitivity permutations: {args.sensitivity_permutations}",
        "",
    ]
    for prefix, ancestry in [("nean", "Neanderthal"), ("deni", "Denisovan")]:
        values = statistics[prefix]
        lines.extend(
            [
                ancestry,
                f"Raw distance r: {values['raw_r']:.4f}",
                f"Partial distance r: {values['partial_r']:.4f}",
                f"Distance-only R2: {values['distance_only_r_squared']:.4f}",
                f"Expanded descriptive R2: {values['expanded_r_squared']:.4f}",
                f"Distance QAP beta per 1000 km: {values['distance_qap_beta']:.6f}",
                f"Distance QAP p: {values['distance_qap_p']:.4f}",
                "FDR q<0.10 positive z>2 outliers: "
                f"{values['fdr_q_lt_0.10_positive_z_gt_2']}",
                "",
            ]
        )
    (args.output_dir / "correction_stats.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
