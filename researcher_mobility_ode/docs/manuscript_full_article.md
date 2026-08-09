# Quantifying the Point of No Return in Global AI/ML Research Communities

**Article type:** Research Article

## Abstract

Artificial intelligence (AI) and machine learning (ML) research is increasingly concentrated in a few regions, raising the risk that smaller research communities fall below a minimum viable coauthor pool and cannot recover. We model each civilisation as a six-compartment system of domestic and abroad early-career, high-impact, and principal-investigator researchers, and estimate transition rates from OpenAlex Artificial Intelligence works (subfield 1702). The minimum viable coauthor threshold is defined as M = k × c_bar, where c_bar is the mean number of authors per work and k is the median number of distinct last-author groups observed per recent year. Across 9 groups, equilibrium domestic active pools remain above their thresholds, but the closest point of no return is observed for the Other Civilizations group, where a proportional change of 0.75 in I0 (critical factor 0.25×) would drive the active pool to its threshold. A simulated reduction in dropout yields the largest margin gain per unit proportional change in every group, making it the most sensitive transition lever in the model. Historical and saturating-inflow counterfactuals show that the model is most sensitive to exogenous entry and attrition. These results provide a quantitative framework for early, safety-factor-bound policy scenarios that preserve civilisational diversity in AI/ML research.

**Keywords:** researcher mobility; artificial intelligence; civilisation grouping; ordinary differential equations; point of no return; innovation studies

## Highlights

- Nine civilisations modelled as six-compartment ODEs fitted to OpenAlex AI/ML data.
- Closest point of no return for the active pool is Other Civilizations via I0 (critical factor 0.25×).
- Simulated dropout reduction yields the largest margin gain per unit proportional change across all groups.

## Data and Code Availability

This study uses publication metadata from the OpenAlex API (subfield 1702, Artificial Intelligence; 2000–2023). The extraction and analysis code, the country-to-civilisation mapping, and the result CSVs used to generate this manuscript are available in the public GitHub repository https://github.com/bougtoir/researcher-mobility-ode. OpenAlex data are released under CC0.

## Declarations

**Funding:** [To be completed / removed for double-blind review]

**Competing interests:** [To be completed / removed for double-blind review]

**Author contributions:** [To be completed / removed for double-blind review]

**Acknowledgments:** [To be completed / removed for double-blind review]

## 1. Introduction

Most debates on research mobility focus on net flows: which country gains researchers and which loses them. Net-flow accounting is useful for headlines, but it hides the transition rates that actually move researchers between career stages and locations[1]. A small proportional change in one of those rates can, over time, push a research community below the minimum coauthor pool it needs to remain viable. Once the pool falls below that threshold, recovery becomes difficult or impossible, even if policy is later reversed. That is the point of no return that motivates this paper[1].

Artificial intelligence and machine learning have become the archetypal general-purpose technologies of the current era[6,7,8]. Their development depends on a relatively small, highly mobile workforce of doctoral and post-doctoral researchers, principal investigators, and research engineers[2]. The geographic concentration of this workforce has generated both scientific and geopolitical concern. Policymakers in the United States, China, Europe, Japan, India and elsewhere now treat AI talent as a strategic input, and several governments have introduced incentives to attract or retain researchers[5,6]. Most of those policies are evaluated by their immediate net-flow effects. They rarely ask which transition in the career pipeline is the binding constraint, or how close a community is to a threshold where the field can no longer sustain itself.

The civilisation framework offers a natural way to partition the global research population into culturally and institutionally coherent arenas[5]. We adapt Huntington's nine civilisations for AI/ML mobility by keeping the United States, China (Sinic), India (Hindu), Japan, and the Islamic world as distinct groups, splitting the Western bloc into the United States, Anglosphere excluding the United States, Continental Europe and Other Western, and merging the smaller Latin American, Orthodox and African communities into Other Civilizations. This grouping reflects the empirical size and mobility patterns observed in the data rather than a normative claim about civilisational identity.

The central argument of the paper is that preserving civilisational diversity in AI/ML is not only a normative preference but also a safeguard against technological dead ends. When a single region or a small oligopoly dominates a field, the set of research questions, evaluation norms, and institutional incentives narrows[6]. A diverse ecosystem generates competing approaches, which increases the probability that unexpected breakthroughs and error correction survive[6]. If transition rates can be observed with enough temporal resolution, policy can intervene before a community reaches the point of no return. Early, proportionate interventions can prevent the emergence of a monopoly or oligopoly without requiring large ex post rescues.

