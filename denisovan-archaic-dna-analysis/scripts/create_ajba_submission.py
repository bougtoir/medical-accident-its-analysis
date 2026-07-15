"""Build the American Journal of Human Biology submission package."""

from __future__ import annotations

import re
import shutil
import zipfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches as PptInches
from pptx.util import Pt as PptPt

import ajba_content as revised_content


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
FIGURE_DIR = PROJECT_DIR / "figures"
OUTPUT_DIR = PROJECT_DIR / "docs" / "ajhb_submission"
OUTPUT_FIGURE_DIR = OUTPUT_DIR / "figures"
JOURNAL = "American Journal of Human Biology"
JOURNAL_SHORT = "AJHB"
ARTICLE_TYPE = "Original Research Article"
TITLE = (
    "Pairwise sharing of Neanderthal and Denisovan introgression across global "
    "populations: An exploratory geographic analysis"
)
RUNNING_TITLE = "Geography of archaic DNA sharing"
AUTHOR = "Onishi Tatsuki"
AFFILIATION = "Data Science and AI Innovation Research Promotion Center"
CORRESPONDENCE = (
    "Onishi Tatsuki, Data Science and AI Innovation Research Promotion Center; "
    "Email: bougtoir@gmail.com"
)
ABSTRACT = (
    "Archaic introgression is usually summarized as ancestry proportion within "
    "individuals or populations. We evaluated whether pairwise similarity in the "
    "genomic distribution of Neanderthal- and Denisovan-like segments provides an "
    "additional, explicitly geographic description of population relationships. "
    "High-confidence hmmix calls from 3,134 individuals in 66 populations were "
    "summarized in 500-kb windows, producing 2,145 unique population pairs. "
    "Sharing was quantified as the Pearson correlation between population-level "
    "window-frequency vectors and modeled against geographic distance, maximum "
    "European-admixture fraction, and same-continent status. Matrix-level "
    "association was assessed with Mantel permutation tests in non-admixed "
    "populations. Neanderthal and Denisovan sharing declined with distance "
    "(raw r=-0.485 and -0.466; partial r=-0.311 and -0.300). Corrected models "
    "explained 51.0% and 49.5% of pairwise variation, respectively. Non-admixed "
    "Mantel correlations were -0.616 and -0.581 (both permutation p=0.0001). "
    "No positive-residual population pair survived false-discovery-rate correction "
    "at q<0.10. Exploratory analysis of a 500-kb interval centered on ABO identified "
    "two Neanderthal-like segments among 41 Indigenous American HGDP individuals; "
    "both were closest to Vindija among three reference genomes, but only one "
    "overlapped the ABO gene. These observations do not demonstrate a migration "
    "route. Pairwise archaic sharing captures broad geographic structure, while "
    "specific residual and locus-level patterns remain hypothesis-generating and "
    "require independent modern and ancient genomic validation."
)
KEYWORDS = (
    "archaic introgression; Neanderthal; Denisovan; population genetics; "
    "geographic distance; ABO; human migration"
)


REFERENCES = [
    "Green RE, Krause J, Briggs AW, et al. A draft sequence of the Neandertal genome. Science. 2010;328(5979):710-722. doi:10.1126/science.1188021.",
    "Reich D, Green RE, Kircher M, et al. Genetic history of an archaic hominin group from Denisova Cave in Siberia. Nature. 2010;468(7327):1053-1060. doi:10.1038/nature09710.",
    "Sankararaman S, Mallick S, Dannemann M, et al. The genomic landscape of Neanderthal ancestry in present-day humans. Nature. 2014;507(7492):354-357. doi:10.1038/nature12961.",
    "Sankararaman S, Mallick S, Patterson N, Reich D. The combined landscape of Denisovan and Neanderthal ancestry in present-day humans. Curr Biol. 2016;26(9):1241-1247. doi:10.1016/j.cub.2016.03.037.",
    "Jacobs GS, Hudjashov G, Saag L, et al. Multiple deeply divergent Denisovan ancestries in Papuans. Cell. 2019;177(4):1010-1021.e32. doi:10.1016/j.cell.2019.02.035.",
    "Segurel L, Thompson EE, Flutre T, et al. The ABO blood group is a trans-species polymorphism in primates. Proc Natl Acad Sci U S A. 2012;109(45):18493-18498. doi:10.1073/pnas.1210603109.",
    "Calafell F, Roubinet F, Ramirez-Soriano A, et al. Evolutionary dynamics of the human ABO gene. Hum Genet. 2008;124(2):123-135. doi:10.1007/s00439-008-0530-8.",
    "Halverson MS, Bolnick DA. An ancient DNA test of a founder effect in Native American ABO blood group frequencies. Am J Phys Anthropol. 2008;137(3):342-347. doi:10.1002/ajpa.20887.",
    "Condemi S, Mazières A, Faux P, et al. Blood groups of Neandertals and Denisova decrypted. PLoS One. 2021;16(7):e0254175. doi:10.1371/journal.pone.0254175.",
    "Quilodran CS, Rio J, Tsoupas A, Currat M. Past human expansions shaped the spatial pattern of Neanderthal ancestry. Sci Adv. 2023;9(42):eadg9817. doi:10.1126/sciadv.adg9817.",
    "Skov L, Hui R, Shchur V, et al. Detecting archaic introgression using an unadmixed outgroup. PLoS Genet. 2018;14(9):e1007641. doi:10.1371/journal.pgen.1007641.",
    "Prüfer K, de Filippo C, Grote S, et al. A high-coverage Neandertal genome from Vindija Cave in Croatia. Science. 2017;358(6363):655-658. doi:10.1126/science.aao1887.",
    "1000 Genomes Project Consortium. A global reference for human genetic variation. Nature. 2015;526(7571):68-74. doi:10.1038/nature15393.",
    "Bergström A, McCarthy SA, Hui R, et al. Insights into human genetic variation and population history from 929 diverse genomes. Science. 2020;367(6484):eaay5012. doi:10.1126/science.aay5012.",
    "Benjamini Y, Hochberg Y. Controlling the false discovery rate: A practical and powerful approach to multiple testing. J R Stat Soc Series B Stat Methodol. 1995;57(1):289-300. doi:10.1111/j.2517-6161.1995.tb02031.x.",
    "Mantel N. The detection of disease clustering and a generalized regression approach. Cancer Res. 1967;27(2):209-220.",
    "Ohashi J, Naka I, Kimura R, et al. Polymorphisms in the ABO blood group gene in three populations in the New Georgia group of the Solomon Islands. J Hum Genet. 2006;51(5):407-411. doi:10.1007/s10038-006-0375-8.",
    "Raghavan M, Skoglund P, Graf KE, et al. Upper Palaeolithic Siberian genome reveals dual ancestry of Native Americans. Nature. 2014;505(7481):87-91. doi:10.1038/nature12736.",
    "Iasi LNM, Chintalapati M, Skov L, et al. Neanderthal ancestry through time: Insights from genomes of ancient and present-day humans. Science. 2024;386(6727):eadq3010. doi:10.1126/science.adq3010.",
    "Petr M, Pääbo S, Kelso J, Vernot B. Limits of long-term selection against Neandertal introgression. Proc Natl Acad Sci U S A. 2019;116(5):1639-1644. doi:10.1073/pnas.1814338116.",
    "Skoglund P, Mallick S, Bortolini MC, et al. Genetic evidence for two founding populations of the Americas. Nature. 2015;525(7567):104-108. doi:10.1038/nature14895.",
    "Mao X, Zhang H, Qiao S, et al. The deep population history of northern East Asia from the Late Pleistocene to the Holocene. Cell. 2021;184(12):3256-3266.e13. doi:10.1016/j.cell.2021.04.040.",
    "Liu X, Koyama S, Tomizuka K, et al. Decoding triancestral origins, archaic introgression, and natural selection in the Japanese population by whole-genome sequencing. Sci Adv. 2024;10(16):eadi8419. doi:10.1126/sciadv.adi8419.",
]


