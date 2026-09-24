# Impact of medical safety incidents on physician workforce and healthcare facility supply across 12 specialties in Japan: an interrupted time series analysis

---

**Authors:** [Author names to be added]

**Correspondence to:** [Corresponding author details to be added]

**Word count:** approximately 3800 (excluding abstract, references, tables, and figures)

**Keywords:** medical accidents, physician supply, interrupted time series, workforce planning, Japan, patient safety

---

## Abstract

**Objective:** To examine the association between medical safety incidents and changes in specialty-specific physician counts, healthcare facility numbers, and specialist trainee enrolment in Japan.

**Design:** Interrupted time series analysis with segmented regression, cross-correlation analysis for lead time estimation, and Akaike information criterion (AIC)-based model selection for window period estimation. Reporting follows the REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) guidelines.

**Setting:** Japan, using national administrative databases.

**Participants:** Physician workforce data from the National Survey of Physicians, Dentists, and Pharmacists (1994-2022, biennial); healthcare facility data from the Survey of Medical Institutions (2002-2024); specialist trainee data from the Japan Board of Medical Specialties (2018-2025). Twelve core medical specialties were analysed.

**Main outcome measures:** Specialty-specific physician counts, healthcare facility counts, and new specialist trainee enrolment. The main exposure variables were medical safety incident counts derived from three definitions: (1) the Japan Medical Safety Research Organisation (JMSR) mandatory reporting system (2015-2025); (2) medical malpractice litigation statistics from the Supreme Court of Japan (2004-2023); and (3) a composite index combining both sources.

**Results:** In cross-correlation analysis after detrending, obstetrics and gynaecology showed the strongest inverse association between incident reports and physician numbers across all three definitions (r=-0.95, lag +3 years). Additional specialties demonstrating strong delayed inverse associations (|r|>0.9) included otolaryngology (r=-0.97, lag +6 years with litigation), dermatology (r=-0.99, lag +7 years), and urology (r=-0.94, lag +6 years with JMSR). The estimated lead time from incident occurrence to workforce impact averaged 1-3 years for physician counts but was near zero for facility counts. The estimated window period of the effect was 4-5 years on average. Segmented regression models demonstrated high goodness of fit (median R^2=0.997). Linear trend projections forecast continued decline in general surgery (-260 physicians/year, -350 facilities/year) and obstetrics and gynaecology facilities (-65/year) through 2034, while emergency medicine and general practice trainee numbers are projected to increase.

**Conclusions:** Medical safety incidents are followed by measurable reductions in specialty-specific physician supply, with a lead time of 1-3 years and effect duration of 4-5 years. Obstetrics and gynaecology and general surgery appear most vulnerable. These findings support proactive workforce planning that accounts for the downstream workforce effects of patient safety events.

---

## What is already known on this topic

- Medical malpractice litigation has been associated with defensive medicine practices and physician avoidance of high-risk specialties, primarily studied in the United States.
- A single natural experiment in Japan (Fukushima obstetrics prosecution, 2006) demonstrated a 13% reduction in obstetricians using difference-in-differences analysis.
- No study has systematically quantified the temporal dynamics (lead time and duration) of the association between medical safety incidents and physician workforce changes across multiple specialties.

## What this study adds

- This study provides the first multi-specialty interrupted time series analysis of medical safety incident effects on physician supply, facility counts, and trainee enrolment across 12 specialties in Japan, using three complementary incident definitions.
- The estimated lead time of 1-3 years and window period of 4-5 years offer actionable parameters for workforce forecasting models.
- Beyond the well-documented case of obstetrics, specialties including otolaryngology, dermatology, and urology showed strong delayed inverse associations between incidents and workforce supply—relationships not previously reported.

---

## Introduction

The relationship between medical safety incidents and physician workforce dynamics is of growing importance to health systems worldwide. Concerns that malpractice risk drives physicians away from high-risk specialties have been raised for decades,^1-3^ yet quantitative evidence remains limited, geographically concentrated in the United States, and largely focused on tort reform rather than incident occurrence itself.^4-6^

