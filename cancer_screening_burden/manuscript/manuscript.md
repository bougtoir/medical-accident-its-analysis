# False-positive cascade and healthcare capacity burden of direct-to-consumer multi-cancer early detection blood tests in Japan: a scenario modelling study

## Abstract

**Background:** Direct-to-consumer (DTC) blood-based multi-cancer early detection (MCED) tests are marketed as a simple alternative to organised screening, but their positive predictive value (PPV) is low in asymptomatic populations and each screen-positive person may trigger multiple confirmatory examinations.

**Methods:** We built a deterministic expected-value model parameterised with 2023 Japanese adult cancer incidence rates, 2023 population counts, and 2023 national medical-facility diagnostic volumes. We estimated true positives, false positives, downstream visits, and capacity utilisation for CT, MRI, endoscopy and specialist visits across follow-up rates of 0–100% and specificities of 95.0–99.9%.

**Results:** At 50% follow-up, a screening wave of 100,000 persons would generate 383.5 true positives and 7994.5 false positives (overall PPV 4.60%; FP/TP ratio 20.8). Total downstream visits would reach 15684.4, with maximum capacity utilisation 146.6% (specialist visits). Any follow-up rate above 40% already exceeds illustrative capacity. PPV ranged from 0.70% (Ovarian) to 8.00% (Colorectal) across cancer types and was strongly age-dependent.

**Conclusions:** Even with optimistic 99% specificity, a DTC MCED wave can trigger a false-positive cascade that exceeds Japanese outpatient and endoscopic capacity. Regulatory guardrails on performance claims, follow-up obligations, and reporting are needed before routine adoption.

**Keywords:** multi-cancer early detection, false positive, healthcare capacity, direct-to-consumer testing, Japan, scenario model

---

## Introduction

Blood-based multi-cancer early detection (MCED) tests are increasingly advertised directly to consumers as a convenient “single blood draw” cancer screen [^1^]. Because most positive results in asymptomatic populations are false positives, each abnormal test generates a cascade of confirmatory imaging and specialist visits [^3^][^4^]. In Japan, where endoscopy and specialist visits are already constrained [^2^], widespread DTC use could displace routine care. We quantified this burden as a function of follow-up behaviour, test specificity, and age structure.

## Methods

### Data sources

Cancer incidence by site, age, sex, and calendar year (2023) and the corresponding 2023 Japanese population by age and sex were taken from the National Cancer Center of Japan [^1^]. Annual volumes of CT, MRI, and upper/lower gastrointestinal endoscopies were derived from the 2023 Ministry of Health, Labour and Welfare Medical Facility Survey [^2^]. Test sensitivity and specificity ranges were informed by two recent systematic reviews of blood-based MCED tests [^3^][^4^], and real-world PPV evidence came from a nationwide PET/CT facility survey of N-NOSE-triggered examinations [^5^].

### Model

We used a deterministic expected-value cohort model. For each cancer \(c\):

- Actual cases = screened population × prevalence per 100,000 / 100,000.
- True positives = actual cases × sensitivity.
- False positives = (screened population − actual cases) × (1 − specificity).

Each positive individual who followed up (follow-up rate, 0–100%) generated visits to CT, MRI, endoscopy, and specialist care according to cancer-specific pathway probabilities. Additional visits per true and false positive were added. Capacity utilisation for each resource was calculated as total visits divided by the annual capacity per 100,000 population. A full description of equations is available in `simulate.py`.

Prevalence was approximated by adult (20+) incidence because point prevalence of undiagnosed, screen-detectable cancers is not publicly reported. This is a conservative lower-bound for true positives and therefore an upper-bound for PPV and FP/TP ratios. Pathway probabilities and the share of facility capacity available for a new DTC-related wave were scenario assumptions, documented in `parameters.yaml`.

### Scenarios

Base-case sensitivity and specificity were 0.70 and 0.990. We varied follow-up rate from 0 to 100% and specificity from 0.950 to 0.999 in a sensitivity sweep. The available-for-cancer-workup share of national diagnostic capacity was set to 20%.

## Results

### Scenario parameters

Table 1 summarises the data sources and base-case parameter values.

**Table 1. Data sources and scenario parameters.**

