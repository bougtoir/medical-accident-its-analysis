#!/usr/bin/env python3
"""Generate cover letter docx for EEH submission."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUTPUT = Path(__file__).parent / "cover_letter.docx"


def main():
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.line_spacing = 1.5

    # Date
    p = doc.add_paragraph()
    p.add_run("[Date]")
    doc.add_paragraph()

    # Addressee
    p = doc.add_paragraph()
    p.add_run("The Editors")
    p = doc.add_paragraph()
    run = p.add_run("Explorations in Economic History")
    run.italic = True
    doc.add_paragraph()

    # Opening
    p = doc.add_paragraph("Dear Editors,")
    doc.add_paragraph()

    # Body
    paras = [
        'I am pleased to submit the manuscript entitled "Network Exclusion and State Collapse: '
        'From Maritime Isolation to Technological Access Denial in the Long Run of History" for '
        'consideration by Explorations in Economic History.',

        'Using a comparative dataset of 96 historical polities spanning antiquity to the present, '
        'we distinguish between deliberate closure (policy-based trade bans, sakoku, bloc membership) '
        'and what we term "technical network exclusion": involuntary disconnection from the dominant '
        'exchange network of an era due to geographic or technological constraints. The manuscript '
        'presents four features that we believe are of interest to the journal\'s readership.',

        'First, a systematic sensitivity analysis demonstrates that reclassifying seven technically '
        'excluded polities transforms a non-significant association between closure and conquest '
        '(Fisher\'s exact p = 0.187) into a significant one (p = 0.020), while the core stock–flow '
        'odds ratio remains stable (OR = 1.774).',

        'Second, we analyze conditional closure—cases where polities maintained selective technology '
        'channels while restricting broader trade. Examples include Tokugawa Japan\'s rangaku through '
        'Dejima, Qing China\'s Canton system, Joseon Korea\'s tributary trade, and the Soviet Union\'s '
        'bloc-internal technology sharing. The mixed outcomes of these cases suggest that the open/closed '
        'dichotomy is insufficient; the conditions under which selective channels mitigate technology gaps '
        'merit further investigation.',

        'Third, the dose–response gradient across closure types—technical exclusion (100% conquest) > '
        'policy bans > sakoku (with partial conduit) > bloc > open—points to technology flow disruption, '
        'rather than trade restriction per se, as the critical mechanism.',

        'Fourth, the mechanism generalizes beyond geographic isolation: as the dominant network shifts '
        'from sea lanes to semiconductors, AI, and advanced robotics, states structurally excluded from '
        'these platforms may face analogous vulnerabilities.',

        'We probe the closure–conquest association with four causal identification strategies—instrumental '
        'variables, propensity score matching, a natural experiment framing, and a robustness battery '
        'including E-values, permutation tests, and leave-one-out analysis. The strongest evidence comes '
        'from the natural experiment approach: technically excluded polities show a 100% conquest rate '
        'compared with 62.3% for open polities (Fisher\'s exact p = 0.048), with no significant '
        'differences in observable covariates.',

        'The manuscript contains approximately 7,000 words, 5 tables, and 4 figures. Supplementary '
        'Table S1 provides the complete dataset. We confirm that this work has not been published or '
        'submitted elsewhere.',

        'We suggest the following reviewers based on their expertise in quantitative economic history:',
    ]

    for text in paras:
        doc.add_paragraph(text)

    # Reviewer list
    reviewers = [
        'Prof. Jörg Baten (University of Tübingen) — cliometric methods and long-run development',
        'Prof. Stephen Broadberry (University of Oxford) — comparative economic history and GDP estimation',
        'Prof. Nathan Nunn (University of British Columbia) — long-run persistence and historical institutions',
    ]
    for r in reviewers:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1.27)
        p.add_run(f"• {r}")

    doc.add_paragraph()

    # Closing
    doc.add_paragraph("Sincerely,")
    doc.add_paragraph()
    doc.add_paragraph("[Author Name]")
    doc.add_paragraph("[Affiliation]")
    doc.add_paragraph("[Email]")

    doc.save(str(OUTPUT))
    print(f"Saved: {OUTPUT}")


if __name__ == '__main__':
    main()