INTRODUCTION = [
    (
        "Genomic comparisons established that present-day non-African populations "
        "carry ancestry inherited from Neanderthals and that several Asian and "
        "Oceanian populations also carry ancestry related to Denisovans.{1,2} "
        "Subsequent maps of introgressed sequence showed that the amount and genomic "
        "distribution of archaic ancestry vary among populations, reflecting "
        "demographic history, drift, selection, and multiple episodes of gene "
        "flow.{3-5} These features make archaic segments potentially informative "
        "about population relationships, but they also create substantial scope "
        "for confounding."
    ),
    (
        "The present study was motivated by the long-recognized high frequency of "
        "blood group O in Indigenous American populations. ABO is an unusually "
        "persistent polymorphic system with trans-species and population-specific "
        "histories.{6,7} Ancient-DNA work has tested founder-effect explanations for "
        "Native American ABO frequencies, and archaic genomes contain distinguishable "
        "ABO allelic backgrounds.{8,9} We therefore began with ABO as a focused, "
        "biologically interpretable locus and then asked whether any locus-level "
        "observation was accompanied by a broader genome-wide geographic pattern."
    ),
    (
        "Quilodran and colleagues modeled the spatial distribution of Neanderthal "
        "ancestry and demonstrated that past range expansions can generate broad "
        "geographic gradients.{10} Our framework differs in four respects. First, "
        "it jointly describes Neanderthal and Denisovan sharing rather than a single "
        "ancestry proportion. Second, the unit of analysis is a population pair and "
        "its correlation across genomic windows. Third, residuals are examined only "
        "after explicit adjustment for designated recent admixture and continental "
        "grouping. Fourth, Wallace Line and Lydekker Line interpretations are treated "
        "as geographic visualizations of a bivariate signal, not as direct tests of "
        "a particular migration event."
    ),
    (
        "We hypothesized that pairwise similarity in the genomic distribution of "
        "archaic segments would decline with geographic distance and that the "
        "combined Neanderthal-Denisovan pattern would differentiate continental and "
        "Oceanian population structure. The objectives were to quantify this decay, "
        "assess robustness to designated recent admixture, test matrix-level "
        "association, identify any statistically supported positive-residual pairs, "
        "and place a reproducible ABO-centered analysis within the genome-wide "
        "context. All locus-level and residual analyses were prespecified as "
        "exploratory and hypothesis-generating."
    ),
]


METHODS = [
    (
        "Data sources and study populations",
        [
            (
                "We analyzed publicly available archaic-introgression segments "
                "generated with hmmix, a method designed to detect archaic sequence "
                "without requiring an unadmixed modern outgroup.{11} Segment files "
                "for the 1000 Genomes Project and Human Genome Diversity Project "
                "(HGDP) were obtained from Zenodo record 14136628. The files include "
                "similarity counts to Altai, Vindija, Denisova, and Chagyrskaya "
                "references; the Vindija reference derives from a high-coverage "
                "Neanderthal genome.{12} Population metadata followed the source "
                "1000 Genomes and HGDP resources.{13,14}"
            ),
            (
                "Segments with mean posterior probability below 0.8 were excluded. "
                "Populations with fewer than seven represented individuals were "
                "excluded from the genome-wide analysis, leaving 3,134 individuals "
                "in 66 populations. Calls were retained as Neanderthal, Denisovan, "
                "or Both according to the source annotation. The analysis used "
                "de-identified public data and involved no new recruitment, sampling, "
                "or individual-level phenotype inference."
            ),
        ],
    ),
    (
        "Genome-wide population vectors and pairwise sharing",
        [
            (
                "The autosomal genome was partitioned into 500-kb windows. For each "
                "population and archaic category, overlapping high-confidence calls "
                "were converted to a diploid-normalized frequency vector by dividing "
                "the number of called haplotypes by twice the number of individuals. "
                "Pairwise sharing was the Pearson correlation between two population "
                "vectors. Separate 66 by 66 Neanderthal and Denisovan matrices yielded "
                "2,145 unique off-diagonal population pairs for each ancestry type."
            ),
            (
                "Population coordinates were assigned from sampling-location metadata "
                "or population centroids used in the original analysis scripts. Great-"
                "circle distance was computed with the Haversine formula. Correlation "
                "coefficients summarize similarity in the spatial distribution of "
                "called windows; they do not establish identity by descent."
            ),
        ],
    ),
    (
        "Confounding correction and sensitivity analysis",
        [
            (
                "For population pair i,j, sharing was modeled as a linear function of "
                "geographic distance, the maximum designated European-admixture "
                "fraction of the two populations, and an indicator that both "
                "populations belonged to the same continental group. Designated "
                "fractions were Puerto Rican (PUR) 0.64, Colombian in Medellín (CLM) "
                "0.57, Mexican ancestry in Los Angeles (MXL) 0.48, Peruvian in Lima "
                "(PEL) 0.16, African Caribbean in Barbados (ACB) 0.04, and African "
                "ancestry in the southwestern United States (ASW) 0.20. These values "
                "are operational sensitivity metadata, not "
                "individual ancestry estimates."
            ),
            (
                "We report uncorrected and corrected coefficients of determination, "
                "raw correlations, and partial correlations obtained by residualizing "
                "distance and sharing against the admixture and same-continent "
                "covariates. Because pairwise rows share populations, conventional "
                "row-level p values do not represent independent observations and "
                "are not used as primary evidence. Sensitivity analyses excluded all "
                "pairs involving a designated admixed population."
            ),
        ],
    ),
    (
        "Residual outliers and matrix-level testing",
        [
            (
                "Positive corrected residuals were standardized within ancestry type. "
                "Pairs with z>2.0 were evaluated with permutation-derived nominal "
                "p values, bootstrap confidence intervals, and Benjamini-Hochberg "
                "false discovery rate (FDR) correction.{15} The prespecified reporting "
                "threshold was q<0.10. Results from admixed pairs were retained for "
                "diagnostic comparison but were not interpreted as evidence for "
                "ancient migration."
            ),
            (
                "Matrix-level association between geographic distance and sharing was "
                "tested in non-admixed populations using a Mantel permutation test "
                "with 9,999 population-label permutations.{16} The permutation acts "
                "on population labels and therefore preserves the dependence "
                "structure of symmetric distance and sharing matrices."
            ),
        ],
    ),
    (
        "ABO-centered exploratory analysis",
        [
            (
                "The ABO gene was defined on GRCh38 as chr9:133,233,278-133,276,024. "
                "We analyzed both strict gene overlap and a 500-kb interval "
                "(chr9:133.0-133.5 Mb). The same mean-probability threshold of 0.8 "
                "was applied. Population carrier frequencies used unique individuals "
                "as the numerator and all represented individuals as the denominator."
            ),
            (
                "For each Neanderthal or Both segment in the 500-kb interval, Altai, "
                "Vindija, and Chagyrskaya similarity counts were compared. A unique "
                "maximum defined the closest reference; equal maxima were retained as "
                "ties rather than assigned arbitrarily. Indigenous American HGDP "
                "populations were Pima, Maya, and Colombian; PEL, MXL, CLM, and PUR "
                "were analyzed separately as admixed American populations."
            ),
            (
                "The O2-defining variant was rs41302905, evaluated on the GRCh38 "
                "reference orientation as the T allele. Population frequencies were "
                "retrieved from Ensembl Variation for 1000 Genomes Phase 3 and compared "
                "descriptively with published New Georgia, Solomon Islands ABO*O02 "
                "frequencies.{17} This comparison does not establish that the modern "
                "allele was inherited from a specific archaic lineage."
            ),
        ],
    ),
    (
        "Ancient-genome comparison and software",
        [
            (
                "Ancient ABO-window observations were reproducibly extracted from "
                "the public Neanderthal-segment catalogue of the "
                "Neanderthal-ancestry-through-time "
                "study. The resulting individual-level summary was used only for a "
                "descriptive visualization because ancient and modern calls were "
                "produced by different pipelines and coverage regimes. No formal "
                "temporal trend test was performed."
            ),
            (
                "Analyses were conducted in Python using pandas, NumPy, SciPy, "
                "statsmodels, Matplotlib, and seaborn. Document outputs used "
                "python-docx, python-pptx, and Pillow. Exact package versions are "
                "recorded by the execution environment when the package is rebuilt."
            ),
        ],
    ),
]


