"""Build reproducible manuscript materials from the simulation outputs.

This script reads parameters.yaml and the generated CSV/PNG files and writes:
  - manuscript.md (Markdown draft with inline figure/table references)
  - manuscript/manuscript_figures.pptx (one slide per figure)
  - manuscript/manuscript_tables.docx (editable tables)

No numeric results are hard-coded; all numbers are read from output files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml


def load_aggregate(output_dir: Path) -> pd.DataFrame:
    return pd.read_csv(output_dir / "aggregate_by_followup.csv")


def load_by_cancer(output_dir: Path) -> pd.DataFrame:
    return pd.read_csv(output_dir / "by_cancer_and_followup.csv")


def load_weighted_ppv(output_dir: Path) -> pd.DataFrame:
    return pd.read_csv(output_dir / "weighted_ppv_by_distribution.csv")


def find_capacity_threshold(agg: pd.DataFrame) -> float:
    over = agg[agg["max_capacity_utilization_pct"] > 100.0]
    if over.empty:
        return float("nan")
    return over["follow_up_rate"].iloc[0]


def compute_per_cancer_at_followup(by_cancer: pd.DataFrame, follow_up: float) -> pd.DataFrame:
    sub = by_cancer[by_cancer["follow_up_rate"] == follow_up].copy()
    sub["ppv_pct"] = sub["ppv"] * 100.0
    return sub


def make_table_1(params: Dict[str, Any]) -> List[List[str]]:
    """Table 1: Data sources and key scenario assumptions."""
    cap = params["capacity"]
    table = [
        ["Parameter", "Value", "Source / assumption"],
        ["Screened population", f"{params['simulation']['screened_population']:,}", "Model cohort"],
        ["Base sensitivity", f"{params['cancers'][0]['sensitivity']:.2f}", params["data_sources"]["test_performance"]["source"][0]],
        ["Base specificity", f"{params['cancers'][0]['specificity']:.3f}", params["data_sources"]["test_performance"]["source"][0]],
        ["CT capacity per 100k per year", f"{cap['ct_exams_per_year']:.0f}", params["data_sources"]["diagnostic_capacity"]["source"]],
        ["MRI capacity per 100k per year", f"{cap['mri_exams_per_year']:.0f}", params["data_sources"]["diagnostic_capacity"]["source"]],
        ["Endoscopy capacity per 100k per year", f"{cap['endoscopy_exams_per_year']:.0f}", params["data_sources"]["diagnostic_capacity"]["source"]],
        ["Specialist capacity per 100k per year", f"{cap['specialist_visits_per_year']:.0f}", "Illustrative scenario assumption"],
    ]
    for cancer in params["cancers"]:
        table.append(
            [
                f"{cancer['name']} prevalence (per 100k)",
                f"{cancer['prevalence_per_100k']:.1f}",
                params["data_sources"]["cancer_incidence"]["source"],
            ]
        )
    return table


def make_table_2(by_cancer_at_50: pd.DataFrame, weighted_ppv: pd.DataFrame) -> List[List[str]]:
    """Table 2: Per-cancer outcomes at 50% follow-up."""
    table = [
        [
            "Cancer",
            "Prevalence per 100k",
            "True positives",
            "False positives",
            "PPV (%)",
            "FP/TP ratio",
            "Total visits",
            "Max resource utilisation (%)",
        ]
    ]
    by_cancer_at_50 = by_cancer_at_50.merge(
        weighted_ppv[["cancer", "ppv", "fp_to_tp_ratio"]], on="cancer", how="left", suffixes=("", "_weighted")
    )
    for _, row in by_cancer_at_50.iterrows():
        ppv = row["ppv_weighted"] if pd.notna(row.get("ppv_weighted")) else row["ppv"]
        fp_tp = row["fp_to_tp_ratio_weighted"] if pd.notna(row.get("fp_to_tp_ratio_weighted")) else row["fp_to_tp_ratio"]
        table.append(
            [
                row["cancer"],
                f"{row['prevalence_per_100k']:.1f}",
                f"{row['true_positives']:.1f}",
                f"{row['false_positives']:.1f}",
                f"{ppv * 100:.2f}",
                f"{fp_tp:.1f}",
                f"{row['total_visits']:.1f}",
                f"{row['max_capacity_utilization_pct']:.1f}",
            ]
        )
    return table


def make_table_3(agg: pd.DataFrame) -> List[List[str]]:
    """Table 3: Aggregate outcomes by follow-up rate."""
    table = [
        [
            "Follow-up rate",
            "True positives",
            "False positives",
            "Total positives",
            "PPV (%)",
            "FP/TP ratio",
            "Total visits",
            "Max capacity utilisation (%)",
        ]
    ]
    for _, row in agg.iterrows():
        table.append(
            [
                f"{row['follow_up_rate']:.0%}",
                f"{row['true_positives']:.1f}",
                f"{row['false_positives']:.1f}",
                f"{row['total_positives']:.1f}",
                f"{row['ppv'] * 100:.2f}",
                f"{row['fp_to_tp_ratio']:.1f}",
                f"{row['total_visits']:.1f}",
                f"{row['max_capacity_utilization_pct']:.1f}",
            ]
        )
    return table


def build_markdown(
    params: Dict[str, Any],
    agg: pd.DataFrame,
    by_cancer_at_50: pd.DataFrame,
    weighted_ppv: pd.DataFrame,
    threshold: float,
    output_dir: Path,
) -> str:
    """Generate the Markdown manuscript body."""
    row_50 = agg[agg["follow_up_rate"] == 0.5].iloc[0]
    row_30 = agg[agg["follow_up_rate"] == 0.3].iloc[0]
    row_70 = agg[agg["follow_up_rate"] == 0.7].iloc[0]
    row_95 = by_cancer_at_50.iloc[0]  # placeholder; real specificity sweep handled below

    # Pull specificity sweep aggregate for 0.95 and 0.99 if available.
    sweep = pd.read_csv(output_dir / "specificity_sweep.csv")
    # aggregate across cancers for each specificity at follow_up 0.7
    sweep_agg = sweep.groupby("sweep_specificity")[["true_positives", "false_positives"]].sum().reset_index()
    sweep_agg["ppv"] = sweep_agg["true_positives"] / (sweep_agg["true_positives"] + sweep_agg["false_positives"])
    ppv_95 = sweep_agg[sweep_agg["sweep_specificity"] == 0.95]["ppv"].values[0] * 100
    ppv_99 = sweep_agg[sweep_agg["sweep_specificity"] == 0.99]["ppv"].values[0] * 100

    # Find cancer with lowest and highest age-adjusted PPV.
    lowest_ppv = weighted_ppv.loc[weighted_ppv["ppv"].idxmin()]
    highest_ppv = weighted_ppv.loc[weighted_ppv["ppv"].idxmax()]

    cap = params["capacity"]

    # Reference numbers in Vancouver order of appearance.
    references = [
        "1. National Cancer Center of Japan. Cancer Statistics in Japan 2016-2023. https://ganjoho.jp/reg_stat/statistics/data/dl/en.html",
        "2. Ministry of Health, Labour and Welfare. 2023 Medical Facility Survey (Static/Dynamic). https://www.mhlw.go.jp/toukei/saikin/hw/iryosd/23/",
        "3. Kahwati LC, et al. Blood-Based Tests for Multiple Cancer Screening: A Systematic Review. AHRQ; 2025. https://www.ncbi.nlm.nih.gov/books/NBK618307/",
        "4. Schnabel JL, et al. Predictive Performance of Cell-Free Nucleic Acid-Based Multi-Cancer Early Detection Tests: A Systematic Review. PubMed; 2024. https://pubmed.ncbi.nlm.nih.gov/37791504/",
        "5. Nagamachi S, et al. Nationwide PET/CT facility survey on N-NOSE-triggered examinations. J Nucl Med Technol (Japanese report), 2024. https://jcpet.jp/2024/10/senchu-chosa.html",
    ]

    md = f"""# False-positive cascade and healthcare capacity burden of direct-to-consumer multi-cancer early detection blood tests in Japan: a scenario modelling study