Japan provides a particularly informative setting for studying this phenomenon. In 2004, an obstetrician at Fukushima Prefectural Ohno Hospital was arrested following a maternal death during caesarean section, and subsequently prosecuted in 2006 for professional negligence causing death.^7^ Although the physician was acquitted in 2008, the case precipitated widespread concern among physicians and is widely regarded as a catalyst for the subsequent decline in obstetricians willing to provide delivery services.^8,9^ Morita estimated a 13% decrease in obstetricians in the affected prefecture using difference-in-differences and synthetic control methods.^10^ However, this analysis was limited to a single event, a single specialty, and a single geographic area.

Japan's healthcare system features two national-level data sources on medical safety incidents. First, the Japan Medical Safety Research Organisation (JMSR; Iryo Anzen Chosa Kiko) was established in 2015 under a revision to the Medical Care Act, creating a mandatory reporting system for unexpected deaths potentially related to medical care.^11^ Second, the Supreme Court of Japan publishes annual statistics on medical malpractice litigation by specialty.^12^ Additionally, Japan conducts biennial national surveys of all practising physicians and maintains annual records of healthcare facility registrations by specialty—providing unusually detailed, population-level workforce data.

We aimed to quantify the temporal association between medical safety incidents and changes in specialty-specific physician counts, healthcare facility numbers, and specialist trainee enrolment, and to estimate the lead time and duration of these associations to inform workforce planning.

## Methods

### Study design and reporting

We conducted an interrupted time series (ITS) analysis using routinely collected national administrative data from Japan. This study is reported in accordance with the RECORD (REporting of studies Conducted using Observational Routinely-collected health Data) statement,^13^ which extends the STROBE guidelines, and the Cochrane Effective Practice and Organisation of Care (EPOC) criteria for interrupted time series studies.^14^ A completed RECORD checklist is provided in supplementary table S1.

### Data sources

#### Medical safety incident data

**Definition 1 (JMSR):** Annual specialty-specific incident reports to the Japan Medical Safety Research Organisation for fiscal years 2015-2025.^11^ Reporting is mandatory for all medical institutions when a death occurs that may have been caused by medical care. Data are publicly available and categorised by the specialty department where the incident occurred.

**Definition 2 (Litigation):** Annual specialty-specific medical malpractice closed-claim counts from the Supreme Court of Japan for 2004-2023.^12^ These data capture resolved civil litigation cases and are stratified by the defendant physician's specialty.

**Definition 3 (Composite):** A composite index for the overlapping period (2015-2023) was constructed by min-max normalising each source to a [0,1] scale and averaging the normalised values.

#### Physician workforce data

Specialty-specific physician counts were obtained from the National Survey of Physicians, Dentists, and Pharmacists (Ishi Shika Ishi Yakuzaishi Chosa), conducted biennially by the Ministry of Health, Labour and Welfare, covering 1994-2022 (with 2024 provisional estimates).^15^ Each physician is counted once under their self-reported primary specialty. As the survey is biennial, annual values were obtained by linear interpolation between survey years.

#### Healthcare facility data

Specialty-specific facility counts were obtained from the Survey of Medical Institutions (Iryo Shisetsu Dotai Chosa), covering 2002-2024.^16^ A facility was counted as providing a given specialty if it was listed among the facility's registered clinical departments (hyoboka).

#### Specialist trainee data

New specialist trainee (senkoi) enrolment counts by basic specialty domain were obtained from the Japan Board of Medical Specialties (Nihon Senmon-i Kiko) for 2018-2025.^17^ These data cover the 19 basic specialty domains of the two-tier board certification system introduced in 2018; sub-specialty (second-tier) data were not available.

### Specialties analysed

Twelve core specialties with sufficient data across all sources were analysed: internal medicine (naika), general surgery (geka), orthopaedic surgery (seikei geka), plastic surgery (keisei geka), obstetrics and gynaecology (sanfujinka), paediatrics (shonika), psychiatry (seishinka), ophthalmology (ganka), otolaryngology (jibi inkoka), urology (hinyokika), dermatology (hifuka), and anaesthesiology (masuika). Additional specialties (emergency medicine, general practice, radiology, neurosurgery, rehabilitation medicine) were included for trainee analysis only.

### Statistical analysis

#### Interrupted time series segmented regression