RESULTS = [
    (
        "Genome-wide distance decay",
        (
            "Across 2,145 population pairs, Neanderthal sharing correlated negatively "
            "with distance (raw r=-0.4847), as did Denisovan sharing (raw r=-0.4656). "
            "After residualization against designated European-admixture fraction and "
            "same-continent status, the corresponding partial correlations were "
            "-0.3105 and -0.3001. The corrected models explained 51.00% of "
            "Neanderthal and 49.53% of Denisovan pairwise variation, compared with "
            "23.50% and 21.67% in distance-only models (Figure 1; Table 1)."
        ),
        ["Figure 1", "Table 1"],
    ),
    (
        "Population structure in sharing matrices",
        (
            "Heat maps of 31 geographically representative populations showed broad "
            "within-region blocks in both matrices, with a sharper Oceanian contrast "
            "for Denisovan sharing (Figure 2). The display is a selected subset for "
            "legibility; all 66 populations contributed to the statistical analysis."
        ),
        ["Figure 2"],
    ),
    (
        "Geographic interpretation",
        (
            "A schematic places the sharing analysis within established broad "
            "dispersal and archaic-admixture contexts (Figure 3). It intentionally "
            "does not encode estimated migration magnitudes. The bivariate signal is "
            "consistent with a strong change in Denisovan-related ancestry across "
            "island Southeast Asia toward Sahul. Wallace Line and Lydekker Line "
            "terminology is used as biogeographic context, not as a claim that the "
            "present analysis dates or uniquely identifies a crossing event."
        ),
        ["Figure 3"],
    ),
    (
        "Sensitivity to designated recent admixture",
        (
            "Excluding every pair involving PUR, CLM, MXL, PEL, ACB, or ASW "
            "strengthened the raw Neanderthal distance correlation from approximately "
            "-0.485 to -0.615 (Figure 4). Several high positive residuals in the full "
            "analysis involved admixed American populations, including PEL. These "
            "patterns are compatible with recent ancestry mixtures and were not used "
            "as independent support for a Beringian migration interpretation."
        ),
        ["Figure 4"],
    ),
    (
        "Residual outlier testing",
        (
            "Among non-admixed pairs, the Mantel correlation was -0.6157 for "
            "Neanderthal sharing and -0.5809 for Denisovan sharing; both permutation "
            "p values were 0.0001. No positive-residual pair survived false-discovery-"
            "rate correction at q<0.10 for either ancestry type. Nominal residual "
            "rankings are therefore reported only as exploratory diagnostics rather "
            "than statistically supported outliers."
        ),
        [],
    ),
    (
        "ABO-window segment composition",
        (
            "The reproducible 500-kb ABO-centered scan identified 834 Neanderthal or "
            "Both segments, of which 129 overlapped the gene itself. Closest-reference "
            "composition varied by broad group, but 335 of 834 segments had tied "
            "maximum similarity and were not forced to a lineage. In the Indigenous "
            "American HGDP subset, two segments were observed among 41 individuals: "
            "one in Pima overlapped ABO and one in Maya lay downstream within the "
            "500-kb interval. Both were Vindija-closest, but n=2 cannot support a "
            "regional proportion or ancestry-route conclusion (Figure 5; Table 2)."
        ),
        ["Figure 5", "Table 2"],
    ),
    (
        "O2 allele and introgression-window frequencies",
        (
            "The O2-defining rs41302905 T allele had published frequencies of 5.1%, "
            "16.3%, and 14.1% in Munda, Paradise, and Rawaki, respectively, whereas "
            "selected 1000 Genomes frequencies were lower and concentrated mainly in "
            "European and admixed American populations.{17} In contrast, carrier "
            "frequencies for any Neanderthal-like segment in the 500-kb ABO interval "
            "were 7/8 in Papuan Sepik and 7/9 in Papuan Highlands, despite no strict "
            "ABO overlap in either population. The two panels therefore summarize "
            "different biological quantities and should not be interpreted as a "
            "locus-level association (Figure 6)."
        ),
        ["Figure 6"],
    ),
    (
        "ANE hypothesis and ancient comparison",
        (
            "Ancient North Eurasian (ANE) ancestry contributes to published models of "
            "First American ancestry.{18} Figure 7 shows how an ANE-mediated pathway "
            "could generate a testable hypothesis for the two modern Indigenous "
            "American ABO-window segments, while explicitly separating the hypothesis "
            "from evidence. A descriptive extraction from ancient-genome outputs "
            "showed heterogeneous reference matches and several individuals with no "
            "recorded interval segment. Because those calls and modern hmmix calls "
            "were generated differently, Figure 8 presents no temporal test or "
            "turnover estimate.{19}"
        ),
        ["Figure 7", "Figure 8"],
    ),
    (
        "Bivariate global summary",
        (
            "A literature-derived bivariate map summarizes the complementary "
            "geographic distributions of Neanderthal- and Denisovan-related ancestry "
            "(Figure 9).{2-5} Neanderthal ancestry is broadly distributed outside "
            "Africa, whereas high Denisovan ancestry is concentrated in Oceania and "
            "some island Southeast Asian groups. The map is contextual and is not "
            "used in the regression or residual tests."
        ),
        ["Figure 9"],
    ),
]