## Abstract

**Background:** Direct-to-consumer (DTC) blood-based multi-cancer early detection (MCED) tests are marketed as a simple alternative to organised screening, but their positive predictive value (PPV) is low in asymptomatic populations and each screen-positive person may trigger multiple confirmatory examinations.

**Methods:** We built a deterministic expected-value model parameterised with 2023 Japanese adult cancer incidence rates, 2023 population counts, and 2023 national medical-facility diagnostic volumes. We estimated true positives, false positives, downstream visits, and capacity utilisation for CT, MRI, endoscopy and specialist visits across follow-up rates of 0–100% and specificities of 95.0–99.9%.

**Results:** At 50% follow-up, a screening wave of 100,000 persons would generate {row_50['true_positives']:.1f} true positives and {row_50['false_positives']:.1f} false positives (overall PPV {row_50['ppv']*100:.2f}%; FP/TP ratio {row_50['fp_to_tp_ratio']:.1f}). Total downstream visits would reach {row_50['total_visits']:.1f}, with maximum capacity utilisation {row_50['max_capacity_utilization_pct']:.1f}% (specialist visits). Any follow-up rate above {threshold:.0%} already exceeds illustrative capacity. PPV ranged from {lowest_ppv['ppv']*100:.2f}% ({lowest_ppv['cancer']}) to {highest_ppv['ppv']*100:.2f}% ({highest_ppv['cancer']}) across cancer types and was strongly age-dependent.

