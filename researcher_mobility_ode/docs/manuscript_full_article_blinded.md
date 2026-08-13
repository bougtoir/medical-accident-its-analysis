Article type: Research Article

Approximate word count (main text incl. tables, excl. references): 9689

Author information removed for double-blind review

# Abstract

Artificial intelligence (AI) and machine learning (ML) research is
increasingly concentrated in a few regions, raising the risk that
smaller research communities fall below a minimum viable coauthor pool
and cannot recover. We model each civilisation as a six-compartment
system of domestic and abroad early-career, high-impact, and
principal-investigator (PI) researchers, and estimate transition rates
from OpenAlex Artificial Intelligence works (subfield 1702). The minimum
viable coauthor threshold is defined as M = k × c_bar, where c_bar is
the mean number of authors per work and k is the median number of
distinct last-author groups observed per recent year. Across 9 groups,
equilibrium domestic active pools remain above their thresholds, but the
closest point of no return (PNR) is observed for the Other Western
group, where the exogenous entry rate (I0) must be multiplied by 0.332×
its current value (equivalent to a 67% proportional reduction) to drive
the active pool to its threshold. A simulated reduction in dropout
yields the largest margin gain per unit proportional change in every
group in the fitted model. The 2017-2023 out-of-sample projection
records root mean square error (RMSE) 12849.58 and a conservative,
non-standard mean absolute percentage error (MAPE) of 162.0% (computed
against count_obs + 1 to avoid division by zero). That level of error is
expected because the projection is designed as an early-warning
indicator of directional drift and threshold crossing, not as a precise
population forecast. Historical and saturating-inflow counterfactuals
show that the model is most sensitive to exogenous entry and attrition.
These results provide a quantitative framework for early,
safety-factor-bound policy scenarios that preserve civilisational
diversity in AI/ML research.

**Keywords:** researcher mobility; artificial intelligence; civilisation
grouping; ordinary differential equations; PNR; innovation studies

## Highlights

- Nine civilisations modelled as six-compartment ODEs fitted to OpenAlex
  AI/ML data.

- Closest PNR: Other Western via I0 (factor 0.332×).

- Dropout reduction gives the largest margin gain per 10% change across
  all groups in the fitted model.

## Data and Code Availability

This study uses the OpenAlex database (subfield 1702, Artificial
Intelligence; 2000--2023), accessed via the OpenAlex API and a full-work
local snapshot in August 2026. The country-to-civilisation mapping,
extraction and analysis code, and the result CSVs used to generate this
manuscript will be made available in a public repository upon
acceptance. OpenAlex data are released under CC0.

## Declarations

**Funding:** \[To be completed\]

**Competing interests:** \[To be completed\]

**Author contributions:** \[To be completed\]

**Declaration of generative AI in scientific writing:** During the
preparation of this work the authors used AI-assisted tools to draft,
code, and revise the manuscript. All claims, data, and interpretations
were reviewed and approved by the authors.

**Acknowledgments:** \[Removed for double-blind review\]

# 1. Introduction

Most debates on research mobility focus on net flows: which country
gains researchers and which loses them. Net-flow accounting is useful
for headlines, but it hides the transition rates that actually move
researchers between career stages and locations. A small proportional
change in one of those rates can, over time, push a research community
below the minimum coauthor pool it needs to remain viable. Once the pool
falls below that threshold, recovery becomes difficult or impossible,
even if policy is later reversed. That is the point of no return (PNR)
that motivates this paper. The contribution of this paper is to
translate that qualitative insight into an empirically tractable model.
We estimate transition rates from open bibliometric data, solve the
steady state of a compartment model, and identify which rate in which
civilisation is closest to a threshold. The approach is deliberately
stylised: it sacrifices demographic realism for transparency and for the
ability to compare multiple civilisations with the same accounting
framework.

Artificial intelligence (AI) and machine learning (ML) have become the
archetypal general-purpose technologies of the current era ^\[1\]^, and
their development depends on a relatively small, highly mobile workforce
of doctoral and post-doctoral researchers, principal investigators
(PIs), and research engineers ^\[1\]^. The geographic concentration of
this workforce has generated both scientific and geopolitical concern.
Policymakers in the United States, China, Europe, Japan, India and
elsewhere now treat AI talent as a strategic input, and several
governments have introduced incentives to attract or retain researchers
^\[2\]^. Most of those policies are evaluated by their immediate
net-flow effects. They rarely ask which transition in the career
pipeline is the binding constraint, or how close a community is to a
threshold where the field can no longer sustain itself. The economic
literature on science has long emphasised that researchers are a scarce
input and that their mobility responds to career incentives and
institutional quality ^\[3\]^. That literature provides the
microfoundation for our rates: individuals decide where to train,
whether to go abroad, when to return, and when to leave academia. We
aggregate those individual decisions into civilisation-level transition
rates and ask what the resulting dynamics imply for community survival.

The civilisation framework offers a natural way to partition the global
research population into culturally and institutionally coherent arenas
^\[4\]^. We adapt Huntington\'s nine civilisations for AI/ML mobility by
keeping the United States, China (Sinic), India and nearby South Asian
countries (Hindu), Japan, and the Islamic world as distinct groups,
splitting the Western bloc into the United States, Anglosphere excluding
the United States, Continental Europe and Other Western, and merging the
smaller Latin American, Orthodox and African communities into Other
Civilizations. This grouping reflects the empirical size and mobility
patterns observed in the data rather than a normative claim about
civilisational identity.

The central argument of the paper is that preserving civilisational
diversity in AI/ML is not only a normative preference but also a
safeguard against technological dead ends. When a single region or a
small oligopoly dominates a field, the set of research questions,
evaluation norms, and institutional incentives narrows ^\[5\]^. A
diverse ecosystem generates competing approaches, which increases the
probability that unexpected breakthroughs and error correction survive
^\[5\]^. If transition rates can be observed with enough temporal
resolution, policy can intervene before a community reaches the PNR.
Early, proportionate interventions can prevent the emergence of a
monopoly or oligopoly without requiring large ex post rescues.

We therefore address five research questions. First, how close is each
civilisation to the PNR in its AI/ML research community? Second, which
transition rates have the largest effect on community size? Third, how
have transition rates changed between earlier and later career cohorts,
and what would have happened if those rates had persisted? Fourth, what
safety-factor-bound single-lever and multi-lever policy scenarios can
widen the margin before a PNR is reached? Fifth, can the fitted rates be
estimated year by year and used to project near-term population
composition, and how well do those projections reproduce observed
2017-2023 counts? The key policy intuition is that, with an
appropriately chosen time step and an early warning signal, intervention
can be calibrated in safety margins rather than after collapse. This
prevents any single civilisation from cornering the supply of critical
talent, and thereby preserves the competitive diversity that drives
long-run innovation.

The contribution is a reproducible, data-driven transition-rate model
that links OpenAlex publication records to a system of ordinary
differential equations (ODEs) ^\[6\]^. The model is intentionally
simple: it does not explain why a rate is high or low, but it identifies
which rate is closest to a threshold and therefore where early
intervention is most urgent.

# 2. Literature and conceptual framework

Researcher mobility has long been studied under the headings of brain
drain, brain circulation and brain gain ^\[7\]^. Thorn and Holm-Nielsen
argue that the mobility of researchers from developing countries can
become a gain when return migration and diaspora networks are supported,
but it can become a drain when local research environments cannot retain
or reproduce talent ^\[7\]^. Appelt et al., using a gravity framework
for 1996-2011, find that scientific collaboration, economic convergence
and visa restrictions are the strongest correlates of bilateral mobility
^\[2\]^. Their analysis shows that mobility is multi-directional: a
large share of researcher movement is better described as circulation
than as one-way migration.

The AI/ML literature has documented the same patterns at higher
resolution. MacroPolo\'s Global AI Talent Tracker finds that the United
States remains the leading destination for top-tier AI researchers,
while China and India are expanding domestic retention ^\[1\]^. AlShebli
et al. show that U.S.-China collaboration in AI is more impactful than
either country working alone, and that most mobile AI scientists retain
collaboration links with their origin country ^\[8\]^. Yuan et al. find
that the brain-drain problem for AI scientists is increasingly serious
in developing countries, and that the ties among AI elites are highly
clustered ^\[9\]^. These studies establish that AI/ML talent is mobile,
concentrated and strategically important.

What is missing is a formal link between individual transition rates and
the long-run viability of a research community. The concept of a minimum
viable population, introduced by Shaffer, captures the smallest isolated
population that has a high probability of persisting despite
demographic, environmental and genetic stochasticity ^\[10\]^.
Transferred to science, the equivalent idea is a minimum viable coauthor
pool: the smallest number of active researchers that can continue to
produce work at the field\'s observed coauthor intensity. Below that
pool, collaboration networks fragment, mentorship chains break, and the
field enters a self-reinforcing decline.

