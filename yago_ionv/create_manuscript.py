"""
Generate Methods (Statistical Analysis) and Results sections
for the IONV during cesarean section study.

Outputs:
  - manuscript_methods_results.docx  (inline figures + tables)
  - figures.pptx                     (editable, one figure per slide)
"""

import json, re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import pandas as pd

BASE = Path(__file__).resolve().parent
FIG = BASE / "figures"

with open(BASE / "summary_stats.json") as f:
    S = json.load(f)

# ============================================================
# Helper: superscript citations using font.superscript
# ============================================================
def add_text_with_refs(para, text):
    parts = re.split(r"(\{[^}]+\})", text)
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            run = para.add_run(part[1:-1])
            run.font.superscript = True
            run.font.size = Pt(8)
        else:
            run = para.add_run(part)
            run.font.size = Pt(10)


def add_heading(doc, text, level=2):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
    return h


# ============================================================
# Build document
# ============================================================
doc = Document()

style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(10)
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(6)

# ========================= METHODS ========================= #
add_heading(doc, "Methods", level=1)
add_heading(doc, "Study Design and Setting")

p = doc.add_paragraph()
add_text_with_refs(p,
    "This retrospective, single-center, observational study was conducted at "
    "Juntendo University Shizuoka Hospital, Japan, using medical records from "
    "April 1, 2014, to October 23, 2024. The study was approved by the institutional "
    "review board and conducted in accordance with the Declaration of Helsinki (2013 revision) "
    "and the Japanese Ethical Guidelines for Medical and Biological Research Involving Human "
    "Subjects (2021). Informed consent was waived via an opt-out mechanism."
)

add_heading(doc, "Participants")
p = doc.add_paragraph()
add_text_with_refs(p,
    "We included women aged ≥18 years who underwent cesarean section under regional "
    "anesthesia (spinal, epidural, or combined spinal-epidural). "
    "Exclusion criteria were: general anesthesia, cardiac arrest in the operating room, "
    "pre-anesthesia systolic blood pressure <90 mmHg, intrauterine fetal death, "
    "vanishing twin, and triplet pregnancy."
)

add_heading(doc, "Outcome Measures")
p = doc.add_paragraph()
add_text_with_refs(p,
    "Because this was a retrospective study and nausea and vomiting could not be directly "
    "ascertained from medical records, intraoperative antiemetic use was employed as a "
    "surrogate marker for IONV.{2,3} "
    "The primary outcome was antiemetic use during the period from anesthesia induction to "
    "delivery or from delivery to operating room exit (i.e., any intraoperative antiemetic use). "
    "The secondary outcome was antiemetic use from anesthesia induction to delivery only. "
    "Antiemetics included ondansetron, granisetron, metoclopramide, droperidol, "
    "prochlorperazine (Novamin), hydroxyzine (Atarax-P), and dexamethasone."
)

p = doc.add_paragraph()
add_text_with_refs(p,
    "Patients who received antiemetics before anesthesia induction (during the admission-to-anesthesia "
    "period) were excluded from the outcome analysis, as pre-anesthesia antiemetic administration "
    "was considered likely prophylactic.{12-14}"
)

add_heading(doc, "Statistical Analysis")
p = doc.add_paragraph()
add_text_with_refs(p,
    "Continuous variables were summarized as median [interquartile range] and compared using "
    "the Mann-Whitney U test. Categorical variables were summarized as n (%) and compared using "
    "the chi-square test or Fisher's exact test where expected cell counts were <5."
)

p = doc.add_paragraph()
add_text_with_refs(p,
    "Multivariable logistic regression was performed to evaluate the association between "
    "twin pregnancy and IONV, adjusting for known risk factors: "
    "age, body mass index (BMI), gestational age, emergency cesarean section, prior cesarean section, "
    "hypertensive disorders of pregnancy (HDP), epidural anesthesia, surgery time, and "
    "intraoperative hypotension (systolic blood pressure <90 mmHg).{7,8} "
    "Uterine exteriorization was not included in the model because of excessive missing data "
    "(available in only approximately 20% of the cohort). "
    "Results are presented as odds ratios (OR) with 95% confidence intervals (CI). "
    "A two-sided P < 0.05 was considered statistically significant. "
    "All analyses were performed using Python 3.12 with statsmodels 0.14, scipy 1.14, "
    "and scikit-learn 1.6."
)

