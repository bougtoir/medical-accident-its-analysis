"""
Generate PPTX with all figures for STROBE manuscript.
1 slide per figure, English labels, widescreen.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from PIL import Image

BASE = Path(__file__).resolve().parent

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_slide(prs, img_path, title_text, caption_text):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Title
    left, top = Inches(0.5), Inches(0.2)
    txBox = slide.shapes.add_textbox(left, top, Inches(12.333), Inches(0.6))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)
    p.alignment = PP_ALIGN.CENTER

    # Image (centered, scaled proportionally)
    img = Image.open(img_path)
    iw, ih = img.size
    max_w = Inches(11.5)
    max_h = Inches(5.5)
    scale = min(max_w / iw, max_h / ih)
    w_px = int(iw * scale)
    h_px = int(ih * scale)
    left_img = (prs.slide_width - w_px) / 2
    top_img = Inches(0.9) + (max_h - h_px) / 2
    slide.shapes.add_picture(str(img_path), left_img, top_img, w_px, h_px)

    # Caption
    txBox2 = slide.shapes.add_textbox(Inches(0.5), Inches(6.7), Inches(12.333), Inches(0.7))
    tf2 = txBox2.text_frame
    p2 = tf2.paragraphs[0]
    p2.text = caption_text
    p2.font.size = Pt(11)
    p2.font.italic = True
    p2.alignment = PP_ALIGN.CENTER

figures = [
    (BASE / "figures_strobe" / "fig_flowchart.png",
     "Figure 1. STROBE Flow Diagram",
     "Participant selection from initial assessment (N=3,479) through primary analysis (N=3,188) and sensitivity subgroup (N=663)."),
    (BASE / "figures_e" / "fig1_rates_comparison.png",
     "Figure 2. IONV Rates: Broad vs Narrow Definition",
     "Comparison of antiemetic use between singleton and twin groups using broad (all 7 drugs) and narrow (5-HT3 antagonists only) definitions."),
    (BASE / "figures_e" / "fig2_forest_E_primary.png",
     "Figure 3. Forest Plot — Narrow Antiemetic Definition",
     "Multivariable logistic regression for 5-HT3 antagonist use (primary outcome). Reduced model (6 covariates)."),
    (BASE / "figures_e" / "fig4_protocol_vs_defE.png",
     "Figure 4. Twin Effect: Broad vs Narrow Definition",
     "Adjusted odds ratios for twin pregnancy across broad and narrow antiemetic definitions."),
    (BASE / "figures_e" / "fig3_covariate_sensitivity.png",
     "Figure 5. Covariate Sensitivity Analysis",
     "Robustness of twin effect across 20 covariate models for narrow-definition primary outcome (all P < 0.05)."),
    (BASE / "figures_excl" / "fig1_rates_comparison.png",
     "Figure 6. IONV Rates — Elective Low-Risk Subgroup",
     "IONV rates in sensitivity subgroup (N=663) after excluding emergency CS, prior CS, HDP, preoperative steroid."),
    (BASE / "figures_excl" / "fig4_broad_vs_narrow.png",
     "Figure 7. Twin Effect — Elective Low-Risk Subgroup",
     "Adjusted odds ratios in sensitivity subgroup: aOR increased from 3.18 to 13.59 for narrow definition."),
]

for img_path, title, caption in figures:
    if img_path.exists():
        add_slide(prs, img_path, title, caption)

out_path = BASE / "figures_strobe.pptx"
prs.save(str(out_path))
print(f"PPTX saved to {out_path}")
