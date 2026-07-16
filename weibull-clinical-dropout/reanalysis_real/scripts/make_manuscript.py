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
    "Yu Y, Xian S, Yang D, Mu L, Han Y, Luo W, et al. Temporal trends in tuberculosis "
    "incidence among the aging population in Southwest China: a retrospective study. "
    "BMC Geriatr. 2026;26:373. doi:10.1186/s12877-026-07373-2.",
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
                  "reproducible analysis of published curves quantifying the heterogeneity "
                  "that hinders a unified retention intervention")
    r.bold = True; r.font.size = Pt(15)
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Brief Report").italic = True

    heading(doc, "Abstract")
    para(doc,
         "**Background** Loss to follow-up (LTFU) during tuberculosis (TB) treatment is a major "
         "barrier to cure and transmission control{1}. Its determinants are multilevel and "
         "context-dependent{2} and interventions to prevent it show inconsistent, setting-specific "
         "effectiveness{3}, but whether the *timing* of LTFU follows a consistent hazard shape "
         "across settings has not been quantified.")
    para(doc,
         "**Methods** We fitted two-parameter Weibull cumulative-incidence models "
         "F(t)=1\u2212exp(\u2212(t/\u03bb)^k) to four real, published time-to-event curves recovered "
         "by figure digitization: two TB treatment cohorts (Ethiopia{4}, China{5}) and two non-TB "
         "comparators (HIV/ART retention{6}; antipsychotic time-to-discontinuation{7}). The shape "
         "parameter k (k>1 increasing-failure-rate [IFR]; k<1 decreasing-failure-rate [DFR]) was "
         "estimated with a bootstrap 95% confidence interval (CI) and compared with exponential and "
         "log-normal fits by the Akaike information criterion (AIC).", space_before=4)
    para(doc,
         f"**Results** The shape parameter diverged within TB: Ethiopia k={kfmt('TB-Ethiopia')} "
         f"(IFR) versus China k={kfmt('TB-China')} (DFR) \u2014 opposite sides of k=1 from only two "
         f"cohorts, with non-identical outcome definitions. Both comparators were DFR (HIV/ART "
         f"k={kfmt('ART/HIV')}; antipsychotic k={kfmt('Antipsychotic')}), i.e. mutually consistent.",
         space_before=4)
    para(doc,
         "**Conclusions** TB LTFU is not uniformly increasing-hazard: its hazard shape is "
         "heterogeneous across countries, plausibly because the country-specific mechanisms that "
         "generate LTFU differ. This gives a compact, reproducible quantification of why pooled TB "
         "evidence and a one-size retention intervention are hard to build, whereas the comparator "
         "interventions may pool more readily. The cause of the divergence is unknown and warrants "
         "individual-level study.", space_before=4)
    para(doc, "**Keywords** Tuberculosis; Loss to follow-up; Treatment adherence; Weibull; "
              "Hazard function; Survival analysis; Age at onset; Health systems", space_before=4)

    heading(doc, "Background")
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

    heading(doc, "Methods")
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

    heading(doc, "Results")
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

    heading(doc, "Discussion")
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
    para(doc,
         "One candidate deserves explicit mention because it could unify the two observations "
         "\u2014 that the unrelated comparators behaved alike while the two TB settings did not "
         "\u2014 namely the age structure of disease onset. The two TB cohorts arise from "
         "demographically divergent epidemics: TB in China is increasingly concentrated in the "
         "elderly{8}, whereas high-burden sub-Saharan settings such as Ethiopia are dominated by "
         "young adults, and age was itself a significant risk factor for LTFU in the Ethiopian "
         "cohort{4}. If the age-at-onset distribution governs competing mortality, comorbidity and "
         "the reasons patients disengage, it could plausibly determine whether the LTFU hazard "
         "rises or falls over the course of treatment \u2014 in effect a time-to-onset (age) "
         "distribution modulating the time-to-LTFU hazard. We stress that this is a hypothesis, "
         "not a result: our curves are aggregate and not age-stratified, so neither an "
         "age-at-onset distribution nor an age-by-LTFU-timing interaction can be fitted here "
         "without inventing data. Testing it would require age-stratified time-to-LTFU curves or "
         "individual patient data.")
    para(doc,
         "The observation has practical implications for TB programmes, particularly in "
         "resource-limited, high-burden settings where retention resources are scarce and must be "
         "targeted. Because the hazard shape encodes *when* patients disengage, it maps directly "
         "onto the timing of adherence support: a front-loaded (DFR) setting argues for "
         "concentrating counselling, financial or social support in the intensive phase, whereas a "
         "late-accelerating (IFR) setting argues for sustained or intensified support in the "
         "continuation phase. A retention package optimized for one hazard shape will be mistimed "
         "in the other, which offers a concrete, quantitative reason why globally standardized "
         "adherence interventions have shown inconsistent effects across programmes{3}. Routinely "
         "reporting the time-to-LTFU curve \u2014 not only the final cumulative proportion \u2014 "
         "would let national programmes locate their own hazard shape and time support "
         "accordingly, and would make cross-country evidence poolable in a way that a single "
         "summary statistic cannot.")

    heading(doc, "Limitations")
    para(doc,
         "Only two TB and two comparator curves met the bar of a genuinely time-resolved, "
         "openly available dropout curve, so the analysis is small and hypothesis-generating. "
         "Estimates come from digitized aggregate curves, "
         "not individual patient data; the Ethiopian estimate is a competing-risk "
         "*subdistribution*-hazard shape; the antipsychotic cohort is small (n\u224842) and "
         "illustrative; KM plateaus reflect administrative censoring. The findings are "
         "hypothesis-generating, not confirmatory.")

    heading(doc, "Conclusions")
    para(doc,
         "Across the few TB cohorts that publish a time-resolved LTFU curve, the Weibull hazard "
         "shape is not consistent: two national settings fell on opposite sides of k=1, whereas "
         "two unrelated chronic-treatment comparators were mutually consistent (both DFR). The "
         "heterogeneity of TB LTFU is therefore visible in the hazard shape itself and offers a "
         "compact, reproducible explanation for why pooled TB evidence and a single unified "
         "retention strategy are difficult to construct. Individual-level data with harmonized "
         "LTFU definitions are needed to identify what drives the divergence.")

    heading(doc, "Declarations")
    para(doc, "**Ethics approval and consent to participate** Not applicable. This study is a "
              "secondary analysis of aggregate, already-published, de-identified survival curves "
              "and involved no new human participants or individual-level data.")
    para(doc, "**Consent for publication** Not applicable.", space_before=4)
    para(doc, "**Clinical trial number** Not applicable.", space_before=4)
    para(doc, "**Availability of data and materials** All source figures, digitized CSV datasets, "
              "analysis code and a one-command build that regenerates every reported number, "
              "Table 1 and Figure 1 are openly available in the project repository. No result is "
              "hard-coded; every value is reproduced from the source data by the released code.",
         space_before=4)
    para(doc, "**Competing interests** The authors declare that they have no competing interests.",
         space_before=4)
    para(doc, "**Funding** This study received no specific funding.", space_before=4)
    para(doc, "**Authors' contributions** The author(s) conceived the study, digitized the source "
              "curves, implemented the analysis and wrote the manuscript. All authors read and "
              "approved the final manuscript.", space_before=4)
    para(doc, "**Acknowledgements** Not applicable.", space_before=4)

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


