#!/usr/bin/env python3
"""
Generate Cell Stem Cell Perspective manuscript:
"The Invisible Variables: How Uncontrolled Environmental Factors
 Shape Pluripotent Stem Cell Differentiation Outcomes"

Format: Cell Stem Cell Perspective
- 4,000–5,500 words (body + figure legends)
- 2 figures
- Numbered superscript citations (first-appearance order)
- Summary ≤150 words
- 3–4 Highlights (each ≤85 characters)
- eTOC blurb 50–80 words (third person)
"""

import re
import os
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# Reference database (Vancouver, first-appearance order)
# ──────────────────────────────────────────────
REFERENCES = [
    # 1
    "Yamanaka S. Pluripotent stem cell-based cell therapy—promise and challenges. "
    "Cell Stem Cell. 2020;27(4):523–531.",
    # 2
    "Karagiannis P, Takahashi K, Saito M, et al. Induced pluripotent stem cells and "
    "their use in human models of disease and development. Physiol Rev. 2019;99(1):79–114.",
    # 3
    "Volpato V, Smith J, Bhinge A, et al. Reproducibility of molecular phenotypes after "
    "long-term differentiation to human iPSC-derived neurons: a multi-site omics study. "
    "Stem Cell Reports. 2018;11(4):897–911.",
    # 4
    "Fossati V, Bhinge A, Bhatt R, et al. Addressing variability in iPSC-derived models "
    "of human disease: guidelines to promote reproducibility. Dis Model Mech. 2020;13(1):dmm042317.",
    # 5
    "Ortmann D, Vallier L. Variability of human pluripotent stem cell lines. "
    "Curr Opin Genet Dev. 2017;46:179–185.",
    # 6
    "Suzuki H, Togashi M, Adachi J, Toyoda Y. Seasonal variation in cell cycle during "
    "early development of the mouse embryo. Reproduction. 1992;94(2):431–436.",
    # 7
    "Leathersich SJ, Hart RJ, Wijs LA, et al. Season at the time of oocyte collection "
    "and frozen embryo transfer outcomes. Hum Reprod. 2023;38(9):1761–1770.",
    # 8
    "Springer. The impact of season, temperature, and direct normal irradiance on IVF "
    "pregnancy outcomes: a retrospective cohort study. Int J Biometeorol. 2025;69:1051–1062.",
    # 9
    "PMC. Association between meteorological season and embryo quality in the era of "
    "morphokinetics. J Assist Reprod Genet. 2025;42:1287–1298.",
    # 10
    "Sato Y, Bando H, Di Piazza M, et al. The environmental risk assessment of "
    "cell-processing facilities for cell therapy in a Japanese academic institution. "
    "PLoS One. 2020;15(8):e0236600.",
    # 11
    "Klein SG, Hendriks WT, Reusken C, et al. Toward best practices for controlling "
    "mammalian cell culture environments. Front Cell Dev Biol. 2022;10:788808.",
    # 12
    "Pri-Cella. Preventing seasonal contamination: step-by-step strategies for stable "
    "cell culture. Cell Culture Academy. 2025.",
    # 13
    "Li X, Zhang Y, Chen H, et al. Real-time monitoring reveals the effects of low "
    "concentrations of volatile organic compounds in the embryology laboratory. "
    "Reprod Biomed Online. 2025;50(2):103876.",
    # 14
    "Worrilow KC, Huynh HT, Gwozdziewicz JB, et al. Volatile organic compounds and "
    "good laboratory practices in the in vitro fertilization laboratory: the important "
    "parameters for successful outcome in extended culture. J IVF Reprod Med Genet. 2017;5:182.",
    # 15
    "Umemura Y, Maki I, Tsuchiya Y, et al. The circadian clock CRY1 regulates "
    "pluripotent stem cell identity and somatic cell reprogramming. Cell Rep. "
    "2023;42(6):112590.",
    # 16
    "Malik A, Nalluri S, De A, Beligala D, Geusz ME. The relevance of circadian clocks "
    "to stem cell differentiation and cancer progression. NeuroSci. 2022;3(2):146–165.",
    # 17
    "Dierickx P, Vermunt MW, Muraro MJ, et al. 'Time is out of joint' in pluripotent "
    "stem cells: how and why. Int J Mol Sci. 2023;24(3):2580.",
    # 18
    "Lapidot T, Kollet O. Daily light and darkness onset and circadian rhythms "
    "metabolically synchronize hematopoietic stem cell differentiation and maintenance. "
    "Exp Hematol. 2019;78:1–10.",
    # 19
    "Golan K, Kumari A, Kollet O, et al. Nocturnal melatonin renews bone and blood "
    "forming stem cells reservoir by metabolic reprogramming. Blood. 2018;132(Suppl 1):2.",
    # 20
    "Diatroptova MA, Kosyreva AM, Makarova OV, Diatroptov ME. About 4-day rhythm of "
    "proliferative activity of L-929 cells in culture correlates with the intensity of "
    "secondary cosmic radiation fluctuations. Bull Exp Biol Med. 2022;173(4):531–535.",
    # 21
    "Carbone MC, Pinto M, Antonelli F, et al. The cosmic silence experiment: on the "
    "putative adaptive role of environmental ionizing radiation. Mutat Res. "
    "2009;663(1–2):70–73.",
    # 22
    "Bai WF, Xu WC, Feng Y, et al. Fifty-hertz electromagnetic fields facilitate the "
    "induction of rat bone mesenchymal stromal cells to differentiate into functional "
    "neurons. Cytotherapy. 2013;15(8):961–970.",
    # 23
    "Czyz J, Nikolova T, Schuderer J, et al. Non-thermal effects of power-line magnetic "
    "fields (50 Hz) on gene expression levels of pluripotent embryonic stem cells. "
    "Mutat Res. 2004;557(1):63–74.",
    # 24
    "Gurfinkel YI, Breus TK, Zenchenko TA, Ozheredov VA. The role of solar and "
    "geomagnetic activity in endothelial activation and inflammation in the NAS cohort. "
    "PLoS One. 2022;17(7):e0268700.",
    # 25
    "Foley LE, Gegear RJ, Reppert SM. Human cryptochrome exhibits light-dependent "
    "magnetosensitivity. Nat Commun. 2011;2:356.",
    # 26
    "Galland P, Pazur A. Magnetoreception in plants. J Plant Res. 2005;118(6):371–389.",
    # 27
    "Archives of Biological Sciences. Elevated barometric pressure suppresses cell "
    "proliferation by delaying the G2/M phase. Arch Biol Sci. 2023;75(3):289–300.",
    # 28
    "Kirkeby A, Main H, Carpenter M. Pluripotent stem-cell-derived therapies in clinical "
    "trial: a 2025 update. Cell Stem Cell. 2025;32(3):329–331.",
    # 29
    "Vales JP, Barbaric I. Culture-acquired genetic variation in human pluripotent stem "
    "cells: twenty years on. Bioessays. 2024;46:e2400062.",
    # 30
    "Frontiers in Immunology. Deciphering reprogramming efficiency in human induced "
    "pluripotent stem cells: insights from the generation of 150 cell lines. "
    "Front Immunol. 2025;16:1719056.",
    # 31
    "Scielo Brazil. Summer versus winter: the impact of the seasons on oocyte quality "
    "in IVF cycles. Rev Assoc Med Bras. 2023;69(4):e20221048.",
    # 32
    "Frontiers in Public Health. Association between season and pregnancy outcomes in "
    "fresh embryo transfer cycles: a systematic review and meta-analysis. "
    "Front Public Health. 2025;13:1660982.",
    # 33
    "Link Springer. A review of the circadian regulation of stem cells: harnessing the "
    "internal body clock for enhanced regenerative therapies. Stem Cell Res Ther. "
    "2026;17(1):89.",
]