We therefore address four research questions. First, how close is each civilisation to the point of no return in its AI/ML research community? Second, which transition rates have the largest effect on community size? Third, how have transition rates changed between earlier and later career cohorts, and what would have happened if those rates had persisted? Fourth, what safety-factor-bound policy packages can widen the margin before a point of no return is reached?

The contribution is a reproducible, data-driven transition-rate model that links OpenAlex publication records to a system of ordinary differential equations. The model is intentionally simple: it does not explain why a rate is high or low, but it identifies which rate is closest to a threshold and therefore where early intervention is most urgent.

## 2. Literature and conceptual framework

Researcher mobility has long been studied under the headings of brain drain, brain circulation and brain gain[4,5,10]. Thorn and Holm-Nielsen argue that the mobility of researchers from developing countries can become a gain when return migration and diaspora networks are supported, but it can become a drain when local research environments cannot retain or reproduce talent[8]. Appelt et al., using a gravity framework for 1996-2011, find that scientific collaboration, economic convergence and visa restrictions are the strongest correlates of bilateral mobility[3]. Their analysis shows that mobility is multi-directional: a large share of researcher movement is better described as circulation than as one-way migration.

The AI/ML literature has documented the same patterns at higher resolution. MacroPolo's Global AI Talent Tracker finds that the United States remains the leading destination for top-tier AI researchers, while China and India are expanding domestic retention[2]. AlShebli et al. show that U.S.-China collaboration in AI is more impactful than either country working alone, and that most mobile AI scientists retain collaboration links with their origin country[9]. Yuan et al. find that the brain-drain problem for AI scientists is increasingly serious in developing countries, and that the ties among AI elites are highly clustered[10]. These studies establish that AI/ML talent is mobile, concentrated and strategically important.

What is missing is a formal link between individual transition rates and the long-run viability of a research community. The concept of a minimum viable population, introduced by Shaffer, captures the smallest isolated population that has a high probability of persisting despite demographic, environmental and genetic stochasticity[11]. Transferred to science, the equivalent idea is a minimum viable coauthor pool: the smallest number of active researchers that can continue to produce work at the field's observed coauthor intensity. Below that pool, collaboration networks fragment, mentorship chains break, and the field enters a self-reinforcing decline.

This framing generates four testable hypotheses. H1: Across all groups, the equilibrium active pool exceeds the minimum viable threshold, but the distance to the threshold varies widely. H2: Dropout is the transition rate with the largest negative effect, because attrition removes researchers from every compartment. H3: The largest positive transition lever is principal-investigator promotion (p_D), followed by domestic hit generation (h_D). H4: Smaller civilisations, and those with older cohort structures, sit closer to their point of no return.

## 3. Data and grouping

We extracted AI/ML works and author histories from the OpenAlex API for subfield `subfields/1702` (Artificial Intelligence), using works published between 2000 and 2023[3]. Authors were assigned to a civilisation by the majority country of their affiliated institutions. The mapping is documented in the repository and is reproduced here only in summary. The final groups are: United States, Anglosphere ex-US, Continental Europe, Sinic, Japanese, Hindu, Islamic, Other Western, and Other Civilizations.

Table 1 reports the size and composition of the extracted cohort. The sample is a reproducible pilot extraction; absolute counts are small because the goal is to demonstrate the transition-rate framework rather than to provide a definitive census of global AI/ML researchers.

| Group | Authors | Works | Active | Hits | PIs | Career start | Abroad |
|---|---|---|---|---|---|---|---|
| Anglosphere ex-US | 27 | 1977 | 26 | 25 | 14 | 2006.2 | 19 |
| Continental Europe | 49 | 3850 | 46 | 41 | 23 | 2006.1 | 23 |
| Hindu | 26 | 1754 | 26 | 20 | 13 | 2008.0 | 4 |
| Islamic | 20 | 830 | 20 | 13 | 9 | 2011.5 | 7 |
| Japanese | 26 | 1236 | 21 | 17 | 11 | 2005.7 | 4 |
| Other Civilizations | 20 | 843 | 19 | 14 | 9 | 2009.0 | 6 |
| Other Western | 15 | 947 | 15 | 14 | 5 | 2008.2 | 8 |
| Sinic | 41 | 3397 | 40 | 31 | 20 | 2007.3 | 16 |
| United States | 49 | 4210 | 44 | 46 | 28 | 2006.4 | 17 |

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
| Continental Europe | 1208.42 | 129.07 | 1079.36 | 2.82 | 0.00255 | 0.12532 | 0.00510 |
| Hindu | 1497.37 | 66.04 | 1431.33 | 1.52 | 0.00106 | 0.11765 | 0.00213 |
| Islamic | 892.42 | 126.52 | 765.89 | 1.16 | 0.00141 | 0.13072 | 0.00282 |
| Japanese | 206.81 | 50.48 | 156.33 | 1.42 | 0.00993 | 0.13904 | 0.01985 |
| Other Civilizations | 424.70 | 104.60 | 320.10 | 1.15 | 0.00310 | 0.13072 | 0.00620 |
| Other Western | 513.12 | 57.17 | 455.95 | 0.87 | 0.00200 | 0.17647 | 0.00400 |
| Sinic | 1783.64 | 112.34 | 1671.29 | 2.38 | 0.00140 | 0.12059 | 0.00281 |
| United States | 770.21 | 132.49 | 637.71 | 2.77 | 0.00404 | 0.10294 | 0.00808 |