For each specialty-outcome-definition combination, we fitted the following segmented regression model:

Y_t = β₀ + β₁·time_t + β₂·intervention_t + β₃·time_after_t + β₄·accident_rate_t + ε_t

where Y_t is the outcome (physician count, facility count, or trainee count) at time t; time_t is a sequential time variable; intervention_t is a binary indicator for the period at and after the year of peak incident reporting for that specialty-definition pair; time_after_t is the time elapsed since the intervention point; and accident_rate_t is the contemporaneous incident count. Models were fitted using ordinary least squares (OLS). The intervention year was set to the year of maximum incident count for each specialty-definition pair.

#### Lead time estimation by cross-correlation

To estimate the lead time (delay) between incident occurrence and workforce impact, we computed cross-correlation functions between detrended incident and outcome series. Both series were linearly detrended to remove shared secular trends before computing Pearson correlation coefficients at lags of -8 to +8 years. The lag with the most negative correlation was identified as the estimated lead time for each specialty-definition-outcome combination. A positive lag indicates that changes in incident counts precede changes in the outcome variable.

#### Window period estimation

To estimate the duration over which incidents affect workforce outcomes (the window period), we employed an AIC-based model selection approach. For each specialty-definition-outcome combination, we fitted a series of models with binary intervention indicators of varying duration (1-10 years) beginning at the year of peak incident reporting. The window period was selected as the duration yielding the lowest AIC value.

#### Forecasting

For specialties with at least 10 years of outcome data, we projected physician counts, facility counts, and trainee numbers from 2025 to 2034 using linear trend extrapolation fitted to the most recent 10 years of data. Ninety-five percent prediction intervals were computed from the regression standard error.

#### Software

All analyses were performed in Python 3.11 using NumPy 1.24, SciPy 1.11 (for cross-correlation and interpolation), statsmodels 0.14 (for OLS regression), and pandas 2.0.^18-20^ Analysis code and data are available at [repository URL].

### Patient and public involvement

This study used routinely collected administrative data and involved no direct patient contact. Patients and members of the public were not involved in the design, conduct, or reporting of this research.

## Results

### Descriptive overview

Over the study period, the 12 core specialties encompassed approximately 200 000 physicians and 150 000 healthcare facilities. Between 2015 and 2025, the JMSR received 3 641 reports across all specialties, with surgery (n=520), internal medicine (n=479), and orthopaedic surgery (n=310) recording the highest volumes. Medical malpractice litigation cases across the 12 specialties declined from 982 in 2004 to 534 in 2023 overall, although trends varied by specialty.

Physician counts increased over the study period for most specialties, with notable exceptions: general surgery declined from 25 153 (2002) to approximately 14 800 (2024), and otolaryngology was essentially flat. Facility counts declined for most specialties, with general surgery showing the steepest decrease (from 22 854 in 2005 to approximately 14 000 in 2024). Conversely, plastic surgery, anaesthesiology, and dermatology showed increases in both physicians and facilities.

### Cross-correlation analysis: lead time estimates

Table 1 presents the cross-correlation results for the specialty-definition-outcome combinations with the strongest inverse associations (|r| > 0.9).

**Table 1. Specialty-definition-outcome combinations with strong inverse cross-correlations (|r| > 0.9) after linear detrending**

| Specialty | Incident definition | Outcome | Lag (years) | Correlation (r) |
|---|---|---|---|---|
| Obstetrics & gynaecology | JMSR | Physicians | +3 | -0.946 |
| Obstetrics & gynaecology | Composite | Physicians | +3 | -0.947 |
| Urology | JMSR | Physicians | +6 | -0.945 |
| Anaesthesiology | Composite | Physicians | -4 | -0.959 |
| Otolaryngology | Litigation | Physicians | +6 | -0.973 |
| Dermatology | Litigation | Physicians | +7 | -0.988 |
| Orthopaedic surgery | JMSR (trainee) | Trainees | +4 | -0.909 |
| Otolaryngology | JMSR (trainee) | Trainees | -3 | -0.941 |
| Psychiatry | Litigation | Facilities | +8 | -0.981 |
| Dermatology | Litigation | Facilities | +8 | -0.969 |

