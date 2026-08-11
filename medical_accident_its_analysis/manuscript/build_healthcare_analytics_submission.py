#!/usr/bin/env python3
"""Build a Healthcare Analytics (Elsevier) submission package for the rate-based
analysis of litigation risk and specialty physician workforce in Japan.

Outputs (all derived from results/reanalysis_results.json and data_primary/):
  - manuscript/ha_manuscript_en.docx   anonymised main manuscript
  - manuscript/ha_title_page.docx        title page (separate, with author info)
  - manuscript/ha_cover_letter.docx      cover letter addressed to Healthcare Analytics
  - manuscript/ha_highlights.docx      3-5 highlights (<=85 chars each)
  - manuscript/ha_supplementary.docx     supplementary figures & tables
  - output/ha_Figure_1.png .. Figure_2.png            main figure files
  - output/ha_Supplementary_Figure_1.png .. 3.png      supplementary figure files
  - manuscript/ha_figures.pptx           editable main figure slides
  - manuscript/ha_supplementary_figures.pptx editable supplementary figure slides

Main manuscript is double-anonymisation compliant: no author identifiers,
affiliations or acknowledgements in the body. Figures/tables in the main
manuscript are limited to 4 (2 figures + 2 tables); remaining figures/tables
are placed in the supplementary file.
"""
import os
import json
import re
import zipfile
import pandas as pd
from lxml import etree
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PInches, Pt as PPt

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(BASE)
DP = os.path.join(PROJ, "data_primary")
OUT = os.path.join(PROJ, "output")
RES = json.load(open(os.path.join(PROJ, "results", "reanalysis_results.json")))

try:
    from latex2mathml.converter import convert as _latex_to_mathml
except ImportError:  # pragma: no cover
    _latex_to_mathml = None

_XSL_PATH = os.path.join(BASE, "MML2OMML.XSL")
if not os.path.exists(_XSL_PATH):
    _XSL_PATH = "/tmp/MML2OMML.XSL"
if os.path.exists(_XSL_PATH):
    _XSLT = etree.XSLT(etree.parse(_XSL_PATH))
else:
    _XSLT = None

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]
EN = {"内科": "Internal medicine", "外科": "Surgery", "整形外科": "Orthopaedics",
      "形成外科": "Plastic surgery", "産婦人科": "Obstetrics & gynaecology",
      "小児科": "Paediatrics", "精神科": "Psychiatry", "眼科": "Ophthalmology",
      "耳鼻咽喉科": "Otolaryngology", "泌尿器科": "Urology", "皮膚科": "Dermatology",
      "麻酔科": "Anaesthesiology"}


def load(name):
    df = pd.read_csv(os.path.join(DP, name)).set_index("specialty")
    df.columns = [int(c) for c in df.columns]
    return df.loc[CORE]


def prim(label_key):
    for r in RES["primary"]:
        if label_key in r["label"]:
            return r
    raise KeyError(label_key)


def sens(label_key):
    for r in RES["sensitivity"]:
        if label_key in r["label"]:
            return r
    raise KeyError(label_key)


PHYS = prim("physician growth ~ lagged litigation rate")
HOSP = prim("hospital growth ~ lagged litigation rate")
REV = prim("Reverse")
CNT = sens("COUNTS contrast")
ANN = sens("Annual hospital")
INT = sens("interpolated-annual")
EQP, EQH = RES["equivalence"][0], RES["equivalence"][1]
SP = RES["descriptive"]["spearman_litrate_vs_physgrowth"]
n_pos = sum(1 for v in SP.values() if v["rho"] > 0)
n_sig = sum(1 for v in SP.values() if v["p"] < 0.05)
BIEN = RES["grid"]["biennial_years"]
YEARS = f"{BIEN[0]}\u2013{BIEN[-1]}"
N_SPEC = len(CORE)
PER = 1000  # rate scale (cases per 1,000 physicians)
MARGIN1 = int(RES["equivalence"][0]["tests"][0]["margin"] * 100)
MARGIN2 = int(RES["equivalence"][1]["tests"][1]["margin"] * 100)

# JMSR/MAIS sensitivity (report counts added as a control)
JMSR = sens("JMSR")
JMSR_CORR = RES["jmsr_correlation"]
JMSR_START = JMSR_CORR["years"][0] + 1  # outcome years start one year after first JMSR lag

# Nikkei Telecom media coverage sensitivity (national annual article counts)
MEDIA = sens("Media-adjusted")
MEDIA_CORR = RES["media_correlation"]
MEDIA_START = MEDIA_CORR["years"][0] + 1   # outcome years start one year after first media lag
MEDIA_END = MEDIA_CORR["years"][-1]        # last outcome year of the media sensitivity

# Public repository and reproducibility metadata
PUBLIC_REPO = "https://github.com/bougtoir/medical-accident-its-analysis"

# Holm-adjusted p-value for the exploratory JOCS-CP indicator in the hospital model
JOCS_HOLM = next((
    t["holm_p"] for t in RES["multiple_comparison"]["tests"]
    if "hospital" in t["label"].lower() and "JOCS-CP" in t["label"]
), None)

# Load primary dataframes for year ranges/resolution (used in supplementary table and limitations)
PHYS_DF = load("physicians_by_specialty.csv")
HOSP_DF = load("facilities_hospital_by_specialty.csv")
CLINIC_DF = load("facilities_clinic_by_specialty.csv")
LIT_DF = load("litigation_by_specialty.csv")


def _resolution(df):
    diffs = [df.columns[i + 1] - df.columns[i] for i in range(len(df.columns) - 1)]
    return max(set(diffs), key=diffs.count)


def _year_label(years):
    return f"{years[0]}\u2013{years[-1]}"


PHYS_RES = _resolution(PHYS_DF)
HOSP_RES = _resolution(HOSP_DF)
CLINIC_RES = _resolution(CLINIC_DF)

# Descriptive counts used in abstract and results (computed once, not hard-coded)
DESCR = RES["descriptive"]["biennial_first_last"]["by_specialty"]
GREW = sum(1 for v in DESCR.values() if v["phys_last"] > v["phys_first"])
FELL = sum(1 for v in DESCR.values() if v["litrate_last"] < v["litrate_first"])
SURG = DESCR[EN["外科"]]
SURG_PCT = 100 * (SURG["phys_last"] / SURG["phys_first"] - 1)
SPAN = BIEN[-1] - BIEN[0]
SURG_DESC = f"general surgery, which changed by {SURG_PCT:+.1f}%"

# Useful helpers
_per = f"{PER:,}"
def _fmt_pct(x):
    return f"{x:+.2f}"


