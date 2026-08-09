# Quantifying the Point of No Return in Global AI/ML Research Communities

**Article type:** Research Article

## Abstract

Artificial intelligence (AI) and machine learning (ML) research is increasingly concentrated in a few regions, raising the risk that smaller research communities fall below a minimum viable coauthor pool and cannot recover. We model each civilisation as a six-compartment system of domestic and abroad early-career, high-impact, and principal-investigator researchers, and estimate transition rates from OpenAlex Artificial Intelligence works (subfield 1702). The minimum viable coauthor threshold is defined as M = k × c_bar, where c_bar is the mean number of authors per work and k is the median number of distinct last-author groups observed per recent year. Across 9 groups, equilibrium domestic active pools remain above their thresholds, but the closest point of no return is observed for the Other Civilizations group, where a proportional change of 0.75 in I0 (critical factor 0.25×) would drive the active pool to its threshold. Dropout is the most powerful positive policy lever: reducing it by 10% yields the largest margin gain per unit effort in every group. Historical and saturating-inflow counterfactuals show that the model is most sensitive to exogenous entry and attrition. These results provide a quantitative framework for early, safety-factor-bound interventions that preserve civilisational diversity in AI/ML research.

**Keywords:** researcher mobility; artificial intelligence; civilisation grouping; ordinary differential equations; point of no return; innovation studies

## Highlights

- Nine civilisations modelled as six-compartment ODEs fitted to OpenAlex AI/ML data.
- Closest point of no return for the active pool is Other Civilizations via I0 (critical factor 0.25×).
- Reducing researcher dropout is the largest positive lever across all groups.

## Data and Code Availability

This study uses publication metadata from the OpenAlex API (subfield 1702, Artificial Intelligence; 2000–2023). The extraction and analysis code, the country-to-civilisation mapping, and the result CSVs used to generate this manuscript are available in the public GitHub repository https://github.com/bougtoir/researcher-mobility-ode. OpenAlex data are released under CC0.

## Declarations

**Funding:** [To be completed / removed for double-blind review]

**Competing interests:** [To be completed / removed for double-blind review]

**Author contributions:** [To be completed / removed for double-blind review]

**Acknowledgments:** [To be completed / removed for double-blind review]

## 1. Introduction

Most debates on research mobility focus on net flows: which country gains researchers and which loses them. Net-flow accounting is useful for headlines, but it hides the transition rates that actually move researchers between career stages and locations[1]. A small proportional change in one of those rates can, over time, push a research community below the minimum coauthor pool it needs to remain viable. Once the pool falls below that threshold, recovery becomes difficult or impossible, even if policy is later reversed. That is the point of no return that motivates this paper[1].

Artificial intelligence and machine learning have become the archetypal general-purpose technologies of the current era[6,7,8]. Their development depends on a relatively small, highly mobile workforce of doctoral and post-doctoral researchers, principal investigators, and research engineers[6]. The geographic concentration of this workforce has generated both scientific and geopolitical concern. Policymakers in the United States, China, Europe, Japan, India and elsewhere now treat AI talent as a strategic input, and several governments have introduced incentives to attract or retain researchers[5,6]. Most of those policies are evaluated by their immediate net-flow effects. They rarely ask which transition in the career pipeline is the binding constraint, or how close a community is to a threshold where the field can no longer sustain itself.

The civilisation framework offers a natural way to partition the global research population into culturally and institutionally coherent arenas[2]. We adapt Huntington's nine civilisations for AI/ML mobility by keeping the United States, China (Sinic), India (Hindu), Japan, and the Islamic world as distinct groups, splitting the Western bloc into the United States, Anglosphere excluding the United States, Continental Europe and Other Western, and merging the smaller Latin American, Orthodox and African communities into Other Civilizations. This grouping reflects the empirical size and mobility patterns observed in the data rather than a normative claim about civilisational identity.

The central argument of the paper is that preserving civilisational diversity in AI/ML is not only a normative preference but also a safeguard against technological dead ends. When a single region or a small oligopoly dominates a field, the set of research questions, evaluation norms, and institutional incentives narrows[11]. A diverse ecosystem generates competing approaches, which increases the probability that unexpected breakthroughs and error correction survive[11]. If transition rates can be observed with enough temporal resolution, policy can intervene before a community reaches the point of no return. Early, proportionate interventions can prevent the emergence of a monopoly or oligopoly without requiring large ex post rescues.