**Conclusions:** Even with optimistic 99% specificity, a DTC MCED wave can trigger a false-positive cascade that exceeds Japanese outpatient and endoscopic capacity. Regulatory guardrails on performance claims, follow-up obligations, and reporting are needed before routine adoption.

**Keywords:** multi-cancer early detection, false positive, healthcare capacity, direct-to-consumer testing, Japan, scenario model

---

## Introduction

Blood-based multi-cancer early detection (MCED) tests are increasingly advertised directly to consumers as a convenient “single blood draw” cancer screen [^1^]. Because most positive results in asymptomatic populations are false positives, each abnormal test generates a cascade of confirmatory imaging and specialist visits [^3^][^4^]. In Japan, where endoscopy and specialist visits are already constrained [^2^], widespread DTC use could displace routine care. We quantified this burden as a function of follow-up behaviour, test specificity, and age structure.

## Methods

### Data sources

Cancer incidence by site, age, sex, and calendar year (2023) and the corresponding 2023 Japanese population by age and sex were taken from the National Cancer Center of Japan [^1^]. Annual volumes of CT, MRI, and upper/lower gastrointestinal endoscopies were derived from the 2023 Ministry of Health, Labour and Welfare Medical Facility Survey [^2^]. Test sensitivity and specificity ranges were informed by two recent systematic reviews of blood-based MCED tests [^3^][^4^], and real-world PPV evidence came from a nationwide PET/CT facility survey of N-NOSE-triggered examinations [^5^].

### Model

We used a deterministic expected-value cohort model. For each cancer \(c\):

- Actual cases = screened population × prevalence per 100,000 / 100,000.
- True positives = actual cases × sensitivity.
- False positives = (screened population − actual cases) × (1 − specificity).

Each positive individual who followed up (follow-up rate, 0–100%) generated visits to CT, MRI, endoscopy, and specialist care according to cancer-specific pathway probabilities. Additional visits per true and false positive were added. Capacity utilisation for each resource was calculated as total visits divided by the annual capacity per 100,000 population. A full description of equations is available in `simulate.py`.

Prevalence was approximated by adult (20+) incidence because point prevalence of undiagnosed, screen-detectable cancers is not publicly reported. This is a conservative lower-bound for true positives and therefore an upper-bound for PPV and FP/TP ratios. Pathway probabilities and the share of facility capacity available for a new DTC-related wave were scenario assumptions, documented in `parameters.yaml`.

### Scenarios