DISCUSSION = [
    (
        "Pairwise correlations across genomic windows captured broad geographic "
        "structure in both Neanderthal and Denisovan calls. Adjustment for designated "
        "recent admixture and continental grouping increased explained variance, "
        "indicating that uncorrected distance decay combines multiple demographic "
        "processes. Matrix-level Mantel tests supported a robust negative geographic "
        "association, but the absence of false-discovery-rate-significant residual "
        "outliers is equally important: the present data support broad structure, not "
        "specific exceptional population connections."
    ),
    (
        "The distinction from the framework of Quilodran et al.{10} is structural "
        "rather than competitive. Their spatial models ask how expansions shape "
        "Neanderthal ancestry across populations. Our bivariate approach asks whether "
        "two populations distribute archaic calls similarly across windows and "
        "whether this pairwise similarity changes with distance. Joint Neanderthal "
        "and Denisovan views can distinguish populations with superficially similar "
        "total archaic burdens, but correlation also discards absolute ancestry levels "
        "and can be sensitive to sparse windows."
    ),
    (
        "The Denisovan matrix and global map reproduce the qualitative contrast "
        "between continental Asia and Oceania. Wallace and Lydekker lines are useful "
        "labels for discussing this transition, but neither line is itself a "
        "statistical covariate in the current models. Denser island sampling and "
        "explicit spatial models would be required to localize a discontinuity or "
        "attribute it to a specific pulse of settlement or introgression."
    ),
    (
        "The ABO analysis illustrates both the appeal and danger of a focal locus. "
        "ABO has deep allelic history and plausible immune-related selection, while "
        "long-term selection can reshape the retention of Neanderthal sequence.{6,20} "
        "However, a 500-kb carrier call is not equivalent to an ABO allele, and the "
        "O2-defining variant cannot be labeled Neanderthal-derived solely because "
        "similar ABO backgrounds occur in an archaic genome. Recombination, linkage "
        "disequilibrium, reference similarity, and independent persistence of "
        "ancestral variation all complicate interpretation."
    ),
    (
        "The two Vindija-closest Indigenous American window segments are particularly "
        "underpowered. Only the Pima segment overlaps the gene; the Maya segment does "
        "not. Two segments among 41 sampled individuals do not justify a 100% regional "
        "estimate, and similarity to a reference genome is not proof that the segment "
        "traveled through ANE or Beringia. Published ANE and Population Y models "
        "provide testable demographic contexts, not confirmation of this locus-level "
        "route.{18,21}"
    ),
    (
        "Post-Columbian admixture is a major concern for American population pairs. "
        "The sensitivity analysis showed that removal of designated admixed "
        "populations strengthened distance decay, and PEL-containing residuals were "
        "prominent in diagnostic rankings. Such pairs may be informative about recent "
        "mixture or reference-panel composition, but they should not be treated as "
        "decisive evidence for ancient trans-Beringian continuity."
    ),
    (
        "Several statistical limitations remain. Population pairs are not independent "
        "because each population appears in many rows; accordingly, partial-"
        "correlation p values from row-level calculations would be anticonservative "
        "if interpreted as independent-sample tests. The Mantel procedure addresses "
        "matrix dependence for the global distance association but does not solve "
        "every inferential issue. Window correlations also ignore linkage "
        "disequilibrium, variable callability, segment age, and whether similarities "
        "are identity by descent or identity by state. Population-level ecological "
        "associations cannot be transferred to individuals."
    ),
    (
        "Power is constrained by modest population sample sizes, sparse Denisovan "
        "calls outside Oceania, and multiple testing across 2,145 pairs. The absence "
        "of significant outliers may reflect both genuinely smooth structure and "
        "limited power, but it cannot be converted into evidence for a nominated "
        "pair. Independent validation should use larger modern panels, ancient "
        "genomes from Beringia and island Southeast Asia, haplotype phylogenies, "
        "independent genetic-distance covariates, and spatial mixed models."
    ),
    (
        "The framework yields concrete predictions. If the ABO-window observation is "
        "linked to ANE ancestry, homologous haplotypes should occur in independently "
        "sequenced ANE-related and Beringian genomes with a coherent local genealogy. "
        "If the Oceanian discontinuity reflects multiple Denisovan ancestries, "
        "haplotype-resolved calls should change across island transects rather than "
        "only in total proportion. Northeast Asian and Japanese datasets can test "
        "whether the low-Denisovan, high-Neanderthal bivariate position is stable "
        "across methods and sampling schemes.{22,23} ABO and O2 predictions should be "
        "tested directly with phased alleles, not inferred from nearby segment calls."
    ),
    (
        "In conclusion, pairwise archaic-segment sharing is a useful descriptive "
        "complement to ancestry proportions and recovers a reproducible geographic "
        "distance-decay signal. The corrected analysis does not identify any "
        "non-admixed pair as a statistically supported positive outlier, and the "
        "ABO-centered findings are based on very small counts. The appropriate "
        "interpretation is exploratory: the analyses prioritize hypotheses and "
        "sampling targets for independent genomic validation rather than demonstrate "
        "a previously unknown migration route."
    ),
]


FIGURES = {
    1: (
        "fig1_sharing_vs_distance.png",
        "Archaic-segment sharing and geographic distance. Each point is a population pair. Lines summarize distance associations for Neanderthal and Denisovan sharing. Source identifiers in selected labels include CHS (Southern Han Chinese), FIN (Finnish), and PEL (Peruvian in Lima). Pairwise rows are dependent and are not interpreted as independent observations.",
    ),
    2: (
        "fig2_sharing_heatmap.png",
        "Pairwise sharing heat maps for 31 representative populations. Axis labels are source population identifiers. The displayed subset improves legibility; regression and Mantel analyses used all 66 populations.",
    ),
    3: (
        "fig3_minard_migration.png",
        "Schematic context for human dispersal and archaic introgression. Line widths and branch positions are illustrative and do not estimate migration magnitude, ancestry proportion, or event timing beyond the labeled broad intervals.",
    ),
    4: (
        "fig4_sensitivity_admixed.png",
        "Sensitivity of Neanderthal sharing-distance correlation to exclusion of designated admixed populations. Correlations describe pairwise rows and are accompanied by matrix-level tests in the main analysis.",
    ),
    5: (
        "fig5_abo_sublineage.png",
        "Neanderthal-like segments in the 500-kb ABO-centered interval. (A) Closest-reference composition retains tied maxima. n denotes segments, not individuals. (B) Traceable segments for selected HGDP individuals. The Pima and one Bougainville segment overlap ABO; the Maya segment is within the interval but downstream of the gene.",
    ),
    6: (
        "fig6_o2_introgression.png",
        "Distinct summaries of the O2-defining allele and ABO-window introgression. (A) rs41302905 T-allele frequencies from Ensembl/1000 Genomes and Ohashi et al. (2006). (B) Frequency of individuals carrying any Neanderthal-like segment in chr9:133.0-133.5 Mb. The panels use different sources and are not an association analysis.",
    ),
    7: (
        "fig7_ane_model.png",
        "Ancient North Eurasian pathway hypothesis. Dashed arrows connect a published broad ancestry model to the modern ABO-window observation. The diagram is hypothesis-generating and does not infer that either segment followed a particular route.",
    ),
    8: (
        "fig8_temporal_dynamics.png",
        "Descriptive ancient and modern ABO-window summaries. Ancient observations were reproducibly extracted from the public Neanderthal-segment catalogue of Iasi et al. (2024) at the GRCh37 ABO interval; modern calls use hmmix. Different pipelines and coverage preclude a formal temporal comparison.",
    ),
    9: (
        "fig9_bivariate_world_map.png",
        "Literature-derived bivariate global context. Circle size represents approximate Neanderthal ancestry and color intensity represents approximate Denisovan ancestry. Source identifiers shown in parentheses are FIN (Finnish), GBR (British), CEU (Utah residents with Northern and Western European ancestry), FRA (French), IBS (Iberian), and TSI (Toscani). Values are contextual approximations from published studies and were not used in the pairwise statistical models.",
    ),
}

TITLE = revised_content.TITLE
RUNNING_TITLE = revised_content.RUNNING_TITLE
AUTHOR = revised_content.AUTHOR
AFFILIATION = revised_content.AFFILIATION
CORRESPONDENCE = revised_content.CORRESPONDENCE
ABSTRACT = revised_content.ABSTRACT
KEYWORDS = revised_content.KEYWORDS
REFERENCES = revised_content.REFERENCES
REFERENCE_KEYS = revised_content.REFERENCE_KEYS
INTRODUCTION = revised_content.INTRODUCTION
METHODS = revised_content.METHODS
RESULTS = revised_content.RESULTS
DISCUSSION = revised_content.DISCUSSION
FIGURES = revised_content.FIGURES
SUPPORTING_FIGURES = revised_content.SUPPORTING_FIGURES


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 2
    normal.paragraph_format.space_after = Pt(0)
    for name in ["Title", "Heading 1", "Heading 2"]:
        style = document.styles[name]
        style.font.name = "Times New Roman"
        style.font.color.rgb = RGBColor(0, 0, 0)


def add_cited_paragraph(document: Document, text: str, italic: bool = False):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Inches(0.3)
    run = paragraph.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    run.italic = italic
    return paragraph


