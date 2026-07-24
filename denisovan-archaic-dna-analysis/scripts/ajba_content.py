"""Revised AJBA manuscript content populated from current analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
STATISTICS = json.loads(
    (PROJECT_DIR / "data" / "correction_stats.json").read_text(encoding="utf-8")
)
NEANDERTHAL = STATISTICS["nean"]
DENISOVAN = STATISTICS["deni"]
PROVENANCE = json.loads(
    (PROJECT_DIR / "data" / "analysis_provenance.json").read_text(encoding="utf-8")
)


def value(statistics: dict[str, object], key: str, digits: int = 3) -> str:
    return f"{float(statistics[key]):.{digits}f}"


def _abo_counts() -> dict[str, int]:
    segments = pd.read_csv(PROJECT_DIR / "data" / "abo_neanderthal_segments.csv")
    populations = pd.read_csv(PROJECT_DIR / "data" / "abo_population_summary.csv")
    indigenous = populations["analysis_group"] == "Indigenous Americas"
    return {
        "interval_segments": int(len(segments)),
        "strict_overlap": int(segments["strict_overlap"].sum()),
        "ties": int((segments["closest_reference"] == "Tie").sum()),
        "indigenous_individuals": int(populations.loc[indigenous, "n_total"].sum()),
    }


ABO = _abo_counts()
INDIVIDUALS = int(PROVENANCE["individuals"])
POPULATIONS = int(PROVENANCE["included_populations"])
PAIRS = int(PROVENANCE["population_pairs"])
PRIMARY_PERMUTATIONS = int(STATISTICS["permutations"])
SENSITIVITY_PERMUTATIONS = int(STATISTICS["sensitivity_permutations"])


TITLE = (
    "Population structure, not special connections: a dependence-aware baseline "
    f"for archaic-segment sharing across {POPULATIONS} human populations"
)
RUNNING_TITLE = "A dependence-aware archaic-sharing baseline"
AUTHOR = "Onishi Tatsuki"
AFFILIATION = "Data Science and AI Innovation Research Promotion Center"
CORRESPONDENCE = (
    "Onishi Tatsuki, Data Science and AI Innovation Research Promotion Center; "
    "Email: bougtoir@gmail.com"
)
ABSTRACT = (
    "Archaic-like segments near focal loci such as the ABO blood-group gene are "
    "often read as evidence of special population connections or migration "
    "routes, yet such readings are rarely tested against a genome-wide baseline "
    "that respects the dependence structure of pairwise data. We built a "
    "reproducible baseline for population-level archaic-segment sharing and used "
    "it as a well-powered negative test of exceptional-connection and "
    "focal-locus claims. High-confidence Neanderthal and Denisovan "
    f"introgression calls from {INDIVIDUALS:,} individuals in {POPULATIONS} "
    "populations were summarised in 500-kilobase windows, and profile similarity "
    f"was computed for {PAIRS:,} population pairs. Distance associations and "
    "pair-level outliers were assessed with population-label permutation tests "
    "and false-discovery-rate control. Profile similarity declined with "
    f"geographic distance for Neanderthal (r={value(NEANDERTHAL, 'raw_r')}) and "
    f"Denisovan (r={value(DENISOVAN, 'raw_r')}) segments, with partial distance "
    f"correlations of {value(NEANDERTHAL, 'partial_r')} and "
    f"{value(DENISOVAN, 'partial_r')} and permutation P values of "
    f"{value(NEANDERTHAL, 'distance_qap_p', 4)} and "
    f"{value(DENISOVAN, 'distance_qap_p', 4)}. No non-admixed pair reached both a "
    "residual above two standard deviations and a false-discovery rate below "
    "0.10, and a prespecified ABO-window scan showed no route-level signal. "
    "Population-level archaic-segment sharing reflects broad geographic structure "
    "but supports neither exceptional population pairs nor an ABO-mediated "
    "migration history, providing a reusable baseline for evaluating focal-locus "
    "archaic claims."
)
KEYWORDS = (
    "ABO Blood-Group System; Gene Flow; Genetics, Population; "
    "Models, Statistical; Neanderthals"
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
]
REFERENCE_KEYS = [record[0] for record in REFERENCE_RECORDS]
REFERENCES = [record[1] for record in REFERENCE_RECORDS]


INTRODUCTION = [
    (
        "Genomic comparisons established gene flow from Neanderthals "
        "(Homo neanderthalensis) and Denisovans "
        "into ancestors of present-day populations outside Africa (Green et al. 2010; "
        "Reich et al. 2010). The amount and genomic distribution of introgressed "
        "sequence vary among populations because of demographic history, drift, "
        "selection, and multiple introgression histories (Sankararaman et al. 2014; "
        "Sankararaman et al. 2016; Jacobs et al. 2019). These differences invite a "
        "recurring style of inference in which shared archaic segments, often at a "
        "focal locus such as the ABO blood-group gene, are read as evidence of a "
        "special connection between two populations or of a particular migration "
        "route (Calafell et al. 2008; Halverson and Bolnick 2008; Condemi et al. "
        "2021)."
    ),
    (
        "Such claims are difficult to evaluate because pairwise profile similarity is "
        f"dyadic: each of {POPULATIONS} populations appears in many pair rows, so the "
        f"{PAIRS:,} pairs "
        "are not independent observations. Standard row-wise regressions, bootstraps, "
        "or response shuffles do not preserve this population-level dependence, and an "
        "apparently exceptional pair can arise from broad structure alone. What is "
        "generally missing is a genome-wide baseline that constructs population "
        "profiles reproducibly, tests distance and pair-level effects under a "
        "permutation scheme that respects the dependence structure, and applies "
        "explicit multiple-testing control. Quadratic assignment procedures (QAP) "
        "permute population labels on a complete matrix and provide exactly this kind "
        "of dependence-aware test (Krackhardt 1988; Dekker, Krackhardt, and Snijders "
        "2007)."
    ),
    (
        "We build such a baseline and use it as a well-powered negative test of two "
        "recurring claims: that particular population pairs share an exceptional "
        "excess of archaic segments, and that a focal locus such as ABO marks a "
        "specific migration route. A clearly framed negative result under "
        "dependence-aware inference is itself informative, because it sets the "
        "genome-wide expectation that any positive focal-locus or special-connection "
        "claim must exceed. Using "
        "great-circle distance across 66 populations from the 1000 Genomes Project "
        "and Human Genome Diversity Project (HGDP), we test whether Neanderthal- and "
        "Denisovan-segment profile similarity declines with distance, whether any "
        "population pair is a false-discovery-rate-supported residual outlier, and "
        "whether a prespecified interval centered on the ABO blood-group locus, chosen "
        "because ABO has an unusually deep allelic history and has motivated "
        "founder-effect and archaic-background hypotheses (Segurel et al. 2012; "
        "Calafell et al. 2008; Halverson and Bolnick 2008; Condemi et al. 2021), "
        "shows anything beyond the genome-wide expectation. Robustness to alternative "
        "windows, similarity metrics, sample-size thresholds, datasets, co-located "
        "pairs, and regional omission is assessed throughout. The focal ABO analysis "
        "is prespecified as exploratory and is not used to infer a migration route."
    ),
]


METHODS = [
    (
        "Data sources and population inclusion",
        [
            (
                "We analyzed publicly archived segment calls generated with hmmix, a "
                "hidden Markov model-based method that detects candidate archaic "
                "sequence without requiring an unadmixed modern outgroup (Skov et al. "
                "2018). Segment files for the 1000 Genomes Project and Human Genome "
                "Diversity Project (HGDP) samples were obtained from Zenodo record "
                "14136628. Source population definitions followed those resources "
                "(1000 Genomes Project Consortium 2015; Bergström et al. 2020). Secure "
                "Hash Algorithm 256 (SHA-256) checksums of both raw files are "
                "written to the analysis provenance record."
            ),
            (
                "Segments with mean posterior probability below 0.8 were excluded. "
                "Populations with fewer than seven represented individuals were "
                f"excluded, leaving {INDIVIDUALS:,} individuals in {POPULATIONS} "
                "populations. Source calls "
                "annotated as Neanderthal or Both entered the Neanderthal profile; "
                "calls annotated as Denisova or Both entered the Denisovan profile."
            ),
        ],
    ),
    (
        "Population profiles and pairwise similarity",
        [
            (
                "Autosomes were partitioned into 500-kilobase (kb) windows. Within each "
                "ancestry category, overlapping or fragmented source segments were "
                "collapsed so that each individual-haplotype-window contributed at most "
                "one presence. "
                "For each population and window, unique haplotype presences were divided "
                "by twice the number of represented individuals. A runtime validity "
                "check required every frequency to lie between 0 and 1."
            ),
            (
                "For each population pair, Pearson correlation was calculated across "
                "the union of windows with a nonzero frequency in either population. "
                "Pairs required more than 100 union windows for Neanderthal and more "
                "than 50 for Denisovan profiles. The "
                f"{POPULATIONS}-population matrices contained {PAIRS:,} unique "
                "off-diagonal pairs. Correlations describe profile "
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
                "recently admixed American populations: Puerto Ricans from Puerto Rico "
                "(PUR), Colombians from Medellín, Colombia (CLM), people with Mexican "
                "ancestry from Los Angeles, United States (MXL), or Peruvians from "
                "Lima, Peru (PEL). The model also included same-continent status and "
                "same-dataset status. These indicators are coarse sensitivity "
                "covariates, not individual ancestry estimates or "
                "causal controls. Distance-only models were also fit."
            ),
            (
                f"Coefficient P values used {PRIMARY_PERMUTATIONS:,} quadratic "
                "assignment permutations. "
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
                f"distribution across {PRIMARY_PERMUTATIONS:,} population-label "
                "permutations. Because pair residuals are dyadically dependent, this "
                "null was generated by the same joint row-and-column population-label "
                "permutation used for the coefficient tests rather than by row-wise "
                "resampling, following the rationale for multiple-regression quadratic "
                "assignment with dependent dyads (Dekker, Krackhardt, and Snijders "
                "2007). The "
                "Benjamini-Hochberg procedure was applied jointly to all non-admixed "
                "pairs within each ancestry analysis to control the false discovery "
                "rate (FDR) (Benjamini and Hochberg 1995). "
                "A supported positive outlier required z>2 and q<0.10."
            ),
        ],
    ),
    (
        "Robustness analyses",
        [
            (
                "We repeated distance-only population-label tests for 250-kb, 500-kb, "
                "and 1-megabase (Mb) windows. At 500 kb, robustness summaries compared "
                "Pearson, Spearman, and cosine similarity; minimum population sizes of "
                "7, 10, 15, and 20; the complete dataset, non-admixed populations, 1000 "
                "Genomes-only and HGDP-only subsets; exclusion of zero-distance pairs; "
                "and leave-one-continent-out subsets. Full-window Pearson correlation "
                "and presence-absence Jaccard similarity assessed sensitivity to the "
                "nonzero-window union. Sensitivity tests used "
                f"{SENSITIVITY_PERMUTATIONS:,} "
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
                "The ABO gene was defined on Genome Reference Consortium Human Build "
                "38 (GRCh38) as chromosome 9 (chr9):133,233,278-133,276,024. "
                "We distinguished strict gene overlap from any overlap with a 500-kb "
                "interval spanning chr9:133.0-133.5 Mb. Population carrier frequencies "
                "used unique individuals in the numerator and all represented source "
                "individuals in the denominator."
            ),
            (
                "For Neanderthal or Both segments in the interval, similarity counts to "
                "Altai, Vindija, and Chagyrskaya were compared; tied maxima remained "
                "ties. The Vindija reference is a high-coverage Neanderthal genome "
                "(Prüfer et al. 2017). The O2 blood-group subtype-defining rs41302905 T "
                "allele was summarized "
                "from Ensembl/1000 Genomes frequencies and published Solomon Islands "
                "frequencies (Ohashi et al. 2006). Ancient-window observations were "
                "extracted by a documented, reproducible script from the public "
                "Neanderthal-segment catalogue of Iasi et al. (2024), using the GRCh37 "
                "ABO interval that corresponds to the GRCh38 window analysed here; "
                "ancient and modern calls used different pipelines and were not "
                "directly compared statistically."
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
                "the Collective Benefit, Authority to Control, Responsibility, and "
                "Ethics (CARE) Principles (Claw et al. 2018; Carroll et al. 2020). "
                "Population labels were retained only when needed for transparent "
                "source-data description; locus-level observations were not generalized "
                "to communities, and migration routes were not assigned from these data. "
                "The public article, code, and derived aggregate results are the current "
                "means of results availability. These disclosures are made in the "
                "interest of transparent ethical reporting for secondary genomic "
                "analyses."
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
            f"exceeded 1. The analysis retained {POPULATIONS} populations, "
            f"{INDIVIDUALS:,} individuals, and {PAIRS:,} unique population pairs."
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
            f"(P={value(DENISOVAN, 'distance_qap_p', 4)}) (Figure 1)."
        ),
        ["Figure 1"],
    ),
    (
        "Population structure",
        (
            "The representative heat maps showed broad regional blocks and a stronger "
            "Oceanian contrast in the Denisovan profile (Figure 2). The complete "
            "66-population heat map is provided as Figure S1."
        ),
        ["Figure 2"],
    ),
    (
        "Robustness analyses",
        (
            "Negative distance correlations were examined across admixture "
            "exclusions, within-dataset subsets, minimum sample sizes, and regional "
            "omissions. Figure 3 shows the effect of excluding designated recently "
            "admixed populations, and Figure 4 shows window-size results at 250 kb, "
            "500 kb, and 1 Mb. These analyses were treated as robustness checks rather "
            "than independent confirmatory tests."
        ),
        ["Figure 3", "Figure 4"],
    ),
    (
        "Residual outlier testing",
        (
            "No non-admixed pair met both the positive-residual z>2 criterion and "
            "Benjamini-Hochberg q<0.10 for either ancestry category. Nominal residual "
            "ranks are retained in the full pairwise data table for auditability but "
            "are not interpreted as statistically supported population connections "
            "(Table 1)."
        ),
        ["Table 1"],
    ),
    (
        "Prespecified ABO-window check",
        (
            "As a prespecified focal-locus check, the 500-kb ABO-centered scan "
            f"identified {ABO['interval_segments']:,} Neanderthal or Both source "
            f"segments, of which {ABO['strict_overlap']} overlapped the ABO gene and "
            f"{ABO['ties']} were tied for maximum reference similarity. In the "
            "Indigenous American HGDP subset only two segments among "
            f"{ABO['indigenous_individuals']} represented individuals fell in the "
            "interval. Consistent with the genome-wide result, this focal scan "
            "produced no route-level signal; exploratory segment-level compositions "
            "and counts are provided as Supplementary material (Figure S2; Table S1) "
            "and are not interpreted as regional proportions or migration routes."
        ),
        [],
    ),
    (
        "Contextual displays",
        (
            "Several descriptive context panels are provided as supplementary "
            "figures because they do not derive from the pairwise analysis. The "
            "O2-defining allele and ABO-window carrier summaries use different "
            "sources and are displayed descriptively rather than as an association "
            "analysis (Figure S3). Ancient and modern ABO-window observations were "
            "produced by different pipelines and permit no formal temporal comparison "
            "(Figure S4). A bivariate global map summarising each population's mean "
            "Neanderthal and Denisovan segment coverage from the present profiles "
            "provides broad geographic context and was not used in the statistical "
            "models (Figure S5)."
        ),
        [],
    ),
]


DISCUSSION = [
    (
        "After correction of the population-frequency construction, both Neanderthal "
        "and Denisovan profile similarities retained negative geographic associations. "
        "The result is therefore not an artifact of allowing fragmented segments to "
        "contribute repeatedly to the same haplotype-window. The revised estimates "
        "are used throughout the manuscript and submission materials."
    ),
    (
        "The population-label permutation is central to interpretation. A dataset of "
        f"{PAIRS:,} pairs does not contain {PAIRS:,} independent geographic "
        f"comparisons because each of {POPULATIONS} populations appears repeatedly. "
        "QAP preserves the complete matrix "
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
        "geographic distance-decay pattern under dependence-aware permutation tests, "
        "but the same analysis provides no support for an exceptional population pair, "
        "an ABO-mediated migration history, or a specific route through Beringia or "
        "island Southeast Asia. The contribution is therefore less a new signal than "
        "a reproducible, dependence-aware baseline: by combining frequency-constrained "
        "profile construction, population-label QAP inference, and explicit "
        "false-discovery-rate control, it offers a reusable negative control against "
        "which focal-locus and special-connection archaic claims can be judged."
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
        "Sensitivity of the descriptive Neanderthal distance correlation to exclusion "
        "of designated recently admixed populations.",
    ),
    4: (
        "fig5_window_sensitivity.png",
        "Descriptive geographic distance correlations at 250-kb, 500-kb, and 1-Mb "
        "window sizes. Quadratic assignment procedure results are tabulated in "
        "Supplementary Data.",
    ),
}


SUPPORTING_FIGURES = {
    1: (
        "figS1_full_heatmap.png",
        "Complete 66-population Neanderthal and Denisovan profile-similarity matrices.",
    ),
    2: (
        "fig5_abo_sublineage.png",
        "Exploratory ABO-centered analysis preserving the historical grouped-bar and "
        "segment-map layout. Equal maximum-similarity ties are excluded from the "
        "displayed three-reference proportions and retained in Supplementary Data. The "
        "Pima segment overlaps ABO; the Maya segment is within the wider interval but "
        "does not overlap the gene. Counts are segments, not regional frequencies, and "
        "are not interpreted as a migration route.",
    ),
    3: (
        "fig6_o2_introgression.png",
        "O2 blood-group subtype-defining allele frequencies and ABO-window "
        "segment-carrier frequencies. "
        "The panels use different sources and are not an association analysis; "
        "proximity does not establish that the O2 allele is Neanderthal-derived.",
    ),
    4: (
        "fig8_temporal_dynamics.png",
        "Descriptive ancient and modern ABO-window summaries generated by different "
        "pipelines; no formal temporal comparison is made.",
    ),
    5: (
        "fig9_bivariate_world_map.png",
        "Bivariate global context computed in this study. Circle area encodes the "
        "mean per-bin Neanderthal-segment coverage and colour encodes the mean "
        "per-bin Denisovan-segment coverage for each population, both from "
        "data/population_profiles_500kb.npz; coordinates are approximate sampling "
        "locations from data/population_metadata.csv. These descriptive summaries "
        "were not used in the pairwise statistical models.",
    ),
}
