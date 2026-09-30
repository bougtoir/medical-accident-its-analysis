#!/usr/bin/env python3
"""Build a Public Health (Elsevier / Royal Society for Public Health)
submission package for the rate-based analysis of malpractice litigation
and specialty-level physician and hospital supply in Japan.

Outputs (all derived from results/reanalysis_results.json and data_primary/):
  - manuscript/ph_manuscript_en.docx        anonymised main manuscript (tables/figures
                                            as separate documents, placement marked)
  - manuscript/ph_manuscript_en_inline.docx review copy with tables/figures inline
  - manuscript/ph_title_page.docx           separate title page (author info + DoI summary)
  - manuscript/ph_cover_letter.docx         covering letter per Public Health requirements
  - manuscript/ph_declaration_of_interests.docx  separate declaration-of-interests document
  - manuscript/ph_tables.docx               Tables 1-2 as a separate document
  - manuscript/ph_figure_legends.docx       figure captions as a separate document
  - manuscript/ph_supplementary.docx        supplementary figures & tables
  - output/ph_Figure_1.png/.tiff .. Figure_2        main figure files
  - output/ph_Supplementary_Figure_1.png/.tiff .. 2 supplementary figure files
  - manuscript/ph_figures.pptx              editable main figure slides
  - manuscript/ph_supplementary_figures.pptx editable supplementary figure slides

Public Health (Guide for Authors, checked 2026-09-30):
Original Research <=3000 words; structured abstract <=250 words with
Objectives / Study design / Methods / Results / Conclusions; 3-6 keywords;
max 5 tables+figures within the manuscript (extras as online supplementary);
reference style 6 = AMA (superscript Arabic numerals, numbered in order of
appearance); anonymised manuscript with a separate title page; covering
letter must state journal fit, what is known, what the study adds, and that
the paper is unpublished elsewhere; declaration of interests in the title
page AND as a separate document.
"""
import os
import json
import re
import shutil
import zipfile
import pandas as pd
import scipy.stats as stats
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PInches, Pt as PPt
from PIL import Image as PILImage
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(BASE)
DP = os.path.join(PROJ, "data_primary")
OUT = os.path.join(PROJ, "output")
RES = json.load(open(os.path.join(PROJ, "results", "reanalysis_results.json")))

CORE = ["内科", "外科", "整形外科", "形成外科", "産婦人科", "小児科", "精神科",
        "眼科", "耳鼻咽喉科", "泌尿器科", "皮膚科", "麻酔科"]
EN = {"内科": "Internal medicine", "外科": "Surgery", "整形外科": "Orthopaedics",
      "形成外科": "Plastic surgery", "産婦人科": "Obstetrics & gynaecology",
      "小児科": "Paediatrics", "精神科": "Psychiatry", "眼科": "Ophthalmology",
      "耳鼻咽喉科": "Otolaryngology", "泌尿器科": "Urology", "皮膚科": "Dermatology",
      "麻酔科": "Anaesthesiology"}
DISP = dict(EN, **{"麻酔科": "Anaesthesia"})  # British display spelling


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
SURG_DESC = f"Surgery, which changed by {SURG_PCT:+.1f}%"

# Useful helpers
_per = f"{PER:,}"
def _fmt_pct(x):
    return f"{x:+.2f}"


REFS = {
    "maldist": "Ikesu R, Miyawaki A, Kobayashi Y. Physician distribution by specialty and practice setting: findings in Japan in 2000, 2010 and 2016. Tohoku J Exp Med. 2020;251(1):1-8.",
    "malprac": "Studdert DM, Mello MM, Brennan TA. Medical malpractice. N Engl J Med. 2004;350(3):283-292.",
    "defmed": "Hiyama T, Yoshihara M, Tanaka S, et al. Defensive medicine practices among gastroenterologists in Japan. World J Gastroenterol. 2006;12(47):7671-7675.",
    "lakens": "Lakens D. Equivalence tests: a practical primer for t tests, correlations, and meta-analyses. Soc Psychol Personal Sci. 2017;8(4):355-362.",
    "schuir": "Schuirmann DJ. A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680.",
    "jocscp": "Japan Council for Quality Health Care. Japan Obstetric Compensation System for Cerebral Palsy. Tokyo: Japan Council for Quality Health Care; 2009.",
    "phys": "Ministry of Health, Labour and Welfare. Statistics of Physicians, Dentists and Pharmacists. Tokyo: MHLW.",
    "court": "Supreme Court of Japan, Committee on Medical Litigation. Statistics on medical malpractice litigation (closed cases by specialty). Tokyo: Supreme Court of Japan.",
    "facil": "Ministry of Health, Labour and Welfare. Survey of Medical Institutions (Dynamic). Tokyo: MHLW.",
    "mais": "Act on the Promotion of Medical Safety; Medical Accident Investigation System (2015). Tokyo: MHLW.",
    "nikkei": "Nikkei Inc. Nikkei Telecom 21 (news and information database). Tokyo: Nikkei Inc. Accessed 2024.",
    "angrist": "Angrist JD, Pischke JS. Mostly Harmless Econometrics. Princeton: Princeton University Press; 2009.",
    "strobe": "von Elm E, Altman DG, Egger M, et al. The STROBE statement. Lancet. 2007;370(9596):1453-1457.",
    "matsa2007": "Matsa DA. Does malpractice liability keep the doctor away? Evidence from tort reform damage caps. J Legal Stud. 2007;36(S2):S143-S182.",
    "hyman2015": "Hyman DA, Silver C, Black B, Paik M. Does tort reform affect physician supply? Evidence from Texas. Int Rev Law Econ. 2015;42:203-218.",
    "frakes2020": "Frakes MD, Frank MB, Seabury SA. The Effect of Malpractice Law on Physician Supply: Evidence from Negligence-Standard Reforms. J Health Econ. 2020;70:102272.",
    "kessler1996": "Kessler DP, McClellan MB. Do doctors practice defensive medicine?. Q J Econ. 1996;111(2):353-390.",
    "sloan2008": "Sloan FA, Shadle JH. Is there empirical evidence for \"Defensive Medicine\"? A reassessment. J Health Econ. 2008;27(2):481-491.",
    "taniguchi2023": "Taniguchi K, Watari T, Nagoshi K. Characteristics and trends of medical malpractice claims in Japan between 2006 and 2021. PLoS One. 2023;18(12):e0296155.",
    "hasegawa2016": "Hasegawa J, Toyokawa S, Ikenoue T, et al. Relevant obstetric factors for cerebral palsy: from the Nationwide Obstetric Compensation System in Japan. PLoS One. 2016;11(1):e0148122.",
    "morita2018": "Morita H. Criminal prosecution and physician supply. Int Rev Law Econ. 2018;55:1-11.",
    "helland2015": "Helland E, Seabury SA. Tort reform and physician labor supply: a review of the evidence. Int Rev Law Econ. 2015;42:192-202.",
    "bismark2006": "Bismark M, Paterson R. No-fault compensation in New Zealand: harmonizing injury compensation, provider accountability, and patient safety. Health Aff. 2006;25(1):278-286.",
    "mello2011": "Mello MM, Kachalia A, Studdert DM. Administrative compensation for medical injuries: lessons from three foreign systems. New York: The Commonwealth Fund; 2011.",
    "kamijo2025": "Kamijo K, Wada Y, Ishida K, Warsof SL, Saade G, Kawakita T. Medical-legal claims in obstetrics and gynecology: Japan versus the United States. J Healthc Risk Manag. 2025;44(4):5-11.",
    "lin2022": "Lin PL, Huang JP, Fujii T, Cho EH, Huang MC. A survey of specialty choice among obstetrics and gynecology residents in Japan, Korea, and Taiwan. J Obstet Gynaecol Res. 2022;48(7):1968-1977.",
}
_CITE_ORDER = []
BODY_TEXTS = []