def add_title_page(document: Document) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(TITLE)
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(ARTICLE_TYPE).bold = True
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(AUTHOR).bold = True
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(AFFILIATION)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(CORRESPONDENCE)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(f"Running title: {RUNNING_TITLE}")
    document.add_heading("Abstract", level=1)
    paragraph = document.add_paragraph(ABSTRACT)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph = document.add_paragraph()
    paragraph.add_run("Keywords: ").bold = True
    paragraph.add_run(KEYWORDS)
    document.add_page_break()


def table_1_rows() -> list[list[str]]:
    pairs = pd.read_csv(DATA_DIR / "pairwise_sharing_corrected.csv")
    qualifying = pairs[
        (pairs["any_admixed"] == 0)
        & (pairs["nean_resid_z"] > 2)
        & (pairs["nean_fdr_pval"] < 0.10)
    ].sort_values("nean_resid_z", ascending=False)
    rows = [
        [
            "Population 1",
            "Population 2",
            "Region 1",
            "Region 2",
            "Distance (km)",
            "Sharing (r)",
            "z-score",
        ]
    ]
    if qualifying.empty:
        rows.append(
            [
                "No qualifying pair",
                "—",
                "—",
                "—",
                "—",
                "—",
                "No z>2 and q<0.10 result",
            ]
        )
        return rows
    for row in qualifying.itertuples():
        rows.append(
            [
                row.pop1,
                row.pop2,
                row.region1.replace("_", " ").title(),
                row.region2.replace("_", " ").title(),
                f"{row.geo_dist_km:,.0f}",
                f"{row.nean_corr:.3f}",
                f"{row.nean_resid_z:.2f}",
            ]
        )
    return rows


def table_2_rows() -> list[list[str]]:
    sublineage = pd.read_csv(DATA_DIR / "abo_sublineage_summary.csv")
    order = [
        "East Asia",
        "Europe",
        "Indigenous Americas",
        "Admixed Americas",
        "Central/South Asia",
        "Middle East",
        "Oceania",
    ]
    rows = [
        [
            "Region",
            "n",
            "Altai %",
            "Vindija %",
            "Chagyrskaya %",
        ]
    ]
    for group in order:
        group_summary = sublineage[
            (sublineage["analysis_group"] == group)
            & (sublineage["closest_reference"] != "Tie")
        ]
        total = int(group_summary["n_segments"].sum())
        values = {
            row.closest_reference: 100 * row.n_segments / total
            for row in group_summary.itertuples()
        } if total else {}
        rows.append(
            [
                group,
                str(total),
                f"{values.get('Altai', 0):.1f}",
                f"{values.get('Vindija', 0):.1f}",
                f"{values.get('Chagyrskaya', 0):.1f}",
            ]
        )
    return rows


TABLES = {
    1: (
        "Positive-residual Neanderthal pairs after false discovery rate control",
        table_1_rows,
        "The prespecified family contains all non-admixed population pairs. No pair met both z>2 and Benjamini-Hochberg q<0.10; the Denisovan analysis likewise identified no qualifying pair. Complete nominal rankings and dependence-aware model results are provided in Supplementary Data.",
    ),
    2: (
        "ABO-window Neanderthal-reference composition",
        table_2_rows,
        "Counts are classifiable segments, not individuals. Percentages use the three-reference denominator shown by n. Equal maximum-similarity ties are excluded from these percentages but retained in Supplementary Data. The 2/2 Indigenous American value is not a regional frequency estimate; only one segment overlaps ABO.",
    ),
}


def add_word_table(document: Document, table_number: int) -> None:
    title, row_function, note = TABLES[table_number]
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(14)
    run = paragraph.add_run(f"Table {table_number}. {title}")
    run.bold = True
    rows = row_function()
    table = document.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.text = value
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.line_spacing = 1
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(8.5)
                    run.bold = row_index == 0
            if row_index == 0:
                set_cell_shading(cell, "D9EAF7")
    paragraph = document.add_paragraph(f"Note. {note}")
    paragraph.paragraph_format.line_spacing = 1
    for run in paragraph.runs:
        run.font.size = Pt(9)


def add_inline_figure(document: Document, figure_number: int) -> None:
    filename, caption = FIGURES[figure_number]
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(16)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(
        str(FIGURE_DIR / filename), width=Inches(6.35)
    )
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.line_spacing = 1.15
    run = paragraph.add_run(f"Figure {figure_number}. ")
    run.bold = True
    paragraph.add_run(caption)


def add_object(document: Document, label: str) -> None:
    kind, number = label.split()
    if kind == "Figure":
        add_inline_figure(document, int(number))
    else:
        add_word_table(document, int(number))


def add_manuscript_body(document: Document, inline: bool) -> None:
    document.add_heading("Introduction", level=1)
    for text in INTRODUCTION:
        add_cited_paragraph(document, text)
    document.add_heading("Materials and Methods", level=1)
    for heading, paragraphs in METHODS:
        document.add_heading(heading, level=2)
        for text in paragraphs:
            add_cited_paragraph(document, text)
    document.add_heading("Results", level=1)
    for heading, text, objects in RESULTS:
        document.add_heading(heading, level=2)
        add_cited_paragraph(document, text)
        if inline:
            for label in objects:
                add_object(document, label)
    document.add_heading("Discussion", level=1)
    for text in DISCUSSION:
        add_cited_paragraph(document, text)
    document.add_heading("Acknowledgements", level=1)
    document.add_paragraph(
        "The author acknowledges the participants, communities, and investigators whose "
        "contributions made the 1000 Genomes, HGDP, hmmix, and ancient-genome resources "
        "available. Public availability does not remove obligations of respectful reuse."
    )
    document.add_heading("Data Availability", level=1)
    document.add_paragraph(
        "Analysis scripts, aggregate derived data, figures, and document-generation code "
        "are available at https://github.com/bougtoir/denisovan-archaic-dna-analysis "
        "and will be fixed as release ajhb-submission-2026-07 before submission. "
        "The source hmmix segment calls are available from Zenodo record 14136628 "
        "(https://doi.org/10.5281/zenodo.14136628). Raw-file SHA-256 checksums and all "
        "analysis parameters are included in analysis_provenance.json."
    )
    document.add_heading("Funding", level=1)
    document.add_paragraph(
        "This research received no specific grant from any funding agency in the "
        "public, commercial, or not-for-profit sectors."
    )
    document.add_heading("Conflict of Interest", level=1)
    document.add_paragraph("The author declares no conflict of interest.")
    document.add_heading("Ethics Statement", level=1)
    document.add_paragraph(
        "This secondary computational analysis used de-identified public genomic data "
        "and involved no recruitment, participant contact, biospecimen collection, or "
        "new phenotype inference. No separate institutional review determination was "
        "obtained; approvals, consent, and access procedures were those reported by the "
        "source studies. No source community representatives participated in this "
        "secondary study, and no direct community return-of-results process occurred. "
        "Because Indigenous genomic records are included, results are reported only at "
        "the minimum level needed for auditability, are not generalized to communities, "
        "and are not used to assign migration routes. The public article, code, and "
        "aggregate derived results are the current means of results availability."
    )
    document.add_heading("Author Contributions", level=1)
    document.add_paragraph(
        "Onishi Tatsuki: Conceptualization, methodology, formal analysis, "
        "visualization, writing—original draft, and writing—review and editing."
    )
    document.add_heading("Literature Cited", level=1)
    for reference in REFERENCES:
        paragraph = document.add_paragraph(reference)
        paragraph.paragraph_format.first_line_indent = Inches(-0.25)
        paragraph.paragraph_format.left_indent = Inches(0.25)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_after = Pt(4)
        for run in paragraph.runs:
            run.font.size = Pt(10)
    if not inline:
        document.add_heading("Figure Legends", level=1)
        for number, (_, caption) in FIGURES.items():
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.line_spacing = 1.5
            paragraph.paragraph_format.space_after = Pt(8)
            run = paragraph.add_run(f"Figure {number}. ")
            run.bold = True
            paragraph.add_run(caption)
        document.add_heading("Supporting Information Legends", level=1)
        for number, (_, caption) in SUPPORTING_FIGURES.items():
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.line_spacing = 1.5
            paragraph.paragraph_format.space_after = Pt(8)
            run = paragraph.add_run(f"Figure S{number}. ")
            run.bold = True
            paragraph.add_run(caption)


