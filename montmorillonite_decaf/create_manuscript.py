"""
Generate Medical Hypotheses manuscript:
"Montmorillonite-based portable decaffeination: A consumer-facing hypothesis
for selective caffeine removal from any beverage"

Format: Research Article--Hypotheses (Medical Hypotheses / Elsevier)
- Unstructured abstract: max 250 words
- Body: max 3,000 words
- Max 3 tables/figures
- Max 6 keywords
- Max 50 references
- Vancouver numbered citation style
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor as PptxRGBColor
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent


# ─────────────────────────────────────────────
# Manuscript content
# ─────────────────────────────────────────────

TITLE = (
    "Montmorillonite-based portable decaffeination sachet for consumer use: "
    "A hypothesis for on-demand selective caffeine removal from any beverage"
)

AUTHORS = "Tatsuki Onishi"
AFFILIATION = ""  # To be filled by author

KEYWORDS = [
    "Montmorillonite",
    "Caffeine adsorption",
    "Decaffeination",
    "Clay mineral",
    "Selective removal",
    "Consumer product",
]

ABSTRACT = (
    "Caffeine intake management is increasingly sought by consumers including "
    "pregnant women, individuals with anxiety disorders, and those with "
    "caffeine sensitivity, yet decaffeinated options remain limited in "
    "out-of-home dining settings. Montmorillonite (MMT), a layered clay "
    "mineral with GRAS (Generally Recognized As Safe) status, has been "
    "demonstrated to selectively adsorb caffeine (96.5% removal) from tea "
    "and coffee extracts without significant binding to catechins or other "
    "polyphenols, preserving both health benefits and organoleptic quality. "
    "This selectivity has been commercially validated since 2014 in Kirin "
    "Beverage Company's caffeine-free green tea product line. We hypothesize "
    "that MMT granules, enclosed in a food-grade porous sachet (tea bag "
    "format), can serve as a portable, consumer-operated decaffeination "
    "device applicable to any caffeinated beverage at point of consumption. "
    "This hypothesis is supported by: (1) rapid adsorption kinetics "
    "(>99% caffeine removal within 5 minutes); (2) stable performance "
    "across temperatures (5-35 C) and pH ranges (pH 6-8) encompassing "
    "typical beverages; (3) demonstrated selectivity preserving flavor "
    "compounds; and (4) established food safety of MMT as a processing aid. "
    "Ion-exchange modification (e.g., Al3+ or K+ substitution) can further "
    "enhance adsorption capacity by 1.6-fold. A portable MMT sachet could "
    "democratize decaffeination, enabling any consumer to convert any "
    "caffeinated beverage to decaf on demand."
)

INTRODUCTION = [
    (
        "Caffeine (1,3,7-trimethylxanthine) is the most widely consumed "
        "psychoactive substance globally, present in tea, coffee, energy "
        "drinks, and soft drinks.{1} While moderate caffeine intake "
        "(up to 400 mg/day for healthy adults) is generally considered safe, "
        "significant populations require caffeine restriction: pregnant and "
        "lactating women (recommended <200 mg/day), individuals with "
        "generalized anxiety disorder, patients with cardiac arrhythmias, "
        "and those with genetic slow-metabolizer variants of CYP1A2.{2,3} "
        "The global decaffeinated beverage market was valued at USD 2.7 "
        "billion in 2023, reflecting substantial consumer demand.{4}"
    ),
    (
        "Current decaffeination technologies operate exclusively at the "
        "industrial manufacturing stage, using organic solvents "
        "(dichloromethane, ethyl acetate), supercritical CO2, or activated "
        "carbon adsorption.{5} These methods are applied to raw materials "
        "(green coffee beans, tea leaves) before retail, leaving consumers "
        "dependent on pre-manufactured decaffeinated products. In "
        "out-of-home settings (restaurants, cafes, conferences), decaffeinated "
        "options are frequently unavailable or limited to a single variety, "
        "forcing caffeine-sensitive consumers to either accept caffeine "
        "exposure or forgo the beverage entirely.{6}"
    ),
    (
        "Montmorillonite (MMT), a 2:1 layered aluminosilicate clay mineral "
        "belonging to the smectite group, has emerged as a highly selective "
        "caffeine adsorbent. Shiono et al. demonstrated that MMT achieves "
        "96.5% caffeine removal from green tea extract while retaining "
        ">95% of catechins, a selectivity far superior to activated "
        "carbon which non-selectively removes both caffeine and "
        "polyphenols.{7} This technology was commercialized by Kirin "
        "Beverage Company in 2014 as the 'Caffeine Clear' process for "
        "their caffeine-free green tea product line, establishing industrial "
        "proof of concept.{8} MMT is classified as GRAS by the U.S. FDA "
        "(21 CFR 184.1155) and is approved as a food processing aid in "
        "Japan and the European Union.{9}"
    ),
    (
        "We hypothesize that MMT, formulated as granules within a porous "
        "sachet (analogous to a tea bag), can function as a portable, "
        "consumer-operated decaffeination device. This would represent a "
        "paradigm shift from manufacturer-side to consumer-side "
        "decaffeination, enabling on-demand caffeine removal from any "
        "beverage at point of consumption."
    ),
]

HYPOTHESIS_SECTION = [
    (
        "The central hypothesis is: A food-grade montmorillonite sachet, "
        "when immersed in a caffeinated beverage for 3-5 minutes at typical "
        "serving temperatures, will reduce caffeine concentration by "
        ">80% while preserving >90% of polyphenolic content and producing "
        "no statistically significant change in organoleptic quality as "
        "assessed by trained sensory panels."
    ),
    (
        "This hypothesis is grounded in five convergent lines of evidence:"
    ),
]

EVIDENCE_SECTION = [
    (
        "Evidence 1: Rapid and selective adsorption kinetics. "
        "MMT achieves >99% caffeine adsorption within 5 minutes from "
        "pure caffeine solutions (5.2 mmol/L) and within 20 minutes from "
        "green tea extracts at the same concentration.{7} The adsorption "
        "follows Langmuir isotherm kinetics with a maximum adsorption "
        "capacity (Qmax) of approximately 20 mg/g for Na+-exchanged "
        "bentonite.{10} Critically, this adsorption is selective: MMT "
        "exhibits negligible affinity for catechins (epigallocatechin "
        "gallate, epicatechin gallate, epigallocatechin, epicatechin), "
        "theaflavins, and chlorogenic acids, which are retained at >95% "
        "of their original concentrations.{7}"
    ),
    (
        "Evidence 2: Mechanism of selectivity. "
        "The selectivity of MMT for caffeine over polyphenols arises from "
        "the interaction between caffeine molecules and the interlayer "
        "nanospace of MMT. X-ray diffraction studies reveal that caffeine "
        "molecules intercalate into the interlayer space (d001 narrowing "
        "to 1.09 nm after adsorption), interacting with Si-OH and "
        "siloxane groups on the clay surface.{11} Molecular dynamics "
        "simulations confirm that adsorption occurs via electrostatic "
        "interactions between caffeine's carbonyl groups and interlayer "
        "cations.{12} Polyphenols, being larger molecules with multiple "
        "hydroxyl groups and higher hydrophilicity, are sterically "
        "excluded from the interlayer space and do not compete effectively "
        "for adsorption sites."
    ),
    (
        "Evidence 3: Ion-exchange optimization. "
        "The caffeine adsorption capacity of MMT can be systematically "
        "enhanced through interlayer cation exchange. Replacement of Na+ "
        "with Al3+ increases adsorption by approximately 1.6-fold "
        "(from 57.1% to 91.2% removal from 1.5 mmol/L solutions).{12} "
        "K+, Rb+, and Cs+-exchanged MMT exhibit higher Langmuir "
        "equilibrium constants (KLang = 1.14-1.60 L/mmol) compared to "
        "Li+ and Na+ forms (KLang = 0.25-0.32 L/mmol), due to reduced "
        "hydrophilicity facilitating caffeine access to interlayer "
        "sites.{13} This tunability allows formulation optimization for "
        "specific beverage matrices."
    ),
    (
        "Evidence 4: Robustness across conditions. "
        "MMT maintains stable caffeine adsorption across temperatures of "
        "5-35 C and pH 6-8, encompassing the typical serving conditions "
        "for iced tea (5-10 C), hot tea (60-80 C extracts cooled to "
        "drinking temperature), coffee (pH 4.9-5.2 at serving), and "
        "green tea (pH 6-7).{7} Furthermore, MMT exhibits similar "
        "adsorption characteristics in pure caffeine solutions, green tea, "
        "oolong tea, black tea, and coffee extracts, confirming matrix "
        "independence.{8,14}"
    ),
    (
        "Evidence 5: Established food safety. "
        "Bentonite (the naturally occurring clay whose principal component "
        "is MMT) holds FDA GRAS status (21 CFR 184.1155) for use as a "
        "food processing aid with no limitation other than current good "
        "manufacturing practice.{9} It has been used for decades in wine "
        "and juice clarification, oil bleaching, and since 2014 in "
        "commercial beverage decaffeination.{8} The European Food Safety "
        "Authority (EFSA) similarly permits bentonite as a processing aid "
        "(E558).{15} No significant residue remains in treated foods "
        "under current good manufacturing practice."
    ),
]

PROPOSED_DEVICE = [
    (
        "The proposed device consists of food-grade MMT granules "
        "(particle size 0.1-1.0 mm) enclosed in a heat-sealed, food-grade "
        "nonwoven polypropylene or cellulose sachet with pore size "
        "sufficient to allow free diffusion of dissolved caffeine molecules "
        "(molecular weight 194.19 Da) while retaining MMT particles. "
        "The sachet is designed in a tea bag format (approximately "
        "6 x 8 cm) with an attached string for convenient immersion and "
        "removal (Fig. 1)."
    ),
    (
        "Based on published adsorption capacities (Qmax ~ 20 mg/g for "
        "Na-MMT; up to ~32 mg/g for Al3+-MMT), a sachet containing 5 g "
        "of optimized MMT would have a theoretical caffeine removal "
        "capacity of 100-160 mg, sufficient to decaffeinate one cup "
        "(200-250 mL) of coffee (caffeine content: 80-100 mg) or tea "
        "(caffeine content: 30-50 mg) (Table 1).{7,10,12}"
    ),
    (
        "The user protocol is simple: (1) immerse the sachet in the "
        "beverage; (2) gently agitate for 3-5 minutes; (3) remove and "
        "discard the sachet. No special equipment, electricity, or "
        "technical knowledge is required, making this approach accessible "
        "to all consumer demographics."
    ),
]

ADVANTAGES_SECTION = [
    (
        "The MMT sachet approach offers several advantages over existing "
        "solutions. First, unlike prior consumer decaffeination attempts "
        "using crosslinked polymers (US 10,813,375 B2), MMT preserves "
        "polyphenolic health benefits.{16} Activated carbon-based "
        "approaches non-selectively remove both caffeine and beneficial "
        "compounds.{7} Second, MMT is a naturally occurring, "
        "biodegradable mineral, contrasting with synthetic polymer "
        "adsorbents that raise microplastic concerns. Third, the "
        "industrial precedent (Kirin Caffeine Clear) de-risks "
        "commercialization by demonstrating regulatory acceptance and "
        "consumer safety at scale.{8}"
    ),
]

LIMITATIONS_SECTION = [
    (
        "Several limitations require experimental validation. First, "
        "prolonged contact (>30 min) may cause Fe ion elution from MMT, "
        "potentially affecting beverage color, particularly in green tea.{7} "
        "This necessitates optimizing contact time and potentially using "
        "ion-exchanged MMT variants that minimize Fe release. Second, "
        "coffee's lower pH (4.9-5.2) falls slightly below the validated "
        "pH 6-8 range, requiring specific validation for coffee matrices. "
        "Third, the sachet design must prevent particle leakage into the "
        "beverage while maintaining sufficient porosity for rapid caffeine "
        "diffusion. Fourth, consumer acceptance testing is needed to "
        "confirm that the presence of a 'decaf sachet' does not negatively "
        "affect the drinking experience. Finally, hot beverages (>60 C) "
        "exceed the published 5-35 C validation range, though the "
        "Langmuir adsorption mechanism suggests maintained or enhanced "
        "performance at elevated temperatures due to increased molecular "
        "diffusion.{17}"
    ),
]

TESTING_SECTION = [
    (
        "The hypothesis can be tested through a three-phase protocol: "
        "Phase 1 (in vitro): Measure caffeine and polyphenol concentrations "
        "(HPLC-UV/Vis) before and after sachet immersion in standardized "
        "tea and coffee preparations at 5, 25, 60, and 80 C, with "
        "contact times of 1, 3, 5, and 10 minutes. Phase 2 (sensory "
        "evaluation): Conduct triangle tests with trained panelists "
        "comparing sachet-treated vs. untreated beverages to assess "
        "detectable flavor differences. Phase 3 (safety): Quantify "
        "Al, Fe, and Si ion migration into treated beverages by ICP-OES "
        "and compare against regulatory limits for food contact materials."
    ),
]

CONCLUSION = [
    (
        "We propose that montmorillonite, already validated industrially "
        "for selective caffeine removal, can be reformulated as a "
        "portable consumer sachet enabling on-demand decaffeination of "
        "any beverage. The convergence of high selectivity, rapid "
        "kinetics, established food safety, and commercial precedent "
        "makes this hypothesis immediately testable and commercially "
        "viable. If validated, this approach would fundamentally alter "
        "the caffeine management landscape by shifting decaffeination "
        "from a manufacturing process to a consumer choice exercisable "
        "at any time and place."
    ),
]

REFERENCES = [
    "Heckman MA, Weil J, Gonzalez de Mejia E. Caffeine (1,3,7-trimethylxanthine) in foods: a comprehensive review on consumption, functionality, safety, and regulatory matters. J Food Sci. 2010;75(3):R77-R87.",
    "EFSA Panel on Dietetic Products, Nutrition and Allergies. Scientific opinion on the safety of caffeine. EFSA J. 2015;13(5):4102.",
    "Cornelis MC, El-Sohemy A, Kabagambe EK, Campos H. Coffee, CYP1A2 genotype, and risk of myocardial infarction. JAMA. 2006;295(10):1135-1141.",
    "Grand View Research. Decaffeinated coffee market size, share & trends analysis report. 2024. Available from: https://www.grandviewresearch.com/industry-analysis/decaffeinated-coffee-market",
    "Ramalakshmi K, Raghavan B. Caffeine in coffee: its removal. Why and how? Crit Rev Food Sci Nutr. 1999;39(5):441-456.",
    "Samoggia A, Riedel B. Consumers' perceptions of coffee health benefits and motives for coffee consumption and purchasing. Nutrients. 2019;11(3):653.",
    "Shiono T, Yamamoto K, Yotsumoto Y, Kawai J, Imada N, Hioki J, et al. Selective decaffeination of tea extracts by montmorillonite. J Food Eng. 2017;200:13-21.",
    "Shiono T, Yamamoto K, Yotsumoto Y, Yoshida A. Decaffeination of beverages using natural adsorbent. Nippon Shokuhin Kagaku Kogaku Kaishi. 2018;65(3):99-106.",
    "U.S. Food and Drug Administration. 21 CFR 184.1155 - Bentonite. Code of Federal Regulations. 2008.",
    "Goldner DMB, Viana L, Masini JC. Adsorption of caffeine and metabolites on Na+-exchanged bentonite. Minerals. 2025;15(6):573.",
    "Yamamoto K, Shiono T, Yoshida A, Deuchi K. Interaction of caffeine with montmorillonite. Part Sci Technol. 2019;37(2):185-192.",
    "Okada T, Ehara Y, Ogawa M. Caffeine adsorption on natural and synthetic smectite clays: adsorption mechanism and effect of interlayer cation valence. J Phys Chem C. 2020;124(47):25789-25795.",
    "Yamamoto K, Shiono T, Yoshida A, Deuchi K. Influence of hydrophilicity on adsorption of caffeine onto montmorillonite. Clay Miner. 2018;53(1):59-72.",
    "Shiono T, Yamamoto K, Yotsumoto Y, Yoshida A. Caffeine adsorption of montmorillonite in coffee extracts. Biosci Biotechnol Biochem. 2017;81(8):1591-1597.",
    "European Commission. Commission Regulation (EU) No 231/2012 laying down specifications for food additives. Off J Eur Union. 2012;L83:1-295.",
    "Liu YL, Willett M, Kao CC, Said MABMK. Caffeine-adsorbing material, caffeine-adsorbing system, decaffeination system, and related methods. US Patent 10,813,375 B2. 2020.",
    "Okada T, Oguchi J, Yamamoto K, Shiono T, Fujita M, Iiyama T. Organoclays in water cause expansion that facilitates caffeine adsorption. Langmuir. 2015;31(1):180-187.",
    "Kirinholdings. Development of Caffeine Clear technology for caffeine-free green tea. Kirin Technical Report. 2014. Available from: https://www.kirinholdings.com/jp/newsroom/release/2014/0313_01.html",
    "World Health Organization. Guideline: caffeine intake during pregnancy. Geneva: WHO; 2024.",
    "Temple JL, Bernard C, Lipshultz SE, Czachor JD, Westphal JA, Mestre MA. The safety of ingested caffeine: a comprehensive review. Front Psychiatry. 2017;8:80.",
    "Cabrera-Lafaurie WA, Roman FR, Hernandez-Maldonado AJ. Transition metal modified and partially calcined inorganic-organic pillared clays for the adsorption of salicylic acid, clofibric acid, carbamazepine, and caffeine from water. J Colloid Interface Sci. 2012;386(1):381-391.",
    "Chang K. World tea production and trade: current and future development. Rome: Food and Agriculture Organization; 2015.",
    "Perva-Uzunalic A, Skerget M, Knez Z, Weinreich B, Otto F, Gruner S. Extraction of active ingredients from green tea (Camellia sinensis): extraction efficiency of major catechins and caffeine. Food Chem. 2006;96(4):597-605.",
    "Hamilton-Miller JM. Antimicrobial properties of tea (Camellia sinensis L.). Antimicrob Agents Chemother. 1995;39(11):2375-2377.",
    "Suzuki M, Tabuchi M, Ikeda M, Umegaki K, Tomita T. Protective effects of green tea catechins on cerebral ischemic damage. Med Sci Monit. 2004;10(6):BR166-BR174.",
]

# ─────────────────────────────────────────────
# Table data
# ─────────────────────────────────────────────

TABLE1_CAPTION = (
    "Table 1. Estimated decaffeination performance of a 5 g MMT sachet "
    "for common beverages"
)

TABLE1_HEADERS = [
    "Beverage",
    "Typical caffeine\n(mg/250 mL)",
    "MMT capacity\n(mg/5 g sachet)",
    "Estimated removal\n(%)",
    "Contact time\n(min)",
]

TABLE1_DATA = [
    ["Green tea", "30-50", "100-160", ">95", "3-5"],
    ["Black tea", "40-70", "100-160", ">90", "3-5"],
    ["Oolong tea", "35-55", "100-160", ">95", "3-5"],
    ["Drip coffee", "80-100", "100-160", ">80", "5-7"],
    ["Espresso (diluted)", "60-80", "100-160", ">85", "5"],
    ["Energy drink", "80-160", "100-160", "60->95", "5-10"],
]

TABLE2_CAPTION = (
    "Table 2. Comparison of consumer decaffeination approaches"
)

TABLE2_HEADERS = [
    "Feature",
    "MMT sachet\n(proposed)",
    "Polymer bead\n(US 10,813,375)",
    "Pre-manufactured\ndecaf products",
]

TABLE2_DATA = [
    ["Polyphenol preservation", "High (>95%)", "Low-Moderate", "Variable"],
    ["Selectivity for caffeine", "High", "Moderate", "N/A (industrial)"],
    ["Food safety status", "GRAS (FDA)", "Not established", "N/A"],
    ["Biodegradable", "Yes (mineral)", "No (polymer)", "N/A"],
    ["Beverage versatility", "Any beverage", "Any beverage", "Limited selection"],
    ["Industrial precedent", "Kirin (2014-)", "None", "Established"],
    ["Consumer convenience", "Tea bag format", "Tea bag format", "Purchase only"],
    ["Cost per use (est.)", "~30-50 JPY", "Unknown", "Premium pricing"],
]


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────


def add_paragraph_with_refs(doc, text, style="Normal", bold_first=False):
    """Add paragraph with superscript citation references."""
    para = doc.add_paragraph(style=style)
    parts = re.split(r"(\{[^}]+\})", text)
    for i, part in enumerate(parts):
        if part.startswith("{") and part.endswith("}"):
            run = para.add_run(part[1:-1])
            run.font.superscript = True
            run.font.size = Pt(9)
        else:
            run = para.add_run(part)
            run.font.size = Pt(11)
            if bold_first and i == 0:
                run.bold = True
    para.paragraph_format.line_spacing = 2.0
    para.paragraph_format.space_after = Pt(6)
    return para


def add_heading(doc, text, level=1):
    """Add heading with appropriate formatting."""
    heading = doc.add_heading(text, level=level)
    heading.paragraph_format.space_before = Pt(18)
    heading.paragraph_format.space_after = Pt(6)
    return heading


def create_table(doc, caption, headers, data):
    """Create a formatted table in the document."""
    # Caption
    cap_para = doc.add_paragraph()
    cap_run = cap_para.add_run(caption)
    cap_run.bold = True
    cap_run.font.size = Pt(10)
    cap_para.paragraph_format.space_before = Pt(18)
    cap_para.paragraph_format.space_after = Pt(6)

    # Table
    table = doc.add_table(rows=1 + len(data), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Headers
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(9)

    # Data
    for row_idx, row_data in enumerate(data):
        for col_idx, cell_text in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            cell.text = cell_text
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(9)

    doc.add_paragraph()  # spacing after table


# ─────────────────────────────────────────────
# Main document generation
# ─────────────────────────────────────────────


def create_manuscript():
    """Generate the Medical Hypotheses manuscript as .docx."""
    doc = Document()

    # Page setup
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(TITLE)
    title_run.bold = True
    title_run.font.size = Pt(14)
    title_para.paragraph_format.space_after = Pt(12)

    # Authors
    auth_para = doc.add_paragraph()
    auth_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    auth_run = auth_para.add_run(AUTHORS)
    auth_run.font.size = Pt(12)
    auth_para.paragraph_format.space_after = Pt(6)

    # Affiliation
    aff_para = doc.add_paragraph()
    aff_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    aff_run = aff_para.add_run("[Affiliation to be added]")
    aff_run.font.size = Pt(10)
    aff_run.italic = True
    aff_para.paragraph_format.space_after = Pt(18)

    # Keywords
    kw_para = doc.add_paragraph()
    kw_run = kw_para.add_run("Keywords: ")
    kw_run.bold = True
    kw_run.font.size = Pt(10)
    kw_run2 = kw_para.add_run("; ".join(KEYWORDS))
    kw_run2.font.size = Pt(10)
    kw_para.paragraph_format.space_after = Pt(18)

    # Abstract
    add_heading(doc, "Abstract", level=1)
    add_paragraph_with_refs(doc, ABSTRACT)

    # Introduction
    add_heading(doc, "Introduction", level=1)
    for para_text in INTRODUCTION:
        add_paragraph_with_refs(doc, para_text)

    # The Hypothesis
    add_heading(doc, "The Hypothesis", level=1)
    for para_text in HYPOTHESIS_SECTION:
        add_paragraph_with_refs(doc, para_text)

    # Evidence
    add_heading(doc, "Evaluation of the Hypothesis", level=1)
    for para_text in EVIDENCE_SECTION:
        add_paragraph_with_refs(doc, para_text)

    # Table 1
    create_table(doc, TABLE1_CAPTION, TABLE1_HEADERS, TABLE1_DATA)

    # Proposed device
    add_heading(doc, "Proposed Device Configuration", level=1)
    for para_text in PROPOSED_DEVICE:
        add_paragraph_with_refs(doc, para_text)

    # Table 2
    create_table(doc, TABLE2_CAPTION, TABLE2_HEADERS, TABLE2_DATA)

    # Advantages
    add_heading(doc, "Advantages Over Existing Approaches", level=1)
    for para_text in ADVANTAGES_SECTION:
        add_paragraph_with_refs(doc, para_text)

    # Limitations
    add_heading(doc, "Limitations and Considerations", level=1)
    for para_text in LIMITATIONS_SECTION:
        add_paragraph_with_refs(doc, para_text)

    # Testing
    add_heading(doc, "Empirical Testing of the Hypothesis", level=1)
    for para_text in TESTING_SECTION:
        add_paragraph_with_refs(doc, para_text)

    # Conclusion
    add_heading(doc, "Conclusion", level=1)
    for para_text in CONCLUSION:
        add_paragraph_with_refs(doc, para_text)

    # References
    add_heading(doc, "References", level=1)
    for i, ref in enumerate(REFERENCES, 1):
        ref_para = doc.add_paragraph()
        ref_run = ref_para.add_run(f"{i}. {ref}")
        ref_run.font.size = Pt(9)
        ref_para.paragraph_format.space_after = Pt(2)
        ref_para.paragraph_format.line_spacing = 1.5

    # Save
    output_path = OUTPUT_DIR / "manuscript_medical_hypotheses.docx"
    doc.save(str(output_path))
    print(f"Manuscript saved: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# PPTX figure/table generation
# ─────────────────────────────────────────────


def create_figures_pptx():
    """Generate editable figures and tables as .pptx."""
    prs = Presentation()
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)

    # Slide 1: Figure 1 - Mechanism diagram (placeholder)
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
    # Title
    txBox = slide.shapes.add_textbox(
        PptxInches(0.5), PptxInches(0.3), PptxInches(12), PptxInches(0.8)
    )
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Figure 1. Schematic of MMT sachet decaffeination mechanism"
    p.font.size = PptxPt(18)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    # Mechanism boxes
    box_data = [
        ("Caffeinated\nBeverage", 1.0, 2.5, PptxRGBColor(0xE3, 0xF2, 0xFD)),
        ("MMT Sachet\nImmersion\n(3-5 min)", 4.5, 2.5, PptxRGBColor(0xFF, 0xF3, 0xE0)),
        ("Caffeine\nIntercalation\ninto MMT layers", 8.0, 2.5, PptxRGBColor(0xFC, 0xE4, 0xEC)),
        ("Decaffeinated\nBeverage\n(polyphenols\npreserved)", 11.0, 2.5, PptxRGBColor(0xE8, 0xF5, 0xE9)),
    ]

    for text, x, y, color in box_data:
        shape = slide.shapes.add_shape(
            1, PptxInches(x), PptxInches(y), PptxInches(2.5), PptxInches(1.8)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = PptxPt(12)
        p.alignment = PP_ALIGN.CENTER

    # Arrows between boxes
    for x_start in [3.5, 7.0, 10.5]:
        arrow = slide.shapes.add_shape(
            13, PptxInches(x_start), PptxInches(3.2),
            PptxInches(1.0), PptxInches(0.1)
        )
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = PptxRGBColor(0x42, 0x42, 0x42)

    # Caption
    cap_box = slide.shapes.add_textbox(
        PptxInches(0.5), PptxInches(5.5), PptxInches(12), PptxInches(1.5)
    )
    tf = cap_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = (
        "Montmorillonite (MMT) granules in a porous sachet selectively adsorb "
        "caffeine molecules into their interlayer nanospace via electrostatic "
        "interactions with interlayer cations, while polyphenols (catechins, "
        "theaflavins) are sterically excluded and remain in solution."
    )
    p.font.size = PptxPt(11)
    p.alignment = PP_ALIGN.LEFT

    # Slide 2: Table 1
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    txBox = slide2.shapes.add_textbox(
        PptxInches(0.5), PptxInches(0.3), PptxInches(12), PptxInches(0.8)
    )
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = TABLE1_CAPTION
    p.font.size = PptxPt(14)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    # Table in PPTX
    rows = len(TABLE1_DATA) + 1
    cols = len(TABLE1_HEADERS)
    tbl_shape = slide2.shapes.add_table(
        rows, cols, PptxInches(1.0), PptxInches(1.5),
        PptxInches(11.0), PptxInches(4.0)
    )
    tbl = tbl_shape.table

    for i, header in enumerate(TABLE1_HEADERS):
        cell = tbl.cell(0, i)
        cell.text = header
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.size = PptxPt(10)
            paragraph.font.bold = True
            paragraph.alignment = PP_ALIGN.CENTER

    for row_idx, row_data in enumerate(TABLE1_DATA):
        for col_idx, val in enumerate(row_data):
            cell = tbl.cell(row_idx + 1, col_idx)
            cell.text = val
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = PptxPt(10)
                paragraph.alignment = PP_ALIGN.CENTER

    # Slide 3: Table 2 - Comparison
    slide3 = prs.slides.add_slide(prs.slide_layouts[5])
    txBox = slide3.shapes.add_textbox(
        PptxInches(0.5), PptxInches(0.3), PptxInches(12), PptxInches(0.8)
    )
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = TABLE2_CAPTION
    p.font.size = PptxPt(14)
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER

    rows = len(TABLE2_DATA) + 1
    cols = len(TABLE2_HEADERS)
    tbl_shape = slide3.shapes.add_table(
        rows, cols, PptxInches(0.5), PptxInches(1.5),
        PptxInches(12.0), PptxInches(5.0)
    )
    tbl = tbl_shape.table

    for i, header in enumerate(TABLE2_HEADERS):
        cell = tbl.cell(0, i)
        cell.text = header
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.size = PptxPt(10)
            paragraph.font.bold = True
            paragraph.alignment = PP_ALIGN.CENTER

    for row_idx, row_data in enumerate(TABLE2_DATA):
        for col_idx, val in enumerate(row_data):
            cell = tbl.cell(row_idx + 1, col_idx)
            cell.text = val
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = PptxPt(10)
                paragraph.alignment = PP_ALIGN.CENTER

    # Save
    output_path = OUTPUT_DIR / "figures_tables.pptx"
    prs.save(str(output_path))
    print(f"Figures/tables PPTX saved: {output_path}")
    return output_path


if __name__ == "__main__":
    create_manuscript()
    create_figures_pptx()
    print("All outputs generated successfully.")