| Parameter | Value | Source / assumption |
|---|---|---|
| Screened population | 100,000 | Model cohort |
| Base sensitivity | 0.70 | Kahwati LC et al. Blood-Based Tests for Multiple Cancer Screening: A Systematic Review. AHRQ 2025. https://www.ncbi.nlm.nih.gov/books/NBK618307/ |
| Base specificity | 0.990 | Kahwati LC et al. Blood-Based Tests for Multiple Cancer Screening: A Systematic Review. AHRQ 2025. https://www.ncbi.nlm.nih.gov/books/NBK618307/ |
| CT capacity per 100k per year | 5676 | Ministry of Health, Labour and Welfare, 2023 Medical Facility Survey (Static/Dynamic), 05sisetu05.xlsx |
| MRI capacity per 100k per year | 2678 | Ministry of Health, Labour and Welfare, 2023 Medical Facility Survey (Static/Dynamic), 05sisetu05.xlsx |
| Endoscopy capacity per 100k per year | 2583 | Ministry of Health, Labour and Welfare, 2023 Medical Facility Survey (Static/Dynamic), 05sisetu05.xlsx |
| Specialist capacity per 100k per year | 8000 | Illustrative scenario assumption |
| Gastric prevalence (per 100k) | 84.3 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Colorectal prevalence (per 100k) | 123.8 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Lung prevalence (per 100k) | 99.7 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Breast prevalence (per 100k) | 83.2 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Prostate prevalence (per 100k) | 82.1 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Liver prevalence (per 100k) | 26.2 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Pancreatic prevalence (per 100k) | 38.2 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |
| Ovarian prevalence (per 100k) | 10.3 | National Cancer Center of Japan, Cancer Statistics in Japan 2016-2023 |

### Per-cancer burden at 50% follow-up

At a 50% follow-up rate, the model estimated 383.5 true positives and 7994.5 false positives across all eight cancers (Table 2). Colorectal had the highest age-adjusted PPV (8.00%) and Ovarian the lowest (0.70%). The FP/TP ratio ranged from 11.5 to 137.4.

**Table 2. Per-cancer outcomes at 50% follow-up (per 100,000 screened).**

| Cancer | Prevalence per 100k | True positives | False positives | PPV (%) | FP/TP ratio | Total visits | Max resource utilisation (%) |
|---|---|---|---|---|---|---|---|
| Gastric | 84.3 | 59.0 | 999.2 | 5.60 | 16.9 | 2084.3 | 18.4 |
| Colorectal | 123.8 | 86.7 | 998.8 | 8.00 | 11.5 | 2170.7 | 20.0 |
| Lung | 99.7 | 69.8 | 999.0 | 6.50 | 14.3 | 2295.7 | 21.3 |
| Breast | 83.2 | 58.2 | 999.2 | 5.50 | 17.2 | 1632.4 | 17.4 |
| Prostate | 82.1 | 57.5 | 999.2 | 5.40 | 17.4 | 1654.5 | 17.0 |
| Liver | 26.2 | 18.4 | 999.7 | 1.80 | 54.4 | 1702.8 | 16.2 |
| Pancreatic | 38.2 | 26.7 | 999.6 | 2.60 | 37.4 | 2144.1 | 19.7 |
| Ovarian | 10.3 | 7.2 | 999.9 | 0.70 | 137.4 | 1999.8 | 19.0 |

### Capacity impact

Total downstream visits rose from 0.0 at 0% follow-up to 31368.8 at 100% follow-up (Fig. 1). Resource utilisation is shown in Fig. 2. The first illustrative capacity ceiling was exceeded at a follow-up rate of 40% (specialist visits), and at 50% follow-up maximum utilisation was 146.6%.

![Figure 1: Total downstream visits by follow-up rate](output/total_visits_by_followup.png)
**Fig. 1.** Total downstream diagnostic and specialist visits generated by a blood-based MCED screening wave of 100,000 persons, by follow-up rate.

![Figure 2: Diagnostic capacity utilisation by follow-up rate](output/capacity_utilization.png)
**Fig. 2.** Capacity utilisation (%) for CT, MRI, endoscopy, and specialist visits as follow-up rate increases. Values above 100% indicate demand exceeding the illustrative annual capacity available for a DTC screening wave.