We therefore address four research questions. First, how close is each civilisation to the point of no return in its AI/ML research community? Second, which transition rates have the largest effect on community size? Third, how have transition rates changed between earlier and later career cohorts, and what would have happened if those rates had persisted? Fourth, what safety-factor-bound policy packages can widen the margin before a point of no return is reached?

The contribution is a reproducible, data-driven transition-rate model that links OpenAlex publication records to a system of ordinary differential equations. The model is intentionally simple: it does not explain why a rate is high or low, but it identifies which rate is closest to a threshold and therefore where early intervention is most urgent.

## 2. Literature and conceptual framework

Researcher mobility has long been studied under the headings of brain drain, brain circulation and brain gain[4,5,10]. Thorn and Holm-Nielsen argue that the mobility of researchers from developing countries can become a gain when return migration and diaspora networks are supported, but it can become a drain when local research environments cannot retain or reproduce talent[4]. Appelt et al., using a gravity framework for 1996-2011, find that scientific collaboration, economic convergence and visa restrictions are the strongest correlates of bilateral mobility[5]. Their analysis shows that mobility is multi-directional: a large share of researcher movement is better described as circulation than as one-way migration.

The AI/ML literature has documented the same patterns at higher resolution. MacroPolo's Global AI Talent Tracker finds that the United States remains the leading destination for top-tier AI researchers, while China and India are expanding domestic retention[6]. AlShebli et al. show that U.S.-China collaboration in AI is more impactful than either country working alone, and that most mobile AI scientists retain collaboration links with their origin country[7]. Yuan et al. find that the brain-drain problem for AI scientists is increasingly serious in developing countries, and that the ties among AI elites are highly clustered[8]. These studies establish that AI/ML talent is mobile, concentrated and strategically important.

What is missing is a formal link between individual transition rates and the long-run viability of a research community. The concept of a minimum viable population, introduced by Shaffer, captures the smallest isolated population that has a high probability of persisting despite demographic, environmental and genetic stochasticity[9]. Transferred to science, the equivalent idea is a minimum viable coauthor pool: the smallest number of active researchers that can continue to produce work at the field's observed coauthor intensity. Below that pool, collaboration networks fragment, mentorship chains break, and the field enters a self-reinforcing decline.

This framing generates four testable hypotheses. H1: Across all groups, the equilibrium active pool exceeds the minimum viable threshold, but the distance to the threshold varies widely. H2: Dropout is the transition rate with the largest negative effect, because attrition removes researchers from every compartment. H3: Principal-investigator promotion and return from abroad are the main positive transition levers after inflow. H4: Smaller civilisations, and those with older cohort structures, sit closer to their point of no return.

## 3. Data and grouping

We extracted AI/ML works and author histories from the OpenAlex API for subfield `subfields/1702` (Artificial Intelligence), using works published between 2000 and 2023[3]. Authors were assigned to a civilisation by the majority country of their affiliated institutions. The mapping is documented in the repository and is reproduced here only in summary. The final groups are: United States, Anglosphere ex-US, Continental Europe, Sinic, Japanese, Hindu, Islamic, Other Western, and Other Civilizations.

Table 1 reports the size and composition of the extracted cohort. The sample is a reproducible pilot extraction; absolute counts are small because the goal is to demonstrate the transition-rate framework rather than to provide a definitive census of global AI/ML researchers.

| Group | Authors | Works | Active | Hits | PIs | Career start | Abroad |
|---|---|---|---|---|---|---|---|
| Anglosphere ex-US | 27 | 1977 | 26 | 25 | 14 | 2006.2 | 19 |
| Continental Europe | 48 | 3840 | 45 | 40 | 23 | 2006.2 | 22 |
| Hindu | 26 | 1754 | 26 | 20 | 13 | 2008.0 | 4 |
| Islamic | 20 | 830 | 20 | 13 | 9 | 2011.5 | 7 |
| Japanese | 26 | 1236 | 21 | 17 | 11 | 2005.7 | 4 |
| Other Civilizations | 20 | 843 | 19 | 14 | 9 | 2009.0 | 6 |
| Other Western | 15 | 947 | 15 | 14 | 5 | 2008.2 | 8 |
| Sinic | 41 | 3397 | 40 | 31 | 20 | 2007.3 | 16 |
| United States | 50 | 4220 | 45 | 47 | 28 | 2006.3 | 18 |