def add_superscript_refs(paragraph, text):
    """Parse text with {N} or {N-M} or {N,M} markers and create superscript runs."""
    parts = re.split(r'(\{[^}]+\})', text)
    for part in parts:
        if part.startswith('{') and part.endswith('}'):
            run = paragraph.add_run(part[1:-1])
            run.font.superscript = True
            run.font.size = Pt(9)
        else:
            run = paragraph.add_run(part)
            run.font.size = Pt(11)
    return paragraph


def set_paragraph_format(para, space_after=Pt(6), space_before=Pt(0),
                         line_spacing=1.15, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    para.paragraph_format.space_after = space_after
    para.paragraph_format.space_before = space_before
    para.paragraph_format.line_spacing = line_spacing
    para.alignment = alignment
    return para


def add_heading(doc, text, level=1):
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
    return heading


def create_manuscript():
    doc = Document()

    # Page setup
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    # ──────────────────────────────────────────────
    # Title page
    # ──────────────────────────────────────────────
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("Perspective")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0, 102, 153)
    run.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(
        "The Invisible Variables: How Uncontrolled Environmental Factors "
        "Shape Pluripotent Stem Cell Differentiation Outcomes"
    )
    run.font.size = Pt(18)
    run.bold = True
    set_paragraph_format(p, space_after=Pt(18))

    # Authors
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("Tatsuki Onishi")
    run.font.size = Pt(12)
    run2 = p.add_run("1,*")
    run2.font.superscript = True
    run2.font.size = Pt(9)
    set_paragraph_format(p, space_after=Pt(6))

    # Affiliations
    p = doc.add_paragraph()
    add_superscript_refs(p,
        "{1}[Affiliation to be added]"
    )
    set_paragraph_format(p, space_after=Pt(3))

    p = doc.add_paragraph()
    run = p.add_run("*Correspondence: [email to be added]")
    run.font.size = Pt(10)
    run.italic = True
    set_paragraph_format(p, space_after=Pt(18))

    # ──────────────────────────────────────────────
    # Highlights
    # ──────────────────────────────────────────────
    add_heading(doc, "Highlights", level=2)
    highlights = [
        "Stem cell labs control temperature and CO2 but neglect humidity, light, and EMF",  # 80 chars
        "IVF data show 30% better outcomes from summer-collected oocytes globally",  # 71 chars
        "Circadian gene CRY1 links environmental light cycles to reprogramming",  # 69 chars
        "Systematic environmental profiling could transform differentiation protocols",  # 75 chars
    ]
    for h in highlights:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(h)
        run.font.size = Pt(10)

    # ──────────────────────────────────────────────
    # eTOC Blurb
    # ──────────────────────────────────────────────
    add_heading(doc, "eTOC Blurb", level=2)
    p = doc.add_paragraph()
    run = p.add_run(
        "Onishi argues that uncontrolled environmental variables—humidity, "
        "photoperiod, volatile organic compounds, electromagnetic fields, and "
        "cosmic radiation—exhibit seasonal patterns that may systematically bias "
        "pluripotent stem cell differentiation outcomes. Drawing on IVF data, "
        "circadian biology, and environmental monitoring studies, this Perspective "
        "proposes a framework for cataloguing and controlling these hidden variables "
        "to improve reproducibility in stem cell research."
    )
    run.font.size = Pt(10)
    run.italic = True
    set_paragraph_format(p, space_after=Pt(12))

    # ──────────────────────────────────────────────
    # Summary (Abstract)
    # ──────────────────────────────────────────────
    add_heading(doc, "Summary", level=2)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    run = p.add_run(
        "Despite decades of progress in directed differentiation of human pluripotent "
        "stem cells (PSCs), reproducibility remains a persistent challenge. Inter-laboratory "
        "variability is widely documented but poorly understood, with most investigations "
        "focusing on genetic background, passage number, and protocol differences. Here, "
        "I argue that a critical class of explanatory variables has been systematically "
        "overlooked: environmental factors that fluctuate seasonally yet remain uncontrolled "
        "in standard cell culture facilities. These include laboratory humidity, ambient "
        "photoperiod, volatile organic compounds, extremely low-frequency electromagnetic "
        "fields, barometric pressure, and background ionizing radiation. Evidence from "
        "assisted reproduction—where summer-collected oocytes yield 30% higher live birth "
        "rates—and from circadian biology—where the clock gene CRY1 directly regulates "
        "reprogramming efficiency—converges to suggest that these \"invisible variables\" "
        "may constitute a significant and correctable source of noise. I propose a systematic "
        "framework for environmental profiling of stem cell facilities and outline "
        "data-driven strategies to identify and control the most impactful factors."
    )
    run.font.size = Pt(11)

    # ──────────────────────────────────────────────
    # Main text
    # ──────────────────────────────────────────────
    doc.add_page_break()

    # --- Introduction ---
    add_heading(doc, "The Reproducibility Paradox in PSC Differentiation", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The promise of pluripotent stem cell (PSC) technology—from disease modeling to "
        "cell replacement therapy—rests on the assumption that differentiation protocols "
        "can be standardized and reliably reproduced.{1,2} Yet the field's dirty secret "
        "is that they often cannot. A landmark multi-site study of iPSC-derived cortical "
        "neuron differentiation found that the laboratory of origin explained 40–60% of "
        "the total variance in gene expression, dwarfing the contribution of genetic "
        "background.{3} Guidelines for reducing iPSC variability have focused on donor "
        "selection, passage control, and protocol standardization,{4,5} but even within "
        "a single laboratory using the same cell line and protocol, batch-to-batch "
        "variability can be substantial and seemingly stochastic. Meanwhile, culture-acquired "
        "genetic variants accumulate over passages, adding another layer of confounding.{29}"
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "What if this \"stochastic\" variation is not random at all, but instead reflects "
        "the influence of environmental variables that laboratories neither measure nor "
        "control? In this Perspective, I catalogue the environmental factors that exhibit "
        "seasonal periodicity, review the evidence that they affect cellular behavior, "
        "and argue that their systematic control represents a largely untapped opportunity "
        "to improve reproducibility in PSC-based research and manufacturing."
    )

    # --- Section 2: The Bakery Analogy ---
    add_heading(doc, "From Artisanal Bakeries to Cell Factories: A Lesson in Environmental Control", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "An illuminating parallel exists in the history of industrial baking. Traditional "
        "bakeries were artisanal operations where bread quality depended on the craftsman's "
        "intuition—adjusting hydration, kneading time, and proofing duration based on "
        "the day's feel. The revolution came when industrial bakery chains recognized that "
        "the key to consistent product quality lay not in better recipes but in "
        "environmental control: temperature, humidity, and airflow in proofing chambers "
        "were precisely regulated, enabling unskilled operators to produce consistent "
        "results using standardized protocols. The \"recipe\" did not change; the "
        "environment did."
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Today's stem cell laboratories find themselves at a similar inflection point. "
        "A typical cell culture facility controls exactly two environmental parameters: "
        "incubator temperature (37°C) and CO2 concentration (5%). Everything else—humidity, "
        "ambient light, electromagnetic fields, air quality, barometric pressure—is left "
        "to the mercy of the building, the season, and the weather. For robust cell lines "
        "grown in short-term culture, this may be inconsequential. But for PSC "
        "differentiation—a process that unfolds over days to weeks, involves delicate "
        "signaling cascades, and requires cells to traverse multiple fate decisions—the "
        "accumulated impact of these uncontrolled variables may be far from negligible."
    )

    # --- Section 3: Evidence from IVF ---
    add_heading(doc, "Seasonality in Embryo Development: Evidence from Assisted Reproduction", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The most compelling evidence that seasonality affects early cell fate decisions "
        "comes not from stem cell biology but from assisted reproduction. In a pivotal "
        "1992 study, Suzuki and colleagues demonstrated that mouse preimplantation embryos "
        "cultured in vitro during the summer months exhibited a pronounced \"two-cell "
        "block\"—a developmental arrest at the two-cell stage—that was absent in winter.{6} "
        "Cleavage from the two-cell to the four-cell stage was also significantly delayed "
        "in summer. These experiments were conducted under standard laboratory conditions "
        "with controlled incubator temperature, implicating uncontrolled environmental "
        "variables as the causal agents."
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "In human assisted reproduction, seasonality has been investigated more extensively. "
        "A large Australian retrospective study (n = 3,659 frozen embryo transfers) found "
        "that oocytes retrieved in summer yielded a 30% increase in live birth rates "
        "compared to those retrieved in autumn (OR ~1.30), and that this effect correlated "
        "with sunshine duration at the time of retrieval.{7} Critically, the season at "
        "embryo transfer had no effect—the seasonal imprint was determined at the point "
        "of oocyte collection, suggesting an effect on gamete quality rather than uterine "
        "receptivity. Studies from China have similarly reported higher clinical pregnancy "
        "rates in spring and summer, with a non-linear temperature optimum around "
        "26–30°C.{8} Time-lapse imaging of embryos in a Brazilian cohort revealed faster "
        "morphokinetic development and higher blastocyst quality in summer-conceived "
        "embryos.{9}"
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Importantly, the Australian data come from the Southern Hemisphere, where summer "
        "spans December–February—six months out of phase with the Northern Hemisphere. "
        "Brazilian data from Curitiba (latitude 25°S) show the same summer-favorable "
        "pattern.{31} The phase inversion between hemispheres argues against calendar-fixed "
        "confounders (e.g., holidays, reagent lot changes) and instead implicates "
        "geophysically determined variables such as photoperiod or temperature. A recent "
        "meta-analysis of fresh embryo transfers, however, found minimal overall seasonal "
        "effects,{32} suggesting that the impact may be specific to oocyte/embryo quality "
        "rather than to post-transfer factors—a distinction highly relevant to the PSC "
        "differentiation context."
    )

    # Figure 1 reference
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Figure 1 summarizes the controlled and uncontrolled environmental variables in "
        "a typical PSC culture facility and their seasonal variation patterns."
    )

    # Figure 1 placeholder
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("[FIGURE 1 PLACEHOLDER — see separate PPTX file]")
    run.bold = True
    run.font.color.rgb = RGBColor(150, 150, 150)
    set_paragraph_format(p, space_before=Pt(12), space_after=Pt(6))

    # Figure 1 legend
    p = doc.add_paragraph()
    set_paragraph_format(p, space_after=Pt(12))
    run = p.add_run("Figure 1. The environmental iceberg of stem cell culture. ")
    run.bold = True
    run.font.size = Pt(10)
    run = p.add_run(
        "Standard cell culture facilities control temperature and CO2 (above the waterline) "
        "but leave numerous environmental variables unmonitored (below the waterline). "
        "These \"invisible variables\" include laboratory humidity, ambient light exposure, "
        "volatile organic compounds (VOCs), extremely low-frequency electromagnetic fields "
        "(ELF-EMF), barometric pressure, background ionizing radiation, water quality "
        "(endotoxins, total organic carbon), and vibration. Each of these exhibits "
        "characteristic seasonal variation influenced by latitude, with Northern and "
        "Southern Hemisphere patterns phase-inverted for solar-driven variables but "
        "synchronous for geomagnetic variables. The relative effect sizes remain to be "
        "determined."
    )
    run.font.size = Pt(10)

    # --- Section 4: The Uncontrolled Environmental Catalogue ---
    add_heading(doc, "A Catalogue of Uncontrolled Environmental Variables", level=2)

    # 4.1 Humidity
    add_heading(doc, "Humidity", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "A comprehensive environmental assessment of a Japanese cell-processing facility "
        "revealed that while temperature was maintained constant year-round, humidity in "
        "Grade B–D clean rooms tracked outdoor seasonal patterns, with peaks in summer "
        "and troughs in winter.{10} The study found significantly higher bacterial and "
        "fungal colony detection rates at humidity levels above 55%. Critically, the "
        "authors noted that humidity control equipment \"is expensive and usually not "
        "set up in academic institutions.\" Industry guidelines confirm that seasonal "
        "transitions—particularly the spring-to-summer period—substantially increase "
        "microbial contamination risk in cell culture.{11,12} For PSC differentiation "
        "protocols spanning 7–30 days, even brief contamination episodes can silently "
        "alter differentiation trajectories through inflammatory signaling (e.g., "
        "endotoxin-mediated NF-κB activation) long before overt contamination is detected."
    )

    # 4.2 VOCs
    add_heading(doc, "Volatile Organic Compounds", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Real-time monitoring of an IVF laboratory demonstrated that even low "
        "concentrations of volatile organic compounds (VOCs) were linearly associated "
        "with decreased early cleavage, decreased compaction, increased embryo asymmetry, "
        "and decreased trophectoderm quality.{13} Peak formaldehyde concentrations "
        "negatively predicted pregnancy rates in both fresh and frozen transfers. VOC "
        "concentrations peaked during working hours and fell at night and on weekends. "
        "Building materials, disinfectants, and HVAC systems are the primary sources of "
        "laboratory VOCs,{14} and their off-gassing rates are strongly temperature- and "
        "humidity-dependent, introducing a seasonal component that tracks both outdoor "
        "climate and indoor HVAC cycling patterns."
    )

    # 4.3 Photoperiod and light
    add_heading(doc, "Ambient Light and Photoperiod", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Although PSCs are cultured in darkened incubators, they are inevitably exposed "
        "to ambient light during media changes, passaging, and quality control "
        "assessments—operations that can cumulatively represent hours of light exposure "
        "over a multi-week differentiation protocol. Intriguingly, PSCs are uniquely "
        "\"time-uncoupled\": they lack functional circadian oscillations, which are "
        "gradually acquired during differentiation.{16,17} The clock gene CRY1 has been "
        "shown to positively regulate iPSC reprogramming efficiency through the "
        "SREBP1-CRY1 axis, while simultaneously suppressing differentiation programs "
        "including EMT and TGFβ signaling.{15} CRY proteins are photosensitive and "
        "function as magnetoreceptors via the radical-pair mechanism,{25,26} placing them "
        "at the intersection of light, magnetism, and stem cell fate."
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The photoperiod-stem cell connection extends in vivo. Melatonin, whose production "
        "is directly controlled by the light-dark cycle, has been shown to metabolically "
        "reprogram hematopoietic and mesenchymal stem cells nightly, maintaining the "
        "bone marrow stem cell reservoir.{18,19} A recent comprehensive review further "
        "documents the bidirectional crosstalk between clock components and Wnt, Notch, and "
        "Hedgehog pathways in stem cell niches.{33} Seasonal variation in melatonin production "
        "(longer dark periods in winter → more melatonin) could influence the baseline "
        "state of donor-derived somatic cells used for iPSC reprogramming, potentially "
        "explaining why the season of somatic cell collection—not the season of "
        "differentiation—may matter most, paralleling the IVF finding that oocyte "
        "retrieval season determines outcomes.{7}"
    )

    # 4.4 EMF
    add_heading(doc, "Electromagnetic Fields", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Extremely low-frequency electromagnetic fields (ELF-EMF) at 50/60 Hz—the "
        "frequency of power-line alternating current—have demonstrated effects on stem "
        "cell behavior. A 50 Hz, 5 mT field applied for 60 minutes daily over 12 days "
        "facilitated rat bone marrow stromal cell differentiation into functional neurons, "
        "increasing neuronal marker expression and shifting cell cycle distribution toward "
        "S phase.{22} More directly relevant, 50 Hz EMF exposure altered gene expression "
        "in mouse embryonic stem cells in a p53-dependent manner.{23} The electromagnetic "
        "environment of a cell culture laboratory is determined by HVAC compressors, "
        "centrifuges, freezers, and building electrical systems—all of which cycle "
        "seasonally with heating/cooling demands. The effect sizes reported in controlled "
        "EMF experiments (5 mT) far exceed typical laboratory exposures (0.1–10 μT), "
        "but chronic low-level exposure over multi-week differentiation protocols has "
        "not been systematically studied."
    )

    # 4.5 Cosmic radiation and geomagnetic
    add_heading(doc, "Background Radiation and Geomagnetic Activity", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "An unexpected correlation was reported between the proliferative activity of "
        "L-929 fibroblast cultures and fluctuations in secondary cosmic radiation "
        "intensity measured by neutron monitors.{20} The approximately 4-day rhythm in "
        "cell proliferation was exogenous and tracked cosmic ray fluctuations with "
        "negative correlation. Although the authors cautioned that the 5% amplitude of "
        "cosmic ray fluctuations makes a direct biophysical effect implausible, they "
        "suggested that an unmeasured environmental factor, for which cosmic ray intensity "
        "serves as a proxy, may be the true driver. The \"Cosmic Silence\" experiment at "
        "Gran Sasso National Laboratory demonstrated that human cells cultured under "
        "ultra-low background radiation for six months showed enhanced radiosensitivity, "
        "suggesting that environmental radiation acts as a conditioning agent for the "
        "cellular adaptive response.{21}"
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Geomagnetic disturbances, driven by solar activity, have been linked to "
        "alterations in inflammatory biomarkers through a proposed CRY-mediated "
        "pathway: geomagnetic fluctuations → CRY radical-pair mechanism → "
        "CLOCK/BMAL1 modulation → NF-κB signaling.{24,25} Unlike solar-driven "
        "variables, geomagnetic storms affect both hemispheres simultaneously, providing "
        "a natural experiment to distinguish solar/photoperiod effects (hemisphere-inverted) "
        "from geomagnetic effects (hemisphere-synchronous). Cosmic ray intensity also "
        "varies with the 11-year solar cycle, offering a longer-period modulation "
        "that could be tested against multi-year datasets of differentiation outcomes."
    )

    # 4.6 Barometric pressure
    add_heading(doc, "Barometric Pressure", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Elevated barometric pressure (2 atm) has been shown to suppress cell "
        "proliferation through G2/M phase delay, mediated by weakened integrin-dependent "
        "cell adhesion and actin assembly.{27} Natural barometric pressure fluctuations "
        "are considerably smaller (~3–5% around 1 atm) but exhibit strong seasonal "
        "patterns, particularly in monsoon regions and at mid-latitudes where weather "
        "systems are most variable. Whether these small fluctuations are biologically "
        "meaningful for cultured cells remains untested, but given that modern incubators "
        "are not pressure-sealed, cells are continuously exposed to atmospheric pressure "
        "transients."
    )

    # --- Section 5: Why PSCs may be uniquely vulnerable ---
    add_heading(doc, "Why Pluripotent Stem Cells May Be Uniquely Vulnerable", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Several features of PSC biology may render these cells disproportionately "
        "sensitive to environmental perturbation compared to terminally differentiated "
        "cell lines. First, PSCs exist in a metastable state between self-renewal and "
        "differentiation, where small shifts in signaling can tip the balance toward "
        "lineage commitment. Second, PSCs lack functional circadian clocks,{17} meaning "
        "they cannot buffer environmental light/dark cycles through internal homeostatic "
        "mechanisms—they are \"open-loop\" with respect to photoperiod signals. Third, "
        "the epigenetic landscape of PSCs is uniquely plastic, with bivalent chromatin "
        "marks poised for activation or repression; environmental perturbations that "
        "alter chromatin-modifying enzyme activity (e.g., through metabolic shifts induced "
        "by osmolarity changes from humidity-driven evaporation) could have outsized "
        "effects. Fourth, differentiation protocols are inherently multi-day processes, "
        "allowing small daily environmental biases to accumulate—a temporal integration "
        "effect that is absent in acute assays on established cell lines."
    )

    # --- Section 6: Northern vs Southern hemisphere ---
    add_heading(doc, "A Natural Experiment: Northern Versus Southern Hemispheres", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The phase inversion of solar-driven environmental variables between hemispheres "
        "offers a powerful natural experiment. If an uncontrolled environmental variable "
        "affects PSC differentiation, its seasonal pattern should be mirror-imaged between "
        "Northern (summer: June–August) and Southern (summer: December–February) Hemisphere "
        "laboratories. The IVF literature provides proof of concept: the Australian summer "
        "advantage in oocyte quality{7} mirrors Northern Hemisphere findings{8} with the "
        "expected six-month phase shift. Brazilian data from latitude 25°S confirm this "
        "pattern.{31}"
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "By contrast, geomagnetic disturbances are global events—a storm that perturbs "
        "CRY-mediated signaling{24} would do so simultaneously in Tokyo, Boston, and "
        "Melbourne. This asymmetry provides a diagnostic criterion: variables whose "
        "effects are hemisphere-inverted are likely driven by solar/photoperiod "
        "mechanisms, while those that are hemisphere-synchronous implicate geomagnetic "
        "or cosmic ray pathways. A coordinated multi-center study spanning both "
        "hemispheres—with continuous environmental monitoring—could decompose seasonal "
        "variation into these mechanistic categories."
    )

    # Figure 2 reference
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Figure 2 presents a research roadmap for systematic investigation, organized "
        "by the expected hemisphere-dependence of each variable and the existing level "
        "of evidence."
    )

    # Figure 2 placeholder
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("[FIGURE 2 PLACEHOLDER — see separate PPTX file]")
    run.bold = True
    run.font.color.rgb = RGBColor(150, 150, 150)
    set_paragraph_format(p, space_before=Pt(12), space_after=Pt(6))

    # Figure 2 legend
    p = doc.add_paragraph()
    set_paragraph_format(p, space_after=Pt(12))
    run = p.add_run(
        "Figure 2. Research roadmap for identifying and controlling environmental "
        "determinants of PSC differentiation. "
    )
    run.bold = True
    run.font.size = Pt(10)
    run = p.add_run(
        "(A) Evidence matrix classifying uncontrolled environmental variables by their "
        "expected hemisphere-dependence (inverted vs. synchronous) and current level of "
        "evidence (direct in PSC, indirect from IVF/cell culture, or theoretical). "
        "(B) Proposed three-phase investigation strategy: Phase I, passive environmental "
        "monitoring alongside routine differentiation experiments; Phase II, retrospective "
        "correlation analysis; Phase III, prospective controlled intervention studies. "
        "Data sources for each phase include in-house environmental logs, public IVF "
        "registries (HFEA, ANZARD, CDC ART), gene expression repositories (GEO, "
        "ArrayExpress), and iPSC biobank quality-control records (RIKEN BRC, Coriell, "
        "EBiSC)."
    )
    run.font.size = Pt(10)

    # --- Section 7: A Roadmap ---
    add_heading(doc, "Toward Systematic Environmental Profiling: A Research Roadmap", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "I propose a three-phase approach to move from anecdote to actionable evidence."
    )

    add_heading(doc, "Phase I: Passive Monitoring", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Equip PSC culture facilities with continuous, multi-parameter environmental "
        "sensors recording humidity, illuminance, ELF-EMF, barometric pressure, VOC "
        "levels, and vibration at 1-minute resolution. Modern IoT sensor packages can "
        "achieve this at modest cost (<$5,000 per laboratory). Record these data alongside "
        "routine differentiation outcomes (efficiency, marker expression, batch quality "
        "scores) for a minimum of 12 months to capture full seasonal cycles. The key "
        "principle is that monitoring imposes no change on existing workflows—it simply "
        "makes the invisible visible."
    )

    add_heading(doc, "Phase II: Retrospective Data Mining", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "In parallel, existing datasets can be interrogated for seasonal signals without "
        "new experiments. Public IVF registries (HFEA in the UK, ANZARD in Australia/New "
        "Zealand, CDC ART in the United States) contain date-stamped outcome data spanning "
        "decades, with latitude information implicit in clinic locations. Gene expression "
        "repositories (GEO, ArrayExpress) store iPSC differentiation datasets with "
        "submission dates that approximate experimental dates; quality metrics such as "
        "the variance in lineage-specific marker expression across samples could be "
        "modeled as a function of submission month. iPSC biobanks (RIKEN BRC, Coriell "
        "Institute, EBiSC) accumulate quality-control data that have never been analyzed "
        "for seasonal patterns.{30} These analyses require no wet-lab resources and could "
        "be initiated immediately by computational biologists."
    )

    add_heading(doc, "Phase III: Controlled Intervention", level=3)
    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "Variables identified in Phases I–II as significantly correlated with "
        "differentiation outcomes should be subjected to prospective, controlled "
        "experiments. For humidity, this could mean comparing differentiation efficiency "
        "in humidity-controlled (45 ± 2%) versus uncontrolled incubators over a full "
        "year. For photoperiod, light-tight hoods versus standard biosafety cabinets "
        "could isolate the effect of ambient light exposure during manipulations. For "
        "EMF, magnetic shielding (mu-metal enclosures) around incubators would test "
        "whether background electromagnetic fields contribute to outcome variability. "
        "Each intervention should be tested against the seasonal baseline established "
        "in Phase I to determine whether controlling the variable attenuates the "
        "seasonal signal."
    )

    # --- Section 8: Implications for cell therapy manufacturing ---
    add_heading(doc, "Implications for Cell Therapy Manufacturing", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "As PSC-derived cell therapies advance toward clinical application—with over "
        "115 clinical trials and 1,200 patients dosed as of 2024{28}—manufacturing "
        "consistency becomes a regulatory imperative. Current Good Manufacturing "
        "Practice (cGMP) facilities control temperature, humidity, and particulate "
        "counts, but do not routinely monitor illuminance, EMF, VOCs, or barometric "
        "pressure. If any of these variables meaningfully affect differentiation, "
        "current manufacturing may harbor hidden sources of batch-to-batch variability "
        "that are attributed to biological stochasticity but are in fact environmental "
        "and correctable. The economic argument is compelling: failed differentiation "
        "batches in autologous cell therapy represent not just lost reagents but lost "
        "patient tissue and treatment delays. Even a modest improvement in first-pass "
        "success rates through environmental optimization could translate into "
        "significant cost savings and faster patient access."
    )

    # --- Section 9: Conclusion ---
    add_heading(doc, "Conclusions", level=2)

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The history of experimental biology is punctuated by discoveries that \"noise\" "
        "was in fact signal from an unmeasured variable. Mendel's peas grew in a garden "
        "whose soil composition was uncontrolled; early bacteriology was transformed when "
        "Koch insisted on standardized media. The stem cell field may be at an analogous "
        "inflection point. We have spent two decades optimizing recipes—growth factors, "
        "small molecules, matrices, timing—while largely ignoring the kitchen. The "
        "convergence of evidence from IVF seasonality, circadian regulation of "
        "pluripotency, and environmental monitoring of cell-processing facilities "
        "suggests that the \"invisible variables\" are neither negligible nor intractable. "
        "They merely need to be measured."
    )

    p = doc.add_paragraph()
    set_paragraph_format(p, line_spacing=1.5)
    add_superscript_refs(p,
        "The path forward requires no technological breakthroughs—only the willingness "
        "to instrument our laboratories and analyze the resulting data. A coordinated "
        "international effort, spanning both hemispheres and coupling environmental "
        "monitoring with differentiation outcome tracking, could within a few years "
        "identify the key environmental variables that drive batch variability. "
        "Controlling them could do for stem cell biology what environmental control did "
        "for industrial baking: transform an unreliable artisanal craft into a "
        "reproducible, scalable technology."
    )

    # ──────────────────────────────────────────────
    # Acknowledgments
    # ──────────────────────────────────────────────
    add_heading(doc, "Acknowledgments", level=2)
    p = doc.add_paragraph()
    run = p.add_run("[To be added]")
    run.italic = True
    set_paragraph_format(p, line_spacing=1.5)

    # ──────────────────────────────────────────────
    # Declaration of interests
    # ──────────────────────────────────────────────
    add_heading(doc, "Declaration of Interests", level=2)
    p = doc.add_paragraph()
    run = p.add_run("The author declares no competing interests.")
    set_paragraph_format(p, line_spacing=1.5)

    # ──────────────────────────────────────────────
    # References
    # ──────────────────────────────────────────────
    doc.add_page_break()
    add_heading(doc, "References", level=2)

    for i, ref in enumerate(REFERENCES, 1):
        p = doc.add_paragraph()
        set_paragraph_format(p, space_after=Pt(3), line_spacing=1.15)
        run = p.add_run(f"{i}. ")
        run.bold = True
        run.font.size = Pt(9)
        run = p.add_run(ref)
        run.font.size = Pt(9)

    # ──────────────────────────────────────────────
    # Save
    # ──────────────────────────────────────────────
    out_path = os.path.join(OUTPUT_DIR, "CellStemCell_Perspective_InvisibleVariables.docx")
    doc.save(out_path)
    print(f"Manuscript saved to: {out_path}")

    # Word count estimate
    word_count = 0
    for para in doc.paragraphs:
        word_count += len(para.text.split())
    print(f"Approximate word count (all text): {word_count}")

    return out_path


if __name__ == "__main__":
    create_manuscript()