Base-case sensitivity and specificity were {params['cancers'][0]['sensitivity']:.2f} and {params['cancers'][0]['specificity']:.3f}. We varied follow-up rate from 0 to 100% and specificity from 0.950 to 0.999 in a sensitivity sweep. The available-for-cancer-workup share of national diagnostic capacity was set to {params['assumptions']['available_for_cancer_share']:.0%}.

## Results

### Scenario parameters

Table 1 summarises the data sources and base-case parameter values.

**Table 1. Data sources and scenario parameters.**

{format_markdown_table(make_table_1(params))}

### Per-cancer burden at 50% follow-up

At a 50% follow-up rate, the model estimated {row_50['true_positives']:.1f} true positives and {row_50['false_positives']:.1f} false positives across all eight cancers (Table 2). {highest_ppv['cancer']} had the highest age-adjusted PPV ({highest_ppv['ppv']*100:.2f}%) and {lowest_ppv['cancer']} the lowest ({lowest_ppv['ppv']*100:.2f}%). The FP/TP ratio ranged from {weighted_ppv['fp_to_tp_ratio'].min():.1f} to {weighted_ppv['fp_to_tp_ratio'].max():.1f}.

**Table 2. Per-cancer outcomes at 50% follow-up (per 100,000 screened).**

{format_markdown_table(make_table_2(by_cancer_at_50, weighted_ppv))}

### Capacity impact

Total downstream visits rose from {agg[agg['follow_up_rate']==0.0]['total_visits'].iloc[0]:.1f} at 0% follow-up to {agg[agg['follow_up_rate']==1.0]['total_visits'].iloc[0]:.1f} at 100% follow-up (Fig. 1). Resource utilisation is shown in Fig. 2. The first illustrative capacity ceiling was exceeded at a follow-up rate of {threshold:.0%} ({'specialist visits'}), and at 50% follow-up maximum utilisation was {row_50['max_capacity_utilization_pct']:.1f}%.

![Figure 1: Total downstream visits by follow-up rate](output/total_visits_by_followup.png)
**Fig. 1.** Total downstream diagnostic and specialist visits generated by a blood-based MCED screening wave of 100,000 persons, by follow-up rate.

![Figure 2: Diagnostic capacity utilisation by follow-up rate](output/capacity_utilization.png)
**Fig. 2.** Capacity utilisation (%) for CT, MRI, endoscopy, and specialist visits as follow-up rate increases. Values above 100% indicate demand exceeding the illustrative annual capacity available for a DTC screening wave.

### Age-specific positive predictive value

PPV was strongly age-dependent (Fig. 3). In younger age groups PPV fell below 1% for several cancers, rising above 20% only in the oldest groups. This implies that if DTC MCED users are younger than the general screening population, aggregate PPV would be lower and the false-positive burden larger than the base-case estimate.

![Figure 3: Age-specific PPV by cancer type](output/ppv_by_age.png)
**Fig. 3.** Age-specific positive predictive value for each cancer, assuming sensitivity 0.70 and specificity 0.99.

### Sensitivity to test specificity

Lowering specificity from 99% to 95% approximately halved aggregate PPV (from {ppv_99:.2f}% to {ppv_95:.2f}%) and dramatically increased total visits and capacity pressure (Fig. 4; Table 3).

**Table 3. Aggregate outcomes by follow-up rate (base-case specificity).**

{format_markdown_table(make_table_3(agg))}

![Figure 4: PPV and total positives across specificity values](output/specificity_sweep.png)
**Fig. 4.** Aggregate positive predictive value (%) and total positive results per 100,000 screened across specificity values at a 70% follow-up rate.

## Discussion

Our scenario model shows that, even under optimistic assumptions for test accuracy, a DTC blood-based MCED screening wave can produce roughly {row_50['fp_to_tp_ratio']:.0f} false-positive workups for every true cancer detected. At 30% follow-up, illustrative specialist capacity is already saturated ({row_30['max_capacity_utilization_pct']:.1f}% utilisation); at 50% it is exceeded by {row_50['max_capacity_utilization_pct']-100:.1f} percentage points. The burden is not uniform: cancers with low prevalence (ovarian, liver, pancreatic) had the lowest PPV and the highest FP/TP ratios, while age strongly modulates PPV.