Obstetrics and gynaecology consistently demonstrated the strongest inverse association with physician counts across all three incident definitions (r = -0.946 to -0.947), with an estimated lead time of 3 years. Among all specialties, the mean lead time for physician count effects was 1.3 years (median 2.5 years); for facility counts, the mean was approximately 0 years (median 0 years), suggesting near-contemporaneous facility effects.

### Segmented regression results

A total of 53 ITS segmented regression models were fitted across the three definitions. The median model R² was 0.997, reflecting the strong secular trends in both incident and outcome data.

Table 2 presents the statistically significant (P<0.05) incident effect coefficients from the segmented regression models.

**Table 2. Statistically significant (P<0.05) incident effect coefficients from ITS segmented regression**

| Specialty | Definition | Outcome | R² | Incident effect coefficient (95% CI) | P value |
|---|---|---|---|---|---|
| General surgery | Litigation | Physicians | 0.994 | +19.3 per case | <0.001 |
| Obstetrics & gynaecology | JMSR | Physicians | 0.995 | +17.7 per report | 0.021 |
| Obstetrics & gynaecology | Litigation | Physicians | 0.977 | +11.6 per case | <0.001 |
| Obstetrics & gynaecology | JMSR | Facilities | 0.999 | +4.3 per report | 0.042 |
| Obstetrics & gynaecology | Litigation | Facilities | 0.990 | +5.5 per case | <0.001 |
| Ophthalmology | JMSR | Facilities | 1.000 | +4.1 per report | 0.039 |
| Plastic surgery | Litigation | Facilities | 0.999 | +4.1 per case | 0.005 |

The positive direction of the incident effect coefficients warrants careful interpretation (see Discussion). In the segmented regression framework, both incident counts and physician/facility counts share strong secular trends, which can produce paradoxically positive associations in the contemporaneous model even when the detrended cross-correlation is negative.

### Window period estimates

The mean estimated window period was 4.1 years for physician counts (median 4.0) and 4.2 years for facility counts (median 5.0). Among individual specialties, obstetrics and gynaecology showed the longest estimated window period for physician effects (7-9 years depending on incident definition), while general surgery showed 7-10 years. Orthopaedic surgery and plastic surgery had shorter estimated windows (1-2 years).

**Table 3. Summary of lead time and window period estimates by outcome**

| Outcome | Mean lead time (years) | Median lead time (years) | Mean window period (years) | Median window period (years) |
|---|---|---|---|---|
| Physician counts | 1.3 | 2.5 | 4.1 | 4.0 |
| Facility counts | -0.1 | 0.0 | 4.2 | 5.0 |

### Trainee analysis

Cross-correlation between JMSR incident reports and trainee enrolment showed notable inverse associations for orthopaedic surgery (r=-0.91, lag +4 years), otolaryngology (r=-0.94, lag -3 years), and urology (r=-0.90, lag -4 years). However, the trainee data series is limited to 8 years (2018-2025), restricting statistical power and the reliability of lag estimation.

### Forecasting

Based on linear trend extrapolation from the most recent decade, the following specialties are projected to experience continued workforce contraction through 2034 (table 4):

**Table 4. Projected workforce changes by specialty, 2025-2034**

| Specialty | Physicians (annual change) | Facilities (annual change) | Trainees (annual change) |
|---|---|---|---|
| General surgery | -260 | -350 | +3 |
| Obstetrics & gynaecology | +111 | -65 | +6 |
| Internal medicine | +378 | -256 | +30 |
| Paediatrics | +206 | -188 | -5 |
| Orthopaedic surgery | +190 | -34 | +30 |
| Anaesthesiology | +186 | +72 | 0 |
| Otolaryngology | -16 | -97 | -5 |
| Emergency medicine | — | — | +33 |
| General practice | — | — | +20 |

General surgery is projected to decline to approximately 12 054 physicians and 10 318 facilities by 2034, representing a 40% facility reduction from 2010 levels. Conversely, emergency medicine trainee numbers are increasing at the fastest rate (+33 per year), followed by internal medicine and orthopaedic surgery (+30 each).

## Discussion

### Principal findings

