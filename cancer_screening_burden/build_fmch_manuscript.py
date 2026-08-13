"""Build a Family Medicine and Community Health (FMCH) formatted manuscript.

This script reuses the analysis outputs and the generic build pipeline from
build_manuscript.py, then adjusts the front matter (Key points, structured
abstract with Keywords) and adds the required post-conclusion sections
(Author contributions, Acknowledgements, Funding, Competing interests,
Data availability).  No numeric results are hard-coded.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

from build_manuscript import (
    build_figures_pptx,
    build_markdown,
    build_tables_docx,
    compute_per_cancer_at_followup,
    load_aggregate,
    load_capacity_summary,
    load_by_cancer,
    load_weighted_ppv,
    make_table_1,
    make_table_2,
    make_table_3,
    make_table_4,
    markdown_to_docx,
    _fp_to_tp_ratio,
    _ppv,
)
from simulate import choose_summary_rate, find_capacity_threshold


def _parse_capacity_threshold(agg: pd.DataFrame) -> tuple[str, str]:
    """Return (rate_str, resource) for the first capacity exceedance."""
    s = find_capacity_threshold(agg, threshold=100.0)
    if s.startswith("not"):
        return "not reached in the scanned range", ""
    m = re.search(r"([0-9]+)%\s*\(([^)]+)\)", s)
    if not m:
        return "unknown", ""
    return f"{int(m.group(1))}%", m.group(2).strip().lower()


def _compute_context(
    params: Dict[str, Any],
    agg: pd.DataFrame,
    by_cancer: pd.DataFrame,
    weighted_ppv: pd.DataFrame,
    capacity_impact: pd.DataFrame,
    capacity_summary: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """Compute all narrative numbers shared by the FMCH manuscript."""
    follow_up_rates = agg["follow_up_rate"].tolist()
    row_50 = agg[agg["follow_up_rate"] == choose_summary_rate(follow_up_rates, 0.5)].iloc[0]

    row_50_ppv = _ppv(row_50["true_positives"], row_50["false_positives"]) * 100
    row_50_fp_tp = _fp_to_tp_ratio(row_50["true_positives"], row_50["false_positives"])

    threshold_rate, threshold_resource = _parse_capacity_threshold(agg)
    threshold_str = (
        f"{threshold_rate} ({threshold_resource})"
        if threshold_resource
        else threshold_rate
    )

    weighted = weighted_ppv.copy()
    weighted["ppv"] = weighted.apply(
        lambda r: _ppv(r["true_positives"], r["false_positives"]), axis=1
    )
    weighted["fp_to_tp_ratio"] = weighted.apply(
        lambda r: _fp_to_tp_ratio(r["true_positives"], r["false_positives"]), axis=1
    )

    lowest_ppv = weighted.loc[weighted["ppv"].idxmin()]
    highest_ppv = weighted.loc[weighted["ppv"].idxmax()]

    # Specificity sweep.
    sweep = pd.read_csv(output_dir / "specificity_sweep.csv")
    sweep_agg = (
        sweep.groupby("sweep_specificity")[["true_positives", "false_positives"]]
        .sum()
        .reset_index()
    )
    sweep_agg["ppv"] = sweep_agg["true_positives"] / (
        sweep_agg["true_positives"] + sweep_agg["false_positives"]
    )
    spec_values = sweep_agg["sweep_specificity"].tolist()
    spec_95 = choose_summary_rate(spec_values, 0.95)
    spec_99 = choose_summary_rate(spec_values, 0.99)
    ppv_95 = sweep_agg[sweep_agg["sweep_specificity"] == spec_95]["ppv"].values[0] * 100
    ppv_99 = sweep_agg[sweep_agg["sweep_specificity"] == spec_99]["ppv"].values[0] * 100
    ppv_ratio = ppv_95 / ppv_99 if ppv_99 > 0 else 0.0

    baseline_cases = capacity_summary.get("baseline_cases_per_specialist", 0.0)
    fp_visits = capacity_summary.get("fp_visits_per_specialist", 0.0)
    total_cases = capacity_summary.get("cases_per_specialist_with_fp", baseline_cases + fp_visits)
    percent_change = capacity_summary.get("percent_change", 0.0)

    return {
        "row_50": row_50,
        "row_50_ppv": row_50_ppv,
        "row_50_fp_tp": row_50_fp_tp,
        "threshold_str": threshold_str,
        "lowest_ppv": lowest_ppv,
        "highest_ppv": highest_ppv,
        "ppv_95": ppv_95,
        "ppv_99": ppv_99,
        "ppv_ratio": ppv_ratio,
        "baseline_cases": baseline_cases,
        "fp_visits": fp_visits,
        "total_cases": total_cases,
        "percent_change": percent_change,
    }


def _fmch_abstract(ctx: Dict[str, Any], params: Dict[str, Any]) -> str:
    row = ctx["row_50"]
    return (
        "**Background:** Direct-to-consumer blood-based multi-cancer early detection "
        "(MCED) tests are advertised as a convenient single-blood-draw screen. In "
        "asymptomatic populations most positive results are false positives, each "
        "triggering imaging, endoscopy, and specialist follow-up visits.\n\n"
        "**Methods:** A deterministic expected-value model was parameterised with 2023 "
        "adult cancer incidence and population data, 2023 national diagnostic volumes, "
        "and specialist capacity derived from NDB Open Data outpatient counts and "
        "Japanese specialist-board counts. True positives, false positives, downstream "
        "visits, capacity utilisation, and per-specialist case load were estimated across "
        "follow-up rates of 0-100% and specificities of 95.0-99.9%.\n\n"
        f"**Results:** In a 100,000-person cohort at 50% follow-up and {params['cancers'][0]['specificity']:.3f} "
        f"specificity, the model generated {row['true_positives']:.1f} true positives and "
        f"{row['false_positives']:.1f} false positives (positive predictive value "
        f"{ctx['row_50_ppv']:.2f}%; false-positive/true-positive ratio "
        f"{ctx['row_50_fp_tp']:.1f}). Total downstream visits reached "
        f"{row['total_visits']:.1f}, with maximum capacity utilisation "
        f"{row['max_capacity_utilization_pct']:.1f}% (specialist visits). The "
        f"illustrative capacity ceiling was exceeded at a follow-up rate of "
        f"{ctx['threshold_str']}. False-positive specialist visits added "
        f"{ctx['fp_visits']:.1f} visits per relevant specialist, raising the effective "
        f"cases per specialist from {ctx['baseline_cases']:.1f} to "
        f"{ctx['total_cases']:.1f} ({ctx['percent_change']:.0f}% increase).\n\n"
        "**Conclusions:** Even with optimistic 99% specificity, a direct-to-consumer "
        "MCED wave can trigger a false-positive cascade that exceeds outpatient and "
        "endoscopic capacity. Transparent positive predictive value reporting, "
        "performance thresholds, and clear follow-up obligations are needed before "
        "routine adoption."
    )


def _key_points(ctx: Dict[str, Any]) -> str:
    row = ctx["row_50"]
    return (
        "### Key points\n\n"
        "- **Question:** What diagnostic and specialist workload is generated when "
        "direct-to-consumer blood-based multi-cancer early detection (MCED) tests return "
        "positive results in an asymptomatic population?\n"
        f"- **Finding:** A 100,000-person MCED wave at 50% follow-up produced "
        f"{row['true_positives']:.0f} true positives and {row['false_positives']:.0f} "
        f"false positives (PPV {ctx['row_50_ppv']:.2f}%), exceeding the illustrative "
        f"specialist capacity ceiling once follow-up exceeded "
        f"{ctx['threshold_str'].split(' ')[0]}.\n"
        "- **Meaning:** Without regulatory guardrails on performance claims and "
        "follow-up obligations, widespread direct-to-consumer MCED screening could "
        "overload primary and specialty care with unnecessary investigations."
    )


def _post_conclusion_sections() -> str:
    return (
        "## Author contributions\n\n"
        "All authors contributed to the study design, data interpretation, and critical "
        "revision of the manuscript, and approved the final version.\n\n"
        "## Acknowledgements\n\n"
        "We thank colleagues in primary care and health services research for feedback on "
        "earlier drafts.\n\n"
        "## Funding\n\n"
        "No external funding was received for this study.\n\n"
        "## Competing interests\n\n"
        "The authors declare no competing interests.\n\n"
        "## Patient and public involvement\n\n"
        "Patients or members of the public were not directly involved in the design, "
        "conduct, reporting, or dissemination of this modelling study.\n\n"
        "## Data availability\n\n"
        "All data sources are publicly available and listed in Table 1. Analysis code, "
        "parameters, and outputs are available at "
        "https://github.com/bougtoir/cancer-screening-burden-data-driven."
    )


def build_fmch_markdown(
    params: Dict[str, Any],
    agg: pd.DataFrame,
    by_cancer_at_50: pd.DataFrame,
    weighted_ppv: pd.DataFrame,
    capacity_impact: pd.DataFrame,
    capacity_summary: Dict[str, Any],
    output_dir: Path,
) -> str:
    """Generate the FMCH-formatted Markdown manuscript."""
    ctx = _compute_context(
        params, agg, by_cancer_at_50, weighted_ppv, capacity_impact, capacity_summary, output_dir
    )

    # Reuse the generic manuscript for the body and references, then replace the
    # abstract and add FMCH-specific front/back matter.
    generic_md = build_markdown(
        params,
        agg,
        by_cancer_at_50,
        weighted_ppv,
        capacity_impact,
        capacity_summary,
        output_dir,
    )

    # Extract title line and keywords.
    title_match = re.search(r"^(# .+)$", generic_md, re.MULTILINE)
    title = title_match.group(1) if title_match else ""
    kw_match = re.search(r"\*\*Keywords:\*\* (.+)$", generic_md, re.MULTILINE)
    keywords = kw_match.group(1).strip() if kw_match else ""

    # Locate the separator between abstract/keywords and the introduction.
    intro_match = re.search(r"\n---\n\n(## Introduction)", generic_md)
    if not intro_match:
        raise ValueError("Could not locate '---\n\n## Introduction' separator in generic manuscript.")
    body = generic_md[intro_match.start(1):]

    refs_match = re.search(r"\n## References\n\n", body)
    if not refs_match:
        raise ValueError("Could not locate '## References' in generic manuscript.")
    body_before_refs = body[: refs_match.start()].rstrip()

    # Insert a reporting-guidelines note immediately before the Results section.
    reporting = (
        "### Reporting\n\n"
        "This scenario modelling study is reported in accordance with the "
        "Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) "
        "statement and the Statistical Analyses and Methods in the Published Literature "
        "(SAMPL) guidelines where applicable."
    )
    body_before_refs = body_before_refs.replace(
        "\n## Results\n", f"\n{reporting}\n\n## Results\n"
    )

    references = body[refs_match.start():]

    fmch_md = (
        f"{title}\n\n"
        f"{_key_points(ctx)}\n\n"
        "## Abstract\n\n"
        f"{_fmch_abstract(ctx, params)}\n\n"
        f"**Keywords:** {keywords}\n\n"
        "---\n\n"
        f"{body_before_refs}\n\n"
        f"{_post_conclusion_sections()}\n\n"
        f"{references}"
    )
    return fmch_md


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FMCH-formatted manuscript materials")
    parser.add_argument("--params", type=Path, default=Path("parameters.yaml"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--manuscript", type=Path, default=Path("manuscript"))
    args = parser.parse_args()

    args.manuscript.mkdir(parents=True, exist_ok=True)

    with open(args.params, "r", encoding="utf-8") as f:
        params = yaml.safe_load(f)

    agg = load_aggregate(args.output)
    by_cancer = load_by_cancer(args.output)
    weighted_ppv = load_weighted_ppv(args.output)
    by_cancer_at_50 = compute_per_cancer_at_followup(by_cancer, 0.5)
    capacity_impact = pd.read_csv(args.output / "specialist_capacity_impact.csv")
    capacity_summary = load_capacity_summary(args.output)

    md = build_fmch_markdown(
        params,
        agg,
        by_cancer_at_50,
        weighted_ppv,
        capacity_impact,
        capacity_summary,
        args.output,
    )
    (args.manuscript / "manuscript_fmch.md").write_text(md, encoding="utf-8")

    tables = {
        "Table 1. Data sources and scenario parameters": make_table_1(params),
        "Table 2. Per-cancer outcomes at 50% follow-up": make_table_2(by_cancer_at_50, weighted_ppv),
        "Table 3. Aggregate outcomes by follow-up rate": make_table_3(agg),
        "Table 4. Baseline cases per specialist and incremental false-positive burden": make_table_4(capacity_impact),
    }
    build_tables_docx(tables, args.manuscript / "manuscript_fmch_tables.docx")

    build_figures_pptx(args.output, args.manuscript / "manuscript_fmch_figures.pptx")

    markdown_to_docx(md, args.manuscript / "manuscript_fmch.docx", args.output)

    print(f"FMCH manuscript materials written to {args.manuscript.resolve()}")


if __name__ == "__main__":
    main()
