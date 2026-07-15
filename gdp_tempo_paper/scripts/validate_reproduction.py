"""Validate regenerated numerical outputs against the archived release metrics.

The baseline JSON is verification data only: it is never read by an analysis or
manuscript-building function and therefore cannot influence reported results.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = ROOT / "reproduction" / "expected_metrics.json"
REPORT_PATH = ROOT / "reproduction" / "reproduction_report.json"


def collect_metrics() -> dict[str, object]:
    fair = pd.read_csv(ROOT / "data" / "full_fair_eval.csv")
    oos = pd.read_csv(ROOT / "data" / "full_oos.csv")
    k_level = json.loads((ROOT / "data" / "k_level_summary.json").read_text())
    variance = pd.read_csv(ROOT / "tables" / "table6_tempo_artifact.csv")
    wealth = pd.read_csv(ROOT / "data" / "counterfactual_wealth.csv")
    models = ("M0", "M1", "M2", "M3", "M4", "Mobs")
    return {
        "n_countries_full": int(fair["iso3"].nunique()),
        "full_fair_B_rmse_median": {
            model: float(fair[f"{model}_B_rmse"].median()) for model in models
        },
        "full_oos_mape_median": {
            model: float(oos[f"{model}_oos_mape"].median()) for model in models
        },
        "k_level": {
            "n_countries": k_level["n_countries"],
            "median_K_pct_diff": k_level["K_pct_diff"]["median"],
            "median_TFP_shift_pct": k_level["TFP_shift_pct"]["median"],
            "median_labor_share_shift_pp": k_level["labor_share_shift_pp"]["median"],
            "countries_K_lower_than_M0": k_level["countries_K_lower_than_M0"],
            "min_K_pct_diff": k_level["K_pct_diff"]["min"],
        },
        "tfp_variance": {
            "tempo_only_max_pct": float(variance["Tempo share %"].max()),
            "joint_max_pct": float(variance["Joint share %"].max()),
        },
        "counterfactual_wealth": {
            "produced_capital_gap_max_pct": float(wealth["pca_gap_pct"].max()),
            "total_wealth_gap_max_pct": float(wealth["tow_gap_pct"].max()),
        },
    }


def compare(expected: object, actual: object, path: str = "metrics") -> list[str]:
    failures: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected mapping"]
        for key, value in expected.items():
            if key not in actual:
                failures.append(f"{path}.{key}: missing")
            else:
                failures.extend(compare(value, actual[key], f"{path}.{key}"))
    elif isinstance(expected, (int, float)):
        if not isinstance(actual, (int, float)) or not math.isclose(
            float(expected), float(actual), rel_tol=1e-10, abs_tol=1e-9
        ):
            failures.append(f"{path}: expected {expected}, got {actual}")
    elif expected != actual:
        failures.append(f"{path}: expected {expected!r}, got {actual!r}")
    return failures


def required_artifacts() -> list[Path]:
    figures = [ROOT / "figures" / f"fig{number}_{name}_en.png" for number, name in (
        (1, "m_ranking"), (2, "oos"), (3, "trajectories"),
        (4, "gamma_price"), (5, "concept"), (6, "rpim"),
        (7, "delta_sensitivity"), (8, "conditional_oos"),
        (9, "rho2_regression"), (10, "k_divergence"),
        (11, "tfp_consequence"), (12, "labor_share"),
        (13, "solow_decomp"), (14, "counterfactual_wealth"),
    )]
    tables = [
        ROOT / "data" / "fig3_trajectories.csv",
        ROOT / "tables" / "table1_model_metrics.csv",
        ROOT / "tables" / "table2_correspondence.csv",
        ROOT / "tables" / "table3_rpim.csv",
        ROOT / "tables" / "table4_extended_oos.csv",
        ROOT / "tables" / "table5_k_level.csv",
        ROOT / "tables" / "table6_tempo_artifact.csv",
    ]
    return figures + tables


def main() -> None:
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    actual = collect_metrics()
    failures = compare(expected, actual)
    missing = [str(path.relative_to(ROOT)) for path in required_artifacts() if not path.exists()]
    failures.extend(f"missing artifact: {path}" for path in missing)
    report = {
        "status": "passed" if not failures else "failed",
        "expected_metrics": expected,
        "regenerated_metrics": actual,
        "missing_artifacts": missing,
        "failures": failures,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Reproduction validation passed; report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