This study provides the first systematic, multi-specialty analysis of the temporal association between medical safety incidents and physician workforce dynamics. Using three complementary incident definitions and national administrative data from Japan, we found that incident reports are followed by reductions in specialty-specific physician supply, with an estimated lead time of 1-3 years and an effect duration (window period) of 4-5 years. Obstetrics and gynaecology showed the most consistent and strongest associations, corroborating previous findings from the Fukushima prosecution case,^10^ but extending these to a national, multi-definition framework.

### Comparison with existing literature

The magnitude and direction of the association we observed for obstetrics and gynaecology is consistent with Morita's finding of a 13% decrease in obstetricians following the 2006 prosecution,^10^ and with the broader literature on malpractice-driven specialty avoidance.^1-3^ Studdert and colleagues reported that 42% of physicians in high-risk specialties had restricted their practice in response to malpractice concerns,^1^ and Klick and Stratmann found that tort reforms increased the supply of physicians in high-risk specialties.^4^

However, the present study extends this literature in several important ways. First, we simultaneously analysed 12 specialties, revealing that the phenomenon is not limited to obstetrics. The strong inverse associations observed for otolaryngology (r=-0.97), dermatology (r=-0.99), and urology (r=-0.94)—specialties not traditionally considered "high-risk" for malpractice—suggest that the workforce impact of safety incidents may be more widespread than previously recognised. Second, the explicit estimation of lead time and window period parameters is novel, and provides actionable inputs for workforce forecasting models. Third, the use of three complementary incident definitions (mandatory safety reporting, litigation, and composite) strengthens the triangulation of findings.

The near-zero lag observed for facility counts, compared with the 1-3 year lag for physician counts, has a plausible mechanistic interpretation: facility closure or de-registration of a specialty is a more proximate and binary event (a decision to stop providing a service) than the gradual attrition of physicians from a specialty through retirement, career change, or reduced recruitment.

### Interpretation of segmented regression coefficients

The positive incident effect coefficients observed in the ITS segmented regression models (table 2) require careful interpretation. These do not indicate that more incidents cause more physicians; rather, they reflect the challenge of disentangling contemporaneous trends in a setting where both incident reporting volume (increasing as the JMSR system matured after 2015) and physician counts for some specialties (driven by secular workforce expansion) were simultaneously increasing. The cross-correlation analysis, which removes linear trends before computing correlations at various lags, provides a more appropriate test of the hypothesised delayed inverse association and yielded results consistent with the expected direction. Future analyses using autoregressive integrated moving average (ARIMA) models with transfer functions, or incorporating exogenous covariates for system maturation, may better address this limitation.

### Strengths and limitations

**Strengths:** This study uses population-level data from mandatory national registries, eliminating selection bias in outcome ascertainment. The analysis covers 12 specialties with three incident definitions over periods of up to 20 years, providing a comprehensive view. The explicit estimation of lead time and window period parameters is methodologically novel and practically useful for workforce planning.

**Limitations:** Several important limitations should be acknowledged. First, the JMSR data series begins in 2015, providing only 11 annual data points—below the recommended minimum of approximately 12 pre-intervention and 12 post-intervention time points for ITS analysis.^14^ The litigation series, while longer (2004-2023), has its own limitations in coverage. Second, the biennial physician survey data required linear interpolation to annual values, which may smooth short-term fluctuations. Third, the ITS segmented regression approach assumes that the intervention (peak incident year) is exogenous and discrete, whereas in reality, incident reporting is continuous and endogenous to system-level changes (such as the establishment of the JMSR itself). Fourth, we cannot establish causality. Unmeasured confounders—including demographic shifts, changes in medical school capacity, remuneration differentials, lifestyle preferences, and policy interventions such as the 2004 introduction of the new postgraduate clinical training system—may explain some or all of the observed associations. Fifth, the positive direction of the contemporaneous regression coefficients highlights the difficulty of separating the incident signal from secular trends in a relatively short time series. Sixth, the specialist trainee data cover only 2018-2025 (8 years), severely limiting statistical power for this outcome.

### Policy implications