REFS = {
    "maldist": "Yamaguchi S, et al. Regional and specialty maldistribution of physicians in Japan. J Epidemiol. 2020;30(1):1-8.",
    "malprac": "Studdert DM, Mello MM, Brennan TA. Medical malpractice. N Engl J Med. 2004;350(3):283-292.",
    "defmed": "Hiyama T, et al. Defensive medicine and malpractice concern in Japan. J Clin Gastroenterol. 2006;40(9):779-780.",
    "lakens": "Lakens D. Equivalence tests: a practical primer for t tests, correlations, and meta-analyses. Soc Psychol Personal Sci. 2017;8(4):355-362.",
    "schuir": "Schuirmann DJ. A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680.",
    "jocscp": "Japan Council for Quality Health Care. Japan Obstetric Compensation System for Cerebral Palsy. Tokyo: Japan Council for Quality Health Care; 2009.",
    "phys": "Ministry of Health, Labour and Welfare. Statistics of Physicians, Dentists and Pharmacists. Tokyo: MHLW; 2024. Available from: https://www.mhlw.go.jp/english/database/db-hw/",
    "court": "Supreme Court of Japan, Committee on Medical Litigation. Statistics on medical malpractice litigation (closed cases by specialty). Tokyo: Supreme Court of Japan; 2024.",
    "facil": "Ministry of Health, Labour and Welfare. Survey of Medical Institutions (Dynamic). Tokyo: MHLW; 2024. Available from: https://www.mhlw.go.jp/english/database/db-hw/",
    "mais": "Act on the Promotion of Medical Safety; Medical Accident Investigation System (2015). Tokyo: MHLW; 2015.",
    "jmsr_data": "Japan Medical Safety Research Organisation. Annual reports of medical accident investigations (2015-2024). Tokyo: JMSR; 2025.",
    "nikkei": "Nikkei Inc. Nikkei Telecom 21. Tokyo: Nikkei Inc. Accessed 2024. Available from: https://telecom21.nikkei.co.jp/.",
    "angrist": "Angrist JD, Pischke JS. Mostly Harmless Econometrics. Princeton: Princeton University Press; 2009.",
    "cameron2015": "Cameron AC, Miller DL. A practitioner's guide to cluster-robust inference. J Hum Resour. 2015;50(2):317-372.",
    "strobe": "von Elm E, Altman DG, Egger M, et al. The STROBE statement. Lancet. 2007;370(9596):1453-1457.",
    "matsa2007": "Matsa DA. Does malpractice liability keep the doctor away? Evidence from tort reform damage caps. J Legal Stud. 2007;36(S2):S143-S182.",
    "hyman2015": "Hyman DA, Silver C, Black B, Paik M. Does tort reform affect physician supply? Evidence from Texas. Int Rev Law Econ. 2015;42:203-218.",
    "frakes2020": "Frakes MD, Frank MB, Seabury SA. The effect of malpractice law on physician supply: Evidence from negligence-standard reforms. J Health Econ. 2020;70:1-16.",
    "kessler1996": "Kessler DP, McClellan MB. Do doctors practice defensive medicine?. Q J Econ. 1996;111(2):353-390.",
    "sloan2008": "Sloan FA, Shadle JH. Is there empirical evidence for \"Defensive Medicine\"? A reassessment. J Health Econ. 2008;27(2):481-491.",
    "taniguchi2023": "Taniguchi K, Watari T, Nagoshi K. Characteristics and trends of medical malpractice claims in Japan between 2006 and 2021. PLoS One. 2023;18(12):e0296155.",
    "hasegawa2016": "Hasegawa J, Toyokawa S, Ikenoue T, et al. Relevant obstetric factors for cerebral palsy: from the Nationwide Obstetric Compensation System in Japan. PLoS One. 2016;11(1):e0148122.",
    "morita2018": "Morita H. Criminal prosecution and physician supply. Int Rev Law Econ. 2018;55:1-11.",
    "helland2015": "Helland E, Seabury SA. Tort reform and physician labor supply: a review of the evidence. Int Rev Law Econ. 2015;42:192-202.",
    "bismark2006": "Bismark M, Paterson R. No-fault compensation in New Zealand: harmonizing injury compensation, provider accountability, and patient safety. Health Aff. 2006;25(1):278-286.",
    "mello2011": "Mello MM, Kachalia A, Studdert DM. Administrative compensation for medical injuries: lessons from three foreign systems. New York: The Commonwealth Fund; 2011.",
    "kamijo2025": "Kamijo K, Wada Y, Ishida K, Warsof SL, Saade G, Kawakita T. Medical-legal claims in obstetrics and gynecology: Japan versus the United States. J Healthc Risk Manag. 2025;44(4):5-11. doi:10.1002/jhrm.70001.",
    "lin2022": "Lin PL, Huang JP, Fujii T, Cho EH, Huang MC. A survey of specialty choice among obstetrics and gynecology residents in Japan, Korea, and Taiwan. J Obstet Gynaecol Res. 2022;48(7):1968-1977.",
}
_CITE_ORDER = []
BODY_TEXTS = []


def wc(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


def add_math(doc, latex, inline=False, para=None):
    """Insert an OMML equation from LaTeX source.

    Falls back to italicised plain text if latex2mathml or the XSLT is not
    available, so the manuscript remains usable in any environment.
    """
    if _latex_to_mathml is None or _XSLT is None:
        if para is None:
            para = doc.add_paragraph()
        run = para.add_run(latex)
        run.italic = True
        run.font.name = "Cambria Math" if inline else "Times New Roman"
        return para

    mathml = _latex_to_mathml(latex)
    mathml_tree = etree.fromstring(mathml)
    omml_tree = _XSLT(mathml_tree)
    omml_root = omml_tree.getroot()

    if para is None:
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para._element.append(omml_root)
    return para


def fmt(x, d=3):
    return f"{x:+.{d}f}" if isinstance(x, float) else str(x)


def p_tost_fmt(p, digits=3):
    """Format a TOST p-value; report '<0.001' when rounded to zero."""
    if p is None:
        return ""
    fmt_str = f"{{p:.{digits}f}}"
    s = fmt_str.format(p=p)
    return "<0.001" if s == "0." + "0" * digits else s


def cite_number(keys):
    nums = []
    for k in keys:
        if k not in _CITE_ORDER:
            _CITE_ORDER.append(k)
        nums.append(_CITE_ORDER.index(k) + 1)
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ",".join(out)


def _setup_doc():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.paragraph_format.line_spacing = 2.0
    st.paragraph_format.space_after = Pt(6)
    return doc


def _add_runs(par, text, size=Pt(12), bold=False, italic=False):
    for part in re.split(r"(\{[^}]+\})", text):
        if part.startswith("{") and part.endswith("}"):
            keys = [k.strip() for k in part[1:-1].split(",")]
            r = par.add_run(f"[{cite_number(keys)}]")
            r.font.superscript = True
        elif part:
            r = par.add_run(part)
            r.font.size = size
            r.bold = bold
            r.italic = italic
        if part:
            par.runs[-1].font.name = "Times New Roman"


def head(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0, 0, 0)
        r.font.name = "Times New Roman"
    return h


def body(doc, text, **kw):
    p = doc.add_paragraph()
    _add_runs(p, text, **kw)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)
    BODY_TEXTS.append(p.text)
    return p


def para(doc, text, **kw):
    p = doc.add_paragraph()
    _add_runs(p, text, **kw)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)
    return p


def field(doc, label, text):
    p = doc.add_paragraph()
    r = p.add_run(label + " ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    _add_runs(p, text)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)
    return p


def figure(doc, fn, caption, width=Inches(5.8)):
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(14)
    cap.paragraph_format.space_after = Pt(6)
    rc = cap.add_run(caption)
    rc.bold = True
    rc.font.size = Pt(10)
    rc.font.name = "Times New Roman"
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, fn)
    if os.path.exists(img):
        p.add_run().add_picture(img, width=width)
    doc.add_paragraph()


def table(doc, headers, rows, caption):
    cap = doc.add_paragraph()
    cap.paragraph_format.space_before = Pt(14)
    cap.paragraph_format.space_after = Pt(6)
    rc = cap.add_run(caption)
    rc.bold = True
    rc.font.size = Pt(10)
    rc.font.name = "Times New Roman"
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        p = cell.paragraphs[0]
        r = p.add_run(str(h))
        r.bold = True
        r.font.size = Pt(9)
        r.font.name = "Times New Roman"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            p = cells[i].paragraphs[0]
            pr = p.add_run(str(v))
            pr.font.size = Pt(9)
            pr.font.name = "Times New Roman"
            if i > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()