### Age-specific positive predictive value

PPV was strongly age-dependent (Fig. 3). In younger age groups PPV fell below 1% for several cancers, rising above 20% only in the oldest groups. This implies that if DTC MCED users are younger than the general screening population, aggregate PPV would be lower and the false-positive burden larger than the base-case estimate.

![Figure 3: Age-specific PPV by cancer type](output/ppv_by_age.png)
**Fig. 3.** Age-specific positive predictive value for each cancer, assuming sensitivity 0.70 and specificity 0.99.

### Sensitivity to test specificity

Lowering specificity from 99% to 95% approximately halved aggregate PPV (from 4.58% to 0.95%) and dramatically increased total visits and capacity pressure (Fig. 4; Table 3).

**Table 3. Aggregate outcomes by follow-up rate (base-case specificity).**

| Follow-up rate | True positives | False positives | Total positives | PPV (%) | FP/TP ratio | Total visits | Max capacity utilisation (%) |
|---|---|---|---|---|---|---|---|
| 0% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 0.0 | 0.0 |
| 10% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 3136.9 | 29.3 |
| 20% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 6273.8 | 58.6 |
| 30% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 9410.6 | 87.9 |
| 40% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 12547.5 | 117.2 |
| 50% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 15684.4 | 146.6 |
| 60% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 18821.3 | 175.9 |
| 70% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 21958.2 | 205.2 |
| 80% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 25095.1 | 234.5 |
| 90% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 28231.9 | 263.8 |
| 100% | 383.5 | 7994.5 | 8378.0 | 4.60 | 20.8 | 31368.8 | 293.1 |

![Figure 4: PPV and total positives across specificity values](output/specificity_sweep.png)
**Fig. 4.** Aggregate positive predictive value (%) and total positive results per 100,000 screened across specificity values at a 70% follow-up rate.

## Discussion

Our scenario model shows that, even under optimistic assumptions for test accuracy, a DTC blood-based MCED screening wave can produce roughly 21 false-positive workups for every true cancer detected. At 30% follow-up, illustrative specialist capacity is already saturated (87.9% utilisation); at 50% it is exceeded by 46.6 percentage points. The burden is not uniform: cancers with low prevalence (ovarian, liver, pancreatic) had the lowest PPV and the highest FP/TP ratios, while age strongly modulates PPV.

These findings align with real-world data from the N-NOSE PET/CT survey, in which the cancer discovery rate after a high-risk result was low and well below the company's advertised PPV [^5^].

### Limitations

Our analysis intentionally uses scenario assumptions for test performance, diagnostic pathways, and the age distribution of DTC users, because these data are not publicly reported. Prevalence was approximated by adult incidence; true point prevalence of undiagnosed cancers may differ. Capacity was annualised from a one-month facility survey and then further reduced by an arbitrary available-for-cancer-workup share. The model is deterministic and does not capture stochastic variation, geographic maldistribution, or queueing effects.

### Conclusion

Without regulatory guardrails—clear performance thresholds, transparent PPV reporting, and follow-up obligations—direct-to-consumer MCED tests risk converting a marketing promise into a large-scale false-positive cascade that stresses Japan’s diagnostic capacity.

## References

1. National Cancer Center of Japan. Cancer Statistics in Japan 2016-2023. https://ganjoho.jp/reg_stat/statistics/data/dl/en.html

2. Ministry of Health, Labour and Welfare. 2023 Medical Facility Survey (Static/Dynamic). https://www.mhlw.go.jp/toukei/saikin/hw/iryosd/23/

3. Kahwati LC, et al. Blood-Based Tests for Multiple Cancer Screening: A Systematic Review. AHRQ; 2025. https://www.ncbi.nlm.nih.gov/books/NBK618307/

4. Schnabel JL, et al. Predictive Performance of Cell-Free Nucleic Acid-Based Multi-Cancer Early Detection Tests: A Systematic Review. PubMed; 2024. https://pubmed.ncbi.nlm.nih.gov/37791504/

5. Nagamachi S, et al. Nationwide PET/CT facility survey on N-NOSE-triggered examinations. J Nucl Med Technol (Japanese report), 2024. https://jcpet.jp/2024/10/senchu-chosa.html