# ========================= RESULTS ========================= #
add_heading(doc, "Results", level=1)
add_heading(doc, "Study Population")

n_total = S["n_total_before_exclusion"]
n_excl = S["n_excluded"]
n_analysis = S["n_analysis"]
n_s = S["n_single"]
n_t = S["n_twin"]
n_pre_ae = S["n_pre_anesthesia_antiemetic_excluded"]

p = doc.add_paragraph()
add_text_with_refs(p,
    f"A total of {n_total:,} women who underwent cesarean section during the study period "
    f"were identified ({S['n_single_raw']:,} singleton and {S['n_twin_raw']:,} twin pregnancies). "
    f"After applying exclusion criteria, {S['n_after_exclusion']:,} patients remained "
    f"({n_total:,} total; {S['excl_general_anesthesia']} "
    f"excluded for general anesthesia, {S['excl_intrauterine_fetal_death']} for intrauterine fetal death, "
    f"{S['excl_vanishing_twin']} for vanishing twin, {S['excl_triplet_pregnancy']} for triplet pregnancy, "
    f"{S['excl_pre-anesthesia_sbp_lt_90_mmhg']} for pre-anesthesia hypotension, and "
    f"{S['excl_no_anesthesia_data_available']} for unavailable anesthesia data). "
    f"An additional {n_pre_ae} patients who received pre-anesthesia antiemetics were excluded "
    f"from the outcome analysis, yielding a final analysis cohort of {n_analysis:,} patients "
    f"({n_s:,} singleton, {n_t:,} twin) (Fig. 1)."
)

# Table 1
add_heading(doc, "Patient Characteristics (Table 1)")
p = doc.add_paragraph()
add_text_with_refs(p,
    "Baseline patient characteristics are summarized in Table 1. "
    "Compared with the singleton group, the twin group had significantly lower age "
    "(32.0 vs 34.0 years, P < 0.001), lower gestational age (37.0 vs 38.0 weeks, P < 0.001), "
    "fewer emergency cesarean sections (35.4% vs 46.8%, P < 0.001), "
    "fewer prior cesarean sections (11.7% vs 45.0%, P < 0.001), "
    "lower hypotension incidence (44.2% vs 52.8%, P = 0.003), "
    "and higher blood loss (1195 vs 650 mL, P < 0.001). "
    "BMI, epidural use, HDP, and preoperative steroid use did not differ significantly "
    "between groups."
)

# Insert Table 1
tab1 = pd.read_csv(BASE / "tables" / "table1_characteristics.csv")
table = doc.add_table(rows=1, cols=4)
table.style = "Table Grid"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = table.rows[0].cells
for i, h_text in enumerate(["Variable", "Singleton", "Twin", "P-value"]):
    hdr[i].text = h_text
    for para in hdr[i].paragraphs:
        for run in para.runs:
            run.bold = True
            run.font.size = Pt(9)

for _, row in tab1.iterrows():
    cells = table.add_row().cells
    cells[0].text = row["Variable"]
    cells[1].text = row["Singleton"]
    cells[2].text = row["Twin"]
    p_val = row["P-value"]
    cells[3].text = f"{p_val:.3f}" if p_val >= 0.001 else "< 0.001"
    for c in cells:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)

doc.add_paragraph()  # spacer

# IONV outcomes
add_heading(doc, "IONV Outcomes")

p_s = S["ionv_primary_single_pct"]
p_t = S["ionv_primary_twin_pct"]
s_s = S["ionv_secondary_single_pct"]
s_t = S["ionv_secondary_twin_pct"]