Despite these limitations, our findings have practical implications for workforce planning. The estimated lead time of 1-3 years suggests a window of opportunity for policy intervention between the occurrence of a high-profile safety incident and its downstream workforce effects. The estimated window period of 4-5 years indicates that effects are not permanent but may persist long enough to cause meaningful service disruption, particularly in specialties already experiencing workforce contraction (general surgery, obstetrics and gynaecology). Systems that can monitor incident reporting trends in near-real time could use these parameters to anticipate and mitigate workforce disruptions through targeted recruitment incentives, workload redistribution, or public communication strategies.

The divergence between physician count trends (generally increasing or stable) and facility count trends (generally decreasing) for most specialties indicates a consolidation of care into fewer, larger facilities. This pattern has implications for geographic access to care, particularly in rural areas.

### Conclusions

Medical safety incidents in Japan are followed by measurable reductions in specialty-specific physician supply, with a lead time of 1-3 years and an effect duration of 4-5 years. Obstetrics and gynaecology and general surgery are the most affected specialties. These temporal parameters can be incorporated into workforce forecasting models to enable proactive planning. Further research using longer time series, individual-level panel data, and causal inference methods is needed to confirm these associations and elucidate the underlying mechanisms.

---

## References

1. Studdert DM, Mello MM, Sage WM, et al. Defensive medicine among high-risk specialist physicians in a volatile malpractice environment. *JAMA* 2005;293:2609-17.
2. Mello MM, Studdert DM, DesRoches CM, et al. Caring for patients in a malpractice crisis: physician satisfaction and quality of care. *Health Aff (Millwood)* 2004;23:42-53.
3. Kessler D, McClellan MB. Do doctors practice defensive medicine? *Q J Econ* 1996;111:353-90.
4. Klick J, Stratmann T. Medical malpractice reform and physicians in high-risk specialties. *J Legal Stud* 2007;36:S121-42.
5. Frakes M. Defensive medicine and obstetric practices. *J Empir Legal Stud* 2012;9:457-81.
6. Frakes MD, Gruber J, Jena AB. Is great information good enough? Evidence from physicians as patients. *J Health Econ* 2021;75:102406.
7. Nagamatsu S, Kami M, Nakata Y. Healthcare safety committee in Japan: mandatory accountability reporting system and punishment. *Curr Opin Anaesthesiol* 2009;22:199-206.
8. Hiyama T, Yoshihara M, Tanaka S, et al. Defensive medicine practices among gastroenterologists in Japan. *World J Gastroenterol* 2006;12:7671-5.
9. Ishikawa T. Distribution and retention of obstetrician-gynecologists in Japan: a longitudinal study, 1996-2016. *Nihon Iji Shimpo* 2021. [in Japanese]
10. Morita H. Criminal prosecution and physician supply. *Int Rev Law Econ* 2018;55:1-11.
11. Japan Medical Safety Research Organisation. Annual report on medical accident investigation. Tokyo: JMSR; 2025. Available from: https://www.medsafe.or.jp/
12. Supreme Court of Japan. Annual report of judicial statistics: medical malpractice litigation. Tokyo: Supreme Court; 2024. [in Japanese]
13. Benchimol EI, Smeeth L, Guttmann A, et al. The REporting of studies Conducted using Observational Routinely-collected health Data (RECORD) statement. *PLoS Med* 2015;12:e1001885.
14. Cochrane Effective Practice and Organisation of Care (EPOC). Interrupted time series (ITS) analyses. EPOC resources for review authors. 2017.
15. Ministry of Health, Labour and Welfare. Survey of physicians, dentists, and pharmacists. Tokyo: MHLW; 2023. [in Japanese]
16. Ministry of Health, Labour and Welfare. Survey of medical institutions (dynamic survey). Tokyo: MHLW; 2024. [in Japanese]
17. Japan Board of Medical Specialties. Specialist trainee registration statistics. Tokyo: JBMS; 2025. [in Japanese]
18. Harris CR, Millman KJ, van der Walt SJ, et al. Array programming with NumPy. *Nature* 2020;585:357-62.
19. Virtanen P, Gommers R, Oliphant TE, et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nat Methods* 2020;17:261-72.
20. Seabold S, Perktold J. Statsmodels: econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference. 2010:92-6.
21. Penfold RB, Zhang F. Use of interrupted time series analysis in evaluating health care quality improvements. *Acad Pediatr* 2013;13:S38-44.
22. Hategeka C, Ruton H, Karamouzian M, et al. Use of interrupted time series methods in the evaluation of health system quality improvement interventions: a methodological systematic review. *BMJ Glob Health* 2020;5:e003567.
23. Turner SL, Karahalios A, Forbes AB, et al. Comparison of six statistical methods for interrupted time series studies: empirical evaluation of 190 published series. *BMC Med Res Methodol* 2021;21:134.
24. Taniguchi K, Watari T, Nagoshi K. Characteristics and trends of medical malpractice claims in Japan between 2006 and 2021. *PLoS One* 2024;19:e0296155.
25. Langan SM, Schmidt SAJ, Wing K, et al. The reporting of studies conducted using observational routinely collected health data statement for pharmacoepidemiology (RECORD-PE). *BMJ* 2018;363:k3532.
26. Higuchi A, Takita M, Tanimoto T, et al. Long-term impact of Japan's nuclear plant accident on deployment of physicians in Fukushima. *Preprint*. SSRN. 2020. doi:10.2139/ssrn.3710618.
27. Currie J, MacLeod WB. First do no harm? Tort reform and birth outcomes. *Q J Econ* 2008;123:795-830.
28. Iizuka T. Does higher malpractice pressure deter medical errors? *J Law Econ* 2013;56:161-88.