def create_manuscript(path: Path, inline: bool) -> None:
    document = Document()
    configure_document(document)
    document.core_properties.title = TITLE
    document.core_properties.author = AUTHOR
    add_title_page(document)
    add_manuscript_body(document, inline)
    document.save(path)


def create_tables_document(path: Path) -> None:
    document = Document()
    configure_document(document)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Editable Tables")
    run.bold = True
    run.font.size = Pt(16)
    paragraph = document.add_paragraph(TITLE)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for number in TABLES:
        add_word_table(document, number)
        if number != max(TABLES):
            document.add_page_break()
    document.save(path)


def create_single_table_document(path: Path, table_number: int) -> None:
    document = Document()
    configure_document(document)
    add_word_table(document, table_number)
    document.save(path)


def create_supporting_information(path: Path) -> None:
    document = Document()
    configure_document(document)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Supporting Information")
    run.bold = True
    run.font.size = Pt(16)
    paragraph = document.add_paragraph(TITLE)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for number, (filename, caption) in SUPPORTING_FIGURES.items():
        heading = document.add_paragraph()
        heading.paragraph_format.space_before = Pt(16)
        run = heading.add_run(f"Figure S{number}. {caption}")
        run.bold = True
        image = document.add_paragraph()
        image.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image.add_run().add_picture(
            str(FIGURE_DIR / filename), width=Inches(6.35)
        )
        if number != max(SUPPORTING_FIGURES):
            document.add_page_break()
    document.add_heading("Supplementary Data Files", level=1)
    document.add_paragraph(
        "Supplementary Data 1: population_metadata.csv. Population, project, sample "
        "size, coordinates, continent assignment, and analysis inclusion."
    )
    document.add_paragraph(
        "Supplementary Data 2: pairwise_sharing_corrected.csv. Complete pairwise "
        "similarity, geographic, covariate, residual, permutation, and false discovery "
        "rate results."
    )
    document.add_paragraph(
        "Supplementary Data 3: model_summary.csv. Quadratic assignment procedure "
        "coefficients, permutation P values, descriptive R-squared values, and "
        "population-deletion intervals."
    )
    document.add_paragraph(
        "Supplementary Data 4: sensitivity_analysis.csv and "
        "window_size_sensitivity.csv. Metric, population-subset, and window-size "
        "robustness summaries."
    )
    document.save(path)


def create_cover_letter(path: Path) -> None:
    document = Document()
    configure_document(document)
    document.styles["Normal"].paragraph_format.line_spacing = 1
    document.styles["Normal"].paragraph_format.space_after = Pt(7)
    for text in [
        "Editor-in-Chief",
        JOURNAL,
        "Wiley",
    ]:
        document.add_paragraph(text)
    document.add_paragraph()
    paragraph = document.add_paragraph()
    run = paragraph.add_run(f"Re: Submission of an {ARTICLE_TYPE}")
    run.bold = True
    document.add_paragraph("Dear Editor-in-Chief,")
    paragraphs = [
        (
            f"I am pleased to submit “{TITLE}” for consideration as an "
            f"{ARTICLE_TYPE} in the {JOURNAL}."
        ),
        (
            "Focal-locus and special-connection interpretations of shared archaic "
            "segments are common in human population biology, yet they are seldom "
            "tested against a genome-wide baseline that respects the dependence "
            "structure of pairwise data. Using publicly archived hmmix "
            f"archaic-introgression calls from {revised_content.INDIVIDUALS:,} "
            f"individuals in {revised_content.POPULATIONS} populations "
            "(1000 Genomes Project and Human Genome Diversity Project), we construct "
            "such a baseline: population profiles are built so that window "
            "frequencies remain within 0-1, distance and pair-level effects are "
            "tested with population-label quadratic assignment permutations, and "
            "multiple testing is controlled with the false-discovery rate."
        ),
        (
            "The analysis shows a broad geographic distance-decay pattern but no "
            "population pair that survives false-discovery-rate correction and no "
            "ABO-window signal beyond the genome-wide expectation. The contribution "
            "is therefore a reusable, dependence-aware negative control against which "
            "focal-locus and special-connection archaic claims can be judged, rather "
            "than a new migration route. This methodologically oriented, "
            "population-biology framing is intended to fit the analytical and "
            "evolutionary scope of the Journal."
        ),
        (
            "The work is original, is not under consideration elsewhere, and uses "
            "de-identified public genomic resources. No new human participants or "
            "specimens were recruited. The manuscript explicitly discloses that no "
            "separate institutional review determination, community participation, or "
            "direct return-of-results process occurred for this secondary analysis. "
            "The author declares no conflict of interest and reports no external funding."
        ),
        (
            "All analysis code and derived outputs are provided through the project "
            "repository. The source archaic-introgression data, generated with hmmix "
            "(a hidden Markov model-based detection method), are publicly archived in "
            "Zenodo. "
            "The submission includes separate figure files, editable tables, and "
            "figure legends in the manuscript."
        ),
    ]
    for text in paragraphs:
        document.add_paragraph(text)
    document.add_paragraph("Sincerely,")
    document.add_paragraph(AUTHOR)
    document.add_paragraph(AFFILIATION)
    document.add_paragraph("Email: bougtoir@gmail.com")
    document.save(path)


def add_slide_title(slide, title: str) -> None:
    box = slide.shapes.add_textbox(
        PptInches(0.6),
        PptInches(0.12),
        PptInches(12.1),
        PptInches(0.7),
    )
    box.text_frame.word_wrap = True
    paragraph = box.text_frame.paragraphs[0]
    paragraph.text = title
    paragraph.font.name = "Arial"
    paragraph.font.size = PptPt(16)
    paragraph.font.bold = True
    paragraph.alignment = PP_ALIGN.CENTER


def add_slide_caption(slide, caption: str) -> None:
    box = slide.shapes.add_textbox(
        PptInches(0.65),
        PptInches(6.55),
        PptInches(12.0),
        PptInches(0.72),
    )
    box.text_frame.word_wrap = True
    paragraph = box.text_frame.paragraphs[0]
    paragraph.text = caption
    paragraph.font.name = "Arial"
    paragraph.font.size = PptPt(8)
    paragraph.alignment = PP_ALIGN.LEFT


def add_picture_contained(slide, path: Path) -> None:
    with Image.open(path) as image:
        width, height = image.size
    area_left = 0.55
    area_top = 0.85
    area_width = 12.2
    area_height = 5.65
    scale = min(area_width / width, area_height / height)
    picture_width = width * scale
    picture_height = height * scale
    left = area_left + (area_width - picture_width) / 2
    top = area_top + (area_height - picture_height) / 2
    slide.shapes.add_picture(
        str(path),
        PptInches(left),
        PptInches(top),
        PptInches(picture_width),
        PptInches(picture_height),
    )


def add_ppt_table(slide, rows: list[list[str]]) -> None:
    table_shape = slide.shapes.add_table(
        len(rows),
        len(rows[0]),
        PptInches(0.45),
        PptInches(1.0),
        PptInches(12.4),
        PptInches(5.5),
    )
    table = table_shape.table
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.text = value
            cell.fill.solid()
            cell.fill.fore_color.rgb = (
                PptRGBColor(217, 234, 247)
                if row_index == 0
                else PptRGBColor(255, 255, 255)
            )
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.name = "Arial"
                paragraph.font.size = PptPt(9)
                paragraph.font.bold = row_index == 0