def wc(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


def fmt(x, d=3):
    return f"{x:+.{d}f}" if isinstance(x, float) else str(x)


def _t95(df):
    return stats.t.ppf(0.975, df)


def ci95(coef, se, df):
    m = _t95(df) * se
    return coef - m, coef + m


def fmt_ci(low, high, d=4):
    return f"{fmt(low, d)}, {fmt(high, d)}"


def result_ci(r, coef_key="coef", se_key="se", df_key="df", default_df=N_SPEC - 1):
    if coef_key == "coef" and "ci_low" in r and "ci_high" in r:
        return r["ci_low"], r["ci_high"]
    coef = r[coef_key]
    se = r[se_key]
    df = r.get(df_key, default_df)
    return ci95(coef, se, df)


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
    # size 10 font, double-spaced, 1-inch margins, minimal formatting
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.54)
        s.right_margin = Cm(2.54)
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(10)
    st.paragraph_format.line_spacing = 2.0
    st.paragraph_format.space_after = Pt(6)
    return doc


def _add_runs(par, text, size=Pt(10), bold=False, italic=False):
    for part in re.split(r"(\{[^}]+\})", text):
        if part.startswith("{") and part.endswith("}"):
            keys = [k.strip() for k in part[1:-1].split(",")]
            # AMA style: superscript Arabic numerals, no brackets
            r = par.add_run(cite_number(keys))
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
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


def box_item(doc, label, text):
    p = doc.add_paragraph()
    rl = p.add_run(label + " ")
    rl.bold = True
    rl.font.size = Pt(12)
    rl.font.name = "Times New Roman"
    _add_runs(p, text)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)
    BODY_TEXTS.append(p.text)
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


def _om_run(text):
    r = OxmlElement('m:r')
    t = OxmlElement('m:t')
    t.text = text
    r.append(t)
    return r


def _om_sub(base, sub):
    e = OxmlElement('m:sSub')
    be = OxmlElement('m:e')
    be.append(_om_run(base))
    se = OxmlElement('m:sub')
    se.append(_om_run(sub))
    e.append(be)
    e.append(se)
    return e


def _om_frac(num, den):
    e = OxmlElement('m:f')
    ne = OxmlElement('m:num')
    ne.append(_om_run(num))
    de = OxmlElement('m:den')
    de.append(_om_run(den))
    e.append(ne)
    e.append(de)
    return e


def _om_frac_e(num_elem, den_elem):
    """Fraction whose numerator/denominator are arbitrary OMML elements."""
    e = OxmlElement('m:f')
    ne = OxmlElement('m:num')
    ne.append(num_elem)
    de = OxmlElement('m:den')
    de.append(den_elem)
    e.append(ne)
    e.append(de)
    return e


def _cjk_class():
    return (r"\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF"
            r"\uAC00-\uD7AF\uFF00-\uFFEF")


def sanitize_cjk_fonts(path):
    """Remove CJK/full-width characters from Office document theme/font XML.

    python-docx and python-pptx default themes insert East Asian font names
    (MS Mincho, MS Gothic, SimSun, Malgun Gothic, etc.) that are full-width or
    contain CJK characters.  Since the manuscript text is English, these fonts
    are not used, but their presence in the ZIP triggers two-byte character
    checks.  This function strips the CJK entries from word/fontTable.xml and
    replaces East Asian typeface names in theme1.xml with 'Arial'."""
    import re, shutil, tempfile
    cjk_re = re.compile(f"[{_cjk_class()}]")
    tmp = path + ".san"
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name.endswith((".xml", ".rels")):
                text = data.decode("utf-8")
                # 1. Drop <w:font> entries in fontTable whose name contains CJK
                if name.endswith("fontTable.xml"):
                    text = re.sub(
                        r'<w:font w:name="[^"]*[' + _cjk_class() + r'][^"]*">.*?</w:font>',
                        "", text, flags=re.S)
                # 2. Replace any typeface value containing CJK with 'Arial' (theme fonts)
                text = re.sub(
                    r'(typeface=")([^"]*[' + _cjk_class() + r'][^"]*)(")',
                    r'\1Arial\3', text)
                data = text.encode("utf-8")
            zout.writestr(name, data)
    shutil.move(tmp, path)