p = doc.add_paragraph()
add_text_with_refs(p,
    f"The primary outcome (any intraoperative antiemetic use) occurred in "
    f"{S['ionv_primary_single_n']} of {n_s:,} singleton patients ({p_s:.1f}%) and "
    f"{S['ionv_primary_twin_n']} of {n_t:,} twin patients ({p_t:.1f}%), "
    f"with no significant difference between groups (P = 0.731) (Table 2, Fig. 1). "
    f"The secondary outcome (antiemetic use before delivery) was similarly not significantly "
    f"different: {S['ionv_secondary_single_n']} ({s_s:.1f}%) in singletons vs "
    f"{S['ionv_secondary_twin_n']} ({s_t:.1f}%) in twins (P = 0.572). "
    f"Post-delivery antiemetic use rates were also comparable (16.0% vs 15.8%, P = 0.938)."
)

# Insert Fig 1
doc.add_paragraph()
p_fig = doc.add_paragraph()
p_fig.alignment = WD_ALIGN_PARAGRAPH.CENTER
if (FIG / "fig1_ionv_rates.png").exists():
    p_fig.add_run().add_picture(str(FIG / "fig1_ionv_rates.png"), width=Inches(5.5))
p_cap = doc.add_paragraph("Figure 1. IONV rates by group.")
p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_cap.runs[0].italic = True
p_cap.runs[0].font.size = Pt(9)
p_cap.paragraph_format.space_before = Pt(12)

# Table 2 (IONV outcomes)
tab2 = pd.read_csv(BASE / "tables" / "table2_ionv_outcomes.csv")
table2 = doc.add_table(rows=1, cols=4)
table2.style = "Table Grid"
table2.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr2 = table2.rows[0].cells
for i, h_text in enumerate(["Outcome", "Singleton", "Twin", "P-value"]):
    hdr2[i].text = h_text
    for para in hdr2[i].paragraphs:
        for run in para.runs:
            run.bold = True
            run.font.size = Pt(9)

for _, row in tab2.iterrows():
    cells = table2.add_row().cells
    cells[0].text = row["Outcome"]
    cells[1].text = row["Singleton"]
    cells[2].text = row["Twin"]
    p_val = row["P-value"]
    cells[3].text = f"{p_val:.3f}" if p_val >= 0.001 else "< 0.001"
    for c in cells:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)

# Antiemetic drug usage
add_heading(doc, "Antiemetic Drug Usage (Table 3)")

p = doc.add_paragraph()
add_text_with_refs(p,
    "The most commonly used antiemetic was metoclopramide (12.3% in singletons, 11.1% in twins), "
    "followed by droperidol (4.0% and 4.1%, respectively) (Table 3). "
    "Ondansetron use was significantly higher in twins (2.0% vs 0.9%, P = 0.041). "
    "Other antiemetic agents did not differ significantly between groups."
)

tab3 = pd.read_csv(BASE / "tables" / "table3_antiemetic_drugs.csv")
table3 = doc.add_table(rows=1, cols=4)
table3.style = "Table Grid"
table3.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr3 = table3.rows[0].cells
for i, h_text in enumerate(["Drug", "Singleton", "Twin", "P-value"]):
    hdr3[i].text = h_text
    for para in hdr3[i].paragraphs:
        for run in para.runs:
            run.bold = True
            run.font.size = Pt(9)

for _, row in tab3.iterrows():
    cells = table3.add_row().cells
    cells[0].text = row["Drug"]
    cells[1].text = row["Singleton"]
    cells[2].text = row["Twin"]
    p_val = row["P-value"]
    cells[3].text = f"{p_val:.3f}" if p_val >= 0.001 else "< 0.001"
    for c in cells:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)

# Multivariable regression
add_heading(doc, "Multivariable Logistic Regression")