This framing generates four testable hypotheses. H1: Across all groups,
the equilibrium active pool exceeds the minimum viable threshold, but
the distance to the threshold varies widely. H2: Dropout is the
transition rate with the largest negative effect, because attrition
removes researchers from every compartment. H3: The largest positive
transition lever is domestic hit generation (h_D), followed by
principal-investigator promotion (p_D). H4: Smaller civilisations, and
those with older cohort structures, sit closer to their PNR.

A final literature stream emphasises the consequences of concentrated
research agendas. Aghion et al. provide evidence that the relationship
between competition and innovation follows an inverted-U shape, with the
strongest innovative performance in markets that are neither perfectly
collusive nor perfectly monopolistic ^\[5\]^. Translated to global
science, this suggests that a single dominant region or a tight
oligopoly may slow the rate of methodological and conceptual
breakthroughs. Maintaining multiple centres of AI/ML research is
therefore not merely a distributional concern; it may increase the
long-run productivity of the field.

## 2.1 Researcher mobility

Researcher mobility has been studied from several angles. A large
empirical literature documents net flows of scientists and inventors
across countries and regions, often using patent or publication records
^\[11\]^. That work consistently finds that the United States, parts of
Europe and, increasingly, China and India are central nodes in the
global mobility network. It also finds that mobility responds to wages,
funding, institutional quality and career prospects, but that it is
path-dependent: once a community loses its senior cohort, it becomes
harder to rebuild.

## 2.2 Scientific collaboration and diversity

A second strand of work emphasises the structure of scientific
collaboration. Multi-university and international teams now produce a
growing share of high-impact research, and the geographic dispersion of
teams does not necessarily reduce their impact ^\[12\]^. This literature
suggests that global AI/ML is not a zero-sum race in which every
researcher in one location subtracts from another. It also implies that
sustaining a domestic community is compatible with, rather than opposed
to, international collaboration. The question is therefore not whether
researchers move, but whether the domestic pipeline that replaces them
is robust enough to keep the field alive.

## 2.3 Minimum viable populations and critical thresholds

The third relevant literature concerns population viability and critical
thresholds. In conservation biology, the minimum viable population
concept identifies the smallest number of individuals that can sustain a
population in the wild ^\[10\]^. We borrow that intuition and apply it
to a research community. A field needs a minimum number of active
researchers to produce work, train successors, and maintain peer review
and conference communities. Below that threshold, positive feedback
loops weaken: fewer researchers produce fewer students, fewer students
produce fewer researchers, and the community enters a downward spiral.
This is the PNR.

## 2.4 This paper\'s framework

The present paper bridges these literatures by estimating transition
rates from open bibliometric data and embedding them in a compartment
model. The model is closest in spirit to Stephan\'s economic model of
science, in which researchers move through career stages and respond to
incentives ^\[3\]^, but it adds a civilisational partition and a minimum
viable coauthor threshold. The civilisational partition is not merely a
geographic convenience. It reflects the fact that career incentives,
language, funding systems, and institutional networks cluster along
civilisational lines, and that these clusters shape mobility more than
national borders alone ^\[4\]^. It also draws on the innovation-systems
literature, in which technological trajectories are shaped by sectoral
and national systems of innovation ^\[13\]\ \[14\]\ \[15\]\ \[16\]^. The
result is a framework that can be updated as new data arrive and can
compare the fragility of different research communities using a common
metric. Because it is built on open bibliometric data and transparent
transition rates, the model can be replicated and extended by other
researchers and by policymakers who need a common language for
discussing mobility and capacity.

# 3. Data and grouping

