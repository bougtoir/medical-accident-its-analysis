#!/usr/bin/env python3
"""Build PPTX with one figure/table per slide (English version).
Code-generated plots are embedded as images; tables are editable PowerPoint tables."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
import os

OUTPUT_DIR = "/home/ubuntu/medical_analysis/output"
MANUSCRIPT_DIR = "/home/ubuntu/medical_analysis/manuscript"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

TITLE_FONT = "Times New Roman"
BODY_FONT = "Times New Roman"
DARK = RGBColor(0x1A, 0x1A, 0x2E)
ACCENT = RGBColor(0x00, 0x52, 0x8A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF5, 0xF5, 0xF5)
HEADER_BG = RGBColor(0x00, 0x52, 0x8A)
ALT_ROW = RGBColor(0xE8, 0xF0, 0xF8)


def add_image_slide(image_path, title_text, caption_text):
    """Add a slide with a code-generated figure (embedded as image)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

    # Title bar
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.7))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.name = TITLE_FONT
    p.font.color.rgb = DARK
    p.alignment = PP_ALIGN.LEFT

    # Image
    if os.path.exists(image_path):
        from PIL import Image
        img = Image.open(image_path)
        img_w, img_h = img.size
        aspect = img_w / img_h

        max_w = Inches(11.5)
        max_h = Inches(5.5)

        if aspect > (max_w / max_h):
            w = max_w
            h = int(w / aspect)
        else:
            h = max_h
            w = int(h * aspect)

        left = int((prs.slide_width - w) / 2)
        top = Inches(1.2)
        slide.shapes.add_picture(image_path, left, top, w, h)
    else:
        txBox2 = slide.shapes.add_textbox(Inches(2), Inches(3), Inches(9), Inches(1))
        tf2 = txBox2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = f"[Image not found: {image_path}]"
        p2.font.size = Pt(14)
        p2.font.italic = True

    # Caption
    txBox3 = slide.shapes.add_textbox(Inches(0.5), Inches(6.8), Inches(12.3), Inches(0.6))
    tf3 = txBox3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = caption_text
    p3.font.size = Pt(11)
    p3.font.italic = True
    p3.font.name = BODY_FONT
    p3.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    p3.alignment = PP_ALIGN.LEFT