if "primary_or_twin" in S:
    or_val = S["primary_or_twin"]
    ci_lo = S["primary_or_twin_ci_lower"]
    ci_hi = S["primary_or_twin_ci_upper"]
    p_val = S["primary_or_twin_p"]
    model_n = int(S["primary_model_n"])
    model_events = int(S["primary_model_events"])

    p_str = f"P = {p_val:.3f}" if p_val >= 0.001 else "P < 0.001"
    p = doc.add_paragraph()
    add_text_with_refs(p,
        f"In multivariable logistic regression (n = {model_n:,}; {model_events} events), "
        f"twin pregnancy was not independently associated with IONV "
        f"(adjusted OR {or_val:.2f}, 95% CI {ci_lo:.2f}–{ci_hi:.2f}; {p_str}) (Fig. 2, Table 4). "
        f"Factors significantly associated with IONV were epidural anesthesia "
        f"(OR 1.66, 95% CI 1.36–2.01; P < 0.001), longer surgery time "
        f"(OR 1.01 per minute, 95% CI 1.01–1.02; P < 0.001), and prior cesarean section "
        f"(OR 0.77, 95% CI 0.62–0.96; P = 0.021; protective)."
    )

# Insert Fig 2 - Forest plot (primary)
if (FIG / "fig2_forest_primary.png").exists():
    doc.add_paragraph()
    p_fig2 = doc.add_paragraph()
    p_fig2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig2.add_run().add_picture(str(FIG / "fig2_forest_primary.png"), width=Inches(5.5))
    p_cap2 = doc.add_paragraph("Figure 2. Forest plot: multivariable logistic regression for IONV (primary outcome).")
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2.runs[0].italic = True
    p_cap2.runs[0].font.size = Pt(9)
    p_cap2.paragraph_format.space_before = Pt(12)

# Insert Table 4
tab4 = pd.read_csv(BASE / "tables" / "table4_logistic_primary.csv")
table4 = doc.add_table(rows=1, cols=5)
table4.style = "Table Grid"
table4.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr4 = table4.rows[0].cells
for i, h_text in enumerate(["Variable", "OR", "95% CI lower", "95% CI upper", "P-value"]):
    hdr4[i].text = h_text
    for para in hdr4[i].paragraphs:
        for run in para.runs:
            run.bold = True
            run.font.size = Pt(9)

for _, row in tab4.iterrows():
    cells = table4.add_row().cells
    cells[0].text = str(row["Variable"])
    cells[1].text = f"{row['OR']:.2f}"
    cells[2].text = f"{row['95% CI lower']:.2f}"
    cells[3].text = f"{row['95% CI upper']:.2f}"
    p_val = row["P-value"]
    cells[4].text = f"{p_val:.3f}" if p_val >= 0.001 else "< 0.001"
    for c in cells:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)

# Secondary outcome
if "secondary_or_twin" in S:
    or_s = S["secondary_or_twin"]
    ci_s_lo = S["secondary_or_twin_ci_lower"]
    ci_s_hi = S["secondary_or_twin_ci_upper"]
    p_s_val = S["secondary_or_twin_p"]
    model_s_n = int(S["secondary_model_n"])
    model_s_events = int(S["secondary_model_events"])

    p_s_str = f"P = {p_s_val:.3f}" if p_s_val >= 0.001 else "P < 0.001"
    p = doc.add_paragraph()
    add_text_with_refs(p,
        f"For the secondary outcome (IONV before delivery; n = {model_s_n:,}, "
        f"{model_s_events} events), twin pregnancy was likewise not significantly associated "
        f"(adjusted OR {or_s:.2f}, 95% CI {ci_s_lo:.2f}–{ci_s_hi:.2f}; {p_s_str}) (Fig. 3, Table 5)."
    )

# Insert Fig 3 - Forest plot (secondary)
if (FIG / "fig3_forest_secondary.png").exists():
    doc.add_paragraph()
    p_fig3 = doc.add_paragraph()
    p_fig3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig3.add_run().add_picture(str(FIG / "fig3_forest_secondary.png"), width=Inches(5.5))
    p_cap3 = doc.add_paragraph("Figure 3. Forest plot: multivariable logistic regression for IONV (secondary outcome).")
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3.runs[0].italic = True
    p_cap3.runs[0].font.size = Pt(9)
    p_cap3.paragraph_format.space_before = Pt(12)