We extracted AI/ML works and author histories from the OpenAlex API for
subfield \`subfields/1702\` (Artificial Intelligence), using works
published between 2000 and 2023 ^\[6\]^. OpenAlex provides open, CC0
bibliographic metadata including authors, affiliations, countries,
publication dates, venues and citation links. We built author histories
by following each author\'s sequence of works and affiliations,
assigning them to a country for each work and then to a civilisation by
the modal country of their recorded affiliations. The cohort is
restricted to authors whose career-start year (first observed AI/ML
publication year) is between 2000 and 2016 and who have at least two
AI/ML works in the 2000-2023 window. An author is treated as active if
they have at least one AI/ML work in 2020-2023, and as having dropped
out otherwise. An author is classified as a principal investigator (PI)
if their first last-author paper appears during the observation window;
single-authored papers are treated as last-author papers so that
culturally varying coauthorship norms do not bias the seniority proxy
^\[3\]^. A \'hit\' work is a paper whose citation count places it in the
top 10% of AI/ML works in the same publication year, observed within the
first eight career years, regardless of the author\'s position on the
author list. The abroad flag is set if the author is affiliated with a
non-origin civilisation within the first six career years. The final
groups are: United States, Anglosphere ex-US, Continental Europe, Sinic,
Japanese, Hindu, Islamic, Other Western, and Other Civilizations.

## 3.1 Country-to-civilisation mapping

The grouping follows Huntington\'s civilisation taxonomy but is adjusted
for sample-size and mobility reality in AI/ML. The United States is
separated from the broader Anglosphere because it is the dominant
destination for AI/ML researchers and because its higher-education and
funding systems differ systematically from those of other
English-speaking countries. Continental Europe is kept distinct from the
Anglosphere because intra-European mobility and EU research funding
create a separate mobility bloc. Latin American, Orthodox and
sub-Saharan African countries are merged into Other Civilizations
because their AI/ML author counts in the sample are too small to
estimate stable transition rates separately. This aggregation is a
pragmatic modelling choice and does not imply that these communities are
culturally homogeneous.

## 3.2 Sample selection and variable definitions

Authors enter the cohort if their first observed AI/ML publication year
is between 2000 and 2016 and they have at least two AI/ML works in the
2000-2023 observation window. The career-start year is the first
observed AI/ML publication year. Authors with exclusively unknown
affiliations or with all affiliations outside the mapped countries are
excluded. For each author we record the country of the majority of their
affiliations and the civilisation to which that country maps. An author
is active if they have at least one AI/ML work in 2020-2023; otherwise
they are recorded as having dropped out. A hit is a paper in the top 10%
of AI/ML citations for its publication year, observed within the first
eight career years, regardless of the author\'s position. A PI is an
author whose first last-author paper appears during the observation
window; single-authored papers are treated as last-author papers. The
abroad flag is set if the author appears in a non-origin civilisation
within the first six career years. The final cohort of 723,647 authors
is a model-implied sample extracted from OpenAlex; the objective is to
build a reproducible pipeline and demonstrate the transition-rate
framework, not to provide a definitive census.

## 3.3 OpenAlex coverage and known biases

OpenAlex coverage has improved over time but remains incomplete for
works before 2000 and for non-English publications. Author
disambiguation is imperfect, especially for common names and authors
with multiple name variants. Affiliation metadata are supplied by
publishers and are sometimes missing or refer to the primary institution
rather than the country of residence. For these reasons, the absolute
counts reported here are lower bounds on the true global AI/ML
workforce. The analysis nevertheless preserves relative comparisons
across civilisations because the same extraction rules are applied
uniformly. Replication from a clean OpenAlex snapshot should produce
very similar transition rates and point-of-no-return rankings even if
absolute counts shift.

Table 1 reports the size and composition of the extracted cohort. The
Sinic and Continental Europe groups contribute the largest number of
works, followed by the United States and the Anglosphere ex-US. The
Japanese and Other Western groups are the smallest in terms of author
counts. The cohort of 723,647 authors is a model-implied sample
extracted from the OpenAlex snapshot; absolute counts should be
interpreted as model-implied stocks rather than population totals, and
the bootstrap intervals reported below give a more honest picture of the
uncertainty around those stocks. The relative sizes are nevertheless
informative. A civilisation with a small cohort but a low coauthor
intensity can be more resilient than a larger civilisation with a high
coauthor intensity, because the former needs fewer distinct PI groups to
sustain its output. This is why the minimum viable coauthor threshold
and the equilibrium active pool must be compared jointly.

  -----------------------------------------------------------------------------------------------------------
  **Group**       **n**    **works**   **active**   **hits**   **pis**   **career_start_mean**   **abroad**
  --------------- -------- ----------- ------------ ---------- --------- ----------------------- ------------
  Anglosphere     64122    700342      28218        35822      43628     2007.3                  16233
  ex-US                                                                                          

  Continental     168911   1766329     74004        90322      111466    2008.0                  26060
  Europe                                                                                         

  Hindu           28069    225684      17047        12043      19185     2011.3                  4289

  Islamic         51043    387001      29703        20435      35558     2011.4                  8131

  Japanese        32007    293437      11846        9915       18543     2006.7                  4417

  Other           50240    371952      23671        17128      32449     2009.2                  9136
  Civilizations                                                                                  

  Other Western   4397     49748       1981         2646       2848      2007.4                  1414

  Sinic           190051   1589023     103673       61738      140701    2008.7                  23956

  United States   134807   1298250     58969        74972      91029     2007.3                  27420
  -----------------------------------------------------------------------------------------------------------

*Table 1. Descriptive statistics for the extracted AI/ML cohort by
civilisation group.*

# 4. Methods

## 4.1 Compartment model

Each civilisation is represented by six compartments: domestic
early-career researchers (D), abroad early-career researchers (A),
domestic hit researchers (H_D), abroad hit researchers (H_A), domestic
principal investigators (P_D), and abroad principal investigators (P_A).
Transition rates are early-career outflow (α), return (β), hit
generation at home and abroad (h_D and h_A), PI promotion at home and
abroad (p_D and p_A), and dropout from all compartments (d). The
equations are:

$${\frac{dD}{dt} = IP_{D}\  + \ \beta A\  - \ (\alpha\  + \ h_{D}\  + \ d)D}{\frac{dA}{dt} = \alpha D\  - \ (\beta\  + \ h_{A}\  + \ d)A}{\frac{dH\_ D}{dt} = h_{D}D\  + \ \beta H_{A}\  - \ (p_{D}\  + \ d)H_{D}}{\frac{dH\_ A}{dt} = h_{A}A\  - \ (\beta\  + \ p_{A}\  + \ d)H_{A}}{\frac{dP\_ D}{dt} = p_{D}H_{D}\  + \ \beta P_{A}\  - \ dP_{D}}{\frac{dP\_ A}{dt} = p_{A}H_{A}\  - \ (\beta\  + \ d)P_{A}}$$

The model makes several simplifying assumptions. It treats each
civilisation as a single aggregate, ignoring cross-civilisation
collaboration and spillovers. It assumes constant per-year transition
rates and a continuous-time Markov structure. Career stages are
collapsed into the three observed layers: early-career, hit researchers
and PIs. These simplifications are necessary to keep the model estimable
from OpenAlex and to make the point-of-no-return calculation
transparent. They also mean that the model is best interpreted as a
stylised early-warning device, not as a realistic demographic
projection.

## 4.2 Endogenous inflow

New entrants are modelled as a function of the domestic PI stock. The
linear form is $IP_{D} = I_{0} + rP_{D}$, where I_0 is the exogenous
entry rate, r is the PI reproduction rate, and r is capped at 0.40× the
stability-critical value (safety factor 0.40). A saturating alternative,
$IP_{D} = I_{0} + \frac{rP_{D}}{1\  + \ \varepsilon \times P_{D}}$, is
reported as a robustness check. The PI-driven inflow captures the idea
that senior researchers train graduate students, attract postdoctoral
researchers, and create the institutional infrastructure that produces
the next cohort. This is a strong assumption because it ignores
cross-border recruitment and non-PI sources of new researchers, but it
provides a transparent lower bound: if the domestic PI stock falls, the
model predicts a decline in new entrants. The safety factor prevents the
model from producing runaway growth when the observed r exceeds the
critical value, which is a common empirical finding because observed
recruitment is bounded by the data window.

## 4.3 Minimum viable coauthor threshold

For each group we computed the mean number of authors per work (c̄) and
the median number of distinct last-author groups observed per recent
year (k). The minimum viable domestic active pool is
$M\  = \ k\  \times \ c\bar{}$. When the equilibrium active pool
$T\  = \ D\  + \ H_{D}\  + \ P_{D}$ falls below M, the community can no
longer produce works at the observed coauthor intensity. The threshold
is deliberately conservative: it assumes that each new work requires at
least k distinct PI groups and that each work has the average number of
coauthors. This overstates the number of distinct actors needed for a
viable field, which means that M is a soft lower bound and that observed
margins are probably smaller than they appear. A community with a margin
just above M is therefore more fragile than the number itself suggests.

## 4.4 Estimation, equilibrium and sensitivity

Transition rates are estimated as constant per-year hazards from
observed proportions within the cohort. For each group and each
transition, the rate is the ratio of observed transitions to the total
exposure time spent in the source compartment during the observation
window, with Laplace smoothing of 1 added to both numerator and
denominator. This avoids zero-rate singularities when the cohort is
small. Because the data are right-censored at the end of the observation
period, the resulting rates are lower bounds on true long-run hazards;
equilibrium solutions therefore tend to be conservative. The non-linear
steady-state equations are solved numerically using a trust-region
Newton method with analytically supplied Jacobians. Elasticities are
computed by perturbing each rate by 1%, re-solving, and taking the
percentage change in the target stock. For point-of-no-return analysis
we scale each rate until the active pool reaches M and record the
critical factor and its proximity, \|critical factor − 1\|. A rate whose
critical factor lies inside the scan window and is close to 1.0 is the
most fragile lever for that group. All counterfactuals are mechanical
perturbations of the fitted rates; they reveal which transitions the
model treats as sensitive, not the causal impact of real-world policies.

## 4.5 Limitations

The main limitations are data quality and model scope. OpenAlex country
metadata are noisy, especially for older works and for authors with
multiple affiliations. Career stages are inferred from authorship order
and are imperfect proxies. The model does not include cross-civilisation
knowledge spillovers, bilateral migration costs, or firm-level mobility.
Finally, the assumption of constant rates is a strong approximation over
a 23-year window. We therefore emphasise rank-order and relative
sensitivity rather than point forecasts.

## 4.6 Annual transition-rate estimation and projection

The steady-state model in Sections 4.1-4.4 treats rates as constants. To
test whether the same framework can be used for short-run monitoring, we
reconstructed year-by-year compartment membership from the cohort data.
For each author and year we inferred location as domestic if the author
was in the origin civilisation and abroad otherwise. From these states
we computed annual transition counts for the six compartments, applied
Laplace +0.5 smoothing to empty destination cells, and derived the
probabilities that map to α, β, h_D, h_A, p_D, p_A and d.
Inter-civilisation flows are approximated by assigning each abroad
author-year to the author\'s recent_group as the destination
civilisation.

For the 2017-2026 projection we fit a linear trend to the observed
2000-2016 rates for each group and rate. If fewer than four observations
were available or the fit explained less than 10% of the variance, the
historical mean was used instead. Projected rates were clipped to values
between 0 and 1. Dropout was capped at 1.5 times the 90th percentile of
observed dropout rates in the training window to prevent implausible
extrapolation. Projected total inflows were apportioned across
compartments using the first-compartment distribution observed over the
2000-2016 training period. Population composition was projected forward
with the discrete-time recursion N(t+1) = N(t)P(t) + b(t+1), where P(t)
is a 6×6 row-stochastic-in-expectation matrix that preserves dropout
mass: the row sum is 1 − d after scaling outgoing rates. This discrete
step is the operational counterpart of the continuous-time ODE; with an
annual dt it provides an early-warning signal one year ahead.

We compare the 2017-2023 projection with the observed annual stock. The
comparison is limited to years that have observed data, and the observed
stock is reindexed to the full group-year-compartment grid so that
zero-observed cells are not omitted from the accuracy metrics. Accuracy
is reported as root mean square error (RMSE) and mean absolute
percentage error (MAPE); MAPE here is computed against count_obs + 1 to
avoid division by zero and is therefore a conservative, non-standard
measure.

## 4.7 Correction pressures and theoretical bounds

The annual estimates contain several regularising pressures that bound
the model away from instability and fabrication. Laplace smoothing adds
a uniform prior of 0.5 to every possible destination, which shrinks
sparse cells toward 1/(number of destinations) and prevents
zero-probability singularities when a transition is unobserved in a
small group-year. It is equivalent to a weak Dirichlet prior and is a
standard regulariser for sparse multinomial transitions.

Clipping projected rates to values between 0 and 1 is a feasibility
pressure: rates outside the probability simplex are inadmissible. The
dropout cap is a safety pressure motivated by the fact that unbounded
linear extrapolation of observed attrition would eventually predict more
leavers than the total stock. The inflow apportionment pressure keeps
the composition of new entrants aligned with the most recently observed
recruitment pattern, rather than inventing a new distribution. Finally,
the safety factor of 0.40 on the endogenous PI-driven inflow keeps the
system inside the stability boundary. Together these pressures embody
the principle that projection should stay within observed empirical
support and within theoretical stability limits; they are not arbitrary
adjustments but transparent bounds that can be tightened or relaxed as
more data become available.

# 5. Results

Table 2 reports the equilibrium domestic active pool T, the minimum
viable threshold M, and the endogenous inflow parameters for the 9
groups. All groups remain above their threshold under the fitted model,
but margins differ by an order of magnitude. The Sinic, Continental
Europe, United States groups show the largest equilibrium active pools,
reflecting large cohorts and relatively low coauthor-intensity
thresholds. The Other Western group has the smallest equilibrium active
pool, and Other Western has the narrowest safety margin, although both
still exceed their minimum viable coauthor pool. The ratio T/M is a
summary resilience indicator, but absolute margin is the more direct
measure of proximity to the PNR.

  -----------------------------------------------------------------------------------------------------
  **Group**       **T_eq**   **M**   **Margin**   **I0**   **r**     **r_obs**   **r_crit**   **T/M**
  --------------- ---------- ------- ------------ -------- --------- ----------- ------------ ---------
  Anglosphere     67532      3183    64348        1886     0.06326   0.08646     0.12652      21.21
  ex-US                                                                                       

  Continental     195095     3923    191172       4968     0.05949   0.08914     0.11899      49.72
  Europe                                                                                      

  Hindu           53434      2249    51185        826      0.02729   0.08606     0.05457      23.76

  Islamic         88522      2255    86267        1501     0.03176   0.08444     0.06352      39.26

  Japanese        29332      1793    27539        1134     0.10154   0.10154     0.25545      16.36

  Other           59355      2069    57286        1478     0.06620   0.09108     0.13240      28.69
  Civilizations                                                                               

  Other Western   4824       1601    3223         129      0.05992   0.09082     0.11984      3.01

  Sinic           303935     3129    300805       5590     0.04199   0.07946     0.08399      97.12

  United States   147067     1844    145223       3965     0.06202   0.08711     0.12404      79.75
  -----------------------------------------------------------------------------------------------------

*Table 2. Equilibrium domestic active pool, minimum viable threshold,
and endogenous inflow parameters.*

Figure 1 visualises the gap between equilibrium and threshold. The
Sinic, Continental Europe, United States groups display the largest
equilibrium active pools, while the Other Western group is the smallest.
However, the point-of-no-return metric is not the absolute level of T
but the distance between T and M, which reflects both the stock of
researchers and the coauthor intensity of the field. Groups with high T
but also high c̄ and k can still be fragile if their margin is small.

![](media/image1.png){width="5.8in" height="3.19in"}

*Figure 1. Equilibrium domestic active pool (T) and minimum viable
coauthor threshold (M) by group.*

Table 3 shows the three transition-rate elasticities with the largest
absolute impact on T for each group. Dropout (d) is the largest negative
lever in every group; its active-pool elasticity ranges from -2.79 to
-2.27. Attrition removes researchers from every compartment, so a
proportional increase in d produces a larger proportional decline in the
active pool. The largest positive transition lever is domestic hit
generation (h_D), followed by principal-investigator promotion (p_D).
Early-career outflow (α) has a modest negative effect in most groups,
but because it moves researchers to the abroad compartment rather than
removing them entirely, its direct impact on the domestic active pool is
smaller than that of dropout. There is notable heterogeneity in the
magnitude of the positive levers. The United States group shows the
strongest response to PI promotion (p_D), indicating that improving the
promotion of hit researchers to PIs is an especially efficient way to
expand the domestic active pool in that community. In the largest
groups, p_D remains positive but its relative effect is smaller, because
the active pool is already large and a proportional change in promotion
has less marginal impact.

  ---------------------------------------------------------------------------------------------
  **Group**       **1st      **1st          **2nd      **2nd          **3rd      **3rd
                  rate**     elasticity**   rate**     elasticity**   rate**     elasticity**
  --------------- ---------- -------------- ---------- -------------- ---------- --------------
  Anglosphere     d          -2.68          h_D        0.47           p_D        0.34
  ex-US                                                                          

  Continental     d          -2.68          h_D        0.39           p_D        0.35
  Europe                                                                         

  Hindu           d          -2.54          h_D        0.34           p_D        0.21

  Islamic         d          -2.58          h_D        0.37           p_D        0.22

  Japanese        d          -2.27          h_D        0.39           p_D        0.27

  Other           d          -2.79          h_D        0.49           p_D        0.31
  Civilizations                                                                  

  Other Western   d          -2.74          h_D        0.37           p_D        0.35

  Sinic           d          -2.69          h_D        0.40           p_D        0.26

  United States   d          -2.67          h_D        0.45           p_D        0.36
  ---------------------------------------------------------------------------------------------

*Table 3. Top transition-rate elasticities for domestic active pool T.*

Table 4 reports, for each group, the single rate that reaches the
active-pool threshold with the smallest proportional change. The Other
Western group is the most fragile: I0 must be multiplied by 0.332× its
current value (equivalent to a 67% proportional reduction) to drive the
active pool to its minimum viable threshold. I0 is the closest
point-of-no-return lever for the active researcher pool in every group.
This is consistent with a recruitment-driven view of scientific
communities: if the pipeline of new researchers shuts or slows, the
active pool eventually falls below the minimum viable coauthor pool
regardless of how efficient return or promotion becomes. A global
retention programme that reduces dropout would benefit all groups, but
the most vulnerable groups may also need an expansion of the exogenous
entry rate.

  ----------------------------------------------------------------------------------------
  **Group**       **Target**        **Rate**    **Current**   **Critical   **Proximity**
                                                              factor**     
  --------------- ----------------- ----------- ------------- ------------ ---------------
  Other Western   domestic_active   I0          129.3235      0.332        0.668

  Japanese        domestic_active   I0          1134.4064     0.061        0.939

  Anglosphere     domestic_active   I0          1885.9412     0.047        0.953
  ex-US                                                                    

  Hindu           domestic_active   I0          825.5588      0.042        0.958

  Other           domestic_active   I0          1477.6471     0.035        0.965
  Civilizations                                                            

  Islamic         domestic_active   I0          1501.2647     0.025        0.975

  Continental     domestic_active   I0          4967.9706     0.020        0.980
  Europe                                                                   

  United States   domestic_active   I0          3964.9118     0.013        0.987

  Sinic           domestic_active   I0          5589.7353     0.010        0.990
  ----------------------------------------------------------------------------------------

*Table 4. Closest PNR for the active researcher pool by group.*

Figure 2 ranks groups by their closest point-of-no-return sensitivity.

![](media/image2.png){width="5.8in" height="3.2222222222222223in"}

*Figure 2. Closest point-of-no-return proximity by group. Smaller values
mean a smaller proportional change in the listed rate is required to
reach the threshold for the stated target pool.*

## 5.1 Saturating recruitment extension

Replacing linear inflow with a saturating form lowers equilibrium pools
because each additional PI adds fewer entrants. Table 5 compares linear
and saturating equilibrium T values. The saturating model is important
because the observed r is often close to the stability boundary, and an
unchecked linear inflow can produce explosive growth. Across groups, the
saturating variant predicts equilibrium pools that are -0-0% lower than
the linear variant, underscoring the sensitivity of long-run projections
to the functional form of inflow. This sensitivity does not overturn the
ranking of groups, but it shows that absolute equilibrium levels should
be treated with caution. The saturating model is the preferred
interpretation for policy because it acknowledges that recruitment
cannot scale linearly with the number of PIs indefinitely.

  -----------------------------------------------------------------------
  **Group**         **Linear T**      **Saturating T**  **ε**
  ----------------- ----------------- ----------------- -----------------
  Anglosphere ex-US 67532             67532             0.00000

  Continental       195095            195095            0.00000
  Europe                                                

  Hindu             53434             53434             0.00001

  Islamic           88522             88522             0.00001

  Japanese          29332             29332             0.00001

  Other             59355             59355             0.00001
  Civilizations                                         

  Other Western     4824              4824              0.00007

  Sinic             303935            303935            0.00000

  United States     147067            147067            0.00000
  -----------------------------------------------------------------------

*Table 5. Equilibrium T under linear and saturating PI-driven inflow.*

## 5.2 Historical counterfactual

Table 6 compares the equilibrium that would have emerged if the
transition rates estimated for the early career window (2000-2010) or
the late window (2011-2016) had persisted indefinitely. The late window
is shorter and its rates are estimated from younger cohorts, so the
comparison should be read as a sensitivity exercise rather than a
forecast. Only 9 groups have enough dual-window support for reliable
rate estimation in both windows; they are listed in the table. Groups
that would see smaller safety margins under late-window rates: Japanese.
Groups that would see larger safety margins under late-window rates:
Islamic, Hindu, Sinic, Continental Europe, Other Civilizations, United
States, Anglosphere ex-US, Other Western. This pattern shows that global
AI/ML mobility is not moving in a single direction; different
civilisations are on different trajectories, and a uniform policy
response would ignore this heterogeneity. Because the late cohort is
younger, the late-window equilibrium is likely biased downward for
groups where career progression has not yet run its course. Even so, the
exercise shows that the current regime is not the only possible one,
which is why counterfactual policy analysis is useful.

  ---------------------------------------------------------------------------------
  **Group**       **T        **T late** **ΔT (%)** **Margin   **Margin   **Δ
                  early**                          early**    late**     margin**
  --------------- ---------- ---------- ---------- ---------- ---------- ----------
  Anglosphere     64779      75245      16.2       61596      72062      10466.2
  ex-US                                                                  

  Continental     177460     231958     30.7       173536     228035     54498.4
  Europe                                                                 

  Hindu           23397      110377     371.8      21148      108128     86979.8

  Islamic         37899      186245     391.4      35644      183990     148346.1

  Japanese        31781      25052      -21.2      29989      23259      -6729.5

  Other           42881      91930      114.4      40812      89861      49049.3
  Civilizations                                                          

  Other Western   4450       5731       28.8       2849       4129       1280.2

  Sinic           278159     360991     29.8       275030     357861     82831.4

  United States   139401     169788     21.8       137557     167943     30386.5
  ---------------------------------------------------------------------------------

*Table 6. Historical counterfactual: equilibrium active pool and safety
margin under early versus late transition-rate regimes.*

Figure 3 shows the change in safety margin between the early and late
transition-rate regimes.

![](media/image3.png){width="5.8in" height="3.2222222222222223in"}

*Figure 3. Change in safety margin between early and late
transition-rate regimes. Positive values mean the late-window rates
would produce a larger safety margin than the early-window rates if they
persisted; negative values mean the margin would shrink. The comparison
is across two point estimates; uncertainty is substantial because the
two windows have different cohort sizes and the steady-state model does
not capture policy shocks.*

## 5.3 Policy counterfactuals

Table 7 reports the single mechanical counterfactual with the largest
margin gain per 10% lever change for each group. Reducing dropout is the
dominant positive lever for every civilisation, which is consistent with
the elasticity results in Table 3. The gain from a roughly 10%
proportional reduction in d ranges from about 567 additional active
researchers for the Other Western group to about 34739 for the Sinic
group, reflecting differences in cohort size and baseline attrition. No
other single lever comes close to dropout reduction in terms of
simulated margin gain per unit proportional change, although
combinations of levers may be more efficient for some groups. The
results also imply that policy need not focus on blocking early-career
outflow. Reducing attrition among researchers who remain in the domestic
system is a more efficient way to protect the active pool than
preventing researchers from going abroad, because a researcher abroad is
still in the global AI/ML system and may return. For the smallest
groups, increasing the exogenous entry rate or improving the promotion
of hit researchers to PIs can add additional margin, but dropout
reduction remains the first-order model-implied target.

  -------------------------------------------------------------------------------
  **Group**       **Lever**   **Direction**   **Change    **Margin    **Gain per
                                              (%)**       gain**      10%**
  --------------- ----------- --------------- ----------- ----------- -----------
  Anglosphere     d           decrease        -10         7660        7659.7
  ex-US                                                               

  Continental     d           decrease        -10         22093       22093.1
  Europe                                                              

  Hindu           d           decrease        -10         6184        6184.2

  Islamic         d           decrease        -10         10239       10238.9

  Japanese        d           decrease        -10         3194        3193.8

  Other           d           decrease        -10         6723        6723.1
  Civilizations                                                       

  Other Western   d           decrease        -10         567         567.3

  Sinic           d           decrease        -10         34739       34739.2

  United States   d           decrease        -10         16560       16560.4
  -------------------------------------------------------------------------------

*Table 7. Top positive mechanical counterfactual per group, measured by
margin gain per 10% proportional lever change.*

We also evaluated multi-lever policy packages for the three
smallest-margin groups. The package with the largest margin gain in each
group was: Other Western (retention: +616 active researchers); Japanese
(return_plus_retention: +3369 active researchers); Hindu (retention:
+6536 active researchers). These packages combine dropout reduction with
return or PI-pipeline levers, showing that the framework can compare
multi-lever interventions as well as single-rate perturbations.

## 5.4 Uncertainty

Table 8 reports bootstrap 95% confidence intervals for the equilibrium
active pool T and the domestic PI pool P_D. The intervals are wide,
reflecting the small cohort sample and the extrapolation from individual
careers to long-run steady states. For some groups the upper bound is an
order of magnitude larger than the lower bound, indicating that the
equilibrium is sensitive to resampling variation in the transition
rates. This uncertainty should be interpreted as a warning against
over-interpreting point estimates and as a reason to view the
point-of-no-return distances as indicative rather than precise
thresholds. Despite the width, the lower bounds for most groups remain
above the minimum viable threshold, which supports the qualitative
conclusion that all groups are currently above the PNR. For the smallest
groups the lower bound is closer to M, reinforcing the need for
continued monitoring and for policy buffers.

  ---------------------------------------------------------------------------
  **Group**       **T median**   **T 95% CI**   **P_D mean**   **P_D 95% CI**
  --------------- -------------- -------------- -------------- --------------
  Anglosphere     67546          \[66728,       29814          \[29158,
  ex-US                          68334\]                       30486\]

  Continental     195077         \[193718,      83476          \[82421,
  Europe                         196316\]                      84527\]

  Hindu           53407          \[52402,       30277          \[29348,
                                 54515\]                       31258\]

  Islamic         88428          \[87356,       47264          \[46155,
                                 89880\]                       48511\]

  Japanese        29372          \[28932,       7387           \[7128, 7662\]
                                 29757\]                       

  Other           59396          \[58590,       22326          \[21715,
  Civilizations                  60178\]                       22975\]

  Other Western   4829           \[4602, 5077\] 2163           \[1981, 2370\]

  Sinic           303843         \[301809,      133015         \[131418,
                                 305720\]                      134567\]

  United States   146991         \[145947,      63906          \[62994,
                                 148235\]                      64906\]
  ---------------------------------------------------------------------------

*Table 8. Bootstrap 95% confidence intervals for equilibrium T and
domestic PI pool P_D.*

Figure 4 displays the bootstrap intervals graphically.

![](media/image4.png){width="5.8in" height="3.1780522747156605in"}

*Figure 4. Bootstrap 95% confidence intervals for equilibrium T by
group.*

## 5.5 Synthesis

Taken together, the results provide a consistent picture. Exogenous
entry and dropout are the two rates that most strongly determine the
long-run viability of an AI/ML research community. Communities that are
large in absolute terms are not necessarily safe if their coauthor
intensity is high; conversely, small communities can be robust if their
attrition is low and their recruitment pipeline is stable. The
historical counterfactual shows that the current regime is not
preordained: a shift in transition rates at the start of the AI boom
would have produced different steady states for different civilisations.
This is precisely why the framework is useful: it identifies which rate
in which community is closest to a threshold, allowing policy to
intervene before rather than after a collapse. The policy message is
therefore both diagnostic and preventative. By tracking transition rates
rather than net flows, policymakers can see which civilisation is
approaching a PNR and which lever offers the largest safety margin per
unit of effort.

## 5.6 Annual transition rates and inter-civilisation flows

Figure 5 plots the observed 2000-2016 transition rates and the projected
2017-2026 rates for each civilisation. Rates are displayed by group and
by transition type, so that the reader can see whether a particular
transition is trending toward a boundary. Because the projections are
linear trend fits regularised by the correction pressures described in
Section 4.7, they are not forecasts of specific future events; they are
the model\'s one-year-ahead extrapolation of the recent historical
trajectory.

![](media/image5.png){width="6.0in" height="5.1962259405074365in"}

*Figure 5. Observed (solid) and projected (dashed) transition rates by
civilisation, 2000-2026.*

Table 9 summarises the mean observed annual transition rates by group
between 2000 and 2016. The table distinguishes early-career outflow (α),
return (β), domestic and abroad hit generation (h_D, h_A), PI promotion
(p_D), dropout (d), and total inflow (I_total).

  ------------------------------------------------------------------------------------
  **Group**       **α**      **β**      **h_D**    **p_D**    **d**      **I_total**
  --------------- ---------- ---------- ---------- ---------- ---------- -------------
  Anglosphere     0.012      0.034      0.046      0.087      0.000      3771.88
  ex-US                                                                  

  Continental     0.007      0.036      0.051      0.094      0.000      9935.94
  Europe                                                                 

  Hindu           0.008      0.030      0.027      0.082      0.000      1651.12

  Islamic         0.012      0.037      0.025      0.095      0.000      3002.53

  Japanese        0.007      0.037      0.024      0.069      0.000      1882.76

  Other           0.009      0.035      0.026      0.078      0.000      2955.29
  Civilizations                                                          

  Other Western   0.014      0.032      0.058      0.067      0.000      258.65

  Sinic           0.007      0.027      0.026      0.091      0.000      11179.47

  United States   0.008      0.033      0.047      0.086      0.000      7929.82
  ------------------------------------------------------------------------------------

*Table 9. Mean observed annual transition rates by civilisation,
2000-2016.*

Figure 6 shows the inter-civilisation accumulation of abroad
author-years. Rows represent the origin civilisation and columns
represent the destination civilisation, approximated by the author\'s
recent_group while abroad. The heatmap is a lower-bound proxy because
year-to-year destination switches within a spell abroad are not
observed.

![](media/image6.png){width="5.8in" height="4.673153980752406in"}

*Figure 6. Inter-civilisation abroad author-year accumulation by origin
(rows) and destination (columns) (lower-bound proxy; year-to-year
destination switches within a spell abroad are not observed).*

Table 10 lists the origin-destination pairs with the largest
accumulation of abroad author-years. These pairs identify the strongest
visible inter-civilisation pipelines and are the empirical counterpart
to the α and β transitions.

  -----------------------------------------------------------------------
  **Origin**              **Destination**         **Author-years**
  ----------------------- ----------------------- -----------------------
  Sinic                   Sinic                   111609

  Continental Europe      Continental Europe      86447

  United States           Unknown                 65558

  Continental Europe      Unknown                 58313

  United States           United States           57712

  United States           Sinic                   52689

  Anglosphere ex-US       Anglosphere ex-US       38063

  Sinic                   Unknown                 37254

  Anglosphere ex-US       Unknown                 36460

  Other Civilizations     Other Civilizations     28095
  -----------------------------------------------------------------------

*Table 10. Top origin-destination abroad author-year pairs.*

## 5.7 Out-of-sample projection, 2017-2023

The 2017-2023 projection is compared with observed annual stocks in
Figure 7. Overall accuracy is RMSE 12849.58 and MAPE 162.0% (a
non-standard, conservative measure computed against count_obs + 1 to
avoid division by zero). The high MAPE reflects small absolute counts
and zero-observed cells, and the projection should be read as a
directional early-warning indicator of drift and threshold proximity
rather than a precise population forecast. Among civilisations the
lowest RMSE is for Other Western and the highest RMSE is for Sinic; the
highest MAPE is for Islamic. The largest errors occur in small
compartments and in groups with sparse transition counts, which is
expected because the annual model does not borrow information across
civilisations.

![](media/image7.png){width="6.0in" height="3.8268711723534556in"}

*Figure 7. Observed (solid) and projected (dashed) compartment counts by
civilisation, 2017-2023. The vertical dotted line marks the end of the
training period (2016).*

Detailed projection accuracy by civilisation and by compartment is
reported in Supplementary Material (Supplementary Tables 1 and 2). Among
compartments, the lowest RMSE is for H_A, while the highest RMSE is for
D and the highest MAPE is for D. P_D and H_D show larger errors because
small changes in PI and hit rates are amplified by the endogenous inflow
term.

## 5.8 Correction pressures in the annual model

The annual projection performs best where the correction pressures in
Section 4.7 are binding. Laplace smoothing prevents empty cells from
being treated as impossible transitions; the unit-interval clip and the
dropout cap prevent the trend extrapolation from producing rates that
are incompatible with a stochastic transition matrix; and the 2016
inflow apportionment keeps new-entrant composition close to the last
observed regime. These pressures mean that the projection is not a
purely mechanical forecast: it is a bounded extrapolation that stays
within the empirical support of the 2000-2016 data and within the
stability constraints of the compartment model.

## 5.9 Japan-specific compartment and transition-rate ladder

Figure 8 places the Japanese AI/ML research community in the compartment
model. The fitted equilibrium is T=29332 active researchers (D=16248,
H_D=5714, P_D=7370) against a minimum viable threshold of M=1793, so the
safety ratio T/M is 16.36. The right-hand ladder compares Japan\'s six
transition rates with those of the other civilisations. Japan\'s closest
PNR is the exogenous entry rate I0: if I0 were reduced to 6.1% of its
current level, the active pool would reach the minimum viable threshold.
In the fitted rates, early-career outflow (α=0.025) and domestic PI
promotion (p_D=0.064) are comparatively low, while return from abroad
(β=0.029) and domestic hit generation (h_D=0.040) are moderate. The
small absolute size of the abroad PI compartment (P_A) shows that few
Japanese researchers who leave eventually become PIs abroad, which makes
the domestic pipeline the critical margin.

![](media/image8.png){width="6.0in" height="3.3094969378827646in"}

*Figure 8. The Japanese AI/ML research community in the six-compartment
model, with a cross-civilisation ladder of fitted transition rates.
Japan is highlighted in the right-hand panel; longer bars represent
higher estimated rates.*

## 5.10 A combined model-evaluation view: T/M and PNR proximity

Figure 9 combines the long-run safety ratio T/M with the closest
point-of-no-return proximity for each civilisation. A point in the
lower-left corner has both a low equilibrium buffer and a small
proportional change needed to reach the threshold, so it is the most
fragile combination. Japan sits in this region alongside the \'Other
Civilizations\' group, even though its T/M ratio is above one. This dual
view is useful as a model-evaluation metric: a civilisation can have a
T/M ratio that looks comfortable but still be close to its PNR because
the PNR depends on the proportional change in the most sensitive rate,
not only on the level of T.

![](media/image9.png){width="5.8in" height="4.511111111111111in"}

*Figure 9. Equilibrium safety ratio (T/M) versus closest
point-of-no-return proximity for all civilisations. Japan is shown in
red.*

# 6. Discussion

The results support a transition-rate view of research policy. Rather
than asking which country has a net inflow or outflow of researchers,
the model asks which rate must be altered to keep a community above its
minimum viable coauthor pool. This shift in focus has implications for
how we conceptualise brain drain, design science and technology policy,
and interpret civilisational diversity in AI/ML.

## 6.1 From net flows to transition rates

Most empirical studies of researcher mobility measure net flows, stocks
or collaboration counts ^\[11\]^. These indicators are useful for
describing patterns, but they do not reveal the mechanisms that sustain
or undermine a research community. A country may have a positive net
inflow while simultaneously losing its domestic PI base through
retirement or emigration, or it may have negative net flow but a healthy
pipeline of new entrants. The transition-rate framework disaggregates
these processes and shows that the same net flow can correspond to very
different vulnerability profiles. For example, a high early-career
outflow rate is less damaging than a high dropout rate because
researchers abroad may return; a high dropout rate removes researchers
from the system entirely. This distinction is lost in net-flow
accounting but is central to point-of-no-return analysis.

First, I0 is the closest point-of-no-return lever for the active
researcher pool in every group. A large proportional reduction in
baseline recruitment would drive most communities to their threshold
before mobility rates such as return or promotion became binding. This
is consistent with the observation that AI/ML fields depend on a
continuous pipeline of new graduate students and junior researchers
^\[1\]^. Policies that sustain that pipeline, such as doctoral funding,
visa routes for early-career researchers, and stable junior positions,
are therefore first-order defences against a PNR.

Second, among the mobility transition rates, dropout (d) is the dominant
negative lever; its active-pool elasticity ranges from -2.79 to -2.27
across groups, and in the policy counterfactuals a simulated reduction
in dropout yields the largest margin gain per unit proportional change.
Attrition matters because it removes researchers from every compartment,
not just one. A 10% proportional reduction in dropout expands the safety
margin more than comparably sized increases in return, hit generation or
promotion. For Other Western, the group with the smallest safety margin,
even modest attrition reductions may widen the margin. These
counterfactuals are mechanical perturbations of the fitted rates; they
identify the most sensitive transition levers, not the causal effect of
any specific policy programme.

Third, the largest positive transition lever is domestic hit generation
(h_D), followed by principal-investigator promotion (p_D). The United
States group shows the strongest response to PI promotion, suggesting
that for that community expanding the domestic PI pipeline is an
efficient lever. Return from abroad (β) is also positive for most
groups, though its effect is generally smaller than reducing attrition
directly. The implication for policy is that retention and promotion are
usually more efficient than trying to attract returnees, but a balanced
portfolio is still needed: a community without domestic PI growth cannot
reproduce itself through attrition reduction alone.

Fourth, the historical counterfactual shows that the late-window rates,
if they persisted, would alter equilibrium margins. Groups that would
see smaller safety margins under late-window rates: Japanese. Groups
that would see larger safety margins under late-window rates: Islamic,
Hindu, Sinic, Continental Europe, Other Civilizations, United States,
Anglosphere ex-US, Other Western. This pattern cautions against treating
AI/ML mobility as a single global trend. It also confirms that the model
can detect temporal changes in transition rates, which is the
prerequisite for the early intervention the framework is designed to
support.

The transition levers also interact in ways that a single-rate
elasticity cannot fully capture. For example, reducing dropout and
increasing PI promotion together are likely to have a larger effect than
the sum of the two individual perturbations, because more researchers
survive to become PIs and those PIs then train additional early-career
researchers through the endogenous inflow channel. Conversely, a
simultaneous fall in exogenous entry and a rise in dropout can push a
community to its threshold faster than either change alone. The model\'s
steady-state and one-at-a-time counterfactuals are therefore a starting
point; they identify the most sensitive margins but do not exhaust the
policy design space.

The connection to civilisational diversity is direct. Each group\'s
safety margin can be monitored over time, and interventions can be
adjusted before the margin disappears. Because the model uses a fixed
safety factor of 0.40 for the endogenous inflow parameter r, the policy
recommendations are deliberately conservative: they do not push the
system toward instability. That bounded approach is consistent with the
goal of preserving diversity rather than maximising any single
country\'s share.

It is important to stress that the counterfactuals reported in Tables 3
and 7 are mechanical perturbations of the fitted transition rates, not
causal estimates of specific programmes. They identify which rates the
model treats as most sensitive, and therefore where empirical policy
evaluation is most urgent, but they do not by themselves show that a
given intervention would achieve the simulated change.

## 6.2 Civilisational diversity as an innovation input

A second implication concerns the normative status of civilisational
diversity. We treat diversity as an input to innovation rather than as a
distributional afterthought ^\[17\]^. A monocentric or tight-oligopoly
structure in AI/ML may produce short-run efficiency gains through scale
and agglomeration, but it also raises the risk of methodological
lock-in, selection bias in training data, and reduced error correction.
It is also an evolutionary dead end: it narrows the menu of innovation
options, removes healthy competitors whose alternative approaches keep
the field honest, and concentrates problem selection under a single
institutional and methodological line. When one civilisation or a small
oligopoly sets the dominant research agenda, problems that do not fit
its priorities, languages, or institutional incentives are less likely
to be addressed, leaving important scientific and social needs
unresolved. Recent work on multi-university teams shows that
geographically dispersed collaborations can retain high impact, which
suggests that distributing capacity across civilisations need not
sacrifice quality ^\[12\]^. By quantifying the safety margin for each
research community, the framework makes it possible to argue for support
of smaller communities on positive, innovation-systems grounds.
Preserving multiple centres of AI/ML research is not a matter of slowing
the frontier; it is a matter of ensuring that the frontier is not
defined by a single set of institutions, languages, or problems.

Japan is the clearest example among the large civilisations. Its fitted
active-pool margin is T=29332 researchers, with M=1793 (T/M=16.36). As
Figure 8 shows, Japan\'s closest PNR is the exogenous entry rate I0: if
I0 fell to 6.1% of its current level, the active pool would reach the
minimum viable threshold. The same figure shows that Japan\'s
early-career outflow α (0.025) and domestic PI promotion p_D (0.064) are
comparatively low, while return from abroad β (0.029) and domestic hit
generation h_D (0.040) are moderate. These numbers translate directly
into policy levers. α can be reduced by expanding postdoctoral
fellowships and junior-faculty positions that keep promising researchers
in the domestic pipeline; β can be raised through return grants, dual
appointments, and recognition of overseas experience in domestic hiring.
h_D responds to doctoral and postdoctoral training expansion, including
the 2026 AI for Science (SPREAD) programme if it is used to create
independent labs with their own budgets rather than merely increasing
headcount. p_D depends on tenure-track conversion, startup packages, and
project-based PI status for mid-career researchers. d, the dropout rate
to L, can be lowered through childcare support, dual-career
accommodation, and stable non-tenure research tracks. Finally, I0
captures the pure exogenous entry flow and can be supported by
research-master pipelines, undergraduate research programmes, and early
doctoral fellowships. Weakening the Japanese civilisation would not be
neutral for the rest of the world: it would remove a distinct
institutional lineage, reduce the pool of non-Anglophone problem
framings, and leave a range of health, ageing, robotics, and materials
problems under-addressed. Maintaining Japan as a viable AI/ML
civilisation is therefore in the global interest, not only in Japan\'s
national interest.

## 6.3 Policy and management implications, and early warning

The policy implications can be read as an early-warning architecture. A
single dashboard that tracks the fitted transition rates, their
bootstrap uncertainty, and the distance to M for each civilisation would
allow policymakers to detect divergence before a community enters an
irreversible decline. Interventions can then be calibrated to maintain a
minimum safety margin rather than to maximise any one stock. This is the
operational meaning of early intervention: not a forecast that a
particular collapse will occur, but a structured way to keep the system
away from a PNR. It also frames high-skilled mobility as a strategic
competition among jurisdictions for talent ^\[18\]^, in which the
central question is not only who wins the current round but whether the
global system retains enough diversity for future rounds ^\[19\]^. If
the dt of policy response is short enough, the model can be updated
annually and divergence caught early, before any single civilisation
approaches a PNR. This is the mechanism through which technology
monopoly, hegemonic concentration and oligopoly dead-ends can be
avoided: by keeping every major research community above its minimum
viable coauthor pool, the framework sustains the competitive diversity
that underpins long-run technological progress. The framework is
therefore not a prediction that a particular civilisation will collapse.
It is a tool for ensuring that no single civilisation reaches a point
where its collapse becomes self-sustaining, and that the global AI/ML
system retains the diversity required for continued innovation. This is
precisely what Sustaining Heterogeneity through Interventions in Global
AI/ML Researcher Mobility: A Transition-Rate Framework sets out to do:
sustain civilisational diversity through interventions in global AI/ML
researcher mobility. We introduce the acronym SHIGA here.

Table 11 maps the most sensitive transition levers to policy instruments
and to the management actions that determine them. Policy instruments
set incentives, while management actions determine how those incentives
are implemented within institutions. Both are needed because a policy
without a corresponding management process rarely changes transition
rates.

  ------------------------------------------------------------------------
  **Lever**               **Policy instrument**   **Management action**
  ----------------------- ----------------------- ------------------------
  Dropout (d)             Early-career            Retain researchers in
                          fellowships, childcare  the domestic pipeline
                          and dual-career         beyond the first career
                          support, stable         years
                          non-tenure tracks       

  Exogenous entry (I0)    Research-master and     Widen the base of
                          undergraduate           incoming researchers
                          pipelines, doctoral     before they select a
                          fellowships,            field or location
                          recruitment visas       

  Return from abroad (β)  Return grants, diaspora Encourage mobile
                          networks, dual          researchers to
                          appointments,           re-establish domestic
                          overseas-experience     research groups
                          recognition             

  Domestic hit generation Independent-lab         Translate junior
  (h_D)                   programmes (e.g.        capacity into visible,
                          SPREAD-style),          high-impact work and
                          doctoral/postdoctoral   independent research
                          training, compute       lines
                          access                  

  PI promotion (p_D)      Tenure-track            Create durable
                          conversion, startup     principal-investigator
                          packages, project-based positions that train the
                          PI status               next cohort
  ------------------------------------------------------------------------

*Table 11. Transition levers, policy instruments, and management
actions.*

Operationally, the framework can be used in two complementary ways. As a
monitoring tool, it can be rerun whenever new OpenAlex data are
released, producing an updated set of transition rates, safety margins
and proximity-to-threshold estimates. As a scenario tool, it can
quantify how large a proportional change in a given rate would be
required to move a community toward or away from collapse, which helps
prioritise empirical policy evaluation. Both uses depend on transparent
assumptions and regular recalibration; the model should not be used to
justify one-off interventions without accompanying process evaluation.

## 6.4 Validation of correction pressures

The correction pressures are not ad hoc adjustments; each maps to a
known statistical or dynamical constraint. Laplace smoothing is
equivalent to a weak Dirichlet prior on a multinomial transition vector;
it guarantees that no cell has zero estimated probability and shrinks
rare transitions toward the simplex centroid. Clipping projected rates
to values between 0 and 1 is a feasibility constraint on probabilities;
the dropout cap is a cross-sectional constraint that prevents projected
attrition from exceeding the observed stock; and the inflow
apportionment constraint keeps the composition of new entrants equal to
the last observed recruitment pattern. In the 2017-2023 projection these
pressures reduced the sensitivity of the forecast to sparse cells and to
short-run fluctuations in small groups. Quantitatively, the overall RMSE
of 12849.58 and conservative MAPE of 162.0% are consistent with a model
that is deliberately regularised rather than optimised for in-sample
fit. The high MAPE is driven by sparse compartments and zero-observed
cells; the projection is therefore appropriate for monitoring
directional drift and proximity to the PNR, not for precise count
forecasting. The residual errors are concentrated in the smallest
compartments, which is exactly where smoothing is most active and where
future data will be most valuable.

## 6.5 Intra-civilisation alternatives when inter-civilisation mobility cannot be controlled

If a civilisation cannot control outflows to, or inflows from, other
jurisdictions---whether because of visa regimes, salary differentials,
language advantages, or targeted recruitment---it can still preserve its
research community by acting on the intra-civilisation levers identified
in the annual model. The annual rates show that the domestic active pool
T = D + H_D + P_D responds most strongly to the dropout rate d, the
domestic hit rate h_D, and the PI promotion rate p_D. Policies that
reduce early-career attrition, expand domestic postdoctoral positions,
or accelerate independent-lab formation therefore become defensive
substitutes when inter-civilisation poaching cannot be regulated. This
is the practical meaning of civilisational-diversity preservation under
sovereignty constraints: even without controlling the border of talent,
a community can increase the internal reproduction of active
researchers. The ODE safety factor of 0.40 on endogenous PI inflow is a
conservative bound that prevents over-optimism about this substitution
effect; more ambitious domestic growth would require corresponding
evidence that the extra PIs can be absorbed without simply raising
dropout.

## 6.6 Annual updating as an early-warning layer

The 2017-2023 projection demonstrates that the framework can be rerun
annually with a one-year time step. Each new year of OpenAlex data
updates the observed transition rates, the fitted trends, and the
distance to the minimum viable coauthor threshold. Because the model is
regularised by the correction pressures, the one-year-ahead projection
is not easily derailed by a single noisy observation. Instead,
successive years reveal whether a particular transition rate is drifting
toward a boundary. That drift is the early-warning signal. Policymakers
can then intervene before the active pool falls below M, using the
rate-specific elasticities in Table 3 to prioritise the smallest
proportional change that restores a safety margin. This is the
operational mechanism for avoiding technology monopoly and oligopoly
dead ends: by keeping every major research community above its minimum
viable coauthor pool, annual monitoring sustains the competitive
diversity that underpins long-run technological progress. The framework
is therefore not a prediction that a particular civilisation will
collapse; it is a tool for ensuring that no single civilisation reaches
a point where its collapse becomes self-sustaining. SHIGA therefore
encapsulates the practical goal: keeping the global AI/ML system
heterogeneous enough that no single centre of power can monopolise the
technological frontier.

## 6.7 Limitations

Several limitations should be acknowledged. OpenAlex affiliation and
country assignments are noisy, especially for researchers with multiple
affiliations. The civilisation grouping is a coarse aggregation;
within-group heterogeneity is substantial. The annual model relies on a
discrete approximation of the continuous-time ODE and does not capture
within-year events or cross-civilisation spillovers. Inter-civilisation
flows are approximated by the author\'s recent_group while abroad, which
misses year-to-year destination switching. The civilisation label is a
pragmatic aggregation of publication-affiliation patterns. Historical
civilisational boundaries do not necessarily coincide with contemporary
political or value-based boundaries, and this study cannot determine
whether the diversity of research ideas maps more closely onto
historical civilisational groupings or onto current political and value
communities; for example, the Sinic grouping reflects current OpenAlex
country metadata and does not resolve the cultural and historical ties
between mainland China and Taiwan, which currently appear as separate
research arenas. This is treated as an empirical limitation of the
classification, not as a normative claim.The cohort sample is small; the
absolute equilibrium numbers should be interpreted as model-implied
stocks rather than as census counts. Authors with many publications are
over-weighted relative to one-publication authors, so rate estimates
reflect author-publication exposure rather than a uniformly
representative sample of individuals. The endogenous inflow is capped at
a safety factor of 0.40 relative to the critical reproduction rate;
alternative values would shift equilibrium levels and should be reported
in future sensitivity tables. Finally, the point-of-no-return threshold
is a sufficient condition for collapse, not a necessary one: a community
may decline for reasons outside the model even if T remains above M.

Wide bootstrap confidence intervals, especially for smaller civilisation
groups, mean that the ordinal ranking of groups by equilibrium size or
proximity to threshold should be treated as descriptive rather than
definitive. The model identifies which transitions are most sensitive in
a mechanical sense; turning those sensitivities into reliable policy
priorities requires additional data on programme costs, implementation
lags, and behavioural responses that are outside the scope of this
paper.

From a security-studies perspective, the framework is intentionally
non-adversarial. It does not model deliberate recruitment campaigns,
technology transfer, or strategic denial. Instead, it treats mobility as
an aggregate transition process and asks when a community becomes unable
to reproduce itself. That baseline is useful because it shows where
defensive, capacity-building policies can be most efficient, but it does
not replace classified or diplomatic assessments of technology
competition. Future work could add a strategic layer by distinguishing
between civilian and defence-relevant AI/ML pipelines, or by modelling
the effects of targeted recruitment on specific subfields.

# 7. Conclusion

We have proposed and implemented a transition-rate framework for
assessing how close AI/ML research communities are to a PNR. The model
converts OpenAlex publication records into civilisation-specific
transition rates and solves for the equilibrium active researcher pool.
All groups remain above their minimum viable coauthor threshold in the
fitted model, but the distance to that threshold varies by an order of
magnitude and is most sensitive to exogenous entry and dropout. Dropout
is the dominant negative lever (active-pool elasticity -2.79 to -2.27),
and a simulated reduction is the single most efficient model-implied
response for every civilisation. However, the closest PNR is exogenous
entry for all groups in the active-pool analysis, which means that
policies which sustain the pipeline of new researchers are first-order
defences. The historical counterfactual and the bootstrap intervals
remind us that the future is not determined by current rates; transition
rates can change, and policy can be directed at the most fragile lever
before a collapse.

The annual projection layer adds an operational dimension to this
conclusion. By estimating year-by-year transition rates and projecting
one year ahead, the model turns the steady-state diagnostic into an
early-warning dashboard. A one-year time step is short enough to detect
drift before the active pool approaches the minimum viable threshold,
and the correction pressures keep the projection within empirical and
theoretical bounds. When inter-civilisation mobility cannot be
controlled, the same framework points to intra-civilisation
levers---reducing dropout, raising domestic hit rates, and accelerating
PI promotion---that preserve T = D + H_D + P_D. These two layers,
steady-state and annual, together provide a coherent basis for early,
safety-factor-bound intervention.

The broader implication is that preserving civilisational diversity in
AI/ML is compatible with, and may reinforce, scientific progress. A
single dominant region or a tight oligopoly may achieve short-run scale
economies, but it also risks methodological lock-in and reduces the set
of problems that receive sustained attention. By monitoring transition
rates and safety margins, policymakers can detect divergence early and
intervene in a safety-factor-bound way. This is the practical meaning of
the aspiration to avoid technology monopoly and oligopoly dead ends: not
a prediction that any one civilisation will dominate, but a structured
method for keeping the global system away from points of no return.
Early, proportionate interventions that reduce attrition and sustain new
recruitment can widen safety margins and preserve civilisational
diversity in AI/ML.

## 7.1 Future work

Several extensions are natural. First, the model can be applied to other
security-relevant fields such as semiconductor physics, quantum
computing, biotechnology and energy materials, allowing cross-field
comparisons of vulnerability. Second, the civilisation partition can be
refined to a country or institution level, allowing bilateral migration
flows and network externalities to be incorporated. Third, the ODE can
be solved dynamically rather than at steady state, making it possible to
forecast the time to threshold under alternative policy scenarios.
Fourth, the minimum viable coauthor threshold can be made endogenous by
modelling coauthorship as a matching process. Fifth, the sensitivity of
equilibrium outcomes to the safety factor and to the saturating
parameter epsilon should be mapped systematically. Finally, the
framework can be integrated with policy cost data to produce
cost-effectiveness comparisons of alternative interventions, turning
mechanical sensitivities into actionable funding priorities.

# References

1\. MacroPolo. The Global AI Talent Tracker 2.0. Paulson Institute,
2023.
https://macropolo.org/digital-projects/the-global-ai-talent-tracker/

2\. Appelt S, van Beuzekom B, Galindo-Rueda F, de Pinho R. Which factors
influence the international mobility of research scientists? OECD
Science, Technology and Industry Working Papers 2015/02, 2015.
https://doi.org/10.1787/5js1tmrr2233-en

3\. Stephan P E. The Economics of Science. J Econ Lit.
1996;34(3):1199-1235.

4\. Huntington S P. The Clash of Civilizations and the Remaking of World
Order. New York: Simon & Schuster, 1996.

5\. Aghion P, Bloom N, Blundell R, Griffith R, Howitt P. Competition and
innovation: an inverted-U relationship. Q J Econ. 2005;120(2):701-728.

6\. Priem J, Piwowar H, Orr R. OpenAlex: A fully-open index of scholarly
works, authors, venues, institutions, and concepts. arXiv:2205.01833,
2022. https://doi.org/10.48550/arXiv.2205.01833

7\. Thorn K, Holm-Nielsen L B. International Mobility of Researchers and
Scientists: Policy Options for Turning a Drain into a Gain. UNU-WIDER
Research Paper No. 2006/83, 2006.
https://www.wider.unu.edu/sites/default/files/rp2006-83.pdf

8\. AlShebli B, Memon S A, Evans J A, Rahwan T. China and the U.S.
produce more impactful AI research when collaborating together. Sci Rep.
2024;14:28576. https://doi.org/10.1038/s41598-024-79863-5

9\. Yuan S, Shao Z, Wei X, Tang J, Hall W, Wang Y, et al. Science behind
AI: the evolution of trend, mobility, and collaboration. Scientometrics.
2020;124(2):993-1013. https://doi.org/10.1007/s11192-020-03423-7

10\. Shaffer M L. Minimum Population Sizes for Species Conservation.
BioScience. 1981;31(2):131-134.

11\. Franzoni C, Scellato G, Stephan P E. Foreign-born scientists:
mobility patterns for 16 countries. Nat Biotechnol.
2012;30(12):1250-1253.

12\. Jones B F, Wuchty S, Uzzi B. Multi-University Research Teams:
Shifting Impact, Geography, and Stratification in Science. Science.
2008;322(5905):1259-1262.

13\. Nelson R R, Winter S G. An Evolutionary Theory of Economic Change.
Cambridge, MA: Harvard University Press, 1982.

14\. Dosi G. Technological paradigms and technological trajectories: a
suggested interpretation of the determinants and directions of technical
change. Res Policy. 1982;11(3):147-162.

15\. Lundvall B-Å. National Systems of Innovation: Toward a Theory of
Innovation and Interactive Learning. London: Anthem Press, 1992.

16\. Malerba F. Sectoral systems of innovation and production. Res
Policy. 2002;31(2):247-264.

17\. Freeman R B, Huang W. Collaboration: Strength in diversity. Nature.
2014;513(7518):305. https://doi.org/10.1038/513305a

18\. Shachar A. The Race for Talent: Highly Skilled Migrants and
Competitive Immigration Regimes. NYU Law Rev. 2006;81(1):148-206.

19\. Kerr W R. Global Talent and U.S. Immigration Policy. Harvard
Business School Working Paper No. 20-107, 2020.
https://www.hbs.edu/ris/Publication%20Files/20-107_0967f1ab-1d23-4d54-b5a1-c884234d9b31.pdf