def add_equation(doc, *parts):
    """Append an OMML (native Word) equation paragraph composed of parts.

    Parts are OxmlElements (e.g. from _om_run, _om_sub, _om_frac) or plain
    strings, which are wrapped in runs.  OMML is the Office Math Markup
    Language used by Word equation objects, not LaTeX."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    om = OxmlElement('m:oMath')
    for part in parts:
        if isinstance(part, str):
            om.append(_om_run(part))
        else:
            om.append(part)
    p._element.append(om)
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


FIGURE_LEGENDS = []


def legend(caption):
    """Record a main-text figure caption for the separate figure-legends file."""
    FIGURE_LEGENDS.append(caption)


def placement(doc, label, inline):
    """In the clean manuscript, mark where a table/figure should appear.
    In the inline review copy the object itself is embedded instead."""
    if inline:
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"[{label} near here]")
    r.italic = True
    r.font.size = Pt(10)
    r.font.name = "Times New Roman"


def mainfig(doc, fn, caption, inline):
    """Embed the figure with caption (inline) or record legend + placement
    marker (clean anonymised manuscript)."""
    if inline:
        figure(doc, fn, caption)
    else:
        FIGURE_LEGENDS.append(caption)
        placement(doc, caption.split(".")[0], inline)


TITLE = (
    f"Malpractice litigation, physician supply and service capacity in Japan, "
    f"{YEARS}: a national equivalence analysis"
)


def build_manuscript(tdoc, inline=False):
    doc = _setup_doc()
    disp = doc if inline else tdoc

    # Title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(18)
    rt = t.add_run(TITLE)
    rt.bold = True
    rt.font.size = Pt(14)
    rt.font.name = "Times New Roman"

    # Structured abstract per Public Health: Objectives / Study design /
    # Methods / Results / Conclusions, <=250 words.
    abstract_text = (
        "Objectives: To quantify how much specialty-level malpractice-litigation "
        "exposure contributes to physician-supply and service-capacity change, and "
        "whether any association is large enough to matter for workforce planning. "
        f"Study design: Observational specialty-level panel of {N_SPEC} clinical "
        f"specialties in Japan, {YEARS}, using nine measured biennial physician "
        "waves. "
        f"Methods: Exposure was closed malpractice claims per {_per} physicians; "
        "biennial log-change in physicians and hospitals was regressed on the lagged "
        "litigation rate with specialty and wave fixed effects and cluster-robust "
        "errors. Two one-sided tests assessed equivalence to a small specified "
        "margin. "
        f"Results: Litigation exposure was not associated with physician growth "
        f"(coefficient {fmt(PHYS['coef'],4)}; 95% CI {fmt(PHYS['ci_low'],4)} to "
        f"{fmt(PHYS['ci_high'],4)}; p={PHYS['p']:.2f}) or hospital growth "
        f"(p={HOSP['p']:.2f}). A 1-SD higher litigation rate changed physician "
        f"growth by less than \u00b1{MARGIN1}% (TOST p={EQP['tests'][0]['p_tost']:.3f}; "
        f"point estimate {fmt(EQP['coef_per_SD']*100,2)}%, 90% CI "
        f"{fmt(EQP['ci90_low']*100,2)}% to {fmt(EQP['ci90_high']*100,2)}%) and "
        f"hospital growth by less than \u00b1{MARGIN2}% (p={EQH['tests'][1]['p_tost']:.3f}); "
        "sensitivity analyses did not alter these conclusions. "
        "Conclusions: Equivalence testing constrained the plausible "
        "specialty-level effect of litigation to a range unlikely to be large "
        "enough to explain workforce change of practical relevance in Japan; "
        "this ecological analysis cannot speak to individual career decisions."
    )
    abstract_wc = wc(abstract_text)
    if abstract_wc > 250:
        raise SystemExit(f"Abstract is {abstract_wc} words; must be <=250")

    head(doc, "Abstract", level=1)
    p = doc.add_paragraph()
    r = p.add_run(abstract_text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.space_after = Pt(6)

    kw = doc.add_paragraph()
    kr = kw.add_run("Keywords: ")
    kr.bold = True
    kr.font.name = "Times New Roman"
    _add_runs(kw, "malpractice litigation; physician supply; service capacity; "
                  "specialty maldistribution; equivalence testing; Japan")
    kw.paragraph_format.space_after = Pt(18)

    # Introduction
    head(doc, "Introduction", level=1)
    body(doc,
         "Uneven distribution of physicians across specialties is a persistent "
         "problem for health-system capacity and workforce planning. In Japan, "
         "high-acuity fields such as surgery, obstetrics and gynaecology, "
         "paediatrics and emergency care are widely perceived as understaffed "
         "despite continued growth in the total physician supply,{maldist} and "
         "similar specialty imbalances are debated in many other health systems. "
         "Identifying which structural determinants actually move specialty-level "
         "supply is therefore a public-health question with direct planning "
         "relevance.")
    body(doc,
         "Malpractice-litigation risk is one commonly proposed deterrent. The "
         "argument is intuitive\u2014physicians avoid fields where they are more "
         "likely to be sued\u2014and is supported by surveys of perceived risk and "
         "defensive practice.{malprac,defmed} Perceptions, defensive behaviour and "
         "actual specialty-level supply are, however, different outcomes; whether "
         "litigation exposure measurably shifts workforce supply is an empirical "
         "question.")
    body(doc,
         "Three methodological problems complicate previous ecological and "
         "time-series claims. First, raw counts of claims and of physicians both "
         "scale with specialty size, so count-based associations can arise "
         "mechanically without any behavioural mechanism. Second, the Japanese "
         "physician census is biennial; interpolating it to an annual series does "
         "not create new independent information, yet treating interpolated years "
         "as observations inflates nominal degrees of freedom. Third, failing to "
         "reject a null hypothesis is not positive evidence that an effect is "
         "negligible\u2014an underpowered null and a genuinely small effect are "
         "observationally equivalent under conventional testing.")
    body(doc,
         "Equivalence testing addresses the policy question more directly. The "
         "relevant issue for workforce planning is not merely whether a litigation "
         "coefficient differs from zero, but whether litigation could plausibly "
         "produce supply changes large enough to matter. Two one-sided tests "
         "(TOST) can bound an effect within a specified margin and thus "
         "distinguish 'no evidence of an effect' from 'evidence against an effect "
         "of policy-relevant magnitude'.{lakens,schuir}")
    body(doc,
         "Japan offers a useful national setting for such a test: administrative "
         "statistics report closed malpractice claims by specialty, the national "
         "physician census and the facility survey cover all specialties over a "
         "16-year window, and the Japan Obstetric Compensation System for "
         "Cerebral Palsy (JOCS-CP), a no-fault scheme launched in January 2009, "
         "provides institutional context for the specialty most often cited in "
         "this debate.{jocscp}")
    body(doc,
         "We therefore aimed to (1) test the association between the lagged "
         "specialty-level litigation rate and biennial physician-supply change, "
         "(2) test whether any effect is statistically equivalent to a small, "
         "specified policy-relevant margin, and (3) examine the corresponding "
         "hospital (service-capacity) outcome and prespecified sensitivity "
         "analyses.")
    # Methods
    head(doc, "Methods", level=1)
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
         "specialty from the Japan Medical Safety Research Organisation (JMSR, 2015-2025){mais} "
         f"and total national newspaper article counts from Nikkei Telecom 21 "
         f"({MEDIA_START}\u2013{MEDIA_END}; keywords: medical accident + medical malpractice).{{nikkei}} "
         "The full extraction pipeline (with source identifiers and SHA-256 checksums) is "
         "documented in the accompanying repository.")
    body(doc,
         "Physician counts use the principal-specialty "
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
         f"The exposure was the litigation rate: closed claims per {_per} physicians "
         "in each specialty-year. Scaling by the number of physicians removes the "
         "mechanical link between specialty size and claim counts.")
    add_equation(
        doc,
        _om_sub("l", "s,t"), " = (",
        _om_frac_e(_om_sub("C", "s,t"), _om_sub("P", "s,t")), ") × 1000")
    body(doc,
         "where C is the number of closed claims, P is the physician count, and "
         "s and t index specialties and years.")
    body(doc,
         f"The primary analysis used the {len(BIEN)} measured biennial physician waves "
         f"({BIEN[0]}\u2013{BIEN[-1]}). For each specialty we computed the biennial "
         "log-change in physician (or hospital) counts and regressed it on the "
         "litigation rate at the start of the interval, in a panel with specialty "
         "and wave fixed effects and standard errors clustered by specialty.{angrist} "
         "Fixed effects absorb time-invariant specialty characteristics and common "
         "shocks, so identification comes from within-specialty deviations in litigation "
         "rate over time.")
    add_equation(
        doc,
        "\u0394 ln ", _om_sub("Y", "s,t"), " = ",
        _om_sub("\u03b1", "s"), " + ", _om_sub("\u03b3", "t"), " + ",
        _om_run("\u03b2"),
        _om_sub("l", "s,t-1"), " + ", _om_run("\u03b4"),
        _om_sub("J", "s,t"), " + ", _om_sub("\u03b5", "s,t"))
    body(doc,
         "where \u0394lnY is the biennial log-change in physicians or hospitals, "
         "\u03b1 and \u03b3 are specialty and wave fixed effects, l is the one-interval-lagged "
         "litigation rate, J is the JOCS-CP indicator for obstetrics and gynaecology from "
         "January 2009 onward, and \u03b5 is the error term clustered by specialty.")
    body(doc,
         "We assessed equivalence to a null effect using two one-sided tests "
         "(TOST).{lakens,schuir} The exposure was standardised so the coefficient is the "
         f"expected log-change per 1-SD increase in litigation rate; we specified "
         f"equivalence margins of \u00b1{MARGIN1}% and \u00b1{MARGIN2}% biennial workforce change "
         "for the present analysis, as changes small enough to be unlikely to alter "
         "national specialty-workforce planning over a biennial interval, and used "
         "the number of specialty clusters minus one as the degrees of freedom. "
         "An indicator for obstetrics and gynaecology from 2009 onward captured the "
         "JOCS-CP period.{jocscp} Sensitivity analyses repeated the models on (i) the "
         "annual hospital series, (ii) a linearly interpolated annual physician series "
         "(with degrees of freedom governed by the measured waves, not the interpolated n), "
         "(iii) raw counts instead of rates, (iv) the annual hospital series 2016-2024 "
         f"additionally controlling for the JMSR report rate (reports per {_per} physicians), "
         f"and (v) the annual hospital series {MEDIA_START}\u2013{MEDIA_END} additionally "
         f"controlling for total Nikkei Telecom article counts. Because the article-count series "
         "is a national yearly variable, it is collinear with full wave fixed effects; this "
         "sensitivity therefore uses specialty fixed effects plus a linear time trend rather "
         "than wave dummies. These last two tests evaluate whether the litigation coefficient "
         "is confounded by or collinear with broader accident reporting or media coverage. "
         "The JOCS-CP indicator is interpreted as an exploratory, contextual "
         "association rather than a causal estimate of the compensation scheme. "
         "Because the primary analyses are "
         "confirmatory and null, we did not adjust for multiplicity. Analyses "
         "used Python (statsmodels); code and data are openly available.")
    add_equation(
        doc,
        _om_sub("H", "01"), ": \u03b2 \u2264 -m    ",
        _om_sub("H", "02"), ": \u03b2 \u2265 m")
    body(doc,
         f"For physician growth m = {MARGIN1}%; for hospital growth m = {MARGIN2}%. "
         "Rejecting both one-sided nulls supports the equivalence conclusion "
         "|\u03b2|<m.")

    # Results
    head(doc, "Results", level=1)
    head(doc, "Workforce and litigation trends", level=2)
    body(doc,
         f"Litigation rates per {_per} physicians varied several-fold across "
         f"specialties and fell over time in {FELL} of {len(CORE)} fields (Supplementary Figure 1). "
         f"Over the same period the physician workforce grew in {GREW} of {len(CORE)} specialties "
         f"(Supplementary Figure 2; Table 1); {SURG_DESC}, was the only exception. Exposure and "
         "workforce therefore did not move in opposite directions as a flight-from-risk "
         "account would predict.")
    rows = []
    for s in CORE:
        v = DESCR[EN[s]]
        rows.append([DISP[s], v["phys_first"], v["phys_last"],
                     f"{v['litrate_first']:.2f}", f"{v['litrate_last']:.2f}",
                     v["hosp_first"], v["hosp_last"]])
    table(disp,
          ["Specialty", f"Physicians {BIEN[0]}", f"Physicians {BIEN[-1]}",
           f"Lit. rate {BIEN[0]}", f"Lit. rate {BIEN[-1]}",
           f"Hospitals {BIEN[0]}", f"Hospitals {BIEN[-1]}"],
          rows,
          f"Table 1. Physicians, litigation rate (per {_per} physicians) and hospitals by "
          "specialty, first and last waves.")
    placement(doc, "Table 1", inline)

    head(doc, "Primary association and equivalence", level=2)
    body(doc,
         f"The lagged litigation rate was not associated with biennial physician growth "
         f"(coefficient {fmt(PHYS['coef'],4)}; 95% CI {fmt(PHYS['ci_low'],4)} to "
         f"{fmt(PHYS['ci_high'],4)}; p={PHYS['p']:.2f}; n={PHYS['n_obs']}) or with hospital "
         f"growth (coefficient {fmt(HOSP['coef'],4)}; 95% CI {fmt(HOSP['ci_low'],4)} to "
         f"{fmt(HOSP['ci_high'],4)}; p={HOSP['p']:.2f}; n={HOSP['n_obs']}). Equivalence "
         f"testing (Figure 1; Table 2) showed that a 1-SD higher litigation rate "
         f"changed biennial physician growth by less than \u00b1{MARGIN1}% (TOST p={EQP['tests'][0]['p_tost']:.3f}; "
         f"point estimate {fmt(EQP['coef_per_SD']*100,2)}% with 90% CI "
         f"{fmt(EQP['ci90_low']*100,2)}% to {fmt(EQP['ci90_high']*100,2)}%), and hospital "
         f"growth by less than \u00b1{MARGIN2}% (p={EQH['tests'][1]['p_tost']:.3f}). The data "
         "thus support, rather than merely fail to reject, the absence of an effect "
         "of policy-relevant magnitude. Detailed TOST results by margin are reported "
         "in Supplementary Table 2.")
    mainfig(doc, "ph_Figure_1.png",
            f"Figure 1. Equivalence (TOST) of the litigation-rate effect against "
            f"\u00b1{MARGIN1}% (physicians) and \u00b1{MARGIN2}% (hospitals) margins; "
            "horizontal bars are 90% confidence intervals, matching the two "
            "one-sided 5% equivalence tests.", inline)
    trow = [
        ["Physician growth ~ lagged rate", f"{fmt(PHYS['coef'],4)}",
         fmt_ci(*result_ci(PHYS)), f"{PHYS['p']:.2f}", PHYS['n_obs']],
        ["Hospital growth ~ lagged rate", f"{fmt(HOSP['coef'],4)}",
         fmt_ci(*result_ci(HOSP)), f"{HOSP['p']:.2f}", HOSP['n_obs']],
        ["Counts contrast (physician)", f"{fmt(CNT['coef'],4)}",
         fmt_ci(*result_ci(CNT)), f"{CNT['p']:.2f}", CNT['n_obs']],
        ["Annual hospital (sensitivity)", f"{fmt(ANN['coef'],4)}",
         fmt_ci(*result_ci(ANN)), f"{ANN['p']:.2f}", ANN['n_obs']],
        ["Interpolated physician (sensitivity)", f"{fmt(INT['coef'],4)}",
         fmt_ci(*result_ci(INT)), f"{INT['p']:.2f}", INT['n_obs']],
        ["Reverse (workforce\u2192litigation)", f"{fmt(REV['coef'],3)}",
         fmt_ci(*result_ci(REV), d=3), f"{REV['p']:.2f}", REV['n_obs']],
    ]
    table(disp,
          ["Model", "Coefficient", "95% CI", "p", "n"],
          trow,
          "Table 2. Panel fixed-effects models and sensitivity analyses.")
    placement(doc, "Table 2", inline)

    head(doc, "Counts versus rates, and confounders", level=2)
    body(doc,
         f"Using raw litigation counts rather than rates did not recover a negative "
         f"association in this measured-only design (p={CNT['p']:.2f}). Figure 2 "
         "illustrates the difference between the two exposure definitions: a count "
         "exposure is confounded by specialty size (panel a), whereas the size-adjusted rate "
         "is not (panel b). The annual hospital and the interpolated annual physician "
         f"sensitivity analyses were also null (p={ANN['p']:.2f} and p={INT['p']:.2f}), "
         "illustrating the importance of exposure scaling and of restricting the "
         "analysis to measured observations. The JOCS-CP indicator was positively "
         f"associated with obstetric hospital growth (coefficient {fmt(HOSP['jocscp_coef'],3)}; 95% CI "
         f"{fmt_ci(*result_ci(HOSP, coef_key='jocscp_coef', se_key='jocscp_se', df_key='jocscp_df'), d=3)}; "
         f"p={HOSP['jocscp_p']:.3f}); this is an exploratory association that cannot "
         "isolate the compensation scheme from contemporaneous obstetric policies "
         "or secular change.")
    mainfig(doc, "ph_Figure_2.png",
            "Figure 2. Biennial physician growth against lagged litigation exposure "
            "measured as (a) counts and (b) rates.", inline)
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
         f"We also evaluated the JMSR medical accident investigation report counts as a "
         f"potential confounder or competing exposure.{{mais}} Over {JMSR_CORR['years'][0]}-"
         f"{JMSR_CORR['years'][-1]}, raw litigation and JMSR report counts were strongly "
         f"correlated across specialties (Pearson r={JMSR_CORR['pooled_r']:.2f}), because large "
         "specialties generate more of both; however, after removing specialty-specific "
         f"levels and trends the within-specialty correlation was negligible (r={JMSR_CORR['detrended_r']:.2f}). "
         f"A model of annual hospital growth for {JMSR_START}-2024 that included both the "
         "lagged litigation rate and the lagged JMSR report rate left the litigation "
         f"coefficient essentially unchanged (coefficient {fmt(JMSR['lit_coef'],4)}; 95% CI "
         f"{fmt_ci(*result_ci(JMSR, coef_key='lit_coef', se_key='lit_se'))}; p={JMSR['lit_p']:.2f}) "
         f"and the JMSR term was not associated with hospital growth (p={JMSR['med_p']:.2f}; "
         "Supplementary Table 3). Thus, the null litigation result is not explained by, nor "
         "masked by, broader medical accident reporting.")
    body(doc,
         f"Finally, we tested national newspaper coverage from Nikkei Telecom 21 as a "
         f"potential confounder.{{nikkei}} Total annual article counts (keywords: "
         f"medical accident + medical malpractice) and total litigation counts were correlated "
         f"(Pearson r={MEDIA_CORR['total_r']:.2f}), consistent with the public salience of "
         f"high-litigation years; however, within the annual hospital panel the lagged "
         "litigation rate and the media-count series were only weakly correlated. "
         f"A model of annual hospital growth for {MEDIA_START}-{MEDIA_END} that included both the "
         f"lagged litigation rate and the lagged article count (per 1,000 articles) left the "
         f"litigation coefficient essentially unchanged (coefficient {fmt(MEDIA['lit_coef'],4)}; 95% CI "
         f"{fmt_ci(*result_ci(MEDIA, coef_key='lit_coef', se_key='lit_se'))}; p={MEDIA['lit_p']:.2f}) "
         f"and the media term was not associated with hospital growth (p={MEDIA['media_p']:.2f}; "
         "Supplementary Table 4). Media coverage therefore does not account for the null "
         "litigation effect either.")

    # Discussion
    head(doc, "Discussion", level=1)
    body(doc,
         "Across 12 specialties over 16 years, higher litigation rates were not "
         "followed by lower physician or hospital supply. More importantly, "
         "equivalence testing turned the conventional null into a positive "
         "statement: a 1-SD higher litigation rate was statistically equivalent "
         f"to a change smaller than \u00b1{MARGIN1}% in biennial physician growth and "
         f"\u00b1{MARGIN2}% in hospital growth. Litigation exposure alone is therefore "
         "unlikely to explain specialty-level workforce change of a magnitude "
         "relevant to national workforce planning in this setting.")
    body(doc,
         "The distinction matters. A non-significant coefficient is compatible "
         "with effects too small to detect and with no effect at all; an "
         "equivalence test bounds the plausible effect within a stated margin. "
         "What our data exclude is a specialty-level association larger than "
         "roughly one per cent of biennial physician growth per 1-SD litigation "
         "rate; they do not exclude smaller effects, effects on individual "
         "career decisions, or effects operating through channels we do not "
         "measure.")
    body(doc,
         "More broadly, the analysis narrows the plausible contribution of "
         "litigation to specialty-level workforce change: rather than merely "
         "failing to detect an association, it places an empirical bound on "
         "the magnitude that such an association could reasonably take within "
         "this setting. This illustrates the value of equivalence-based "
         "inference for workforce-policy questions in which ruling out "
         "effects of practically important magnitude may be more informative "
         "than testing only for statistical departure from zero.")
    body(doc,
         "For public-health workforce planning, the implication is that "
         "specialty maldistribution is likely shaped by multiple structural "
         "determinants\u2014remuneration, training pipelines, workload and working "
         "conditions, and geographic incentives\u2014and that routine civil-litigation "
         "exposure contributes at most a small share of measured supply change. "
         "This does not mean litigation has no effect on behaviour, defensive "
         "practice, stress, or individual specialty preference; it means its "
         "aggregate footprint on specialty-level supply is small relative to a "
         "planning-relevant margin.")
    body(doc,
         "International evidence on tort reform and physician supply is "
         "consistent with a small, heterogeneous effect. Matsa found that U.S. "
         "state damage caps increased the supply of frontier rural specialists "
         "by 10-12 percent but did not affect supply for the average "
         "resident.{matsa2007} Hyman and colleagues found no measurable increase "
         "in physician supply after the 2003 Texas reforms.{hyman2015} Frakes "
         "and colleagues reported localised, modest compositional shifts after "
         "negligence-standard reforms,{frakes2020} and a systematic review "
         "concludes that effects are heterogeneous across states and "
         "specialties.{helland2015} These studies concern U.S. liability "
         "reforms; they are not directly transportable to Japan, but they "
         "bound the plausible size of litigation effects on supply.")
    body(doc,
         "Litigation risk can also shift clinical behaviour without changing "
         "physician counts. U.S. evidence links malpractice reforms to reduced "
         "defensive spending,{kessler1996} though the magnitude is debated; "
         "physicians can respond to liability pressure by changing how they "
         "practise rather than by exiting a specialty.{sloan2008} In Japan, "
         "fee-for-service reimbursement rewards the high-acuity procedural work "
         "that also carries litigation exposure, so the financial return to "
         "remaining in such specialties may dominate any deterrent from civil "
         "claims.")
    body(doc,
         "Japan's civil-litigation context itself is comparatively "
         "low-volume and settlement-prone: among closed malpractice claims "
         "reported by the Supreme Court between 2006 and 2021, more than half "
         "ended in settlement, plaintiffs won about a quarter of judgments, and "
         "claim numbers have declined, especially in obstetrics and "
         "gynaecology.{taniguchi2023} Routine civil claims of this kind are "
         "distinct from criminal prosecution and high-salience events: Morita "
         "found that a criminal prosecution of an obstetrician was followed by "
         "a 13 percent decline in obstetricians,{morita2018} and a Japan\u2013U.S. "
         "comparison links falling obstetric claim rates to the JOCS-CP scheme, "
         "guidelines and investigation systems rather than to litigation "
         "reduction alone.{kamijo2025} Surveys of OB/GYN residents in Japan, "
         "Korea and Taiwan likewise report litigation as a negative but "
         "secondary factor behind workload, lifestyle and professional "
         "interest.{lin2022}")
    body(doc,
         "The Japan Obstetric Compensation System for Cerebral Palsy (2009) "
         "combined no-fault compensation with investigation and prevention in a "
         "specialty facing obstetrician shortages.{hasegawa2016} The positive "
         "JOCS-CP-period coefficient in our hospital-growth model is an "
         "exploratory association and cannot isolate the compensation scheme "
         "from contemporaneous obstetric policies or secular change; it should "
         "not be read as evidence that no-fault compensation increases "
         "hospital supply.")
    head(doc, "Policy implications", level=2)
    body(doc,
         "These findings suggest that workforce planning should not assume that "
         "reducing routine civil-litigation exposure alone will materially "
         "increase specialty supply. Evaluation of other structural "
         "determinants\u2014including remuneration, training pipelines, workload, "
         "geographic incentives and compensation arrangements\u2014remains "
         "necessary. No-fault systems such as New Zealand's and the Nordic "
         "administrative schemes offer compensation without a protracted "
         "adversarial process and may be worth evaluating for Japan,{bismark2006,mello2011} "
         "but this design cannot demonstrate that any such intervention is "
         "superior. Litigation reform may still matter for defensive medicine, "
         "patient compensation and provider\u2013patient trust; it is simply not, "
         "on the present evidence, a demonstrated lever on specialty supply.")
    body(doc,
         "Future research should link individual-level or prefecture-level "
         "career data to local litigation, media and reimbursement "
         "environments, since specialty-level aggregates cannot observe risk "
         "perceptions or career intentions.")

    head(doc, "Limitations", level=2)
    body(doc,
         f"This is an ecological, specialty-level analysis and cannot infer "
         f"individual career decisions. Inference rests on {N_SPEC} specialty "
         f"clusters and {len(BIEN)} measured biennial waves; cluster-robust errors do "
         "not remove all small-cluster concerns, residual power constraints "
         "remain, and the equivalence margins are substantive, researcher-chosen "
         "judgements rather than externally mandated thresholds. Closed claims "
         "are an exposure signal, not a measure of intrinsic incident risk or "
         "of perceived litigation risk.{court} Specialty-specific "
         f"litigation counts could be recovered only from {BIEN[0]}; clinic counts are "
         f"published only every {CLINIC_RES} years; JMSR report counts cover only "
         f"{JMSR_CORR['years'][0]} onward; and media article counts are national totals "
         "that cannot be decomposed by specialty. Hospital counts are only one "
         "proxy for service capacity, residual confounding and policy "
         "co-interventions cannot be excluded, and the JOCS-CP indicator is not "
         "causally identified. Finally, the findings are embedded in Japan's "
         "particular legal, cultural and institutional context and should not "
         "be assumed to generalise to health systems with different liability "
         "regimes or compensation mechanisms.")

    head(doc, "Conclusions", level=1)
    body(doc,
         f"Across {YEARS}, specialty-level malpractice-litigation exposure in "
         "Japan was not associated with physician or hospital decline, and the "
         "physician effect was statistically equivalent to a change within a "
         "small specified margin. The data argue against routine specialty-level "
         "malpractice litigation being a major determinant of national "
         "physician-supply change within the tested effect-size range in "
         "Japan.")

    # Acknowledgements and declarations (per Public Health manuscript order)
    head(doc, "Acknowledgements", level=1)
    para(doc,
         "Declarations of interest: none. "
         "Funding: This research did not receive any specific grant from funding "
         "agencies in the public, commercial, or not-for-profit sectors. "
         "Ethical approval: Not required (secondary analysis of publicly available "
         "aggregate statistics). "
         "Data and code availability: all primary data files, extraction "
         "scripts and analysis code are openly available in the project repository, enabling "
         "full reproduction of every reported number.")

    head(doc, "Declaration of Generative AI and AI-assisted technologies in the "
              "writing process", level=1)
    para(doc,
         "Statement: During the preparation of this work the author(s) used "
         "generative AI-assisted coding tools (Cognition Devin) in order to assist "
         "with data analysis code, figure generation and manuscript drafting. After "
         "using this tool, the author(s) reviewed and edited the content as needed "
         "and take(s) full responsibility for the content of the publication.")

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

    name = "ph_manuscript_en_inline_v3.docx" if inline else "ph_manuscript_en_v3.docx"
    out = os.path.join(BASE, name)
    doc.save(out)
    sanitize_cjk_fonts(out)
    main_wc = sum(wc(t) for t in BODY_TEXTS)
    print(f"wrote {out}; abstract {abstract_wc} words; main body ~{main_wc} words")
    if main_wc > 3000:
        raise SystemExit(f"Main body is {main_wc} words; Public Health limit is <=3000")
    return main_wc, abstract_wc


def build_title_page(main_word_count):
    doc = _setup_doc()
    for _ in range(4):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(18)
    rt = t.add_run(TITLE)
    rt.bold = True
    rt.font.size = Pt(15)
    rt.font.name = "Times New Roman"

    # Public Health title-page requirements: title, authors' initials, surname,
    # main degrees (two only), institution name and location, declaration of
    # interests; corresponding author clearly indicated with address, e-mail,
    # telephone.
    lines = [
        "Authors: Onishi Tatsuki",
        "Main degrees: [main degrees (two only)]",
        "Affiliation (where the work was done): Data Science AI Innovation Research "
        "Promotion Center, Shiga University, 1-1-1 Bamba, Hikone, Shiga 522-8522, Japan",
        "Corresponding author: Tatsuki Onishi",
        "Corresponding author address: Data Science AI Innovation Research Promotion Center, "
        "Shiga University, 1-1-1 Bamba, Hikone, Shiga 522-8522, Japan",
        "Corresponding author email: [corresponding author email]",
        "Corresponding author telephone: [telephone]",
        "Declarations of interest: none",
        "Running title: Litigation and physician supply",
        "Keywords: malpractice litigation; physician supply; service capacity; "
        "specialty maldistribution; equivalence testing; Japan",
        "Funding: This research did not receive any specific grant from funding "
        "agencies in the public, commercial, or not-for-profit sectors.",
        "Ethical approval: Not required (secondary analysis of publicly available "
        "aggregate statistics)",
        f"Word count (main text): approximately {main_word_count} words "
        "(excluding abstract, references, declarations, tables and figure legends)",
        "Article type: Original research",
        "Tables: 2  Figures: 2  Supplementary tables: 4  Supplementary figures: 2",
        "Declaration of generative AI use: Generative AI and AI-assisted technologies "
        "were used to assist with coding, data analysis, figure generation, and "
        "manuscript drafting; the author(s) reviewed and edited the content and take "
        "full responsibility for the publication.",
        "Data availability: all primary data and analysis code are openly available "
        "in the project repository.",
        "CRediT author contribution statement: Tatsuki Onishi conceptualised the study, "
        "collected and curated data, performed the formal analysis, wrote the original draft, "
        "and approved the final manuscript.",
    ]
    for line in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        r.font.size = Pt(12)
        r.font.name = "Times New Roman"

    out = os.path.join(BASE, "ph_title_page.docx")
    doc.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)


def build_declaration_of_interests():
    """Public Health requires a declaration of interests both in the title
    page and as a separate document in the submission process."""
    doc = _setup_doc()
    h = doc.add_paragraph()
    r = h.add_run("Declaration of interests")
    r.bold = True
    r.font.size = Pt(13)
    r.font.name = "Times New Roman"
    p = doc.add_paragraph()
    r = p.add_run("Declarations of interest: none")
    r.font.size = Pt(12)
    r.font.name = "Times New Roman"
    out = os.path.join(BASE, "ph_declaration_of_interests.docx")
    doc.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)


def build_cover_letter():
    doc = _setup_doc()
    for line in ["30 September 2026", "", "The Editors",
                 "Public Health", ""]:
        p = doc.add_paragraph()
        if line:
            r = p.add_run(line)
            r.font.size = Pt(12)
            r.font.name = "Times New Roman"
    p = doc.add_paragraph()
    p.add_run("Dear Editors,").font.size = Pt(12)
    p.runs[0].font.name = "Times New Roman"

    paragraphs = [
        f'We submit an original research article, "{TITLE}", for consideration by '
        "Public Health.",
        "Why this paper fits Public Health: the study addresses specialty-level "
        "physician supply and service capacity\u2014a core public-health workforce and "
        "health-system capacity question listed in the journal's scope. We ask how "
        "much malpractice-litigation exposure, a widely cited deterrent in "
        "high-acuity specialties, actually explains specialty-level workforce change, "
        "and whether any association is large enough to matter for workforce "
        "planning.",
        "What is known: malpractice pressure is often invoked to explain specialty "
        "maldistribution, but previous ecological and time-series claims have "
        "typically related raw counts of claims to raw counts of physicians, "
        "treated interpolated annual series as independent observations, and "
        "interpreted non-significant coefficients as evidence of no effect.",
        f"What this study adds: using national Japanese data for {N_SPEC} clinical "
        f"specialties over {YEARS}, we express exposure as a rate (closed claims "
        f"per {_per} physicians) to remove specialty-size confounding, analyse only "
        "measured biennial physician observations, and apply equivalence (TOST) "
        "testing. The contribution is not simply a non-significant association but "
        "quantitative evidence that any specialty-level physician-supply "
        f"association lies within a small, policy-relevant margin (\u00b1{MARGIN1}% "
        "biennial change per 1-SD litigation rate). Importantly, the contribution "
        "is not limited to a non-significant association: equivalence testing "
        "places an empirical bound on the plausible magnitude of the "
        "litigation\u2013workforce relationship, showing that any specialty-level "
        "effect is unlikely to be large enough to account for workforce change "
        "of practical relevance in this setting.",
        "The manuscript was suggested for transfer to Public Health following "
        "editorial assessment at Health Policy and Technology on the basis of "
        "closer journal scope.",
        "All data and code are openly available and every reported number is "
        "reproducible from the raw primary files in the accompanying repository. "
        "This research did not receive any specific grant from funding agencies in "
        "the public, commercial, or not-for-profit sectors. The work is original, "
        "has not been published elsewhere, is not under consideration elsewhere, "
        "and all authors approve the submission. Declarations of interest: none.",
        "Corresponding author: Tatsuki Onishi, Data Science AI Innovation Research "
        "Promotion Center, Shiga University, 1-1-1 Bamba, Hikone, Shiga 522-8522, "
        "Japan.",
    ]
    for b in paragraphs:
        p = doc.add_paragraph()
        r = p.add_run(b)
        r.font.size = Pt(11)
        r.font.name = "Times New Roman"
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5

    for line in ["Sincerely,", "", "Tatsuki Onishi"]:
        p = doc.add_paragraph()
        if line:
            r = p.add_run(line)
            r.font.size = Pt(12)
            r.font.name = "Times New Roman"

    out = os.path.join(BASE, "ph_cover_letter_v3.docx")
    doc.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)


def build_supplementary():
    doc = _setup_doc()
    head(doc, "Supplementary material", level=1)

    para(doc, f"Supplementary Figure 1. Closed malpractice claims per {_per} physicians by "
              f"specialty, 2008\u20132024 (rates, not counts).")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, "ph_Supplementary_Figure_1.png")
    if os.path.exists(img):
        p.add_run().add_picture(img, width=Inches(5.8))
    doc.add_paragraph()

    para(doc, "Supplementary Figure 2. Physician workforce by specialty, indexed to 2008 (=100).")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img = os.path.join(OUT, "ph_Supplementary_Figure_2.png")
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
                f"{t['p_tost']:.3f}",
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

    out = os.path.join(BASE, "ph_supplementary.docx")
    doc.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)


def build_figure_pptx():
    prs = Presentation()
    prs.slide_width = PInches(13.333)
    prs.slide_height = PInches(7.5)
    blank = prs.slide_layouts[6]

    main_figs = [
        ("ph_Figure_1.png", "Figure 1",
         f"Equivalence (TOST) of the litigation-rate effect against \u00b1{MARGIN1}% and "
         f"\u00b1{MARGIN2}% margins; horizontal bars are 90% confidence intervals."),
        ("ph_Figure_2.png", "Figure 2",
         "Biennial physician growth against lagged litigation exposure measured as (a) counts and (b) rates."),
    ]
    supp_figs = [
        ("ph_Supplementary_Figure_1.png", "Supplementary Figure 1",
         f"Closed malpractice claims per {_per} physicians by specialty, 2008\u20132024 (rates, not counts)."),
        ("ph_Supplementary_Figure_2.png", "Supplementary Figure 2",
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
    out = os.path.join(BASE, "ph_figures.pptx")
    prs.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)

    prs2 = Presentation()
    prs2.slide_width = PInches(13.333)
    prs2.slide_height = PInches(7.5)
    for fn, num, cap in supp_figs:
        add_slide(prs2, fn, num, cap)
    out2 = os.path.join(BASE, "ph_supplementary_figures.pptx")
    prs2.save(out2)
    sanitize_cjk_fonts(out2)
    print("wrote", out2)


def copy_figures():
    """Generate Public Health-ready PNGs from the base figure functions.

    Source figures are rebuilt here so journal-specific versions (without
    embedded captions and in colour where useful) are produced even if the
    generic ha_* and fig* files already exist.  PNGs are then converted to
    TIFF for Elsevier artwork upload."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("figure_en",
        os.path.join(BASE, "build_figures_en.py"))
    figure_en = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(figure_en)
    figure_en.plot_hp_figures(PHYS_DF, LIT_DF, HOSP_DF, RES, BIEN, OUT, prefix="ph")

    for png in ["ph_Figure_1.png", "ph_Figure_2.png",
                "ph_Supplementary_Figure_1.png", "ph_Supplementary_Figure_2.png"]:
        src = os.path.join(OUT, png)
        if not os.path.exists(src):
            raise SystemExit(f"missing figure: {src}")
        tiff = src.replace(".png", ".tiff")
        img = PILImage.open(src)
        dpi = img.info.get('dpi', (300, 300))
        img.save(tiff, format='TIFF', compression='tiff_lzw', dpi=dpi)
        print("wrote", tiff)