def build_manuscript():
    doc = _setup_doc()

    # Title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(18)
    rt = t.add_run(
        "Litigation risk and specialty-level physician workforce allocation in Japan, "
        f"{YEARS}: a sensitivity-analysis framework with equivalence testing"
    )
    rt.bold = True
    rt.font.size = Pt(14)
    rt.font.name = "Times New Roman"

    # Abstract (unstructured, <=250 words)
    abstract_text = (
        "Specialty maldistribution is a healthcare workforce allocation problem "
        "in Japan, where policy discussions often assume that malpractice-litigation "
        "risk pushes physicians away from high-risk specialties. We used this "
        "question as a test case for a transparent, reproducible sensitivity-analysis "
        "framework that evaluates a proposed policy lever while avoiding size "
        "confounding and interpolation of sparse panels. Using national primary data "
        f"for {N_SPEC} specialties ({BIEN[0]}\u2013{BIEN[-1]}), we measured exposure as "
        f"closed malpractice claims per {_per} physicians (rate, not count) and regressed "
        "biennial log-change in physicians and hospitals on the lagged litigation rate "
        "in a panel with specialty and wave fixed effects, cluster-robust standard "
        "errors, small-cluster t(G-1) inference, and two one-sided equivalence "
        f"(TOST) tests. The workforce grew in {GREW} of {N_SPEC} specialties; "
        f"{SURG_DESC}, was the exception. Litigation rate was not associated with "
        f"physician growth (coefficient {fmt(PHYS['coef'],4)}; 95% CI "
        f"{fmt(PHYS['ci_low'],4)} to {fmt(PHYS['ci_high'],4)}; p={PHYS['p']:.2f}) or hospital "
        f"growth (p={HOSP['p']:.2f}). A one-SD higher rate changed physician growth "
        f"by less than \u00b1{MARGIN1}% (TOST p={p_tost_fmt(EQP['tests'][0]['p_tost'])}; "
        f"less than \u00b1{MARGIN2}% was p={p_tost_fmt(EQP['tests'][1]['p_tost'])}); hospital growth "
        f"was within \u00b1{MARGIN2}% (p={p_tost_fmt(EQH['tests'][1]['p_tost'])}) but not the stricter "
        f"\u00b1{MARGIN1}% margin (p={p_tost_fmt(EQH['tests'][0]['p_tost'])}). Sensitivity analyses "
        f"were unchanged and per-specialty rank correlations were mostly positive "
        f"({n_pos}/{N_SPEC}) and none significant. Specialty-level litigation risk is "
        "not associated with workforce decline and is statistically equivalent to a "
        "null effect for physicians. The framework is exportable to other policy "
        "levers in healthcare workforce allocation."
    )
    abstract_wc = wc(abstract_text)
    if abstract_wc > 250:
        raise SystemExit(f"Abstract is {abstract_wc} words; must be <=250")

    head(doc, "Abstract", level=1)
    p = doc.add_paragraph()
    r = p.add_run(abstract_text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)

    kw = doc.add_paragraph()
    kr = kw.add_run("Keywords: ")
    kr.bold = True
    kr.font.name = "Times New Roman"
    _add_runs(kw, "malpractice litigation; physician workforce; specialty maldistribution; "
                  "equivalence testing; health analytics; Japan")
    kw.paragraph_format.space_after = Pt(18)

    # Introduction
    head(doc, "Introduction", level=1)
    body(doc,
         "Japan faces a marked maldistribution of physicians across specialties "
         "despite continued growth in the total physician supply. High-acuity fields "
         "such as surgery, obstetrics and gynaecology, paediatrics and emergency care "
         "are widely perceived as understaffed.{maldist} A recurring policy intuition "
         "is that medical safety incidents and the threat of malpractice litigation push "
         "physicians away from high-risk specialties toward lower-risk practice."
         "{malprac,defmed} If true, reducing litigation exposure would be a lever "
         "against maldistribution.")
    body(doc,
         "Prior work in this area often related raw annual counts of incidents or "
         "lawsuits to raw counts of physicians or facilities. Two features make such "
         "designs prone to spurious association. "
         "First, counts are not adjusted for specialty size: a larger specialty "
         "mechanically accumulates more procedures, more claims and more physicians, so "
         "count-based associations can arise without any behavioural mechanism. Second, the physician census "
         "is collected only biennially; interpolating it to an annual series and "
         "analysing it as if each year were an independent observation inflates the "
         "degrees of freedom of any lag-based method. These pitfalls are not unique to "
         "malpractice research; they arise whenever administrative counts are used to "
         "infer behavioural responses in healthcare organisations. We therefore "
         "treat the litigation-workforce question as a test case for a transparent, "
         "reproducible sensitivity-analysis framework for healthcare workforce "
         "allocation decisions.")
    body(doc,
         "We therefore examined the question using rates rather than counts, using "
         "only measured biennial physician observations, and using equivalence testing\u2014"
         "which can provide positive evidence for the absence of a meaningful effect "
         "rather than merely failing to reject a null.{lakens,schuir} We also account for "
         "the Japan Obstetric Compensation System for Cerebral Palsy (JOCS-CP), a "
         "no-fault scheme launched in January 2009 that sits within the study window "
         "and applies to the specialty most often cited in this debate.{jocscp}")

    # Materials and methods
    head(doc, "Materials and methods", level=1)
    head(doc, "Data sources", level=2)
    body(doc,
         "We report this observational study following the Strengthening the Reporting of "
         "Observational Studies in Epidemiology (STROBE) guidance.{strobe} We "
         f"studied {N_SPEC} core clinical specialties for which the Supreme Court reports "
         "specialty-specific litigation. Three official primary series drove the main "
         "analysis: physician counts by specialty from the biennial Statistics of "
         "Physicians, Dentists and Pharmacists{phys}; closed malpractice claims by "
         "specialty from the Supreme Court of Japan{court}; and hospital counts by "
         "specialty from the annual Survey of Medical Institutions{facil}. Two sensitivity "
         "series were also used: annual medical accident investigation reports by "
         "specialty from the Japan Medical Safety Research Organisation (JMSR, 2015-2024){jmsr_data} "
         f"and total national newspaper article counts from Nikkei Telecom 21 "
         "(2004-2018; the sensitivity analysis uses 2009-2018; keywords: \u533b\u7642\u4e8b\u6545 + \u533b\u7642\u904e\u8aa4).{nikkei} "
         f"The full extraction pipeline (with source identifiers and SHA-256 checksums) is "
         f"documented in the accompanying repository ({PUBLIC_REPO}).")
    body(doc,
         "Physician counts use the principal-specialty (\u4e3b\u305f\u308b\u8a3a\u7642\u79d1) "
         "classification; broad categories were matched to the Supreme Court's "
         "specialty labels, and subspecialties were aggregated in code. Because the "
         "Court assigns multi-specialty cases to a single principal specialty and states "
         "that the counts do not represent the intrinsic risk of each specialty, we "
         "treat litigation as an exposure signal rather than a measure of incident "
         "risk.{court} We distinguish litigation from the Medical Accident Investigation "
         "System, which began in 2015 and covers only deaths and stillbirths judged "
         "unforeseen by the hospital administrator; it is not a general incident-reporting "
         "system and is not used as an exposure here.{mais} Primary data sources and their "
         "resolution are summarised in Supplementary Table 1.")

    head(doc, "Statistical analysis", level=2)
    body(doc,
         "We formalised the evaluation as a sensitivity-analysis framework that varies the "
         "exposure definition (counts versus rates), panel frequency (measured biennial "
         "waves versus interpolated annual values), and potential confounders (JMSR reports, "
         "media coverage, JOCS-CP period) while holding the specialty-level panel "
         "structure constant. "
         f"The exposure was the litigation rate, defined as closed claims per {_per} "
         "physicians in each specialty-year, which removes specialty-size confounding "
         "because large specialties generate more claims for reasons unrelated to "
         f"per-physician risk. The primary analysis used the {len(BIEN)} measured biennial "
         f"physician waves ({BIEN[0]}\u2013{BIEN[-1]}). For each specialty we computed the "
         "biennial log-change in physicians (and, separately, in hospitals) and regressed "
         "it on the litigation rate at the start of the interval, in a panel with specialty "
         "and wave fixed effects and standard errors clustered by specialty.{angrist} "
         f"Clusters are defined by specialty, so G={N_SPEC} and the small-cluster correction "
         "uses a t-distribution with G-1 degrees of freedom for all cluster-robust inference. "
         "Supplementary Figure 1 summarises the sensitivity-analysis framework. The primary "
         "estimating equation, for specialty s and wave t, was as follows.")
    add_math(doc, r"\Delta \log(Y_{st}) = \alpha_s + \delta_t + \beta \cdot \text{litrate}_{s,t-1} + \epsilon_{st}")
    body(doc,
         "Here, Y is either physicians or hospitals, alpha_s are specialty fixed effects, "
         "delta_t are wave fixed effects, and standard errors are clustered by specialty. "
         "For the equivalence analysis we standardised litrate to a z-score, so beta "
         "gives the expected biennial log-change per one-SD increase in the litigation rate.")
    body(doc,
         "We assessed equivalence to a null effect using two one-sided tests (TOST).{lakens,schuir} "
         "For a pre-specified margin m, the two one-sided null hypotheses are")
    add_math(doc, r"H_0: \beta \leq -m \quad \text{and} \quad H_0: \beta \geq +m")
    body(doc,
         "Equivalence is declared when both one-sided tests yield p < alpha. We used "
         f"margins of {MARGIN1}% and {MARGIN2}% biennial workforce change because they are "
         "smaller than typical policy targets for specialty workforce rebalancing and "
         "represent changes that workforce planners would consider substantively small.")
    body(doc,
         "All reported confidence intervals and two-sided p-values use a "
         f"t-distribution with G-1 = {PHYS['df']} degrees of freedom, the small-cluster correction recommended "
         "by Cameron and Miller.{cameron2015} An indicator for obstetrics and gynaecology from 2009 onward captured the "
         "JOCS-CP period.{jocscp} Sensitivity analyses repeated the models on (i) the "
         "annual hospital series, (ii) a linearly interpolated annual physician series "
         "(with degrees of freedom governed by the measured waves, not the interpolated n), "
         "(iii) raw counts instead of rates, (iv) the annual hospital series 2016-2024 "
         f"additionally controlling for the JMSR report rate (reports per {_per} physicians), "
         f"and (v) the annual hospital series {MEDIA_START}\u2013{MEDIA_END} additionally "
         f"controlling for total Nikkei Telecom article counts. Because the article-count series "
         "is a national yearly variable, it is collinear with full wave fixed effects; this "
         "sensitivity therefore uses specialty fixed effects plus a linear time trend rather "
         "than wave dummies. The JOCS-CP indicator and all sensitivity models are exploratory; "
         "we report raw p-values and Holm step-down adjusted p-values for this family. "
         "Analyses used Python (statsmodels); code and data are openly available at "
         f"{PUBLIC_REPO}.")

    # Results
    head(doc, "Results", level=1)
    head(doc, "Workforce and litigation trends", level=2)
    body(doc,
         f"Litigation rates per {_per} physicians varied several-fold across "
         f"specialties and fell over time in {FELL} of {len(CORE)} fields (Supplementary Figure 2). "
         f"Over the same period the physician workforce grew in {GREW} of {len(CORE)} specialties "
         "(Supplementary Figure 3; Table 1); the only exception was general surgery, "
         f"which was essentially flat ({SURG_PCT:+.1f}% across {SPAN} years). Exposure and "
         "workforce therefore did not move in opposite directions as a flight-from-risk "
         "account would predict.")
    rows = []
    for s in CORE:
        v = DESCR[EN[s]]
        rows.append([EN[s], v["phys_first"], v["phys_last"],
                     f"{v['litrate_first']:.2f}", f"{v['litrate_last']:.2f}",
                     v["hosp_first"], v["hosp_last"]])
    table(doc,
          ["Specialty", f"Physicians {BIEN[0]}", f"Physicians {BIEN[-1]}",
           f"Lit. rate {BIEN[0]}", f"Lit. rate {BIEN[-1]}",
           f"Hospitals {BIEN[0]}", f"Hospitals {BIEN[-1]}"],
          rows,
          f"Table 1. Physicians, litigation rate (per {_per} physicians) and hospitals by "
          "specialty, first and last waves.")

    head(doc, "Primary association and equivalence", level=2)
    body(doc,
         f"The lagged litigation rate was not associated with biennial physician growth "
         f"(coefficient {fmt(PHYS['coef'],4)}; 95% CI {fmt(PHYS['ci_low'],4)} to "
         f"{fmt(PHYS['ci_high'],4)}; p={PHYS['p']:.2f}; n={PHYS['n_obs']}) or with hospital "
         f"growth (coefficient {fmt(HOSP['coef'],4)}; p={HOSP['p']:.2f}). Equivalence "
         f"testing (Figure 1; Table 2) showed that a 1-SD higher litigation rate "
         f"changed biennial physician growth by less than \u00b1{MARGIN1}% (TOST p={p_tost_fmt(EQP['tests'][0]['p_tost'])}; "
         f"point estimate {fmt(EQP['coef_per_SD']*100,2)}% with 90% CI "
         f"{fmt(EQP['ci90_low']*100,2)}% to {fmt(EQP['ci90_high']*100,2)}%). For hospital "
         f"growth the point estimate was {fmt(EQH['coef_per_SD']*100,2)}% (90% CI "
         f"{fmt(EQH['ci90_low']*100,2)}% to {fmt(EQH['ci90_high']*100,2)}%): it was within "
         f"the \u00b1{MARGIN2}% margin (p={p_tost_fmt(EQH['tests'][1]['p_tost'])}) but not the stricter "
         f"\u00b1{MARGIN1}% margin (p={p_tost_fmt(EQH['tests'][0]['p_tost'])}). Thus the data are "
         "consistent with the absence of a policy-relevant effect on physician growth, "
         "and with at most a small effect on hospital growth. Detailed TOST results by "
         "margin are reported in Supplementary Table 2.")
    figure(doc, "ha_Figure_1.png",
           f"Figure 1. Equivalence (TOST) of the litigation-rate effect against \u00b1{MARGIN1}% and "
           f"\u00b1{MARGIN2}% margins; horizontal bars are 90% confidence intervals.")
    trow = [
        ["Physician growth ~ lagged rate", f"{fmt(PHYS['coef'],4)}",
         f"{fmt(PHYS['ci_low'],4)}, {fmt(PHYS['ci_high'],4)}", f"{PHYS['p']:.2f}", PHYS['n_obs']],
        ["Hospital growth ~ lagged rate", f"{fmt(HOSP['coef'],4)}",
         f"{fmt(HOSP['ci_low'],4)}, {fmt(HOSP['ci_high'],4)}", f"{HOSP['p']:.2f}", HOSP['n_obs']],
        ["Counts contrast (physician)", f"{fmt(CNT['coef'],4)}", "\u2014", f"{CNT['p']:.2f}", CNT['n_obs']],
        ["Annual hospital (sensitivity)", f"{fmt(ANN['coef'],4)}", "\u2014", f"{ANN['p']:.2f}", ANN['n_obs']],
        ["Interpolated physician (sensitivity)", f"{fmt(INT['coef'],4)}", "\u2014", f"{INT['p']:.2f}", INT['n_obs']],
        ["Reverse (workforce\u2192litigation)", f"{fmt(REV['coef'],3)}", "\u2014", f"{REV['p']:.2f}", REV['n_obs']],
    ]
    table(doc,
          ["Model", "Coefficient", "95% CI", "p", "n"],
          trow,
          "Table 2. Panel fixed-effects models and sensitivity analyses.")

    head(doc, "Counts versus rates, and confounders", level=2)
    body(doc,
         f"Using raw litigation counts rather than rates did not reveal a negative "
         f"association in this measured-only design (p={CNT['p']:.2f}). Figure 2 "
         "shows the contrast: the count exposure is confounded by specialty size (panel a), "
         "whereas the rate-adjusted exposure is not (panel b); points are coloured and shaped "
         "by specialty so readers can identify which fields drive any apparent pattern. "
         f"The annual hospital and interpolated annual-physician sensitivity analyses were also null "
         f"(p={ANN['p']:.2f} and p={INT['p']:.2f}), confirming that the null result is robust to panel "
         "frequency and exposure definition. The JOCS-CP indicator was positive in sign in the "
         f"obstetric-hospital model (coefficient {fmt(HOSP['jocscp_coef'],3)}, raw p={HOSP['jocscp_p']:.3f}), "
         f"but it did not remain significant after the small-cluster correction and Holm "
         f"adjustment for the exploratory sensitivity family (Holm p={JOCS_HOLM:.3f}); we "
         "therefore treat it as exploratory and do not interpret it as a causal policy "
         "effect.")
    figure(doc, "ha_Figure_2.png",
           "Figure 2. Biennial physician growth against lagged litigation exposure measured as "
           "(a) counts and (b) rates. Points are coloured by specialty; the count panel shows "
           "the size confounding that the rate panel removes.")
    body(doc,
         f"Descriptively, per-specialty rank correlations between the lagged litigation "
         f"rate and physician growth were positive in {n_pos} of {N_SPEC} specialties and "
         f"statistically significant in {n_sig}; the direction is therefore, if anything, "
         "opposite to a flight-from-risk hypothesis.")
    body(doc,
         f"A reverse specification (change in litigation rate regressed on lagged "
         f"log physicians) was also null (coefficient {fmt(REV['coef'],3)}, p={REV['p']:.2f}; "
         "Table 2), making a reverse-causation interpretation of the null unlikely.")
    body(doc,
         f"We also evaluated JMSR medical-accident investigation report counts as a "
         f"potential confounder or competing exposure.{{mais}} From {JMSR_CORR['years'][0]} to "
         f"{JMSR_CORR['years'][-1]}, raw litigation and JMSR report counts were strongly "
         f"correlated across specialties (Pearson r={JMSR_CORR['pooled_r']:.2f}), because large "
         "specialties generate more of both. After removing specialty-specific levels and "
         f"trends, however, the within-specialty correlation was negligible (r={JMSR_CORR['detrended_r']:.2f}). "
         f"A model of annual hospital growth for {JMSR_START}-2024 that included both the "
         "lagged litigation rate and the lagged JMSR report rate left the litigation "
         f"coefficient essentially unchanged ({fmt(JMSR['lit_coef'],4)}; p={JMSR['lit_p']:.2f}) "
         f"and the JMSR term was not associated with hospital growth (p={JMSR['med_p']:.2f}; "
         "Supplementary Table 3). The null litigation result is therefore neither explained nor "
         "masked by broader medical-accident reporting.")
    body(doc,
         f"Finally, we tested national newspaper coverage from Nikkei Telecom 21 as a "
         f"potential confounder.{{nikkei}} Total annual article counts (keywords: "
         f"\u533b\u7642\u4e8b\u6545 + \u533b\u7642\u904e\u8aa4) and total litigation counts were correlated "
         f"(Pearson r={MEDIA_CORR['total_r']:.2f}), consistent with greater public attention in "
         f"high-litigation years. Within the annual hospital panel, however, the lagged "
         "litigation rate and the media-count series were only weakly correlated. "
         f"A model of annual hospital growth for {MEDIA_START}-{MEDIA_END} that included both the "
         f"lagged litigation rate and the lagged article count (per 1,000 articles) left the "
         "litigation coefficient essentially unchanged and the media term was not associated "
         f"with hospital growth (p={MEDIA['media_p']:.2f}; Supplementary Table 4). Media coverage "
         "therefore does not explain the null litigation effect either. "
         "Holm step-down adjusted p-values for the exploratory sensitivity family are "
         "reported in Supplementary Table 5.")

    # Discussion
    head(doc, "Discussion", level=1)
    body(doc,
         "Using national primary data, rates rather than counts, and only measured "
         "physician observations, we found no association between specialty-level "
         "malpractice-litigation risk and subsequent physician or hospital decline. "
         f"Equivalence testing showed that any effect of litigation risk on biennial physician "
         f"growth is smaller than {MARGIN1}% (90% CI within the {MARGIN1}% margin), and any "
         f"effect on hospital growth is smaller than {MARGIN2}% (but not confidently smaller than "
         f"{MARGIN1}%). These data therefore do not support the hypothesis that physicians "
         f"systematically abandon high-litigation specialties over {SPAN} years of official statistics.")
    body(doc,
         "A null result is not merely a failure to detect an effect. The narrow "
         "confidence intervals and pre-specified equivalence margins allow us to say "
         "that, if litigation risk does influence specialty-level workforce growth, "
         "the magnitude is too small to matter for workforce planning. Across the "
         "sensitivity analyses, alternative exposure definitions, interpolation, "
         "and potential confounders did not change this conclusion, which is the main value "
         "of the framework for healthcare workforce allocation decisions.")
    body(doc,
         "The raw-count sensitivity did not reveal a negative association in these data, "
         "illustrating that the apparent count-litigation relationship does not translate into "
         "a behavioural effect once specialty size is accounted for (Figure 2). This is a "
         "cautionary example for workforce research that pairs administrative count series, "
         "and shows why rate-based, measured-only designs are preferable when testing "
         "litigation-workforce hypotheses.")
    body(doc,
         "International evidence on tort reform and physician supply is consistent "
         "with a small or context-specific effect. Matsa found that U.S. state damage "
         "caps increased the supply of frontier rural specialists by 10-12 percent, "
         "but did not affect physician supply for the average resident.{matsa2007} "
         "Hyman and colleagues, examining the 2003 Texas reforms, found no measurable "
         "increase in physician supply for high-malpractice-risk specialties, primary "
         "care, or rural physicians.{hyman2015} Frakes and colleagues showed that "
         "negligence-standard reforms could shift the composition of the physician "
         "workforce toward surgery in some regions, yet the effect was localized and "
         "modest.{frakes2020} Against this backdrop, a null effect of civil litigation "
         "risk on Japanese specialty supply is not surprising, especially in a system "
         "with comparatively low litigation volume and predictable damages.")
    body(doc,
         "Even when litigation risk is unrelated to the number of physicians, it may "
         "shape clinical behaviour through defensive medicine. Kessler and McClellan "
         "showed that U.S. malpractice reforms reduced medical expenditures for elderly "
         "heart-disease patients without increasing mortality or complications, "
         "suggesting that defensive practice is one margin of adjustment to liability "
         "pressure.{kessler1996} Subsequent reassessments have debated the magnitude "
         "and robustness of this effect, but the conceptual point remains: physicians "
         "can respond to liability risk by changing how they practise rather than by "
         "exiting a specialty.{sloan2008} In Japan, fee-for-service reimbursement "
         "rewards the high-acuity procedural work that also carries litigation "
         "exposure, so the financial return to remaining in surgery, obstetrics, or "
         "interventional specialties may dominate any deterrent from civil claims.")
    body(doc,
         "Japan's litigation environment itself dampens the likelihood of a "
         "flight-from-risk response. Taniguchi and colleagues analysed all closed "
         "malpractice claims reported by the Supreme Court from 2006 to 2021 and "
         "found that more than half ended in settlement, plaintiffs won only about a "
         "quarter of judgments, and the number of claims has been declining, "
         "especially in obstetrics and gynaecology.{taniguchi2023} The Court data we "
         "use therefore describe a civil system that is low-volume, settlement-prone, "
         "and comparatively favourable to physicians. This context makes it unlikely "
         "that routine civil litigation risk alone would drive physicians out of "
         "high-risk fields.")
    body(doc,
         "The Japan Obstetric Compensation System for Cerebral Palsy (2009) illustrates "
         "a different mechanism. It was introduced partly because of a shortage of "
         "young obstetricians and regional gaps in maternity care, and it combined "
         "no-fault compensation with investigation and prevention.{hasegawa2016} The "
         f"hospital-level JOCS-CP indicator was directionally positive (coefficient "
         f"{fmt(HOSP['jocscp_coef'],3)}, raw p={HOSP['jocscp_p']:.3f}), but it did not remain "
         f"significant after the small-cluster correction and Holm adjustment for the "
         f"exploratory sensitivity family (Holm p={JOCS_HOLM:.3f}). This suggests that, "
         "if the JOCS-CP did support obstetric hospital supply, the effect would be too small "
         "or too confounded by concurrent obstetric policies to be isolated here. "
         "Civil litigation exposure is also distinct from criminal prosecution. Morita "
         "studied the 2004 Fukushima obstetrician prosecution and found a 13 percent "
         "decline in obstetricians, with some switching to gynaecology.{morita2018} "
         "Criminal cases and their media coverage may be far more salient to career "
         "decisions than routine closed civil claims, and our data do not capture that "
         "channel.")
    body(doc,
         "The obstetrics and gynaecology case is the most discussed example of the "
         "litigation-workforce nexus, and it is consistent with our interpretation. "
         "A recent comparison of Japanese and U.S. medical-legal claims in obstetrics and "
         "gynaecology (OB/GYN) found that the proportion of malpractice claims in this specialty fell from "
         "15.1 percent in 2004 to 5.2 percent in 2022, and that claims per 100 OB/GYN "
         "physicians fell from 0.9 in 2007 to 0.4 in 2016, while maternal and neonatal "
         "mortality also declined.{kamijo2025} The authors attribute this to heightened "
         "awareness after a wrongful criminal charge, the JOCS-CP no-fault scheme, "
         "standardised clinical guidelines, and the adverse-event investigation system. "
         "This is not evidence that lowering litigation risk caused the workforce to "
         "grow; it is evidence that obstetric litigation, workforce support, and safety "
         "interventions moved together. Surveys of OB/GYN residents in Japan, Korea, "
         "and Taiwan likewise show that litigation is reported as a negative factor, "
         "but that its perceived importance is smaller where no-fault compensation exists "
         "and that workload, lifestyle, and professional interest remain dominant.{lin2022} "
         "These findings echo our specialty-level result: litigation may matter for "
         "perceptions, but it is not the binding constraint on supply.")
    body(doc,
         "What do these findings imply for policy? Reducing civil malpractice "
         "litigation is unlikely to be a powerful lever for correcting specialty "
         "maldistribution in Japan. Structural incentives are more promising: "
         "no-fault compensation can de-risk high-acuity specialties, and payment "
         "design can reward service in underserved settings and activities. The "
         "JOCS-CP experience supports the former; Japan's fee-for-service schedule "
         "and rural/urban payment adjustments illustrate the latter. Malpractice reform "
         "may still matter for defensive medicine, patient compensation, and provider-patient "
         "trust. But our evidence does not support the claim, at least from these data, that lowering "
         "litigation risk will retain physicians in high-risk specialties. "
         "Policymakers should therefore target structural incentives before "
         "relying on litigation-avoidance messaging.")
    body(doc,
         "International experience with no-fault compensation is consistent with this "
         "policy orientation. New Zealand replaced tort-based medical-injury "
         "compensation with a government-funded no-fault scheme in 1974 and, after "
         "2005 reforms, extended coverage to all treatment injuries; this separated "
         "compensation from negligence findings and largely barred malpractice "
         "litigation.{bismark2006} Sweden and Denmark operate similar administrative "
         "systems in which neutral experts evaluate claims without requiring proof of "
         "provider fault, improving injured patients' access to redress while "
         "controlling liability costs and generating patient-safety learning.{mello2011} "
         "The JOCS-CP is narrower in scope\u2014it covers only obstetric cerebral palsy\u2014"
         "but it moves in the same direction: it provides compensation and cause "
         "analysis without a protracted adversarial process. Extending such an "
         "approach more broadly would be a structural alternative to repeated calls to "
         "reduce malpractice litigation as a workforce strategy.")
    body(doc,
         "Several questions remain for future research. We cannot observe individual "
         "physicians' risk perceptions, career intentions, or responses to media "
         "coverage of high-profile cases. The closed-claim rate is an objective "
         "exposure measure, but it may not capture the perceived risk that drives "
         "specialty choice, especially when criminal prosecutions or sensational media "
         "coverage shape beliefs. Helland and Seabury's review concludes that tort "
         "reform effects on physician supply are heterogeneous across states and "
         "specialties, and that more granular, state-specific designs are needed to "
         "settle the question in the U.S. context.{helland2015} Applying similar "
         "logic in Japan would require individual-level or prefecture-level career "
         "data linked to local litigation, media, and reimbursement environments. "
         "Until then, the present specialty-level rate analysis provides the most "
         "systematic evidence available on the central policy question: whether "
         "malpractice litigation risk drives physicians away from high-risk "
         f"specialties. The answer, in these data, is no—or at least not in a way that is "
         f"detectable or policy-relevant across {len(BIEN)} measured waves ({BIEN[0]}–{BIEN[-1]}).")

    body(doc,
         "The framework we used is intentionally general. Specialty physician workforce "
         "allocation is a recurring healthcare decision problem, and the same "
         "sensitivity-analysis steps—rate adjustment to remove size confounding, measured-"
         "only panels to avoid interpolation, equivalence testing with policy-relevant "
         "margins, and small-cluster inference—can be applied to other proposed levers, "
         "such as fee schedules, regional quotas, or training subsidies. The analytic "
         "contribution is therefore not the malpractice finding itself but a transparent, "
         "reproducible workflow that helps decision-makers distinguish meaningful "
         "workforce effects from spurious count- or interpolation-based associations.")

    head(doc, "Limitations", level=2)
    body(doc,
         f"This is an ecological, specialty-level analysis and cannot speak to "
         f"individual career decisions. The physician census is biennial, giving {len(BIEN)} "
         "measured waves; we addressed the limited power directly through equivalence "
         "testing and by pooling across specialties, but residual power constraints "
         "remain and the equivalence margins are a judgement. Because clusters are "
         f"defined by the {N_SPEC} specialties, the small-cluster correction uses G-1={PHYS['df']} "
         "degrees of freedom; this is the minimum at which cluster-robust t inference is "
         "recommended and is inherent to the data. Specialty-specific "
         f"litigation counts could be recovered only from {BIEN[0]}; pre-{BIEN[0]} specialty tables were "
         "not retrievable from primary sources. Clinic counts by specialty are "
         f"published only every {CLINIC_RES} years and were used descriptively. JMSR "
         f"report counts are available only from {JMSR_CORR['years'][0]} and were used in a "
         f"{JMSR_START}-2024 sensitivity. Media article counts are available only for "
         f"{MEDIA_START}-{MEDIA_END} and are a national total, so they cannot be decomposed by "
         "specialty and are collinear with full wave fixed effects. Litigation counts are assigned to a principal specialty "
         "and, by the Court's own note, do not measure intrinsic specialty risk.{court} "
         "Finally, these findings are "
         "embedded in Japan's particular legal, cultural and institutional "
         "context\u2014including its no-fault obstetric compensation scheme, its "
         "fee-for-service reimbursement structure and its comparatively low-volume "
         "malpractice-litigation culture\u2014so physician responses to litigation risk "
         "may differ in health systems with different liability regimes, compensation "
         "mechanisms or professional norms; the results should not be assumed to "
         "generalise across cultural spheres.")

    head(doc, "Conclusions", level=1)
    body(doc,
         f"Across {YEARS}, specialty-level malpractice-litigation risk in Japan was "
         "not associated with physician or hospital decline in these data, and the "
         "physician effect was statistically equivalent to null within a small margin. "
         "Policies to counter specialty maldistribution may more productively target "
         "structural incentives, especially no-fault compensation, rather than on the "
         "assumption that reducing litigation will retain physicians in high-risk "
         "specialties.")

    # Declaration of generative AI use (Elsevier requirement; place between Conclusions and References)
    head(doc, "Declaration of generative AI use", level=1)
    body(doc,
         "[Authors: insert the Elsevier AI declaration here before submission. "
         "Example wording: During the preparation of this work the author(s) used "
         "[TOOL NAME] in order to [PURPOSE]. After using this tool/service, the "
         "author(s) reviewed and edited the content as needed and take(s) full "
         "responsibility for the content of the publication. If no generative AI was "
         "used, state so.]")

    # Declarations
    head(doc, "Declarations", level=1)
    para(doc,
         "Funding: none. Competing interests: none declared. "
         "Ethics approval: this study used publicly available aggregated national "
         "statistics and did not involve human subjects, identifiable data or patient "
         "records; no ethics approval was required. "
         f"Data and code availability: all primary data files, extraction scripts and "
         "analysis code are openly available in the project repository ("
         f"{PUBLIC_REPO}), enabling full reproduction of every reported number.")

    # References
    head(doc, "References", level=1)
    missing = [k for k in REFS if k not in _CITE_ORDER]
    if missing:
        raise SystemExit(f"orphan references (in list, never cited): {missing}")
    for i, k in enumerate(_CITE_ORDER, 1):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(f"{i}. {REFS[k]}")
        r.font.size = Pt(10)
        r.font.name = "Times New Roman"

    out = os.path.join(BASE, "ha_manuscript_en.docx")
    doc.save(out)
    main_wc = sum(wc(t) for t in BODY_TEXTS)
    print(f"wrote {out}; abstract {abstract_wc} words; main body ~{main_wc} words")
    return main_wc, abstract_wc