![Figure 1](figures/fig1_equilibrium_margin.png)

**Figure 1. Equilibrium domestic active pool (T) and minimum viable coauthor threshold (M) by group.** All groups remain above the threshold, but the margin varies widely.

Table 3 shows the three transition-rate elasticities with the largest absolute impact on T for each group. Dropout (d) is the largest negative lever in every group, with an elasticity between -2.32 and -2.01 for the active pool. The largest positive transition lever is principal-investigator promotion (p_D), followed by domestic hit generation (h_D). The Japanese group shows the highest sensitivity to PI promotion (p_D), indicating that strengthening domestic promotion is especially important for that community.

| Group | 1st rate | 1st elasticity | 2nd rate | 2nd elasticity | 3rd rate | 3rd elasticity |
|---|---|---|---|---|---|---|
| Anglosphere ex-US | d | -2.162 | p_D | 0.116 | beta | 0.046 |
| Continental Europe | d | -2.096 | p_D | 0.066 | beta | 0.044 |
| Hindu | d | -2.011 | p_D | 0.038 | h_D | 0.013 |
| Islamic | d | -2.051 | p_D | 0.057 | h_D | 0.022 |
| Japanese | d | -2.317 | p_D | 0.233 | h_D | 0.111 |
| Other Civilizations | d | -2.125 | p_D | 0.094 | h_D | 0.047 |
| Other Western | d | -2.123 | p_D | 0.137 | h_D | 0.014 |
| Sinic | d | -2.027 | p_D | 0.035 | h_D | 0.021 |
| United States | d | -2.124 | p_D | 0.089 | h_D | 0.063 |

Table 4 reports, for each group, the single rate that reaches the active-pool threshold with the smallest proportional change. The Other Civilizations group is the most fragile: a proportional change of 0.75 in I0 (critical factor 0.25×) would drive the active pool to its minimum viable threshold. For the active researcher pool, I0 is the closest point-of-no-return lever for the active researcher pool in every group.

| Group | Target | Rate | Current | Critical factor | Proximity |
|---|---|---|---|---|---|
| Other Civilizations | domestic_active | I0 | 1.1486 | 0.246 | 0.754 |
| Japanese | domestic_active | I0 | 1.4202 | 0.244 | 0.756 |
| United States | domestic_active | I0 | 2.7692 | 0.172 | 0.828 |
| Anglosphere ex-US | domestic_active | I0 | 1.5548 | 0.159 | 0.841 |
| Islamic | domestic_active | I0 | 1.1638 | 0.142 | 0.858 |
| Other Western | domestic_active | I0 | 0.8723 | 0.111 | 0.889 |
| Continental Europe | domestic_active | I0 | 2.8237 | 0.107 | 0.893 |
| Sinic | domestic_active | I0 | 2.3837 | 0.063 | 0.937 |
| Hindu | domestic_active | I0 | 1.5156 | 0.044 | 0.956 |

![Figure 2](figures/fig2_pnr_proximity.png)

**Figure 2. Closest point-of-no-return proximity by group.** Smaller values mean a smaller proportional change in the listed rate is required to reach the threshold for the stated target pool.

### 5.1 Saturating recruitment extension

Replacing linear inflow with a saturating form lowers equilibrium pools because each additional PI adds fewer entrants. Across groups, saturating equilibrium T is 37-48% lower than the linear variant. Table 5 compares linear and saturating equilibrium T values.