## 4. Methods

### 4.1 Compartment model

Each civilisation is represented by six compartments: domestic early-career researchers (D), abroad early-career researchers (A), domestic hit researchers (H_D), abroad hit researchers (H_A), domestic principal investigators (P_D), and abroad principal investigators (P_A). Transition rates are early-career outflow (α), return (β), hit generation at home and abroad (h_D and h_A), PI promotion at home and abroad (p_D and p_A), and dropout from all compartments (d). The equations are written in Word equation objects in the body of the manuscript.

### 4.2 Endogenous inflow

New entrants are modelled as a function of the domestic PI stock. The linear form is I(P_D) = I_0 + r P_D, with r capped at half the stability-critical value (safety factor 0.5). A saturating alternative, I(P_D) = I_0 + r P_D / (1 + ε P_D), is reported as a robustness check.

### 4.3 Minimum viable coauthor threshold

For each group we computed the mean number of authors per work (c_bar) and the median number of distinct last-author groups observed per recent year (k). The minimum viable domestic active pool is M = k × c_bar. When the equilibrium active pool T = D + H_D + P_D falls below M, the community can no longer produce works at the observed coauthor intensity.

### 4.4 Estimation and equilibrium

Transition rates are estimated as constant per-year hazards from observed proportions within the cohort, with Laplace smoothing to avoid zero probabilities. The ODE system is solved at steady state for each group. Elasticities are computed by perturbing each rate by 1% and re-solving. For point-of-no-return analysis we scale each rate until the active pool reaches M and record the critical factor and its proximity, |critical factor − 1|. Historical counterfactuals split the cohort at career-start year 2010 and re-estimate all rates for the early and late windows. Bootstrap confidence intervals are obtained by resampling authors with replacement. Policy counterfactuals apply proportional changes to individual rates and report the resulting change in safety margin.

## 5. Results

Table 2 reports the equilibrium domestic active pool T, the minimum viable threshold M, and the endogenous inflow parameters for the 9 groups. All groups remain above their threshold under the fitted model, but margins differ by an order of magnitude.

| Group | T_eq | M | Margin | I0 | r | r_obs | r_crit |
|---|---|---|---|---|---|---|---|
| Anglosphere ex-US | 752.12 | 119.78 | 632.34 | 1.55 | 0.00239 | 0.11345 | 0.00478 |
| Continental Europe | 1156.27 | 129.07 | 1027.20 | 2.76 | 0.00261 | 0.12276 | 0.00523 |
| Hindu | 1497.37 | 66.04 | 1431.33 | 1.52 | 0.00106 | 0.11765 | 0.00213 |
| Islamic | 892.42 | 126.52 | 765.89 | 1.16 | 0.00141 | 0.13072 | 0.00282 |
| Japanese | 206.81 | 50.48 | 156.33 | 1.42 | 0.00993 | 0.13904 | 0.01985 |
| Other Civilizations | 424.70 | 104.60 | 320.10 | 1.15 | 0.00310 | 0.13072 | 0.00620 |
| Other Western | 513.12 | 57.17 | 455.95 | 0.87 | 0.00200 | 0.17647 | 0.00400 |
| Sinic | 1783.64 | 112.34 | 1671.29 | 2.38 | 0.00140 | 0.12059 | 0.00281 |
| United States | 801.70 | 132.49 | 669.21 | 2.83 | 0.00396 | 0.10504 | 0.00791 |

![Figure 1](figures/fig1_equilibrium_margin.png)

**Figure 1. Equilibrium domestic active pool (T) and minimum viable coauthor threshold (M) by group.** All groups remain above the threshold, but the margin varies widely.

Table 3 shows the three transition-rate elasticities with the largest absolute impact on T for each group. Dropout (d) is the largest negative lever in every group; promotion of domestic hit researchers to PIs (p_D) and return from abroad (β) are the main positive transition levers after inflow.

| Group | 1st rate | 1st elasticity | 2nd rate | 2nd elasticity | 3rd rate | 3rd elasticity |
|---|---|---|---|---|---|---|
| Anglosphere ex-US | d | -2.162 | p_D | 0.116 | beta | 0.046 |
| Continental Europe | d | -2.100 | p_D | 0.067 | beta | 0.047 |
| Hindu | d | -2.011 | p_D | 0.038 | h_D | 0.013 |
| Islamic | d | -2.051 | p_D | 0.057 | h_D | 0.022 |
| Japanese | d | -2.317 | p_D | 0.233 | h_D | 0.111 |
| Other Civilizations | d | -2.125 | p_D | 0.094 | h_D | 0.047 |
| Other Western | d | -2.123 | p_D | 0.137 | h_D | 0.014 |
| Sinic | d | -2.027 | p_D | 0.035 | h_D | 0.021 |
| United States | d | -2.126 | p_D | 0.087 | h_D | 0.066 |