def build_title_page(main_word_count):
    doc = _setup_doc()
    for _ in range(4):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(18)
    rt = t.add_run(
        "Litigation risk and specialty-level physician workforce allocation in Japan, "
        f"{YEARS}: a sensitivity-analysis framework with equivalence testing"
    )
    rt.bold = True
    rt.font.size = Pt(15)
    rt.font.name = "Times New Roman"

    lines = [
        "Authors: Onishi Tatsuki",
        "Affiliation: Data Science AI Innovation Research Promotion Center, Shiga University, "
        "1-1-1 Bamba, Hikone, Shiga 522-8522, Japan",
        "Corresponding author: Onishi Tatsuki (email: [corresponding author email])",
        f"Word count (main text): approximately {main_word_count} words (excluding abstract, references, declarations, tables and figure legends)",
        "Article type: Original research article",
        "Target journal: Healthcare Analytics (Elsevier)",
        "Tables: 2  Figures: 2  Supplementary tables: 5  Supplementary figures: 2",
        "Conflicts of interest: none declared",
        "Funding: none",
        f"Data availability: all primary data and analysis code are openly available in the project repository ({PUBLIC_REPO}).",
    ]
    for line in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        r.font.size = Pt(12)
        r.font.name = "Times New Roman"

    out = os.path.join(BASE, "ha_title_page.docx")
    doc.save(out)
    print("wrote", out)