| Group | Linear T | Saturating T | ε |
|---|---|---|---|
| Anglosphere ex-US | 752.12 | 411.20 | 0.01429 |
| Continental Europe | 1208.42 | 659.04 | 0.00870 |
| Hindu | 1497.37 | 781.23 | 0.01538 |
| Islamic | 892.42 | 469.06 | 0.02222 |
| Japanese | 206.81 | 129.35 | 0.01818 |
| Other Civilizations | 424.70 | 234.34 | 0.02222 |
| Other Western | 513.12 | 270.32 | 0.04000 |
| Sinic | 1783.64 | 940.82 | 0.01000 |
| United States | 770.21 | 445.87 | 0.00714 |

### 5.2 Historical counterfactual

Table 6 compares the equilibrium that would have emerged if the transition rates estimated for the early career window (2000-2010) or the late window (2011-2016) had persisted indefinitely. The late window is shorter and its rates are estimated from younger cohorts, so the comparison should be read as a sensitivity exercise rather than a forecast. Only 2 groups have enough dual-window support for reliable rate estimation in both windows; they are listed in the table. All 2 groups with dual-window support would see smaller safety margins under late-window rates (Sinic, Continental Europe).

| Group | T early | T late | ΔT (%) | Margin early | Margin late | Δ margin |
|---|---|---|---|---|---|---|
| Continental Europe | 1117.0 | 791.3 | -29.2 | 987.9 | 662.2 | -325.7 |
| Sinic | 1392.6 | 936.4 | -32.8 | 1280.3 | 824.1 | -456.2 |

![Figure 3](figures/fig3_historical_margin.png)

**Figure 3. Change in safety margin between early and late transition-rate regimes.** Positive values mean the late-window rates would produce a larger safety margin if they persisted. The comparison is across two point estimates; uncertainty is substantial because the two windows have different cohort sizes and the steady-state model does not capture policy shocks.

### 5.3 Policy counterfactuals

Table 7 reports the single mechanical counterfactual with the largest margin gain per 10% lever change for each group. Reducing dropout is the dominant positive lever for every civilisation. A roughly 10% proportional reduction in d would add about 26 active researchers in the Japanese group and about 203 in the Sinic group, reflecting differences in cohort size and baseline attrition.

| Group | Lever | Direction | Change (%) | Margin gain | Gain per 10% |
|---|---|---|---|---|---|
| Anglosphere ex-US | d | decrease | -10 | 88.9 | 88.9 |
| Continental Europe | d | decrease | -10 | 141.0 | 141.0 |
| Hindu | d | decrease | -10 | 168.3 | 168.3 |
| Islamic | d | decrease | -10 | 101.2 | 101.2 |
| Japanese | d | decrease | -10 | 25.8 | 25.8 |
| Other Civilizations | d | decrease | -10 | 49.4 | 49.4 |
| Other Western | d | decrease | -10 | 58.3 | 58.3 |
| Sinic | d | decrease | -10 | 202.6 | 202.6 |
| United States | d | decrease | -10 | 92.0 | 92.0 |

### 5.4 Uncertainty

Table 8 reports bootstrap 95% confidence intervals for the equilibrium active pool T and the domestic PI pool P_D. The intervals are wide, reflecting the small cohort sample and the extrapolation from individual careers to long-run steady states.

| Group | T median | T 95% CI | P_D mean | P_D 95% CI |
|---|---|---|---|---|
| Anglosphere ex-US | 752 | [260, 1595] | 823 | [207, 1517] |
| Continental Europe | 1214 | [761, 5174] | 1532 | [638, 5072] |
| Hindu | 1497 | [1492, 1502] | 1421 | [1366, 1446] |
| Islamic | 892 | [883, 899] | 813 | [691, 851] |
| Japanese | 206 | [96, 470] | 173 | [46, 402] |
| Other Civilizations | 425 | [189, 895] | 486 | [144, 848] |
| Other Western | 514 | [506, 518] | 424 | [356, 473] |
| Sinic | 1785 | [842, 3659] | 2210 | [756, 3586] |
| United States | 775 | [412, 2521] | 831 | [334, 2438] |

![Figure 4](figures/fig4_bootstrap_ci.png)

**Figure 4. Bootstrap 95% confidence intervals for equilibrium T by group.** Intervals are asymmetric and wide, reflecting model uncertainty.

## 6. Discussion

The results support a transition-rate view of research policy. Rather than asking which country has a net inflow or outflow of researchers, the model asks which rate must be altered to keep a community above its minimum viable coauthor pool. The answer is not the same for every group, but a clear pattern emerges.