Table 4 reports, for each group, the single rate that reaches the active-pool threshold with the smallest proportional change. The Other Civilizations group is the most fragile: a proportional change of 0.75 in I0 (critical factor 0.25×) would drive the active pool to its minimum viable threshold.

| Group | Target | Rate | Current | Critical factor | Proximity |
|---|---|---|---|---|---|
| Other Civilizations | domestic_active | I0 | 1.1486 | 0.246 | 0.754 |
| Japanese | domestic_active | I0 | 1.4202 | 0.244 | 0.756 |
| United States | domestic_active | I0 | 2.8304 | 0.165 | 0.835 |
| Anglosphere ex-US | domestic_active | I0 | 1.5548 | 0.159 | 0.841 |
| Islamic | domestic_active | I0 | 1.1638 | 0.142 | 0.858 |
| Continental Europe | domestic_active | I0 | 2.7634 | 0.112 | 0.888 |
| Other Western | domestic_active | I0 | 0.8723 | 0.111 | 0.889 |
| Sinic | domestic_active | I0 | 2.3837 | 0.063 | 0.937 |
| Hindu | domestic_active | I0 | 1.5156 | 0.044 | 0.956 |

![Figure 2](figures/fig2_pnr_proximity.png)

**Figure 2. Closest point-of-no-return proximity by group.** Smaller values mean a smaller proportional change in the listed rate is required to reach the threshold for the stated target pool.

### 5.1 Saturating recruitment extension

Replacing linear inflow with a saturating form lowers equilibrium pools because each additional PI adds fewer entrants. Table 5 compares linear and saturating equilibrium T values.

| Group | Linear T | Saturating T | ε |
|---|---|---|---|
| Anglosphere ex-US | 752.12 | 411.20 | 0.01429 |
| Continental Europe | 1156.27 | 632.67 | 0.00870 |
| Hindu | 1497.37 | 781.23 | 0.01538 |
| Islamic | 892.42 | 469.06 | 0.02222 |
| Japanese | 206.81 | 129.35 | 0.01818 |
| Other Civilizations | 424.70 | 234.34 | 0.02222 |
| Other Western | 513.12 | 270.32 | 0.04000 |
| Sinic | 1783.64 | 940.82 | 0.01000 |
| United States | 801.70 | 462.03 | 0.00714 |

### 5.2 Historical counterfactual

Table 6 compares the equilibrium that would have emerged if the transition rates estimated for the early career window (2000-2010) or the late window (2011-2016) had persisted indefinitely. The late window is shorter and its rates are estimated from younger cohorts, so the comparison should be read as a sensitivity exercise rather than a forecast.

| Group | T early | T late | ΔT (%) | Margin early | Margin late | Δ margin |
|---|---|---|---|---|---|---|
| Anglosphere ex-US | 699.2 | 250.1 | -64.2 | 579.5 | 130.3 | -449.2 |
| Continental Europe | 1053.7 | 791.3 | -24.9 | 924.6 | 662.2 | -262.4 |
| Hindu | 902.2 | 608.4 | -32.6 | 836.1 | 542.4 | -293.7 |
| Islamic | 185.5 | 1106.5 | 496.4 | 59.0 | 979.9 | 920.9 |
| Japanese | 184.3 | 235.3 | 27.7 | 133.8 | 184.8 | 51.0 |
| Other Civilizations | 164.4 | 673.8 | 309.8 | 59.8 | 569.2 | 509.3 |
| Other Western | 304.0 | 239.0 | -21.4 | 246.9 | 181.8 | -65.0 |
| Sinic | 1392.6 | 936.4 | -32.8 | 1280.3 | 824.1 | -456.2 |
| United States | 806.7 | 547.3 | -32.1 | 674.2 | 414.8 | -259.3 |

![Figure 3](figures/fig3_historical_margin.png)

**Figure 3. Change in safety margin between early and late transition-rate regimes.** Positive values mean the late-window rates would produce a larger safety margin if they persisted.