def create_presentation(path: Path) -> None:
    presentation = Presentation()
    presentation.slide_width = PptInches(13.333)
    presentation.slide_height = PptInches(7.5)
    blank = presentation.slide_layouts[6]
    for number, (filename, caption) in FIGURES.items():
        slide = presentation.slides.add_slide(blank)
        add_slide_title(slide, f"Figure {number}")
        add_picture_contained(slide, FIGURE_DIR / filename)
        add_slide_caption(slide, caption)
    for number, (filename, caption) in SUPPORTING_FIGURES.items():
        slide = presentation.slides.add_slide(blank)
        add_slide_title(slide, f"Figure S{number}")
        add_picture_contained(slide, FIGURE_DIR / filename)
        add_slide_caption(slide, caption)
    for number, (title, row_function, note) in TABLES.items():
        slide = presentation.slides.add_slide(blank)
        add_slide_title(slide, f"Table {number}. {title}")
        add_ppt_table(slide, row_function())
        add_slide_caption(slide, f"Note. {note}")
    presentation.save(path)


def prepare_separate_figures() -> None:
    OUTPUT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTPUT_FIGURE_DIR.glob("Figure_*"):
        stale.unlink()
    for number, (filename, _) in FIGURES.items():
        source = FIGURE_DIR / filename
        png_target = OUTPUT_FIGURE_DIR / f"Figure_{number}.png"
        tiff_target = OUTPUT_FIGURE_DIR / f"Figure_{number}.tiff"
        shutil.copy2(source, png_target)
        tiff_source = source.with_suffix(".tiff")
        if tiff_source.exists():
            shutil.copy2(tiff_source, tiff_target)
        else:
            with Image.open(source) as image:
                image.convert("RGB").save(
                    tiff_target,
                    format="TIFF",
                    dpi=(300, 300),
                    compression="tiff_lzw",
                )
    for number, (filename, _) in SUPPORTING_FIGURES.items():
        source = FIGURE_DIR / filename
        png_target = OUTPUT_FIGURE_DIR / f"Figure_S{number}.png"
        tiff_target = OUTPUT_FIGURE_DIR / f"Figure_S{number}.tiff"
        shutil.copy2(source, png_target)
        tiff_source = source.with_suffix(".tiff")
        if tiff_source.exists():
            shutil.copy2(tiff_source, tiff_target)
        else:
            with Image.open(source) as image:
                image.convert("RGB").save(
                    tiff_target,
                    format="TIFF",
                    dpi=(300, 300),
                    compression="tiff_lzw",
                )


def validate_content() -> list[str]:
    body_texts = INTRODUCTION.copy()
    for _, paragraphs in METHODS:
        body_texts.extend(paragraphs)
    body_texts.extend(text for _, text, _ in RESULTS)
    body_texts.extend(DISCUSSION)
    joined_body = "\n".join(body_texts)
    uncited_references = []
    for key in REFERENCE_KEYS:
        author, year = key.rsplit(" ", 1)
        variants = [key, f"{author} ({year})"]
        if not any(variant in joined_body for variant in variants):
            uncited_references.append(key)
    figure_mentions = []
    supporting_figure_mentions = []
    table_mentions = []
    for text in body_texts:
        figure_mentions.extend(
            int(value) for value in re.findall(r"Figures? (?!S)(\d+)", text)
        )
        supporting_figure_mentions.extend(
            int(value) for value in re.findall(r"Figures? S(\d+)", text)
        )
        table_mentions.extend(int(value) for value in re.findall(r"Table (\d+)", text))
    figure_order = list(dict.fromkeys(figure_mentions))
    supporting_figure_order = list(dict.fromkeys(supporting_figure_mentions))
    table_order = list(dict.fromkeys(table_mentions))
    unresolved = [
        value
        for value in [
            "[" + "Affiliation to be added]",
            "[" + "To be added]",
            "[" + "Corresponding author details]",
        ]
        if value in "\n".join(body_texts)
    ]
    checks = [
        ("Author-date citations", not re.findall(r"\{\d", joined_body)),
        ("Every reference cited", not uncited_references),
        ("References alphabetized", REFERENCES == sorted(REFERENCES)),
        ("Figure first-appearance order", figure_order == list(FIGURES)),
        (
            "Supporting figure first-appearance order",
            supporting_figure_order == list(SUPPORTING_FIGURES),
        ),
        ("Table first-appearance order", table_order == list(TABLES)),
        ("No placeholder strings", not unresolved),
        ("Running title under 48 characters", len(RUNNING_TITLE) < 48),
        ("Abstract at most 250 words", len(ABSTRACT.split()) <= 250),
        (
            "Three to five keywords",
            3 <= len([k for k in KEYWORDS.split(";") if k.strip()]) <= 5,
        ),
        (
            "All figure source files present",
            all((FIGURE_DIR / filename).exists() for filename, _ in FIGURES.values()),
        ),
        (
            "All supporting figure source files present",
            all(
                (FIGURE_DIR / filename).exists()
                for filename, _ in SUPPORTING_FIGURES.values()
            ),
        ),
    ]
    lines = [
        f"{JOURNAL_SHORT} SUBMISSION VALIDATION",
        "==========================",
        "",
        f"Abstract words: {len(ABSTRACT.split())}",
        f"References: {len(REFERENCES)}",
        f"Uncited references: {uncited_references}",
        f"First-appearance figure order: {figure_order}",
        f"First-appearance supporting figure order: {supporting_figure_order}",
        f"First-appearance table order: {table_order}",
        "",
    ]
    for label, passed in checks:
        lines.append(f"{'PASS' if passed else 'FAIL'}: {label}")
    if not all(passed for _, passed in checks):
        raise RuntimeError("\n".join(lines))
    return lines


def create_checklist(path: Path) -> None:
    content = """# AJHB submission checklist

## Prepared files

- `manuscript_ajhb.docx`: manuscript with figure legends and no embedded figure bodies
- `manuscript_ajhb_inline_review.docx`: internal review copy with figures and tables immediately after first mention
- `Table_1_residual_outliers.docx` and `Table_2_abo_summary.docx`: individual editable tables
- `tables_ajhb.docx`: combined editable Tables 1-2 for internal convenience
- `supporting_information_ajhb.docx`: Supporting Figures S1-S6 and data-file descriptions
- `figures_tables_ajhb.pptx`: Figures 1-5, Figures S1-S6, and Tables 1-2
- `cover_letter_ajhb.docx`: American Journal of Human Biology Original Research Article cover letter
- `figures/Figure_1` through `Figure_5` and `Figure_S1` through `Figure_S6`: separate PNG and TIFF files
- `supplementary_data/`: population metadata, complete pairwise results, model output, sensitivities, and provenance
- `reproducibility_checklist.md`: data provenance, rebuild commands, expected checks, and package versions
- `reference_validation.csv`: DOI/PubMed existence and title checks

## Automated checks

- References use author-date (author-year) style and are alphabetized.
- Every listed reference is cited and every citation has a reference entry.
- Figures 1-5, Figures S1-S6, and Tables 1-2 are first mentioned sequentially.
- The abstract is within 250 words.
- The running title is under 48 characters.
- Required title-page, availability, funding, conflict, ethics, and contribution statements are present.
- No submission placeholder strings remain.

## Author checks before upload

- Confirm the full correspondence postal address.
- Confirm the no-external-funding statement.
- Confirm the conflict-of-interest statement.
- Obtain or confirm an institutional determination for this secondary genomic analysis.
- Review the explicit disclosure of no direct community engagement or return of results.
- Confirm the AJHB article type and current file-size limits in the Wiley submission portal.
- Upload the manuscript without embedded figures; upload each TIFF separately.
- Upload `supporting_information_ajhb.docx` and the supplementary CSV/JSON files.
- Upload `Table_1_residual_outliers.docx` and `Table_2_abo_summary.docx` as editable table files.
- Do not interpret nominal residuals, PEL-containing pairs, or the two Indigenous-American ABO-window segments as definitive migration evidence.

## Submission links

- Author guidelines: https://onlinelibrary.wiley.com/page/journal/15206300/homepage/forauthors.html
- New-submission portal: https://onlinelibrary.wiley.com/journal/15206300
"""
    path.write_text(content, encoding="utf-8")