First, I0 is the closest point-of-no-return lever for the active researcher pool in every group. A large proportional reduction in baseline recruitment would drive most communities to their threshold before mobility rates such as return or promotion became binding. This is consistent with the observation that AI/ML fields depend on a continuous pipeline of new graduate students and junior researchers[6,8]. Policies that sustain that pipeline, such as doctoral funding, visa routes for early-career researchers, and stable junior positions, are therefore first-order defences against a point of no return.

Second, among the mobility transition rates, dropout (d) is the dominant negative lever; its active-pool elasticity ranges from -2.32 to -2.01 across groups, and in the policy counterfactuals a simulated reduction in dropout yields the largest margin gain per unit proportional change. Attrition matters because it removes researchers from every compartment, not just one. A 10% proportional reduction in dropout expands the safety margin more than comparably sized increases in return, hit generation or promotion. For Japanese, the group with the smallest safety margin, even modest attrition reductions may widen the margin. These counterfactuals are mechanical perturbations of the fitted rates; they identify the most sensitive transition levers, not the causal effect of any specific policy programme.

Third, the largest positive transition lever is principal-investigator promotion (p_D), followed by domestic hit generation (h_D). The Japanese group shows the strongest response to PI promotion, suggesting that for that community expanding the domestic PI pipeline is an efficient lever. Return from abroad (β) is also positive for most groups, though its effect is generally smaller than reducing attrition directly. The implication for policy is that retention and promotion are usually more efficient than trying to attract returnees, but a balanced portfolio is still needed: a community without domestic PI growth cannot reproduce itself through attrition reduction alone.

Fourth, the historical counterfactual shows that the late-window rates, if they persisted, would alter equilibrium margins. All 2 groups with dual-window support would see smaller safety margins under late-window rates (Sinic, Continental Europe). This pattern cautions against treating AI/ML mobility as a single global trend. It also confirms that the model can detect temporal changes in transition rates, which is the prerequisite for the early intervention the framework is designed to support.

The transition levers also interact in ways that a single-rate elasticity cannot fully capture. For example, reducing dropout and increasing PI promotion together are likely to have a larger effect than the sum of the two individual perturbations, because more researchers survive to become PIs and those PIs then train additional early-career researchers through the endogenous inflow channel. Conversely, a simultaneous fall in exogenous entry and a rise in dropout can push a community to its threshold faster than either change alone. The model's steady-state and one-at-a-time counterfactuals are therefore a starting point; they identify the most sensitive margins but do not exhaust the policy design space.

The connection to civilisational diversity is direct. Each group's safety margin can be monitored over time, and interventions can be adjusted before the margin disappears. Because the model uses a fixed safety factor of 0.5 for the endogenous inflow parameter r, the policy recommendations are deliberately conservative: they do not push the system toward instability. That bounded approach is consistent with the goal of preserving diversity rather than maximising any single country's share.

It is important to stress that the counterfactuals reported in Tables 3 and 7 are mechanical perturbations of the fitted transition rates, not causal estimates of specific programmes. They identify which rates the model treats as most sensitive, and therefore where empirical policy evaluation is most urgent, but they do not by themselves show that a given intervention would achieve the simulated change.

Several limitations should be acknowledged. OpenAlex affiliation and country assignments are noisy, especially for researchers with multiple affiliations. The civilisation grouping is a coarse aggregation; within-group heterogeneity is substantial. The model is a steady-state ODE and does not capture short-term dynamics, cross-civilisation spillovers, or the non-linear effects of network externalities. The cohort sample is small; the absolute equilibrium numbers should be interpreted as model-implied stocks rather than as census counts. Authors with many publications are over-weighted relative to one-publication authors, so rate estimates reflect author-publication exposure rather than a uniformly representative sample of individuals. The endogenous inflow is capped at a safety factor of 0.5 relative to the critical reproduction rate; alternative values would shift equilibrium levels and should be reported in future sensitivity tables. Finally, the point-of-no-return threshold is a sufficient condition for collapse, not a necessary one: a community may decline for reasons outside the model even if T remains above M.
Wide bootstrap confidence intervals, especially for smaller civilisation groups, mean that the ordinal ranking of groups by equilibrium size or proximity to threshold should be treated as descriptive rather than definitive. The model identifies which transitions are most sensitive in a mechanical sense; turning those sensitivities into reliable policy priorities requires additional data on programme costs, implementation lags, and behavioural responses that are outside the scope of this paper.
Operationally, the framework can be used in two complementary ways. As a monitoring tool, it can be rerun whenever new OpenAlex data are released, producing an updated set of transition rates, safety margins and proximity-to-threshold estimates. As a scenario tool, it can quantify how large a proportional change in a given rate would be required to move a community toward or away from collapse, which helps prioritise empirical policy evaluation. Both uses depend on transparent assumptions and regular recalibration; the model should not be used to justify one-off interventions without accompanying process evaluation.