def create_submission_zip():
    """Bundle all generated Public Health submission files into one archive."""
    zip_path = os.path.join(OUT, "PUBLIC_HEALTH_submission_FINAL_v3.zip")
    files = [
        os.path.join(BASE, "ph_manuscript_en_v3.docx"),
        os.path.join(BASE, "ph_manuscript_en_inline_v3.docx"),
        os.path.join(BASE, "ph_title_page.docx"),
        os.path.join(BASE, "ph_cover_letter_v3.docx"),
        os.path.join(BASE, "ph_declaration_of_interests.docx"),
        os.path.join(BASE, "ph_tables.docx"),
        os.path.join(BASE, "ph_figure_legends.docx"),
        os.path.join(BASE, "ph_supplementary.docx"),
        os.path.join(BASE, "ph_figures.pptx"),
        os.path.join(BASE, "ph_supplementary_figures.pptx"),
        os.path.join(PROJ, "DEVIN_PUBLIC_HEALTH_TRANSFER_PROMPT.txt"),
        os.path.join(PROJ, "DEVIN_PUBLIC_HEALTH_FINISHING_PASS.txt"),
        os.path.join(PROJ, "DEVIN_PUBLIC_HEALTH_CONTRIBUTION_ALIGNMENT_PROMPT.txt"),
        os.path.join(OUT, "ph_Figure_1.png"),
        os.path.join(OUT, "ph_Figure_2.png"),
        os.path.join(OUT, "ph_Supplementary_Figure_1.png"),
        os.path.join(OUT, "ph_Supplementary_Figure_2.png"),
        os.path.join(OUT, "ph_Figure_1.tiff"),
        os.path.join(OUT, "ph_Figure_2.tiff"),
        os.path.join(OUT, "ph_Supplementary_Figure_1.tiff"),
        os.path.join(OUT, "ph_Supplementary_Figure_2.tiff"),
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            if not os.path.exists(path):
                raise SystemExit(f"submission zip missing file: {path}")
            z.write(path, arcname=os.path.basename(path))
    qc = ["PUBLIC_HEALTH_FIT_AUDIT.md", "HOSTILE_REVIEW_PUBLIC_HEALTH.md",
          "CLAIM_CALIBRATION_AUDIT.md", "REFERENCE_AUDIT.md",
          "SCIENTIFIC_CONTRIBUTION_ALIGNMENT.md", "FINAL_HANDOFF.md"]
    with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as z:
        for q in qc:
            fp = os.path.join(PROJ, q)
            if os.path.exists(fp):
                z.write(fp, arcname="_internal_QC/" + q)
    print("wrote", zip_path)


def build_display_docs():
    """Write tables and figure legends as separate documents."""
    ldoc = _setup_doc()
    head(ldoc, "Figure legends", level=1)
    for cap in FIGURE_LEGENDS:
        para(ldoc, cap)
    out = os.path.join(BASE, "ph_figure_legends.docx")
    ldoc.save(out)
    sanitize_cjk_fonts(out)
    print("wrote", out)


def main():
    global BODY_TEXTS, FIGURE_LEGENDS, _CITE_ORDER
    copy_figures()
    tdoc = _setup_doc()
    head(tdoc, "Tables", level=1)
    main_wc, abs_wc = build_manuscript(tdoc, inline=False)
    tout = os.path.join(BASE, "ph_tables.docx")
    tdoc.save(tout)
    sanitize_cjk_fonts(tout)
    print("wrote", tout)
    build_display_docs()  # consumes FIGURE_LEGENDS from the clean build
    # Inline review copy: same text, tables/figures embedded at call sites.
    BODY_TEXTS, FIGURE_LEGENDS, _CITE_ORDER = [], [], []
    build_manuscript(None, inline=True)
    build_title_page(main_wc)
    build_declaration_of_interests()
    build_cover_letter()
    build_supplementary()
    build_figure_pptx()
    create_submission_zip()


if __name__ == "__main__":
    main()