def build_highlights():
    highlights = [
        f"Litigation risk is unrelated to physician or hospital decline in {N_SPEC} specialties.",
        "Count-based links vanish once size confounding and interpolation are removed.",
        "Equivalence testing supports a null physician-growth effect within policy margins.",
        "JOCS-CP effect is exploratory and not robust to small-cluster inference.",
        "Policy should target structural incentives, not litigation-avoidance messaging.",
    ]
    for h in highlights:
        if len(h) > 85:
            raise SystemExit(f"Highlight exceeds 85 characters ({len(h)}): {h}")

    doc = _setup_doc()
    h = doc.add_paragraph()
    r = h.add_run("Highlights")
    r.bold = True
    r.font.size = Pt(13)
    r.font.name = "Times New Roman"
    for item in highlights:
        p = doc.add_paragraph(style="List Bullet")
        p.clear()
        pr = p.add_run(item)
        pr.font.name = "Times New Roman"
        pr.font.size = Pt(12)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(4)
    out = os.path.join(BASE, "ha_highlights.docx")
    doc.save(out)
    print("wrote", out)


def build_cover_letter():
    doc = _setup_doc()
    for line in ["[Date]", "", "Prof. Dr. Madjid Tavana, PhD", "Editor-in-Chief", "Healthcare Analytics", ""]:
        p = doc.add_paragraph()
        if line:
            r = p.add_run(line)
            r.font.size = Pt(12)
            r.font.name = "Times New Roman"
    p = doc.add_paragraph()
    p.add_run("Dear Editor,").font.size = Pt(12)
    p.runs[0].font.name = "Times New Roman"

    paragraphs = [
        f'We submit an original research article, "Litigation risk and specialty-level '
        f'physician workforce allocation in Japan, {YEARS}: a sensitivity-analysis '
        f'framework with equivalence testing", for consideration by Healthcare Analytics.',
        "Healthcare Analytics advances data-driven analytics for healthcare decisions. "
        "Our study treats specialty physician workforce planning as a healthcare "
        "resource-allocation problem and uses it as a test case for a transparent, "
        "reproducible sensitivity-analysis framework. The analytical contribution is "
        "diagnostic: we show how two common observational fallacies—size confounding and "
        "interpolation of sparse panel data—can be identified and removed when a proposed "
        "policy lever (malpractice-litigation risk) is evaluated against physician "
        "workforce outcomes.",
        f"Using national primary data for {N_SPEC} clinical specialties in Japan, we "
        "measure exposure as a size-adjusted rate (closed malpractice claims per "
        f"{_per} physicians) and estimate panel fixed-effects models with equivalence "
        "(TOST) testing. The effect of litigation risk on physician and hospital growth is "
        "statistically equivalent to a null within policy-relevant margins. We show that "
        "count-based associations disappear once specialty-size confounding and "
        "interpolation are removed, and we discuss how structural incentives\u2014"
        "notably no-fault obstetric compensation\u2014may sustain the specialty workforce.",
        f"All data and code are openly available in the project repository "
        f"({PUBLIC_REPO}) and every reported number is reproducible from the raw primary files.",
        "The work is original, not under consideration elsewhere, and all authors approve "
        "the submission. We declare no conflicts of interest.",
    ]
    for b in paragraphs:
        p = doc.add_paragraph()
        r = p.add_run(b)
        r.font.size = Pt(11)
        r.font.name = "Times New Roman"
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5

    for line in ["Sincerely,", "", "[Corresponding author, on behalf of all authors]"]:
        p = doc.add_paragraph()
        if line:
            r = p.add_run(line)
            r.font.size = Pt(12)
            r.font.name = "Times New Roman"

    out = os.path.join(BASE, "ha_cover_letter.docx")
    doc.save(out)
    print("wrote", out)