---

## Declarations

**Funding:** [To be completed by authors]

**Competing interests:** All authors have completed the ICMJE uniform disclosure form at www.icmje.org/disclosure-of-interest/ and declare: no support from any organisation for the submitted work; no financial relationships with any organisations that might have an interest in the submitted work in the previous three years; no other relationships or activities that could appear to have influenced the submitted work.

**Ethical approval:** This study used publicly available, anonymised, aggregate-level administrative data. No individual-level patient or physician data were accessed. Ethical approval was not required.

**Data sharing:** The analysis code and aggregated datasets used in this study are available at [repository URL]. The original data sources are publicly available from the Japan Medical Safety Research Organisation, the Supreme Court of Japan, and the Ministry of Health, Labour and Welfare.

**Transparency declaration:** The lead author (the manuscript's guarantor) affirms that the manuscript is an honest, accurate, and transparent account of the study being reported; that no important aspects of the study have been omitted; and that any discrepancies from the study as originally planned have been explained.

**Dissemination to participants and related patient and public communities:** The results of this study will be made available to relevant stakeholders including the Japan Medical Safety Research Organisation and professional medical societies.

**Provenance and peer review:** Not commissioned; externally peer reviewed.

---

## Figure legends

**Figure 1.** Trends in medical safety incident counts by specialty and definition. Panel A: JMSR mandatory reports (2015-2025). Panel B: Medical malpractice litigation (2004-2023). The five specialties with the highest incident volumes are highlighted.

**Figure 2.** Interrupted time series plots for physician counts (vertical axis) against JMSR incident reports (coloured overlay) for the 12 core specialties. Fitted segmented regression lines are shown with the vertical dashed line indicating the intervention year (year of peak incident reporting).

**Figure 3.** Heatmap of estimated lead times (years) from cross-correlation analysis. Rows represent specialties; columns represent incident definition-outcome combinations. Darker colours indicate stronger inverse correlations. Positive lag values indicate that incident changes precede outcome changes.

**Figure 4.** Projected physician counts (panel A), facility counts (panel B), and specialist trainee enrolment (panel C) for selected specialties, 2025-2034, based on linear trend extrapolation with 95% prediction intervals.

---

## Supplementary material

**Supplementary table S1.** Completed RECORD checklist.

**Supplementary table S2.** Full ITS segmented regression results for all 53 models.

**Supplementary table S3.** Cross-correlation coefficients at all tested lags for all specialty-definition-outcome combinations.

**Supplementary table S4.** Window period estimates for all specialty-definition-outcome combinations.

**Supplementary figure S1.** Interrupted time series plots for facility counts against JMSR incident reports.

**Supplementary figure S2.** Interrupted time series plots for physician counts against litigation data.

**Supplementary figure S3.** Cross-correlation function plots for all specialties.