### 5.3 Policy counterfactuals

Table 7 reports the single intervention with the largest margin gain per 10% lever change for each group. Reducing dropout is the dominant positive lever for every civilisation.

| Group | Lever | Direction | Change (%) | Margin gain | Gain per 10% |
|---|---|---|---|---|---|
| Anglosphere ex-US | d | decrease | -10 | 88.9 | 88.9 |
| Continental Europe | d | decrease | -10 | 135.3 | 135.3 |
| Hindu | d | decrease | -10 | 168.3 | 168.3 |
| Islamic | d | decrease | -10 | 101.2 | 101.2 |
| Japanese | d | decrease | -10 | 25.8 | 25.8 |
| Other Civilizations | d | decrease | -10 | 49.4 | 49.4 |
| Other Western | d | decrease | -10 | 58.3 | 58.3 |
| Sinic | d | decrease | -10 | 202.6 | 202.6 |
| United States | d | decrease | -10 | 95.7 | 95.7 |

### 5.4 Uncertainty

Table 8 reports bootstrap 95% confidence intervals for the equilibrium active pool T and the domestic PI pool P_D. The intervals are wide, reflecting the small cohort sample and the extrapolation from individual careers to long-run steady states.

| Group | T median | T 95% CI | P_D mean | P_D 95% CI |
|---|---|---|---|---|
| Anglosphere ex-US | 752 | [260, 1595] | 823 | [207, 1517] |
| Continental Europe | 1163 | [727, 4966] | 1461 | [605, 4866] |
| Hindu | 1497 | [1492, 1502] | 1421 | [1366, 1446] |
| Islamic | 892 | [883, 899] | 813 | [691, 851] |
| Japanese | 206 | [96, 470] | 173 | [46, 402] |
| Other Civilizations | 425 | [189, 895] | 486 | [144, 848] |
| Other Western | 514 | [506, 518] | 424 | [356, 473] |
| Sinic | 1785 | [842, 3659] | 2210 | [756, 3586] |
| United States | 805 | [428, 2620] | 837 | [343, 2542] |

![Figure 4](figures/fig4_bootstrap_ci.png)

**Figure 4. Bootstrap 95% confidence intervals for equilibrium T by group.** Intervals are asymmetric and wide, reflecting model uncertainty.

## 6. Discussion

The results support a transition-rate view of research policy. Rather than asking which country has a net inflow or outflow of researchers, the model asks which rate must be altered to keep a community above its minimum viable coauthor pool. The answer is not the same for every group, but a clear pattern emerges.

First, exogenous entry (I0) is the closest point of no return for the active researcher pool in every group except the Japanese PI pool. A large proportional reduction in baseline recruitment would drive most communities to their threshold before mobility rates such as return or promotion became binding. This is consistent with the observation that AI/ML fields depend on a continuous pipeline of new graduate students and junior researchers[6,8]. Policies that sustain that pipeline, such as doctoral funding, visa routes for early-career researchers, and stable junior positions, are therefore first-order defences against a point of no return.

Second, among the mobility transition rates, dropout is the dominant lever. Its elasticity is near -2 for every group, and reducing it yields the largest margin gain per unit effort in the policy counterfactuals. Attrition matters because it removes researchers from every compartment, not just one. A 10% reduction in dropout expands the safety margin more than comparably sized increases in return, hit generation or promotion. For groups with small safety margins, such as Japan, even modest attrition reductions may substantially delay the threshold.

Third, the positive transition levers are not symmetric. PI promotion (p_D) and domestic hit generation (h_D) have positive but smaller elasticities than dropout reduction. Return from abroad (β) is also positive, though its effect is generally smaller than keeping researchers from leaving in the first place. The implication for policy is that retention is usually cheaper and more effective than return, but a balanced portfolio is still needed: a community without domestic PI growth cannot reproduce itself through attrition reduction alone.

Fourth, the historical counterfactual shows that the late-window rates, if they persisted, would change equilibrium margins in both directions. Several large groups would see lower safety margins, while Japan and some smaller groups would see higher margins. This heterogeneity cautions against treating AI/ML mobility as a single global trend. It also confirms that the model can detect temporal changes in transition rates, which is the prerequisite for the early intervention the framework is designed to support.