# IONV timing
add_heading(doc, "IONV Timing Distribution")
p = doc.add_paragraph()
add_text_with_refs(p,
    "The majority of IONV events occurred in the post-delivery phase (delivery to operating "
    "room exit), with comparable rates between singletons (16.0%) and twins (15.8%) (Fig. 4). "
    "IONV during the anesthesia-to-delivery phase was infrequent in both groups "
    "(1.9% vs 1.5%)."
)

if (FIG / "fig4_ionv_timing.png").exists():
    doc.add_paragraph()
    p_fig4 = doc.add_paragraph()
    p_fig4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig4.add_run().add_picture(str(FIG / "fig4_ionv_timing.png"), width=Inches(5.0))
    p_cap4 = doc.add_paragraph("Figure 4. IONV rates by timing phase.")
    p_cap4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap4.runs[0].italic = True
    p_cap4.runs[0].font.size = Pt(9)
    p_cap4.paragraph_format.space_before = Pt(12)

# Temporal trend
add_heading(doc, "Temporal Trends")
p = doc.add_paragraph()
add_text_with_refs(p,
    "Temporal trends of IONV rates are shown in Figure 5. "
    "IONV rates remained relatively stable over the study period in both groups, "
    "without a clear upward or downward trend."
)

if (FIG / "fig5_temporal_trend.png").exists():
    doc.add_paragraph()
    p_fig5 = doc.add_paragraph()
    p_fig5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig5.add_run().add_picture(str(FIG / "fig5_temporal_trend.png"), width=Inches(5.0))
    p_cap5 = doc.add_paragraph("Figure 5. Temporal trend of IONV rates by year.")
    p_cap5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap5.runs[0].italic = True
    p_cap5.runs[0].font.size = Pt(9)
    p_cap5.paragraph_format.space_before = Pt(12)

# Antiemetic drug comparison figure
if (FIG / "fig6_antiemetic_drugs.png").exists():
    doc.add_paragraph()
    p_fig6 = doc.add_paragraph()
    p_fig6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fig6.add_run().add_picture(str(FIG / "fig6_antiemetic_drugs.png"), width=Inches(5.0))
    p_cap6 = doc.add_paragraph("Figure 6. Antiemetic drug usage comparison: Singleton vs Twin.")
    p_cap6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap6.runs[0].italic = True
    p_cap6.runs[0].font.size = Pt(9)
    p_cap6.paragraph_format.space_before = Pt(12)

# Save
doc.save(str(BASE / "manuscript_methods_results.docx"))
print("Manuscript saved:", BASE / "manuscript_methods_results.docx")

# ============================================================
# PPTX - editable figures (one per slide)
# ============================================================
from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt

prs = Presentation()
prs.slide_width = PptInches(13.333)
prs.slide_height = PptInches(7.5)

fig_files = sorted(FIG.glob("*.png"))
fig_titles = {
    "fig1_ionv_rates.png": "Figure 1: IONV Rates by Group",
    "fig2_forest_primary.png": "Figure 2: Forest Plot — Primary Outcome",
    "fig3_forest_secondary.png": "Figure 3: Forest Plot — Secondary Outcome",
    "fig4_ionv_timing.png": "Figure 4: IONV Rates by Timing Phase",
    "fig5_temporal_trend.png": "Figure 5: Temporal Trend of IONV Rates",
    "fig6_antiemetic_drugs.png": "Figure 6: Antiemetic Drug Usage Comparison",
}

for fig_path in fig_files:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    
    # Title
    from pptx.util import Emu
    from pptx.dml.color import RGBColor as PptRGB
    txBox = slide.shapes.add_textbox(PptInches(0.5), PptInches(0.2), PptInches(12), PptInches(0.6))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = fig_titles.get(fig_path.name, fig_path.stem)
    p.font.size = PptPt(20)
    p.font.bold = True
    
    # Image (centered)
    img = slide.shapes.add_picture(str(fig_path), PptInches(1.5), PptInches(1.0), PptInches(10), PptInches(5.5))

prs.save(str(BASE / "figures.pptx"))
print("PPTX saved:", BASE / "figures.pptx")

print("Done!")