## 7. Conclusion

We have proposed and implemented a transition-rate framework for assessing how close AI/ML research communities are to a point of no return. The model converts OpenAlex publication records into civilisation-specific transition rates and solves for the equilibrium active researcher pool. All groups remain above their minimum viable coauthor threshold in the fitted model, but the distance to that threshold varies by an order of magnitude and is most sensitive to exogenous entry and dropout. Simulated reductions in attrition and sustained new recruitment widen safety margins in the model, which is consistent with preserving civilisational diversity in AI/ML. Future work should extend the model to network externalities, finer temporal resolution, and additional security-relevant fields such as semiconductor physics, quantum computing, biotechnology and energy materials, allowing cross-field comparisons of vulnerability. Other priorities include systematic sensitivity scans for the safety factor and saturating parameter epsilon, country- or institution-level partitions, dynamic ODE forecasts, endogenous coauthorship matching, and integration with policy cost data to produce cost-effectiveness comparisons of alternative interventions.

## References

1. Yamada Y (momentumyy). 海外で当てた研究者はその後どうなるのか. note.com, 2026. https://note.com/momentumyy/n/n86df5d34282d (accessed 2026-08-09).
2. MacroPolo. The Global AI Talent Tracker 2.0. Paulson Institute, 2023. https://macropolo.org/digital-projects/the-global-ai-talent-tracker/
3. Appelt S, van Beuzekom B, Galindo-Rueda F, de Pinho R. Which factors influence the international mobility of research scientists? OECD Science, Technology and Industry Working Papers 2015/02, 2015. https://doi.org/10.1787/5js1tmrr2233-en
4. Stephan P E. The Economics of Science. J Econ Lit. 1996;34(3):1199-1235.
5. Huntington S P. The Clash of Civilizations and the Remaking of World Order. New York: Simon & Schuster, 1996.
6. Aghion P, Bloom N, Blundell R, Griffith R, Howitt P. Competition and innovation: an inverted-U relationship. Q J Econ. 2005;120(2):701-728.
7. Priem J, Piwowar H, Orr R. OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833, 2022. https://doi.org/10.48550/arXiv.2205.01833
8. Thorn K, Holm-Nielsen L B. International Mobility of Researchers and Scientists: Policy Options for Turning a Drain into a Gain. UNU-WIDER Research Paper No. 2006/83, 2006. https://www.wider.unu.edu/sites/default/files/rp2006-83.pdf
9. AlShebli B, Memon S A, Evans J A, Rahwan T. China and the U.S. produce more impactful AI research when collaborating together. Sci Rep. 2024;14:28576. https://doi.org/10.1038/s41598-024-79863-5
10. Yuan S, Shao Z, Wei X, Tang J, Hall W, Wang Y, et al. Science behind AI: the evolution of trend, mobility, and collaboration. Scientometrics. 2020;124(2):993-1013. https://doi.org/10.1007/s11192-020-03423-7
11. Shaffer M L. Minimum Population Sizes for Species Conservation. BioScience. 1981;31(2):131-134.
12. Franzoni C, Scellato G, Stephan P E. Foreign-born scientists: mobility patterns for 16 countries. Nat Biotechnol. 2012;30(12):1250-1253.
13. Jones B F, Wuchty S, Uzzi B. Multi-University Research Teams: Shifting Impact, Geography, and Stratification in Science. Science. 2008;322(5905):1259-1262.
14. Freeman R B, Huang W. Collaboration: Strength in diversity. Nature. 2014;513(7518):305. https://doi.org/10.1038/513305a
15. Shachar A. The Race for Talent: Highly Skilled Migrants and Competitive Immigration Regimes. NYU Law Rev. 2006;81(1):148-206.
16. Kerr W R. Global Talent and U.S. Immigration Policy. Harvard Business School Working Paper No. 20-107, 2020. https://www.hbs.edu/ris/Publication%20Files/20-107_0967f1ab-1d23-4d54-b5a1-c884234d9b31.pdf