def create_reproducibility_checklist(path: Path) -> None:
    packages = [
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "matplotlib",
        "seaborn",
        "python-docx",
        "python-pptx",
        "Pillow",
    ]
    versions = []
    for package in packages:
        try:
            versions.append(f"- `{package}=={version(package)}`")
        except PackageNotFoundError:
            versions.append(f"- `{package}`: version not available")
    content = f"""# Reproducibility checklist

## Public source data

- hmmix archaic-introgression segment files from the 1000 Genomes Project and Human Genome Diversity Project (HGDP): Zenodo record 14136628
- O2 blood-group subtype-defining `rs41302905 T` frequencies: Ensembl Variation application programming interface endpoint
- Solomon Islands ABO*O02 frequencies: Ohashi et al. 2006, doi:10.1007/s10038-006-0375-8
- Ancient ABO-window summary: reproducibly extracted from the public Neanderthal-segment catalogue of Iasi et al. 2024 (Dryad doi:10.5061/dryad.zw3r228gg; files Neandertal_segments_matching_references_Shared_map.csv and Meta_Data_individuals.csv) by `scripts/build_ancient_abo_summary.py`. Source-file SHA-256 hashes are recorded in `data/ancient_abo_provenance.json`.

## Rebuild order

Run from the project root:

```bash
python scripts/run_ajba_pipeline.py \
  --segments-1kg /path/to/hg38_1000g_segments.txt \
  --segments-hgdp /path/to/hg38_HGDP_segments.txt \
  --permutations 9999 \
  --sensitivity-permutations 999
```

The committed `data/ancient_abo_summary.csv` (supporting temporal figure only) is
regenerated by additionally passing the Iasi et al. 2024 Dryad files:

```bash
python scripts/build_ancient_abo_summary.py \
  --iasi-segments /path/to/Neandertal_segments_matching_references_Shared_map.csv \
  --iasi-metadata /path/to/Meta_Data_individuals.csv
```

## Expected primary checks

- Individuals: {revised_content.INDIVIDUALS:,}
- Populations: {revised_content.POPULATIONS}
- Unique population pairs: {revised_content.PAIRS:,}
- Every population-window frequency is between 0 and 1
- Neanderthal raw distance r: {revised_content.NEANDERTHAL['raw_r']:.4f}
- Denisovan raw distance r: {revised_content.DENISOVAN['raw_r']:.4f}
- Neanderthal expanded descriptive R²: {revised_content.NEANDERTHAL['expanded_r_squared']:.4f}
- Denisovan expanded descriptive R²: {revised_content.DENISOVAN['expanded_r_squared']:.4f}
- Quadratic assignment procedure distance P: {revised_content.NEANDERTHAL['distance_qap_p']:.4f} and {revised_content.DENISOVAN['distance_qap_p']:.4f}
- False discovery rate q<0.10 non-admixed outliers: {revised_content.NEANDERTHAL['fdr_q_lt_0.10_positive_z_gt_2']} and {revised_content.DENISOVAN['fdr_q_lt_0.10_positive_z_gt_2']}
- Neanderthal/Both segments in the 500-kb ABO interval: {revised_content.ABO['interval_segments']:,}
- Strict ABO-overlapping Neanderthal/Both segments: {revised_content.ABO['strict_overlap']}
- Neanderthal/Both segments with tied maximum reference similarity: {revised_content.ABO['ties']}
- Indigenous American window carriers: Pima 1/13, Maya 1/21, Colombian 0/7
- Strict ABO overlap among those carriers: Pima only

## Environment used for the package

{chr(10).join(versions)}

## Interpretation guardrails

- Pairwise correlation does not prove identity by descent.
- Pairwise rows are dependent; inference uses population-label permutations.
- Expanded-model R² is descriptive and not a causal variance decomposition.
- Reference-genome similarity does not prove a specific migration route.
- Admixed American residuals are not treated as ancient-migration evidence.
- No positive-residual non-admixed pair survived false discovery rate correction.
- Ancient and modern ABO-window calls were produced by different pipelines.
"""
    path.write_text(content, encoding="utf-8")


def create_zip(path: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, file_path.relative_to(OUTPUT_DIR))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in ["Table_1_corrected_model.docx"]:
        (OUTPUT_DIR / stale).unlink(missing_ok=True)
    prepare_separate_figures()
    manuscript = OUTPUT_DIR / "manuscript_ajhb.docx"
    review = OUTPUT_DIR / "manuscript_ajhb_inline_review.docx"
    tables = OUTPUT_DIR / "tables_ajhb.docx"
    table_1 = OUTPUT_DIR / "Table_1_residual_outliers.docx"
    table_2 = OUTPUT_DIR / "Table_2_abo_summary.docx"
    supporting = OUTPUT_DIR / "supporting_information_ajhb.docx"
    cover = OUTPUT_DIR / "cover_letter_ajhb.docx"
    presentation = OUTPUT_DIR / "figures_tables_ajhb.pptx"
    checklist = OUTPUT_DIR / "submission_checklist.md"
    reproducibility = OUTPUT_DIR / "reproducibility_checklist.md"
    validation = OUTPUT_DIR / "submission_validation.txt"
    reference_validation = OUTPUT_DIR / "reference_validation.csv"
    supplementary_directory = OUTPUT_DIR / "supplementary_data"
    supplementary_directory.mkdir(parents=True, exist_ok=True)
    create_manuscript(manuscript, inline=False)
    create_manuscript(review, inline=True)
    create_tables_document(tables)
    create_single_table_document(table_1, 1)
    create_single_table_document(table_2, 2)
    create_supporting_information(supporting)
    create_cover_letter(cover)
    create_presentation(presentation)
    create_checklist(checklist)
    create_reproducibility_checklist(reproducibility)
    validation.write_text("\n".join(validate_content()) + "\n", encoding="utf-8")
    supplementary_sources = [
        DATA_DIR / "population_metadata.csv",
        DATA_DIR / "pairwise_sharing_corrected.csv",
        DATA_DIR / "model_summary.csv",
        DATA_DIR / "sensitivity_analysis.csv",
        DATA_DIR / "window_size_sensitivity.csv",
        DATA_DIR / "analysis_provenance.json",
        DATA_DIR / "profile_quality_checks.csv",
        DATA_DIR / "ancient_abo_summary.csv",
        DATA_DIR / "ancient_abo_provenance.json",
    ]
    for source in supplementary_sources:
        shutil.copy2(source, supplementary_directory / source.name)
    zip_files = [
        manuscript,
        table_1,
        table_2,
        supporting,
        cover,
        presentation,
        checklist,
        reproducibility,
        validation,
        *sorted(OUTPUT_FIGURE_DIR.glob("Figure_*")),
        *sorted(supplementary_directory.iterdir()),
    ]
    if reference_validation.exists():
        zip_files.append(reference_validation)
    create_zip(OUTPUT_DIR / "AJHB_submission_package.zip", zip_files)
    print(f"Created {JOURNAL_SHORT} submission materials in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
