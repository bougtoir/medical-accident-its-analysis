"""Generate a short-communication manuscript (docx) + editable figure pptx.

ALL numeric results are read from results/weibull_fits.csv (never hard-coded).
Citation numbers use {n} markers rendered as Word-native superscript runs.
Figure is inserted inline after its first in-text mention; Table 1 is built
from the results CSV. An editable English PPTX (one figure per slide) is also
written.
"""
import os
import re
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PInches, Pt as PPt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
FIGDIR = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "manuscript")
os.makedirs(OUT, exist_ok=True)

FITS = pd.read_csv(os.path.join(RESULTS, "weibull_fits.csv")).set_index("dataset")
FIG = os.path.join(FIGDIR, "weibull_real_fits.png")

# Numbered in order of first appearance in the body (Vancouver).
REFERENCES = [
    "World Health Organization. Global Tuberculosis Report 2024. Geneva: WHO; 2024.",
    "Tsibiyane M, Faye LM, Ndayi K, Sineke N, Tyeshani L, Faleni M, et al. Multilevel "
    "determinants of tuberculosis treatment interruption in rural South Africa: insights from "
    "primary healthcare nurses. Int J Environ Res Public Health. 2026;23(5):598. "
    "doi:10.3390/ijerph23050598.",
    "Kedthongma W, Usaprom S, Phakdeekul W. Community-based interventions to improve "
    "tuberculosis treatment outcomes: a meta-analysis. MethodsX. 2026;16:103893. "
    "doi:10.1016/j.mex.2026.103893.",
    "Fufa DB, Diriba TA, Dame KT, Debusho LK. Competing risk models to evaluate the "
    "factors for time to loss to follow-up among tuberculosis patients at Ambo General "
    "Hospital. Arch Public Health. 2023;81:113. doi:10.1186/s13690-023-01130-2.",
    "Jiang Y, Chen J, Ying M, Liu L, Li M, Lu S, et al. Factors associated with loss to "
    "follow-up before and after treatment initiation among patients with tuberculosis: a "
    "5-year observation in China. Front Med. 2023;10:1136094. doi:10.3389/fmed.2023.1136094.",
    "Daba O, Tsegaye D, Reshad M. Incidence and predictors of loss to follow-up among ART "
    "patients on follow-up at public health facilities in Southwest Ethiopia: a time-to-event "
    "analysis. J Int Assoc Provid AIDS Care. 2026;25:23259582261426232. "
    "doi:10.1177/23259582261426232.",
    "Salas Aranda P, Garcia Cerdan C, Martin Gomez C, Lorenzo Romo C, Turrion Gomez M, "
    "Isidoro Garcia M, et al. Time to discontinuation in routine clinical practice of the "
    "initially prescribed antipsychotic treatment in patients with first-episode psychosis. "
    "Eur Psychiatry. 2025;68(Suppl):PMC12437960.",
]


def kfmt(name):
    r = FITS.loc[name]
    return f"{r['k']:.2f} (95% CI {r['k_lo']:.2f}\u2013{r['k_hi']:.2f})"


def add_runs(p, text):
    """Split on {..} markers -> superscript citation runs; **bold** supported."""
    for seg in re.split(r'(\{[^}]+\})', text):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            run = p.add_run(seg[1:-1])
            run.font.superscript = True
        else:
            parts = re.split(r'(\*\*[^*]+\*\*)', seg)
            for pt in parts:
                if pt.startswith("**") and pt.endswith("**"):
                    run = p.add_run(pt[2:-2]); run.bold = True
                elif pt:
                    p.add_run(pt)


def heading(doc, text, size=13):
    p = doc.add_paragraph()
    p.space_before = Pt(12)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    return p