def build_supplementary():
    doc = _setup_doc()
    head(doc, "Supplementary material", level=1)

    para(doc, "Supplementary Figure 1. Sensitivity-analysis framework for evaluating "
              "malpractice-litigation risk as a healthcare workforce-allocation lever.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, "ha_Supplementary_Figure_1.png")
    if os.path.exists(img):
        p.add_run().add_picture(img, width=Inches(5.8))
    doc.add_paragraph()

    para(doc, f"Supplementary Figure 2. Closed malpractice claims per {_per} physicians by "
              f"specialty, 2008\u20132024 (rates, not counts).")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, "ha_Supplementary_Figure_2.png")
    if os.path.exists(img):
        p.add_run().add_picture(img, width=Inches(5.8))
    doc.add_paragraph()

    para(doc, "Supplementary Figure 3. Physician workforce by specialty, indexed to 2008 (=100).")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, "ha_Supplementary_Figure_3.png")
    if os.path.exists(img):
        p.add_run().add_picture(img, width=Inches(5.8))
    doc.add_paragraph()

    # Supplementary Table 1: data sources
    res_words = {1: "Annual", 2: "Biennial", 3: "Every 3 years"}
    table(doc,
          ["Series", "Source", "Resolution", "Years", "Role"],
          [["Physicians by specialty", "MHLW Statistics of Physicians", res_words.get(PHYS_RES, f"Every {PHYS_RES} years"),
            _year_label(PHYS_DF.columns), "Denominator & outcome"],
           ["Closed malpractice claims", "Supreme Court, by specialty", res_words.get(_resolution(LIT_DF), f"Every {_resolution(LIT_DF)} years"),
            _year_label(LIT_DF.columns), "Exposure (numerator)"],
           ["Hospitals by specialty", "MHLW Survey of Medical Institutions", res_words.get(HOSP_RES, f"Every {HOSP_RES} years"),
            _year_label(HOSP_DF.columns), "Outcome"],
           ["Clinics by specialty", "MHLW Survey (static)", res_words.get(CLINIC_RES, f"Every {CLINIC_RES} years"),
            _year_label(CLINIC_DF.columns), "Descriptive only"],
           ["JMSR report counts", "JMSR / MAIS", "Annual",
            _year_label(JMSR_CORR['years']), "Sensitivity (2016-2024)"],
           ["Newspaper article counts", "Nikkei Telecom 21", "Annual",
            _year_label(MEDIA_CORR['years']), f"Sensitivity ({MEDIA_START}-{MEDIA_END})"]],
          "Supplementary Table 1. Primary data sources and their resolution.")

    # Supplementary Table 2: TOST details
    eqp, eqh = RES["equivalence"][0], RES["equivalence"][1]
    rows = []
    for outcome, eq in [("Physician growth", eqp), ("Hospital growth", eqh)]:
        for t in eq["tests"]:
            rows.append([
                outcome,
                f"{eq['coef_per_SD']*100:+.2f}%",
                f"{eq['ci90_low']*100:+.2f}%, {eq['ci90_high']*100:+.2f}%",
                f"\u00b1{int(t['margin']*100)}%",
                f"{p_tost_fmt(t['p_tost'])}",
                "Yes" if t["equivalent"] else "No"
            ])
    table(doc,
          ["Outcome", "Coef per SD", "90% CI", "Margin", "TOST p", "Equivalent"],
          rows,
          "Supplementary Table 2. Equivalence (TOST) results (effect per +1 SD litigation rate).")

    # Supplementary Table 3: JMSR-adjusted hospital model
    table(doc,
          ["Exposure", "Coefficient", "p", "n"],
          [["Lagged litigation rate", fmt(JMSR["lit_coef"], 4), f"{JMSR['lit_p']:.2f}", JMSR["n_obs"]],
           ["Lagged JMSR report rate", fmt(JMSR["med_coef"], 4), f"{JMSR['med_p']:.2f}", JMSR["n_obs"]]],
          f"Supplementary Table 3. JMSR-adjusted annual hospital growth model "
          f"({JMSR_START}-2024) with both exposures entered simultaneously.")

    # Supplementary Table 4: media-adjusted hospital model
    table(doc,
          ["Exposure", "Coefficient", "p", "n"],
          [["Lagged litigation rate", fmt(MEDIA["lit_coef"], 4), f"{MEDIA['lit_p']:.2f}", MEDIA["n_obs"]],
           ["Lagged media count (per 1,000 articles)", fmt(MEDIA["media_coef"], 4), f"{MEDIA['media_p']:.2f}", MEDIA["n_obs"]]],
          f"Supplementary Table 4. Media-adjusted annual hospital growth model "
          f"({MEDIA_START}-{MEDIA_END}) with a linear time trend; full year fixed effects are "
          "omitted because the national article-count series is collinear with them.")

    # Supplementary Table 5: multiple comparison adjustment
    mc_rows = []
    for t in RES["multiple_comparison"]["tests"]:
        mc_rows.append([t["label"], f"{t['raw_p']:.3f}", f"{t['holm_p']:.3f}"])
    table(doc,
          ["Test", "Raw p", "Holm-adjusted p"],
          mc_rows,
          "Supplementary Table 5. Holm step-down adjusted p-values for the exploratory "
          "sensitivity tests and the JOCS-CP indicator.")

    # STROBE checklist
    head(doc, "STROBE checklist", level=1)
    strobe_items = [
        ("1", "Title and abstract indicate the study design"),
        ("2", "Background and rationale"),
        ("3", "Specific objectives and hypotheses"),
        ("4", "Key elements of study design"),
        ("5", "Data sources, locations and dates"),
        ("6", "Eligibility and selection criteria"),
        ("7", "Definitions of outcomes, exposures and predictors"),
        ("8", "Data sources and measurement methods"),
        ("9", "Discussion of potential sources of bias"),
        ("10", "Explanation of study size"),
        ("11", "Quantitative variables: grouping and transformations"),
        ("12", "Description of all statistical methods"),
        ("13", "Numbers of participants at each stage"),
        ("14", "Descriptive characteristics of participants"),
        ("15", "Outcome data for each exposure category"),
        ("16", "Main results with measures of uncertainty"),
        ("17", "Other analyses (sensitivity and subgroup)"),
        ("18", "Summary of key results with reference to objectives"),
        ("19", "Limitations of bias and imprecision"),
        ("20", "Cautious overall interpretation"),
        ("21", "Generalisability to other populations"),
        ("22", "Registration, protocol, funding, data and code availability"),
    ]
    table(doc,
          ["Item", "Description", "Reported"],
          [[i, desc, "Yes"] for i, desc in strobe_items],
          "STROBE checklist for observational cohort studies.")

    out = os.path.join(BASE, "ha_supplementary.docx")
    doc.save(out)
    print("wrote", out)