def add_table_slide(title_text, headers, rows, caption_text=None):
    """Add a slide with an editable PowerPoint table."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Title
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.7))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.name = TITLE_FONT
    p.font.color.rgb = DARK
    p.alignment = PP_ALIGN.LEFT

    # Table dimensions
    n_rows = 1 + len(rows)
    n_cols = len(headers)
    tbl_width = Inches(12)
    tbl_height = Inches(0.4) * n_rows
    left = Inches(0.667)
    top = Inches(1.3)

    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, tbl_width, tbl_height)
    table = table_shape.table

    # Column widths - distribute evenly with first column wider
    first_col_w = int(tbl_width * 0.22)
    other_col_w = int((tbl_width - first_col_w) / max(n_cols - 1, 1))
    table.columns[0].width = first_col_w
    for i in range(1, n_cols):
        table.columns[i].width = other_col_w

    # Header row
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.name = BODY_FONT
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.fill.solid()
        cell.fill.fore_color.rgb = HEADER_BG

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(11)
            p.font.name = BODY_FONT
            p.font.color.rgb = DARK
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            # Alternate row shading
            if r_idx % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = ALT_ROW

    # Caption
    if caption_text:
        y_cap = top + tbl_height + Inches(0.3)
        txBox2 = slide.shapes.add_textbox(Inches(0.5), y_cap, Inches(12.3), Inches(0.5))
        tf2 = txBox2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = caption_text
        p2.font.size = Pt(11)
        p2.font.italic = True
        p2.font.name = BODY_FONT
        p2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


# ============================================================
# TITLE SLIDE
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
txBox = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(11.3), Inches(2))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = (
    "Impact of medical safety incidents on physician counts and "
    "healthcare facility numbers across 12 specialties in Japan: "
    "an interrupted time series analysis"
)
p.font.size = Pt(28)
p.font.bold = True
p.font.name = TITLE_FONT
p.font.color.rgb = DARK
p.alignment = PP_ALIGN.CENTER

txBox2 = slide.shapes.add_textbox(Inches(2), Inches(4.5), Inches(9.3), Inches(1))
tf2 = txBox2.text_frame
tf2.word_wrap = True
p2 = tf2.paragraphs[0]
p2.text = "Figures and Tables for BMJ Submission"
p2.font.size = Pt(18)
p2.font.name = BODY_FONT
p2.font.color.rgb = ACCENT
p2.alignment = PP_ALIGN.CENTER

p3 = tf2.add_paragraph()
p3.text = "[Author names to be added]"
p3.font.size = Pt(14)
p3.font.name = BODY_FONT
p3.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
p3.alignment = PP_ALIGN.CENTER

# ============================================================
# FIGURES (code-generated, embedded as images)
# ============================================================

add_image_slide(
    os.path.join(OUTPUT_DIR, "accident_trends.png"),
    "Figure 1. Trends in medical safety incident counts by specialty and definition",
    "Panel A: Mandatory reports to the Japan Medical Safety Research Organisation (JMSR, 2015\u20132025). "
    "Panel B: Medical litigation statistics from the Supreme Court of Japan (2004\u20132023). "
    "Top 5 specialties by incident count highlighted."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "its_physicians_def1.png"),
    "Figure 2. Interrupted time series: physician counts vs JMSR reports",
    "Segmented regression fit lines for 12 core specialties. "
    "Vertical dashed lines indicate the intervention year (peak accident reporting year for each specialty)."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "its_physicians_def2.png"),
    "Figure 3. Interrupted time series: physician counts vs litigation statistics",
    "Segmented regression fit lines for 12 core specialties using Supreme Court litigation data (Definition 2). "
    "Vertical dashed lines indicate the intervention year."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "its_facilities_def1.png"),
    "Figure 4. Interrupted time series: facility counts vs JMSR reports",
    "Segmented regression fit lines for healthcare facility counts across 12 core specialties. "
    "Vertical dashed lines indicate the intervention year."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "lead_time_heatmap.png"),
    "Figure 5. Heatmap of estimated lead times (years) from cross-correlation analysis",
    "Rows: specialties. Columns: accident definition \u00d7 outcome combinations. "
    "Darker colour indicates stronger inverse correlation. "
    "Positive lag values indicate accident changes precede outcome changes."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "forecast_physicians.png"),
    "Figure 6. Projected physician counts by specialty (2025\u20132034)",
    "Linear trend extrapolation based on the most recent 10 years of data, with 95% prediction intervals."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "forecast_facilities.png"),
    "Figure 7. Projected facility counts by specialty (2025\u20132034)",
    "Linear trend extrapolation based on the most recent 10 years of data, with 95% prediction intervals."
)

add_image_slide(
    os.path.join(OUTPUT_DIR, "forecast_trainees.png"),
    "Figure 8. Projected trainee registrations by specialty (2025\u20132034)",
    "Linear trend extrapolation based on available data (2018\u20132025), with 95% prediction intervals."
)

# ============================================================
# TABLES (editable PowerPoint tables)
# ============================================================

# Table 1: Cross-correlation results
add_table_slide(
    "Table 1. Strong inverse cross-correlations (|r| > 0.9) after linear detrending",
    ["Specialty", "Definition", "Outcome", "Lag (years)", "r"],
    [
        ["Obstetrics/Gynaecology", "JMSR", "Physicians", "+3", "\u22120.946"],
        ["Obstetrics/Gynaecology", "Mixed", "Physicians", "+3", "\u22120.947"],
        ["Urology", "JMSR", "Physicians", "+6", "\u22120.945"],
        ["Anaesthesiology", "Mixed", "Physicians", "\u22124", "\u22120.959"],
        ["Otorhinolaryngology", "Litigation", "Physicians", "+6", "\u22120.973"],
        ["Dermatology", "Litigation", "Physicians", "+7", "\u22120.988"],
        ["Orthopaedic Surgery", "JMSR (trainees)", "Trainees", "+4", "\u22120.909"],
        ["Otorhinolaryngology", "JMSR (trainees)", "Trainees", "\u22123", "\u22120.941"],
        ["Psychiatry", "Litigation", "Facilities", "+8", "\u22120.981"],
        ["Dermatology", "Litigation", "Facilities", "+8", "\u22120.969"],
    ],
    "Cross-correlation of linearly detrended accident and outcome series at lags \u22128 to +8 years. "
    "Positive lag = accident change precedes outcome change."
)

# Table 2: ITS regression results
add_table_slide(
    "Table 2. Statistically significant (P<0.05) accident effect coefficients from ITS segmented regression",
    ["Specialty", "Definition", "Outcome", "R\u00b2", "Accident effect", "P value"],
    [
        ["General Surgery", "Litigation", "Physicians", "0.994", "+19.3/case", "<0.001"],
        ["Obstetrics/Gynaecology", "JMSR", "Physicians", "0.995", "+17.7/report", "0.021"],
        ["Obstetrics/Gynaecology", "Litigation", "Physicians", "0.977", "+11.6/case", "<0.001"],
        ["Obstetrics/Gynaecology", "JMSR", "Facilities", "0.999", "+4.3/report", "0.042"],
        ["Obstetrics/Gynaecology", "Litigation", "Facilities", "0.990", "+5.5/case", "<0.001"],
        ["Ophthalmology", "JMSR", "Facilities", "1.000", "+4.1/report", "0.039"],
        ["Plastic Surgery", "Litigation", "Facilities", "0.999", "+4.1/case", "0.005"],
    ],
    "Note: Positive coefficients reflect shared secular trends between accident counts and outcomes. "
    "See Discussion for interpretation."
)

# Table 3: Lead time and window period summary
add_table_slide(
    "Table 3. Summary of lead time and window period estimates by outcome",
    ["Outcome", "Mean lead time (yr)", "Median lead time (yr)",
     "Mean window (yr)", "Median window (yr)"],
    [
        ["Physician counts", "1.3", "2.5", "4.1", "4.0"],
        ["Facility counts", "\u22120.1", "0.0", "4.2", "5.0"],
    ],
    "Lead time: delay from accident change to outcome change. "
    "Window period: duration of effect estimated by AIC-based model selection."
)

# Table 4: Projected workforce changes
add_table_slide(
    "Table 4. Projected annual workforce changes by specialty (2025\u20132034)",
    ["Specialty", "Physicians/yr", "Facilities/yr", "Trainees/yr"],
    [
        ["General Surgery", "\u2212260", "\u2212350", "+3"],
        ["Obstetrics/Gynaecology", "+111", "\u221265", "+6"],
        ["Internal Medicine", "+378", "\u2212256", "+30"],
        ["Paediatrics", "+206", "\u2212188", "\u22125"],
        ["Orthopaedic Surgery", "+190", "\u221234", "+30"],
        ["Anaesthesiology", "+186", "+72", "0"],
        ["Otorhinolaryngology", "\u221216", "\u221297", "\u22125"],
        ["Emergency Medicine", "\u2014", "\u2014", "+33"],
        ["General Practice", "\u2014", "\u2014", "+20"],
    ],
    "Linear trend extrapolation from the most recent 10 years of available data."
)

# ============================================================
# SAVE
# ============================================================
output_path = os.path.join(MANUSCRIPT_DIR, "bmj_figures_en.pptx")
prs.save(output_path)
print(f"Saved to {output_path}")