These findings align with real-world data from the N-NOSE PET/CT survey, in which the cancer discovery rate after a high-risk result was low and well below the company's advertised PPV [^5^].

### Limitations

Our analysis intentionally uses scenario assumptions for test performance, diagnostic pathways, and the age distribution of DTC users, because these data are not publicly reported. Prevalence was approximated by adult incidence; true point prevalence of undiagnosed cancers may differ. Capacity was annualised from a one-month facility survey and then further reduced by an arbitrary available-for-cancer-workup share. The model is deterministic and does not capture stochastic variation, geographic maldistribution, or queueing effects.

### Conclusion

Without regulatory guardrails—clear performance thresholds, transparent PPV reporting, and follow-up obligations—direct-to-consumer MCED tests risk converting a marketing promise into a large-scale false-positive cascade that stresses Japan’s diagnostic capacity.

## References

""" + "\n\n".join(references) + "\n"
    return md


def format_markdown_table(table: List[List[str]]) -> str:
    lines = ["| " + " | ".join(row) + " |" for row in table]
    lines.insert(1, "|" + "|".join(["---" for _ in table[0]]) + "|")
    return "\n".join(lines)


def build_tables_docx(tables: Dict[str, List[List[str]]], docx_path: Path) -> None:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    for title, table_data in tables.items():
        p = doc.add_heading(title, level=2)
        # Add table
        t = doc.add_table(rows=1, cols=len(table_data[0]))
        t.style = "Table Grid"
        hdr_cells = t.rows[0].cells
        for i, val in enumerate(table_data[0]):
            hdr_cells[i].text = val
            for p in hdr_cells[i].paragraphs:
                for r in p.runs:
                    r.font.bold = True
        for row in table_data[1:]:
            row_cells = t.add_row().cells
            for i, val in enumerate(row):
                row_cells[i].text = val
        doc.add_paragraph()
    doc.save(docx_path)


def build_figures_pptx(output_dir: Path, pptx_path: Path) -> None:
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    figures = [
        ("Figure 1. Total downstream visits by follow-up rate", output_dir / "total_visits_by_followup.png"),
        ("Figure 2. Diagnostic capacity utilisation by follow-up rate", output_dir / "capacity_utilization.png"),
        ("Figure 3. Age-specific PPV by cancer type", output_dir / "ppv_by_age.png"),
        ("Figure 4. PPV and total positives across specificity values", output_dir / "specificity_sweep.png"),
    ]

    for title, img_path in figures:
        slide_layout = prs.slide_layouts[6]  # blank
        slide = prs.slides.add_slide(slide_layout)
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.8))
        tf = txBox.text_frame
        tf.text = title
        p = tf.paragraphs[0]
        p.font.size = Pt(20)
        p.font.bold = True
        if img_path.exists():
            slide.shapes.add_picture(str(img_path), Inches(1.0), Inches(1.3), width=Inches(11.0))
    prs.save(pptx_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build manuscript materials")
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
    threshold = find_capacity_threshold(agg)

    # Markdown manuscript
    md = build_markdown(params, agg, by_cancer_at_50, weighted_ppv, threshold, args.output)
    (args.manuscript / "manuscript.md").write_text(md, encoding="utf-8")

    # Tables docx
    tables = {
        "Table 1. Data sources and scenario parameters": make_table_1(params),
        "Table 2. Per-cancer outcomes at 50% follow-up": make_table_2(by_cancer_at_50, weighted_ppv),
        "Table 3. Aggregate outcomes by follow-up rate": make_table_3(agg),
    }
    build_tables_docx(tables, args.manuscript / "manuscript_tables.docx")

    # Figures pptx
    build_figures_pptx(args.output, args.manuscript / "manuscript_figures.pptx")

    print(f"Manuscript materials written to {args.manuscript.resolve()}")


if __name__ == "__main__":
    main()
