"""Revised AJBA manuscript content populated from current analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
STATISTICS = json.loads(
    (PROJECT_DIR / "data" / "correction_stats.json").read_text(encoding="utf-8")
)
NEANDERTHAL = STATISTICS["nean"]
DENISOVAN = STATISTICS["deni"]


def value(statistics: dict[str, object], key: str, digits: int = 3) -> str:
    return f"{float(statistics[key]):.{digits}f}"


TITLE = (
    "Geographic distance decay in population-level Neanderthal and Denisovan "
    "segment profiles"
)
RUNNING_TITLE = "Geography of archaic segment profiles"
AUTHOR = "Onishi Tatsuki"
AFFILIATION = "Data Science and AI Innovation Research Promotion Center"
CORRESPONDENCE = (
    "Onishi Tatsuki, Data Science and AI Innovation Research Promotion Center; "
    "Email: bougtoir@gmail.com"
)
ABSTRACT = (
    "Objectives: We tested whether population-level genomic profiles of inferred "
    "Neanderthal- and Denisovan-like segments become less similar with geographic "
    "distance. Materials and Methods: High-confidence hmmix calls from 3,134 "
    "individuals in 66 populations were summarized in 500-kb windows. Each "
    "individual-haplotype-window contributed at most one presence, constraining "
    "population frequencies to 0-1. Pearson similarity was calculated for 2,145 "
    "population pairs. Distance associations were evaluated with population-label "
    "quadratic assignment permutations, population-deletion analyses, and "
    "sensitivities to window size, similarity metric, sample-size threshold, dataset, "
    "zero-distance pairs, and regional omission. Results: Similarity declined with "
    f"distance for Neanderthal (raw r={value(NEANDERTHAL, 'raw_r')}) and Denisovan "
    f"(raw r={value(DENISOVAN, 'raw_r')}) profiles. Expanded descriptive models that "
    "also included designated recent-admixture involvement, same-continent status, "
    f"and same-dataset status had partial distance correlations of "
    f"{value(NEANDERTHAL, 'partial_r')} and {value(DENISOVAN, 'partial_r')}; "
    f"population-label permutation P values for distance were "
    f"{value(NEANDERTHAL, 'distance_qap_p', 4)} and "
    f"{value(DENISOVAN, 'distance_qap_p', 4)}. No positive-residual non-admixed pair "
    "met both z>2 and false-discovery-rate q<0.10. Conclusions: Archaic-segment "
    "profile similarity contains a broad geographic distance-decay signal, but the "
    "analysis does not identify exceptional population connections or demonstrate "
    "specific migration routes. A secondary ABO-window analysis remains "
    "hypothesis-generating."
)
KEYWORDS = (
    "archaic introgression; Neanderthal; Denisovan; population genetics; "
    "geographic distance; quadratic assignment procedure; ABO"
)


REFERENCE_RECORDS = [
    (
        "1000 Genomes Project Consortium 2015",
        "1000 Genomes Project Consortium. 2015. “A Global Reference for Human Genetic "
        "Variation.” Nature 526 (7571): 68–74. https://doi.org/10.1038/nature15393.",
    ),
    (
        "Benjamini and Hochberg 1995",
        "Benjamini, Yoav, and Yosef Hochberg. 1995. “Controlling the False Discovery "
        "Rate: A Practical and Powerful Approach to Multiple Testing.” Journal of the "
        "Royal Statistical Society: Series B 57 (1): 289–300. "
        "https://doi.org/10.1111/j.2517-6161.1995.tb02031.x.",
    ),
    (
        "Bergström et al. 2020",
        "Bergström, Anders, Shane A. McCarthy, Ruoyun Hui, et al. 2020. “Insights into "
        "Human Genetic Variation and Population History from 929 Diverse Genomes.” "
        "Science 367 (6484): eaay5012. https://doi.org/10.1126/science.aay5012.",
    ),
    (
        "Calafell et al. 2008",
        "Calafell, Francesc, Françoise Roubinet, Antonio Ramirez-Soriano, et al. 2008. "
        "“Evolutionary Dynamics of the Human ABO Gene.” Human Genetics 124 (2): "
        "123–35. https://doi.org/10.1007/s00439-008-0530-8.",
    ),
    (
        "Carroll et al. 2020",
        "Carroll, Stephanie Russo, Ibrahim Garba, Oscar L. Figueroa-Rodríguez, et al. "
        "2020. “The CARE Principles for Indigenous Data Governance.” Data Science "
        "Journal 19: 43. https://doi.org/10.5334/dsj-2020-043.",
    ),
    (
        "Claw et al. 2018",
        "Claw, Katrina G., Dorothy Lippert, Jessica Bardill, et al. 2018. “A Framework "
        "for Enhancing Ethical Genomic Research with Indigenous Communities.” Nature "
        "Communications 9: 2957. https://doi.org/10.1038/s41467-018-05188-3.",
    ),
    (
        "Condemi et al. 2021",
        "Condemi, Silvana, Amandine Mazières, Pascal Faux, et al. 2021. “Blood Groups "
        "of Neandertals and Denisova Decrypted.” PLOS ONE 16 (7): e0254175. "
        "https://doi.org/10.1371/journal.pone.0254175.",
    ),
    (
        "Dekker, Krackhardt, and Snijders 2007",
        "Dekker, David, David Krackhardt, and Tom A. B. Snijders. 2007. “Sensitivity "
        "of MRQAP Tests to Collinearity and Autocorrelation Conditions.” Psychometrika "
        "72: 563–81. https://doi.org/10.1007/s11336-007-9016-1.",
    ),
    (
        "Green et al. 2010",
        "Green, Richard E., Johannes Krause, Adrian W. Briggs, et al. 2010. “A Draft "
        "Sequence of the Neandertal Genome.” Science 328 (5979): 710–22. "
        "https://doi.org/10.1126/science.1188021.",
    ),
    (
        "Halverson and Bolnick 2008",
        "Halverson, Melissa S., and Deborah A. Bolnick. 2008. “An Ancient DNA Test of "
        "a Founder Effect in Native American ABO Blood Group Frequencies.” American "
        "Journal of Physical Anthropology 137 (3): 342–47. "
        "https://doi.org/10.1002/ajpa.20887.",
    ),
    (
        "Iasi et al. 2024",
        "Iasi, Leonardo N. M., Manjusha Chintalapati, Laurits Skov, et al. 2024. "
        "“Neanderthal Ancestry through Time: Insights from Genomes of Ancient and "
        "Present-Day Humans.” Science 386 (6727): eadq3010. "
        "https://doi.org/10.1126/science.adq3010.",
    ),
    (
        "Jacobs et al. 2019",
        "Jacobs, Guy S., Georgi Hudjashov, Lauri Saag, et al. 2019. “Multiple Deeply "
        "Divergent Denisovan Ancestries in Papuans.” Cell 177 (4): 1010–21.e32. "
        "https://doi.org/10.1016/j.cell.2019.02.035.",
    ),
    (
        "Krackhardt 1988",
        "Krackhardt, David. 1988. “Predicting with Networks: Nonparametric Multiple "
        "Regression Analysis of Dyadic Data.” Social Networks 10 (4): 359–81. "
        "https://doi.org/10.1016/0378-8733(88)90004-4.",
    ),
    (
        "Ohashi et al. 2006",
        "Ohashi, Jun, Izumi Naka, Ryosuke Kimura, et al. 2006. “Polymorphisms in the "
        "ABO Blood Group Gene in Three Populations in the New Georgia Group of the "
        "Solomon Islands.” Journal of Human Genetics 51 (5): 407–11. "
        "https://doi.org/10.1007/s10038-006-0375-8.",
    ),
    (
        "Petr et al. 2019",
        "Petr, Martin, Svante Pääbo, Janet Kelso, and Benjamin Vernot. 2019. “Limits "
        "of Long-Term Selection against Neandertal Introgression.” Proceedings of the "
        "National Academy of Sciences 116 (5): 1639–44. "
        "https://doi.org/10.1073/pnas.1814338116.",
    ),
    (
        "Prüfer et al. 2017",
        "Prüfer, Kay, Cesare de Filippo, Steffi Grote, et al. 2017. “A High-Coverage "
        "Neandertal Genome from Vindija Cave in Croatia.” Science 358 (6363): 655–58. "
        "https://doi.org/10.1126/science.aao1887.",
    ),
    (
        "Quilodran et al. 2023",
        "Quilodran, Claudio S., Julie Rio, Athanasios Tsoupas, and Mathias Currat. "
        "2023. “Past Human Expansions Shaped the Spatial Pattern of Neanderthal "
        "Ancestry.” Science Advances 9 (42): eadg9817. "
        "https://doi.org/10.1126/sciadv.adg9817.",
    ),
    (
        "Raghavan et al. 2014",
        "Raghavan, Maanasa, Pontus Skoglund, Kelly E. Graf, et al. 2014. “Upper "
        "Palaeolithic Siberian Genome Reveals Dual Ancestry of Native Americans.” "
        "Nature 505 (7481): 87–91. https://doi.org/10.1038/nature12736.",
    ),
    (
        "Reich et al. 2010",
        "Reich, David, Richard E. Green, Martin Kircher, et al. 2010. “Genetic History "
        "of an Archaic Hominin Group from Denisova Cave in Siberia.” Nature 468 "
        "(7327): 1053–60. https://doi.org/10.1038/nature09710.",
    ),
    (
        "Sankararaman et al. 2014",
        "Sankararaman, Sriram, Swapan Mallick, Michael Dannemann, et al. 2014. “The "
        "Genomic Landscape of Neanderthal Ancestry in Present-Day Humans.” Nature 507 "
        "(7492): 354–57. https://doi.org/10.1038/nature12961.",
    ),
    (
        "Sankararaman et al. 2016",
        "Sankararaman, Sriram, Swapan Mallick, Nick Patterson, and David Reich. 2016. "
        "“The Combined Landscape of Denisovan and Neanderthal Ancestry in Present-Day "
        "Humans.” Current Biology 26 (9): 1241–47. "
        "https://doi.org/10.1016/j.cub.2016.03.037.",
    ),
    (
        "Segurel et al. 2012",
        "Segurel, Laure, Emma E. Thompson, Timothée Flutre, et al. 2012. “The ABO Blood "
        "Group Is a Trans-Species Polymorphism in Primates.” Proceedings of the "
        "National Academy of Sciences 109 (45): 18493–98. "
        "https://doi.org/10.1073/pnas.1210603109.",
    ),
    (
        "Skoglund et al. 2015",
        "Skoglund, Pontus, Swapan Mallick, Maria Cátira Bortolini, et al. 2015. "
        "“Genetic Evidence for Two Founding Populations of the Americas.” Nature 525 "
        "(7567): 104–8. https://doi.org/10.1038/nature14895.",
    ),
    (
        "Skov et al. 2018",
        "Skov, Laurits, Ruoyun Hui, Vladimir Shchur, et al. 2018. “Detecting Archaic "
        "Introgression Using an Unadmixed Outgroup.” PLOS Genetics 14 (9): e1007641. "
        "https://doi.org/10.1371/journal.pgen.1007641.",
    ),
    (
        "Turner 2025",
        "Turner, Trudy R. 2025. “Changes to Submissions to the AJBA.” American Journal "
        "of Biological Anthropology 186: e70026. "
        "https://doi.org/10.1002/ajpa.70026.",
    ),
]
REFERENCE_KEYS = [record[0] for record in REFERENCE_RECORDS]
REFERENCES = [record[1] for record in REFERENCE_RECORDS]


INTRODUCTION = [
    (
        "Genomic comparisons established gene flow from Neanderthals and Denisovans "
        "into ancestors of present-day populations outside Africa (Green et al. 2010; "
        "Reich et al. 2010). The amount and genomic distribution of introgressed "
        "sequence vary among populations because of demographic history, drift, "
        "selection, and multiple introgression histories (Sankararaman et al. 2014; "
        "Sankararaman et al. 2016; Jacobs et al. 2019). Most summaries emphasize the "
        "proportion of archaic ancestry within a population. A complementary question "
        "is whether two populations carry inferred archaic segments in similar genomic "
        "locations."
    ),
    (
        "Geographic gradients in archaic ancestry may reflect range expansions and "
        "serial demographic processes rather than a single migration event (Quilodran "
        "et al. 2023). Pairwise profile similarity offers a direct descriptive measure "
        "of shared genomic distribution, but it creates dyadic data: every population "
        "appears in many pair rows. Standard row-wise regression tests, bootstraps, or "
        "response shuffles therefore do not preserve the population-level dependence "
        "structure. Quadratic assignment procedures address this problem by permuting "
        "population labels on a complete matrix (Krackhardt 1988; Dekker, Krackhardt, "
        "and Snijders 2007)."
    ),
    (
        "The primary objective was to test whether Neanderthal- and Denisovan-segment "
        "profile similarity declines with great-circle distance across 66 populations "
        "from the 1000 Genomes Project and Human Genome Diversity Project. We also "
        "tested robustness to alternative genomic windows, similarity metrics, "
        "sample-size thresholds, datasets, co-located pairs, and regional omission. A "
        "secondary analysis of the ABO-centered interval was retained because ABO has "
        "an unusually deep allelic history and has motivated founder-effect and "
        "archaic-background hypotheses (Calafell et al. 2008; Halverson and Bolnick "
        "2008; Segurel et al. 2012; Condemi et al. 2021). This focal analysis was "
        "prespecified as exploratory and was not used to infer a migration route."
    ),
]


METHODS = [
    (
        "Data sources and population inclusion",
        [
            (
                "We analyzed publicly archived hmmix segment calls from 1000 Genomes "
                "and HGDP samples in Zenodo record 14136628. Hmmix detects candidate "
                "archaic sequence without requiring an unadmixed modern outgroup (Skov "
                "et al. 2018). Source population definitions followed the 1000 Genomes "
                "and HGDP resources (1000 Genomes Project Consortium 2015; Bergström "
                "et al. 2020). SHA-256 checksums of both raw files are written to the "
                "analysis provenance record."
            ),
            (
                "Segments with mean posterior probability below 0.8 were excluded. "
                "Populations with fewer than seven represented individuals were "
                "excluded, leaving 3,134 individuals in 66 populations. Source calls "
                "annotated as Neanderthal or Both entered the Neanderthal profile; "
                "calls annotated as Denisova or Both entered the Denisovan profile."
            ),
        ],
    ),
    (
        "Population profiles and pairwise similarity",
        [
            (
                "Autosomes were partitioned into 500-kb windows. Within each ancestry "
                "category, overlapping or fragmented source segments were collapsed so "
                "that each individual-haplotype-window contributed at most one presence. "
                "For each population and window, unique haplotype presences were divided "
                "by twice the number of represented individuals. A runtime validity "
                "check required every frequency to lie between 0 and 1."
            ),
            (
                "For each population pair, Pearson correlation was calculated across "
                "the union of windows with a nonzero frequency in either population. "
                "Pairs required more than 100 union windows for Neanderthal and more "
                "than 50 for Denisovan profiles. The 66-population matrices contained "
                "2,145 unique off-diagonal pairs. Correlations describe profile "
                "similarity and do not establish identity by descent. Spearman "
                "correlation and cosine similarity were calculated as metric "
                "sensitivities."
            ),
            (
                "Population coordinates were consolidated in a versioned metadata "
                "table from source sampling locations or population centroids. "
                "Great-circle distance was calculated with the Haversine formula. "
                "Coordinate uncertainty and co-located population labels were assessed "
                "by excluding zero-distance pairs."
            ),
        ],
    ),
    (
        "Dyadic regression and permutation inference",
        [
            (
                "The primary expanded descriptive model regressed pairwise similarity "
                "on distance per 1,000 km, involvement of one of four designated "
                "recently admixed American populations (PUR, CLM, MXL, or PEL), "
                "same-continent status, and same-dataset status. These indicators are "
                "coarse sensitivity covariates, not individual ancestry estimates or "
                "causal controls. Distance-only models were also fit."
            ),
            (
                "Coefficient P values used 9,999 quadratic assignment permutations. "
                "At each iteration, the response matrix was permuted by the same random "
                "population-label order on rows and columns, after which the model was "
                "refit. Two-sided P values were the proportion of permuted coefficient "
                "magnitudes at least as large as the observed magnitude, including a "
                "plus-one correction. Descriptive R-squared values quantify fit to the "
                "observed pair matrix and are not interpreted as independent "
                "observations or causal variance explained."
            ),
            (
                "Population-deletion stability intervals were calculated by refitting "
                "the expanded model after removing every pair containing one population "
                "in turn and reporting the 2.5th and 97.5th percentiles of the resulting "
                "coefficients. These are sensitivity intervals rather than "
                "independent-sample confidence intervals."
            ),
        ],
    ),
    (
        "Residual outliers and multiple testing",
        [
            (
                "Outlier analysis was restricted to the complete matrix after removing "
                "PUR, CLM, MXL, and PEL. Similarity was modeled using distance, "
                "same-continent status, and same-dataset status. Positive residuals "
                "were standardized by the residual standard deviation. For every pair, "
                "a one-sided nominal P value was calculated from its own residual null "
                "distribution across 9,999 population-label permutations. The "
                "Benjamini-Hochberg procedure was applied jointly to all non-admixed "
                "pairs within each ancestry analysis (Benjamini and Hochberg 1995). "
                "A supported positive outlier required z>2 and q<0.10."
            ),
        ],
    ),
    (
        "Robustness analyses",
        [
            (
                "We repeated distance-only population-label tests for 250-kb, 500-kb, "
                "and 1-Mb windows. At 500 kb, robustness summaries compared Pearson, "
                "Spearman, and cosine similarity; minimum population sizes of 7, 10, "
                "15, and 20; the complete dataset, non-admixed populations, 1000 "
                "Genomes-only and HGDP-only subsets; exclusion of zero-distance pairs; "
                "and leave-one-continent-out subsets. Full-window Pearson correlation "
                "and presence-absence Jaccard similarity assessed sensitivity to the "
                "nonzero-window union. Sensitivity tests used 999 "
                "population-label permutations. No genome-wide callable mask was "
                "available in the source release, so mask-adjusted profiles could not "
                "be evaluated."
            ),
        ],
    ),
    (
        "Secondary ABO-centered analysis",
        [
            (
                "The ABO gene was defined on GRCh38 as chr9:133,233,278-133,276,024. "
                "We distinguished strict gene overlap from any overlap with a 500-kb "
                "interval spanning chr9:133.0-133.5 Mb. Population carrier frequencies "
                "used unique individuals in the numerator and all represented source "
                "individuals in the denominator."
            ),
            (
                "For Neanderthal or Both segments in the interval, similarity counts to "
                "Altai, Vindija, and Chagyrskaya were compared; tied maxima remained "
                "ties. The Vindija reference is a high-coverage Neanderthal genome "
                "(Prüfer et al. 2017). The O2-defining rs41302905 T allele was summarized "
                "from Ensembl/1000 Genomes frequencies and published Solomon Islands "
                "frequencies (Ohashi et al. 2006). Ancient-window observations were "
                "descriptively extracted from public outputs associated with Iasi et "
                "al. (2024); ancient and modern calls were not directly compared "
                "statistically."
            ),
        ],
    ),
    (
        "Ethical review, community engagement, and interpretation",
        [
            (
                "This computational secondary analysis used de-identified public data "
                "and involved no recruitment, contact, biospecimen collection, or new "
                "individual-level phenotype inference. The author did not obtain a "
                "separate institutional review determination for this secondary "
                "analysis; approvals, consent, and data-access procedures were those "
                "reported by the source studies. This limitation is disclosed rather "
                "than treating public availability as equivalent to unrestricted "
                "ethical reuse."
            ),
            (
                "No source community or stakeholder representatives participated in "
                "the design, analysis, interpretation, or dissemination of the present "
                "secondary study, and no direct community return-of-results process was "
                "conducted. Because the dataset includes Indigenous participants and "
                "the topic can affect narratives of ancestry and migration, analyses "
                "were interpreted in light of Indigenous data-governance guidance and "
                "the CARE principles (Claw et al. 2018; Carroll et al. 2020). Population "
                "labels were retained only when needed for transparent source-data "
                "description; locus-level observations were not generalized to "
                "communities, and migration routes were not assigned from these data. "
                "The public article, code, and derived aggregate results are the current "
                "means of results availability. These disclosures follow the expanded "
                "AJBA guidance on ethical review and stakeholder communication (Turner "
                "2025)."
            ),
        ],
    ),
]


RESULTS = [
    (
        "Data-validity correction",
        (
            "Collapsing fragmented segments at the individual-haplotype-window level "
            "removed duplicate contributions that could otherwise make a nominal "
            "frequency exceed 1. In the rebuilt profiles, the maximum frequency was "
            "1.0 for both ancestry categories and no population-window frequency "
            "exceeded 1. The analysis retained 66 populations, 3,134 individuals, and "
            "2,145 unique population pairs."
        ),
        [],
    ),
    (
        "Geographic distance decay",
        (
            "Neanderthal profile similarity declined with distance "
            f"(raw r={value(NEANDERTHAL, 'raw_r')}); the corresponding Denisovan "
            f"correlation was {value(DENISOVAN, 'raw_r')}. Partial distance "
            "correlations from the expanded descriptive models were "
            f"{value(NEANDERTHAL, 'partial_r')} and "
            f"{value(DENISOVAN, 'partial_r')}. Distance-only R-squared values were "
            f"{value(NEANDERTHAL, 'distance_only_r_squared')} and "
            f"{value(DENISOVAN, 'distance_only_r_squared')}; expanded-model values "
            f"were {value(NEANDERTHAL, 'expanded_r_squared')} and "
            f"{value(DENISOVAN, 'expanded_r_squared')}. The QAP distance coefficients "
            f"per 1,000 km were {value(NEANDERTHAL, 'distance_qap_beta', 5)} "
            f"(P={value(NEANDERTHAL, 'distance_qap_p', 4)}) and "
            f"{value(DENISOVAN, 'distance_qap_beta', 5)} "
            f"(P={value(DENISOVAN, 'distance_qap_p', 4)}) (Figure 1; Table 1)."
        ),
        ["Figure 1", "Table 1"],
    ),
    (
        "Population structure and robustness",
        (
            "The representative heat maps showed broad regional blocks and a stronger "
            "Oceanian contrast in the Denisovan profile (Figure 2). The complete "
            "66-population heat map is provided as Figure S1. Negative distance "
            "correlations were examined across admixture exclusions, within-dataset "
            "subsets, minimum sample sizes, and regional omissions (Figure 3). "
            "Window-size results at 250 kb, 500 kb, and 1 Mb are shown in Figure S2. "
            "These analyses were treated as robustness checks rather than independent "
            "confirmatory tests."
        ),
        ["Figure 2", "Figure 3"],
    ),
    (
        "Residual outlier testing",
        (
            "No non-admixed pair met both the positive-residual z>2 criterion and "
            "Benjamini-Hochberg q<0.10 for either ancestry category. Nominal residual "
            "ranks are retained in the full pairwise data table for auditability but "
            "are not interpreted as statistically supported population connections."
        ),
        [],
    ),
    (
        "Secondary ABO-window observations",
        (
            "The 500-kb ABO-centered scan identified 834 Neanderthal or Both source "
            "segments, of which 129 overlapped the ABO gene. Of the 834 interval "
            "segments, 335 had tied maximum reference similarity and were not forced "
            "to a lineage. In the Indigenous American HGDP subset, one Pima segment "
            "overlapped ABO and one Maya segment lay downstream within the wider "
            "interval. Both were Vindija-closest, but two segments among 41 represented "
            "individuals do not support a regional proportion or migration-route "
            "inference (Figure 4; Table 2). O2 frequencies, an Ancient North Eurasian "
            "context diagram, and the non-comparable ancient-window extraction are "
            "provided only as Figure S3, Figure S4, and Figure S5."
        ),
        ["Figure 4", "Table 2"],
    ),
]


DISCUSSION = [
    (
        "After correction of the population-frequency construction, both Neanderthal "
        "and Denisovan profile similarities retained negative geographic associations. "
        "The result is therefore not an artifact of allowing fragmented segments to "
        "contribute repeatedly to the same haplotype-window. The revised estimates "
        "should replace all values from the earlier prototype analysis."
    ),
    (
        "The population-label permutation is central to interpretation. A dataset of "
        "2,145 pairs does not contain 2,145 independent geographic comparisons because "
        "each of 66 populations appears repeatedly. QAP preserves the complete matrix "
        "while testing whether the observed distance coefficient is unusual under "
        "population relabeling (Krackhardt 1988; Dekker, Krackhardt, and Snijders "
        "2007). The expanded-model R-squared values remain descriptive; coarse "
        "same-continent, recent-admixture, and dataset indicators should not be read as "
        "causal adjustment."
    ),
    (
        "The distance-decay signal is compatible with broad serial demographic "
        "structure and the spatial patterning of introgressed sequence described in "
        "earlier work (Sankararaman et al. 2014; Sankararaman et al. 2016; Quilodran "
        "et al. 2023). It does not identify the timing, direction, or number of "
        "migration or introgression events. Population coordinates are approximations, "
        "and archaic-call similarity can also reflect callability, allele-frequency "
        "differences, linkage, selection, and reference-panel composition."
    ),
    (
        "The absence of FDR-supported residual outliers constrains the strongest "
        "historical claims. A highly ranked pair cannot be promoted as evidence for a "
        "special connection when its pair-specific permutation result does not survive "
        "the declared testing family. This is especially important for admixed "
        "American populations, for which recent mixture can alter both inferred "
        "archaic profiles and geographic interpretations."
    ),
    (
        "The ABO analysis illustrates the limits of a focal-locus narrative. ABO has "
        "deep allelic history, and selection can affect the persistence of introgressed "
        "sequence (Segurel et al. 2012; Petr et al. 2019). Nevertheless, an inferred "
        "segment in a 500-kb interval is not an ABO allele, closest-reference similarity "
        "is not a transmission path, and the O2-defining variant cannot be labeled "
        "Neanderthal-derived from proximity alone. The Pima and Maya observations are "
        "individual segment records, not population prevalence estimates."
    ),
    (
        "Published Ancient North Eurasian and multiple-founder models provide broader "
        "contexts for First American ancestry (Raghavan et al. 2014; Skoglund et al. "
        "2015), but they do not validate a route for either ABO-window segment. Such a "
        "claim would require independently sampled ancient genomes, a phased local "
        "genealogy, method-matched calling, and explicit community-engaged governance "
        "for any new Indigenous genomic analysis."
    ),
    (
        "Limitations include modest sizes for several populations, sparse Denisovan "
        "calls outside Oceania, centroid-based distances, lack of a common callable "
        "mask, and correlation measures that do not distinguish identity by descent "
        "from identity by state. The dataset combines two projects, and same-dataset "
        "status only partially represents technical heterogeneity. Population-deletion "
        "and sensitivity analyses assess stability but cannot replace validation in "
        "independent modern and ancient data."
    ),
    (
        "In conclusion, population-level archaic-segment profiles show a broad "
        "geographic distance-decay pattern under dependence-aware permutation tests. "
        "The result supports a descriptive relationship between geography and the "
        "genomic distribution of inferred archaic segments. It does not establish an "
        "exceptional population pair, an ABO-mediated migration history, or a specific "
        "route through Beringia or island Southeast Asia."
    ),
]


FIGURES = {
    1: (
        "fig1_sharing_vs_distance.png",
        "Archaic-segment profile similarity and geographic distance. Each point is a "
        "dependent population pair. Lines are descriptive distance-only fits; reported "
        "P values use population-label quadratic assignment permutations.",
    ),
    2: (
        "fig2_sharing_heatmap.png",
        "Pairwise archaic-segment profile similarity for 31 prespecified populations. "
        "The subset is displayed for legibility; all 66 populations were analyzed.",
    ),
    3: (
        "fig4_sensitivity_admixed.png",
        "Descriptive distance correlations across population, sample-size, dataset, "
        "zero-distance, and leave-one-continent-out sensitivities.",
    ),
    4: (
        "fig5_abo_sublineage.png",
        "Secondary ABO-centered analysis. Closest-reference counts retain tied maxima. "
        "The Pima segment overlaps ABO; the Maya segment is within the wider interval "
        "but does not overlap the gene. Counts are segments, not regional frequencies.",
    ),
}


SUPPORTING_FIGURES = {
    1: (
        "figS1_full_heatmap.png",
        "Complete 66-population Neanderthal and Denisovan profile-similarity matrices.",
    ),
    2: (
        "figS2_window_sensitivity.png",
        "Descriptive geographic distance correlations at 250-kb, 500-kb, and 1-Mb "
        "window sizes; QAP results are tabulated in Supplementary Data.",
    ),
    3: (
        "fig6_o2_introgression.png",
        "O2-defining allele frequencies and ABO-window segment-carrier frequencies. "
        "The panels use different sources and are not an association analysis.",
    ),
    4: (
        "fig7_ane_model.png",
        "Ancient North Eurasian contextual hypothesis. Dashed arrows represent a "
        "testable narrative, not evidence that either observed segment followed the "
        "illustrated route.",
    ),
    5: (
        "fig8_temporal_dynamics.png",
        "Descriptive ancient and modern ABO-window summaries generated by different "
        "pipelines; no formal temporal comparison is made.",
    ),
}