def build_figure_pptx():
    prs = Presentation()
    prs.slide_width = PInches(13.333)
    prs.slide_height = PInches(7.5)
    blank = prs.slide_layouts[6]

    main_figs = [
        ("ha_Figure_1.png", "Figure 1",
         f"Equivalence (TOST) of the litigation-rate effect against \u00b1{MARGIN1}% and "
         f"\u00b1{MARGIN2}% margins; horizontal bars are 90% confidence intervals."),
        ("ha_Figure_2.png", "Figure 2",
         "Biennial physician growth against lagged litigation exposure measured as (a) counts and (b) rates. Points are coloured by specialty; the count panel shows the size confounding that the rate panel removes."),
    ]
    supp_figs = [
        ("ha_Supplementary_Figure_1.png", "Supplementary Figure 1",
         "Sensitivity-analysis framework for evaluating malpractice-litigation risk as a healthcare workforce-allocation lever."),
        ("ha_Supplementary_Figure_2.png", "Supplementary Figure 2",
         f"Closed malpractice claims per {_per} physicians by specialty, 2008\u20132024 (rates, not counts)."),
        ("ha_Supplementary_Figure_3.png", "Supplementary Figure 3",
         "Physician workforce by specialty, indexed to 2008 (=100)."),
    ]

    def add_slide(prs, fn, num, cap):
        s = prs.slides.add_slide(blank)
        tb = s.shapes.add_textbox(PInches(0.5), PInches(0.2), PInches(12.3), PInches(0.7))
        tf = tb.text_frame
        tf.text = num
        tf.paragraphs[0].runs[0].font.size = PPt(24)
        tf.paragraphs[0].runs[0].font.bold = True
        img = os.path.join(OUT, fn)
        if os.path.exists(img):
            s.shapes.add_picture(img, PInches(1.2), PInches(1.1), height=PInches(5.2))
        cb = s.shapes.add_textbox(PInches(0.5), PInches(6.5), PInches(12.3), PInches(0.9))
        cf = cb.text_frame
        cf.word_wrap = True
        cf.text = cap
        cf.paragraphs[0].runs[0].font.size = PPt(14)

    for fn, num, cap in main_figs:
        add_slide(prs, fn, num, cap)
    out = os.path.join(BASE, "ha_figures.pptx")
    prs.save(out)
    print("wrote", out)

    prs2 = Presentation()
    prs2.slide_width = PInches(13.333)
    prs2.slide_height = PInches(7.5)
    for fn, num, cap in supp_figs:
        add_slide(prs2, fn, num, cap)
    out2 = os.path.join(BASE, "ha_supplementary_figures.pptx")
    prs2.save(out2)
    print("wrote", out2)