The connection to civilisational diversity is direct. Each group's safety margin can be monitored over time, and interventions can be adjusted before the margin disappears. Because the model uses a fixed safety factor of 0.5 for the endogenous inflow parameter r, the policy recommendations are deliberately conservative: they do not push the system toward instability. That bounded approach is consistent with the goal of preserving diversity rather than maximising any single country's share.

Several limitations should be acknowledged. OpenAlex affiliation and country assignments are noisy, especially for researchers with multiple affiliations. The civilisation grouping is a coarse aggregation; within-group heterogeneity is substantial. The model is a steady-state ODE and does not capture short-term dynamics, cross-civilisation spillovers, or the non-linear effects of network externalities. The cohort sample is small; the absolute equilibrium numbers should be interpreted as model-implied stocks rather than as census counts. Finally, the point-of-no-return threshold is a sufficient condition for collapse, not a necessary one: a community may decline for reasons outside the model even if T remains above M.

## 7. Conclusion

We have proposed and implemented a transition-rate framework for assessing how close AI/ML research communities are to a point of no return. The model converts OpenAlex publication records into civilisation-specific transition rates and solves for the equilibrium active researcher pool. All groups remain above their minimum viable coauthor threshold in the fitted model, but the distance to that threshold varies by an order of magnitude and is most sensitive to exogenous entry and dropout. Early, proportionate interventions that reduce attrition and sustain new recruitment can widen safety margins and preserve civilisational diversity in AI/ML. Future work should extend the model to network externalities, finer temporal resolution, and additional security-relevant fields.

## References

1. Momentumyy. 人材流出ではなく『遷移係数』で考える研究コミュニティの存亡. note, 2024. https://note.com/momentumyy/n/n86df5d34282d (accessed 2026-08-09).
2. Huntington S P. The Clash of Civilizations and the Remaking of World Order. New York: Simon & Schuster, 1996.
3. Priem J, Piwowar H, Orr R. OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833, 2022. https://doi.org/10.48550/arXiv.2205.01833
4. Thorn K, Holm-Nielsen L B. International Mobility of Researchers and Scientists: Policy Options for Turning a Drain into a Gain. UNU-WIDER Research Paper No. 2006/83, 2006. https://www.wider.unu.edu/sites/default/files/rp2006-83.pdf
5. Appelt S, van Beuzekom B, Galindo-Rueda F, de Pinho R. Which factors influence the international mobility of research scientists? OECD Science, Technology and Industry Working Papers 2015/02, 2015. https://doi.org/10.1787/5js1tmrr2233-en
6. MacroPolo. The Global AI Talent Tracker 2.0. Paulson Institute, 2023. https://macropolo.org/digital-projects/the-global-ai-talent-tracker/
7. AlShebli B, Memon S A, Evans J A, Rahwan T. China and the U.S. produce more impactful AI research when collaborating together. Sci Rep. 2024;14:28576. https://doi.org/10.1038/s41598-024-79863-5
8. Yuan S, Shao Z, Wei X, Tang J, Hall W, Wang Y, et al. Science behind AI: the evolution of trend, mobility, and collaboration. Scientometrics. 2020;124(2):993-1013. https://doi.org/10.1007/s11192-020-03423-7
9. Shaffer M L. Minimum Population Sizes for Species Conservation. BioScience. 1981;31(2):131-134.
10. Franzoni C, Scellato G, Stephan P E. Foreign-born scientists: mobility patterns for 16 countries. Nat Biotechnol. 2012;30(12):1250-1253.
11. Aghion P, Bloom N, Blundell R, Griffith R, Howitt P. Competition and innovation: an inverted-U relationship. Q J Econ. 2005;120(2):701-728.
12. Freeman R B, Huang W. Collaboration: Strength in diversity. Nature. 2014;513(7518):305. https://doi.org/10.1038/513305a
13. Kerr W R. Global Talent and U.S. Immigration Policy. Harvard Business School Working Paper No. 20-107, 2020. https://www.hbs.edu/ris/Publication%20Files/20-107_0967f1ab-1d23-4d54-b5a1-c884234d9b31.pdf
14. Shachar A. The Race for Talent: Highly Skilled Migrants and Competitive Immigration Regimes. NYU Law Rev. 2006;81(1):148-206.
15. Stephan P E. The Economics of Science. J Econ Lit. 1996;34(3):1199-1235.
16. Jones B F, Wuchty S, Uzzi B. Multi-University Research Teams: Shifting Impact, Geography, and Stratification in Science. Science. 2008;322(5905):1259-1262.