def para(doc, text, align=None, space_before=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    if align:
        p.alignment = align
    add_runs(p, text)
    return p


def build_docx():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1)

    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Divergent hazard shapes of tuberculosis treatment loss to follow-up: a "
                  "reproducible re-analysis quantifying the heterogeneity that hinders a "
                  "unified retention intervention")
    r.bold = True; r.font.size = Pt(15)
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Short communication").italic = True

    heading(doc, "Abstract")
    para(doc,
         "Loss to follow-up (LTFU) during tuberculosis (TB) treatment is a major barrier to cure "
         "and transmission control{1}. Its determinants are known to be multilevel and "
         "context-dependent{2}, and community/behavioural interventions to prevent it show "
         "inconsistent, setting-specific effectiveness{3}; why a single retention strategy does "
         "not travel well is unresolved. We give this qualitative problem a quantitative handle by "
         "asking whether the *timing* of LTFU (its hazard shape) is consistent across settings. We "
         "fitted two-parameter Weibull cumulative-incidence models to four real, published "
         "time-to-event curves recovered by figure digitization: two TB cohorts (Ethiopia{4}, "
         "China{5}) and two non-TB comparators (HIV/ART retention{6}; antipsychotic "
         "time-to-discontinuation{7}). The shape parameter k (k>1 increasing-failure-rate [IFR]; "
         "k<1 decreasing-failure-rate [DFR]) **diverged within TB**: Ethiopia "
         f"k={kfmt('TB-Ethiopia')} (IFR) versus China k={kfmt('TB-China')} (DFR) \u2014 opposite "
         "sides of k=1 from only two cohorts, with non-identical outcome definitions. By contrast "
         f"both comparators were DFR (HIV/ART k={kfmt('ART/HIV')}; antipsychotic "
         f"k={kfmt('Antipsychotic')}), i.e. mutually consistent. TB LTFU is therefore **not** "
         "uniformly increasing-hazard: its hazard shape is heterogeneous across countries "
         "(plausibly because the country-specific mechanisms that generate LTFU differ), which "
         "mathematically illustrates why pooled TB evidence and a one-size retention intervention "
         "are hard to build, whereas the comparator interventions may pool more readily. The cause "
         "of the shape divergence is unknown. All results regenerate from code and the digitized "
         "source figures.")

    heading(doc, "1. Introduction")
    para(doc,
         "LTFU interrupts TB treatment, promotes acquired drug resistance and sustains "
         "transmission{1}. Two things are already established. First, the determinants of "
         "treatment interruption are multilevel and strongly context-dependent, differing by "
         "health system, case mix and social setting{2}. Second, interventions intended to keep "
         "patients in care\u2014community-based, behavioural and digital approaches\u2014show "
         "inconsistent, setting-specific effectiveness, so no single strategy has proved "
         "universally transferable{3}. What has been missing is a *quantitative* description of "
         "the phenomenon that plausibly underlies this: whether patients across settings even "
         "disengage on the same time-course. Programmatic reports usually give a single cumulative "
         "LTFU proportion, hiding *when* during treatment patients leave. The hazard shape carries "
         "direct operational meaning: an increasing hazard (k>1) argues for intensified support "
         "late in treatment, a decreasing hazard (k<1) for front-loading it in the earliest weeks. "
         "We therefore asked a narrow question: across TB cohorts that publish a time-resolved "
         "LTFU curve, is the Weibull hazard shape consistent, and how does it compare with dropout "
         "in unrelated chronic treatments? A divergence within TB but consistency among "
         "comparators would give a concrete, reproducible measure of why TB retention resists a "
         "unified approach.")

    heading(doc, "2. Methods")
    para(doc,
         "We used only real, published curves. TB data were the competing-risk LTFU cumulative "
         "incidence at Ambo General Hospital, Ethiopia{4}, and the all-patient time-to-LTFU "
         "Kaplan\u2013Meier curve from a 5-year Chinese cohort{5}. Comparators were an HIV/ART "
         "retention curve{6} and an antipsychotic time-to-discontinuation curve{7}. Curves were "
         "digitized from the published figures by an in-house pixel extractor with axis "
         "calibration read from figure tick marks (values taken from curve pixels, not entered "
         "by hand). For each dataset we fitted the Weibull cumulative-incidence model "
         "F(t)=1\u2212exp(\u2212(t/\u03bb)^k) by nonlinear least squares, obtained a bootstrap "
         "95% CI for k, and compared fit with exponential (k=1) and log-normal models by AIC. "
         "The shape parameter k is unit-free, so mixed follow-up units (months, days) do not "
         "affect the cross-study comparison. Data, code and a one-command build are in the public "
         "repository (Data and code availability).")

    heading(doc, "3. Results")
    p = para(doc,
             "Fitted parameters are shown in Table 1 and the fits are overlaid on the digitized "
             "data in Figure 1. Within TB, the two cohorts fell on **opposite sides** of k=1: the "
             f"Ethiopian competing-risk CIF accelerated over the 6-month course (k={kfmt('TB-Ethiopia')}, "
             f"IFR), whereas the Chinese all-patient curve was strongly front-loaded (k={kfmt('TB-China')}, "
             "DFR), most LTFU occurring in the first months. Both non-TB comparators were DFR "
             f"(HIV/ART k={kfmt('ART/HIV')}; antipsychotic k={kfmt('Antipsychotic')}), i.e. dropout "
             "risk highest early then decelerating.")

    # Table 1 from results CSV
    para(doc, "**Table 1.** Weibull fits to digitized treatment-dropout curves (source of truth: "
              "results/weibull_fits.csv).", space_before=10)
    order = ["TB-Ethiopia", "TB-China", "ART/HIV", "Antipsychotic"]
    tbl = doc.add_table(rows=1, cols=5); tbl.style = "Table Grid"
    for i, h in enumerate(["Dataset (source)", "k (95% CI)", "\u03bb", "R\u00b2", "Hazard pattern"]):
        tbl.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
    for name in order:
        r = FITS.loc[name]
        c = tbl.add_row().cells
        c[0].text = f"{name} \u2014 {r['source']}"
        c[1].text = f"{r['k']:.2f} ({r['k_lo']:.2f}\u2013{r['k_hi']:.2f})"
        c[2].text = f"{r['lam']:.1f}"
        c[3].text = f"{r['r2']:.3f}"
        c[4].text = str(r['hazard_pattern'])

    cap = para(doc, "", space_before=14)
    doc.add_picture(FIG, width=Inches(6.3))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, "**Figure 1.** Weibull cumulative-incidence fits (red) to digitized dropout curves "
              "(points) for two TB cohorts and two comparators. TB is split between IFR (Ethiopia) "
              "and DFR (China), spanning the whole range; comparators are consistently DFR.",
              space_before=4)

    heading(doc, "4. Discussion")
    para(doc,
         "The result puts a number on an accepted but qualitative problem. It is already known "
         "that TB LTFU determinants are context-dependent{2} and that retention interventions do "
         "not transfer cleanly between settings{3}; our contribution is to show that this "
         "heterogeneity is visible in the **hazard shape itself**. Two TB cohorts fell on opposite "
         "sides of k=1 \u2014 one late-accelerating (IFR), one strongly front-loaded (DFR) \u2014 "
         "spanning the entire range that the two unrelated comparators occupied only on the DFR "
         "side. In other words, the comparator interventions were mutually consistent (both DFR) "
         "and would plausibly support a common time-course model, whereas the two TB settings did "
         "not share even the *direction* of their hazard. This is a compact, reproducible "
         "illustration of why pooled TB evidence and a single unified retention intervention are "
         "hard to construct: if countries differ in *when* patients disengage, an intervention "
         "timed for one will be mistimed for another.")
    para(doc,
         "We cannot explain the divergence, and we do not claim to. It is confounded with "
         "different outcome definitions (competing-risk CIF vs all-patient KM), case mix, programme "
         "context and the 6- vs 12-month observation windows, and it rests on digitized aggregate "
         "curves rather than individual patient data. That the mechanism is unknown is precisely "
         "the open question worth stating: the country-specific processes that generate LTFU "
         "appear to differ enough to change the hazard shape, and identifying what drives this "
         "\u2014 regimen phase, health-system factors, or case mix \u2014 would require more TB "
         "cohorts with individual-level data and harmonized LTFU definitions. Until then, the "
         "honest reading is that TB retention is a heterogeneous target, not a single one.")

    heading(doc, "5. Limitations")
    para(doc,
         "Only two TB and two comparator curves met the bar of a genuinely time-resolved, "
         "openly available dropout curve; earlier five-country claims could not be reproduced from "
         "primary sources and are not made here. Estimates come from digitized aggregate curves, "
         "not individual patient data; the Ethiopian estimate is a competing-risk "
         "*subdistribution*-hazard shape; the antipsychotic cohort is small (n\u224842) and "
         "illustrative; KM plateaus reflect administrative censoring. These results are "
         "hypothesis-generating, not confirmatory.")

    heading(doc, "6. Data and code availability")
    para(doc,
         "All source figures, digitized CSVs, analysis code and a one-command build "
         "(`make`) that regenerates every number, the table and Figure 1 are in the public "
         "repository under weibull-clinical-dropout/reanalysis_real/. No result is hard-coded.")

    heading(doc, "References")
    for i, ref in enumerate(REFERENCES, 1):
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(3)
        p.add_run(f"{i}. {ref}")

    path = os.path.join(OUT, "tb_dropout_heterogeneity_short_communication.docx")
    doc.save(path); print("wrote", path)


def build_pptx():
    prs = Presentation(); prs.slide_width = PInches(13.333); prs.slide_height = PInches(7.5)
    blank = prs.slide_layouts[6]
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(PInches(0.5), PInches(0.2), PInches(12.3), PInches(0.8))
    tb.text_frame.text = "Figure 1. Weibull fits to digitized treatment-dropout curves (TB vs comparators)"
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(20)
    s.shapes.add_picture(FIG, PInches(1.4), PInches(1.1), width=PInches(10.5))
    cap = s.shapes.add_textbox(PInches(0.5), PInches(6.7), PInches(12.3), PInches(0.7))
    cap.text_frame.text = ("TB splits between IFR (Ethiopia) and DFR (China); HIV/ART and "
                           "antipsychotic comparators are DFR. Values: results/weibull_fits.csv.")
    cap.text_frame.paragraphs[0].runs[0].font.size = PPt(12)
    path = os.path.join(OUT, "figures_editable_en.pptx")
    prs.save(path); print("wrote", path)


if __name__ == "__main__":
    build_docx()
    build_pptx()