def build_title_page():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1)
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Divergent hazard shapes of tuberculosis treatment loss to follow-up: a "
                  "reproducible analysis of published curves quantifying the heterogeneity "
                  "that hinders a unified retention intervention")
    r.bold = True; r.font.size = Pt(14)
    para(doc, "Article type: Brief Report", space_before=10)
    heading(doc, "Authors")
    para(doc, "Tatsuki Onishi [AUTHOR ORDER / ADDITIONAL CO-AUTHORS TO BE CONFIRMED]")
    heading(doc, "Affiliations")
    para(doc, "1. [Institution, Department, City, Country \u2014 TO BE CONFIRMED]")
    heading(doc, "Corresponding author")
    para(doc, "Tatsuki Onishi. Email: bougtoir@gmail.com. [Postal address / ORCID "
              "\u2014 TO BE CONFIRMED]")
    heading(doc, "Declarations")
    para(doc, "Competing interests: none declared. Funding: none. Ethics approval and consent to "
              "participate: not applicable (secondary analysis of published aggregate data).")
    path = os.path.join(OUT, "title_page.docx")
    doc.save(path); print("wrote", path)


def build_cover_letter():
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1)
    para(doc, "[Date / your address block \u2014 TO BE CONFIRMED]")
    para(doc, "Prof. Xiao-Nong Zhou, Editor-in-Chief", space_before=12)
    para(doc, "Infectious Diseases of Poverty", space_before=2)
    para(doc, "Dear Professor Zhou and Editors,", space_before=12)
    para(doc,
         "Please consider our Brief Report, \u201cDivergent hazard shapes of tuberculosis "
         "treatment loss to follow-up: a reproducible analysis of published curves quantifying the "
         "heterogeneity that hinders a unified retention intervention\u201d, for publication in "
         "Infectious Diseases of Poverty.", space_before=8)
    para(doc,
         "Loss to follow-up (LTFU) during tuberculosis (TB) treatment is a central obstacle to "
         "cure and transmission control in resource-limited, high-burden settings. It is already "
         "recognized that the determinants of treatment interruption are context-dependent and "
         "that adherence interventions transfer poorly between programmes, but this has remained a "
         "qualitative observation. We give it a quantitative handle by asking whether the timing "
         "of LTFU \u2014 its hazard shape \u2014 is consistent across settings. Fitting Weibull "
         "cumulative-incidence models to real, published time-to-event curves, we find that two TB "
         "cohorts fall on opposite sides of a constant hazard (one increasing, one decreasing), "
         "whereas two unrelated chronic-treatment comparators are mutually consistent. This offers "
         "a compact, reproducible explanation for why pooled TB evidence and a single unified "
         "retention strategy are hard to build, and it argues for routinely reporting the "
         "time-to-LTFU curve so programmes can time adherence support to their own hazard shape.",
         space_before=8)
    para(doc,
         "We believe this fits the scope of Infectious Diseases of Poverty: it addresses treatment "
         "and case management of a major infectious disease of poverty, has direct implications "
         "for TB programme implementation and health systems, and is fully reproducible \u2014 all "
         "source figures, digitized data and analysis code that regenerate every reported number "
         "are openly available. The work is original, is not under consideration elsewhere, and "
         "all authors approve the submission. We declare no competing interests.", space_before=8)
    para(doc, "Thank you for your consideration.", space_before=8)
    para(doc, "Sincerely,", space_before=12)
    para(doc, "Tatsuki Onishi, on behalf of the authors", space_before=2)
    path = os.path.join(OUT, "cover_letter.docx")
    doc.save(path); print("wrote", path)


if __name__ == "__main__":
    build_docx()
    build_pptx()
    build_title_page()
    build_cover_letter()