def prepare_figures():
    """Verify that Healthcare Analytics figures have been generated."""
    required = [
        "ha_Figure_1.png", "ha_Figure_2.png",
        "ha_Supplementary_Figure_1.png", "ha_Supplementary_Figure_2.png",
        "ha_Supplementary_Figure_3.png",
    ]
    for fn in required:
        path = os.path.join(OUT, fn)
        if not os.path.exists(path):
            raise SystemExit(f"missing figure: {path}; run manuscript/build_figures_en.py")
        print("verified", path)


def create_submission_zip():
    """Bundle all generated Healthcare Analytics submission files into one archive."""
    zip_path = os.path.join(OUT, "ha_submission.zip")
    files = [
        os.path.join(BASE, "ha_manuscript_en.docx"),
        os.path.join(BASE, "ha_title_page.docx"),
        os.path.join(BASE, "ha_cover_letter.docx"),
        os.path.join(BASE, "ha_highlights.docx"),
        os.path.join(BASE, "ha_supplementary.docx"),
        os.path.join(BASE, "ha_figures.pptx"),
        os.path.join(BASE, "ha_supplementary_figures.pptx"),
        os.path.join(OUT, "ha_Figure_1.png"),
        os.path.join(OUT, "ha_Figure_2.png"),
        os.path.join(OUT, "ha_Supplementary_Figure_1.png"),
        os.path.join(OUT, "ha_Supplementary_Figure_2.png"),
        os.path.join(OUT, "ha_Supplementary_Figure_3.png"),
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            if not os.path.exists(path):
                raise SystemExit(f"submission zip missing file: {path}")
            z.write(path, arcname=os.path.basename(path))
    print("wrote", zip_path)


def main():
    prepare_figures()
    main_wc, abs_wc = build_manuscript()
    build_title_page(main_wc)
    build_highlights()
    build_cover_letter()
    build_supplementary()
    build_figure_pptx()
    create_submission_zip()


if __name__ == "__main__":
    main()
