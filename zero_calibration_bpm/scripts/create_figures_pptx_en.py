#!/usr/bin/env python3
"""Editable English figure deck (.pptx): one figure per slide (16:9)."""

import os

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(SCRIPT_DIR, "..", "figures")
OUTDIR = os.path.join(SCRIPT_DIR, "..", "manuscripts")
OUTPATH = os.path.join(OUTDIR, "BPM_Figures_EN.pptx")
os.makedirs(OUTDIR, exist_ok=True)

# Main figures (submission numbering) followed by the two Supplemental
# Digital Content figures, matching the manuscript.
SLIDES = [
    ("figure2_scenarios_concordance.png", "Figure 1. Concordance by scenario",
     "Device-versus-reference concordance for the four static scenarios; each "
     "panel shows CCC, scale shift v and mean bias. S4 has near-zero bias "
     "despite a 10% gain error."),
    ("figure3_detection_panel.png", "Figure 2. Detection pattern",
     "Which reported analysis detects the error in each scenario (green = "
     "detected, grey = missed). In S4 the mean-bias summary misses the gain "
     "error that all proportional-bias\u2013aware analyses detect."),
    ("figure4_ba_masked_gain.png", "Figure 3. Bland\u2013Altman regression",
     "Difference-versus-mean plots for S2 (flat slope) and S4 (positive slope "
     "despite near-zero mean bias), revealing the masked proportional (gain) "
     "error."),
    ("figure5_dynamic_response.png", "Figure 4. Dynamic response",
     "Frequency response and waveforms for optimal, under-damped and "
     "over-damped systems, with measured-versus-true pulse pressure and the "
     "mean PP ratio."),
    ("figure1_signal_decomposition.png",
     "Supplemental Digital Content 1. Signal decomposition",
     "A DC offset shifts the baseline but leaves pulse pressure unchanged; a "
     "gain error scales the whole waveform. Zeroing corrects the offset but "
     "not the gain error."),
    ("figure6_range_dependence.png",
     "Supplemental Digital Content 2. Range-dependence of the CCC",
     "For one fixed device, CCC and C_b increase as the sampled pressure "
     "range widens, while the scale shift v stays near the true gain ratio."),
]

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

SW, SH = 13.333, 7.5
for fname, title, caption in SLIDES:
    slide = prs.slides.add_slide(blank)

    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(SW - 1.0),
                                  Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run(); run.text = title
    run.font.size = Pt(24); run.font.bold = True

    path = os.path.join(FIGDIR, fname)
    top = 1.05
    avail_h = 5.0
    avail_w = SW - 1.0
    if os.path.exists(path):
        iw, ih = Image.open(path).size
        aspect = iw / ih
        w = avail_w
        h = w / aspect
        if h > avail_h:
            h = avail_h
            w = h * aspect
        left = (SW - w) / 2.0
        slide.shapes.add_picture(path, Inches(left), Inches(top),
                                 width=Inches(w), height=Inches(h))

    cb = slide.shapes.add_textbox(Inches(0.5), Inches(6.3), Inches(SW - 1.0),
                                  Inches(1.0))
    ctf = cb.text_frame
    ctf.word_wrap = True
    cp = ctf.paragraphs[0]
    crun = cp.add_run(); crun.text = caption
    crun.font.size = Pt(13); crun.font.italic = True

prs.save(OUTPATH)
print(f"Figure deck saved: {OUTPATH}")
