# Lin's Concordance Correlation Coefficient: A Missing Metric in Cardiac Output Monitor Validation

## Commentary

**Target Journal**: Journal of Clinical Monitoring and Computing

---

**Authors**: [Author names to be completed]

**Affiliations**: [To be completed]

**Corresponding author**: [To be completed]

**Word count**: ~2,400 (Commentary)

**Keywords**: concordance correlation coefficient, cardiac output, method comparison, Bland-Altman, hemodynamic monitoring, validation

---

## Abstract

The validation of cardiac output (CO) monitoring devices has evolved into a standardised framework comprising Bland-Altman analysis, percentage error, and polar plot assessment. While this triad effectively evaluates bias, limits of agreement, and trending ability, it does not provide a single integrated metric that simultaneously quantifies both accuracy and precision of absolute measurements. Lin's concordance correlation coefficient (CCC), which decomposes overall agreement into precision (Pearson's r) and accuracy (bias correction factor C_b), addresses this gap. Despite its established role in other areas of biomedical method comparison, the CCC has not been incorporated into the standard validation framework for CO monitors. In this commentary, we argue that the CCC and its associated concordance plot should be adopted as a complementary metric in CO monitor validation studies, providing information that is not captured by the current standard analytical approach.

---

## Introduction

Over the past quarter-century, a consensus framework for validating cardiac output (CO) monitoring devices has emerged, anchored by three principal analytical tools: the Bland-Altman plot for assessing bias and limits of agreement [1,2], the percentage error (PE) criterion proposed by Critchley and Critchley for normalised comparison across populations [3], and the polar plot for evaluating trending ability [4,5]. Methodological guidance has been further refined by Cecconi et al. [6], Saugel et al. [7], and Odor et al. [8], establishing a stepwise approach and checklist for method comparison studies.

This framework has served the field well. However, a critical examination reveals an important gap: none of these tools provides an integrated, single-value metric that simultaneously captures both the accuracy (closeness to the true value) and precision (reproducibility) of absolute CO measurements against the 45-degree line of perfect agreement. The Bland-Altman plot evaluates bias and spread of differences but does not directly quantify agreement with the identity line. The PE normalises the limits of agreement but inherits the same limitation. The polar plot evaluates only the direction and magnitude of changes, not absolute values.

Lin's concordance correlation coefficient (CCC), introduced in 1989 [9], was designed precisely to fill this role in method comparison studies. Despite being widely adopted in other biomedical fields---including laboratory medicine, imaging, and pulmonary function testing---the CCC has not been systematically incorporated into the CO monitoring validation literature. In this commentary, we propose that the CCC should be added to the standard validation toolkit for CO monitors and explain the specific diagnostic information it provides beyond existing methods.

## The Current Framework and Its Limitations

### Bland-Altman Analysis

The Bland-Altman plot remains the cornerstone of CO monitor validation [1,2]. By plotting the difference between two methods against their mean, it provides a visual assessment of bias (mean difference) and precision (limits of agreement, LoA = bias +/- 1.96 SD). However, as Odor et al. [8] acknowledged, the Bland-Altman plot has inherent limitations: data points scattered throughout the chart may suggest no consistent bias but do not exclude "hidden or inconsistent bias." Furthermore, the LoA are purely statistical boundaries---they describe where 95% of differences fall but do not directly indicate whether the new device's readings are interchangeable with the reference at the individual measurement level.

A particularly important limitation emerges when a device exhibits proportional bias---that is, when the magnitude of disagreement varies systematically with the level of CO. In such cases, a single set of LoA may be misleading, as the agreement characteristics differ across the measurement range. While regression-based approaches to the Bland-Altman plot can address this [2], they add complexity and are inconsistently applied.

### Percentage Error

The Critchley-Critchley criterion of PE <= +/-30% [3] provides an objective acceptance threshold derived from the known precision of the pulmonary artery catheter (PAC) thermodilution reference (+/-20%). This was a landmark contribution that enabled standardised comparison across studies and populations. However, PE is calculated from the LoA divided by the mean CO, meaning it inherits the limitations of the Bland-Altman analysis. Moreover, the 30% threshold assumes a specific reference method precision; when the reference technique differs (e.g., transoesophageal echocardiography, transpulmonary thermodilution), the threshold should theoretically be recalculated [6], though this adjustment is rarely performed in practice.

### Polar Plot

The polar plot, introduced by Critchley et al. [4], evaluates trending ability by representing the agreement between paired changes in CO as angular deviations from a radial axis. Angular bias, radial limits of agreement, and polar concordance rate describe how well a device tracks dynamic changes. This is clinically important, as trending ability may be more relevant than absolute accuracy for goal-directed therapy. However, the polar plot explicitly evaluates only directional agreement of changes and provides no information about the agreement of absolute values.

### The Gap

Taken together, the current triad evaluates:
- **Bias and spread** (Bland-Altman) --- but not integrated agreement with the identity line
- **Normalised agreement** (PE) --- but inheriting Bland-Altman limitations
- **Trending ability** (Polar plot) --- but only for changes, not absolute values

What is missing is a metric that directly answers: *"How closely do the paired measurements from two methods fall along the 45-degree line of perfect agreement?"* This is precisely what Lin's CCC quantifies.

## Lin's Concordance Correlation Coefficient

### Definition and Decomposition

Lin's CCC (rho_c) evaluates the degree to which pairs of observations fall on the 45-degree line of perfect concordance [9,10]. It is defined as:

    rho_c = (2 * sigma_12) / (sigma_1^2 + sigma_2^2 + (mu_1 - mu_2)^2)

where sigma_12 is the covariance, sigma_1^2 and sigma_2^2 are the variances, and mu_1 and mu_2 are the means of the two measurements.

Crucially, the CCC can be decomposed into two interpretable components:

    rho_c = r * C_b

where:
- **r** (Pearson's correlation coefficient) measures **precision**---the tightness of data around the best-fit line
- **C_b** (bias correction factor) measures **accuracy**---how far the best-fit line deviates from the 45-degree identity line

This decomposition is diagnostically powerful. A device with high r but low C_b is precise but inaccurate (consistent scale or offset error---potentially correctable by recalibration). A device with low r but high C_b has poor precision despite good average accuracy (inherent measurement noise---not correctable by calibration). This distinction has direct implications for device development and clinical decision-making but cannot be extracted from the Bland-Altman plot or PE alone.

### The Concordance Plot

The concordance plot---a scatter plot of Method 1 vs. Method 2 with the 45-degree identity line overlaid---provides an immediate visual assessment of overall agreement. Unlike the Bland-Altman plot, which obscures the actual measurement scale by plotting differences against means, the concordance plot preserves the clinical measurement scale (L/min for CO) on both axes. This allows direct visual identification of:

1. **Scale errors** (slope != 1): the best-fit line diverges from the identity line
2. **Offset errors** (intercept != 0): systematic shift visible at low or high CO values
3. **Range-dependent disagreement**: fanning patterns indicating heteroscedasticity
4. **Outliers**: individual measurements far from the identity line

## A Numerical Illustration

Consider two hypothetical non-invasive CO monitors, both compared against PAC thermodilution in 120 paired measurements (true CO range: 2.0-9.0 L/min, mean ~5.0 L/min) (Figure 1):

**Device A** (proportional bias, good precision):
- Bland-Altman: bias = +0.15 L/min, LoA = [-1.44, +1.75] L/min, PE = 30.5%
- Relationship: CO_A = 1.21 * CO_ref - 0.92 (slope > 1, compensating offset)
- CCC = 0.867 (r = 0.907, C_b = 0.956)

**Device B** (no systematic bias, poor precision):
- Bland-Altman: bias = +0.12 L/min, LoA = [-1.70, +1.93] L/min, PE = 34.9%
- Relationship: CO_B = 0.83 * CO_ref + 1.00 + random noise (SD = 1.10)
- CCC = 0.778 (r = 0.782, C_b = 0.995)

By Bland-Altman analysis alone, Devices A and B appear broadly similar: comparable bias (~0.1 L/min), overlapping LoA ranges, and PE values both in the 30-35% range---near the Critchley-Critchley threshold. A conventional assessment might conclude that both devices have borderline acceptable agreement. However, the CCC decomposition reveals fundamentally different error profiles (Figure 2):

- **Device A**: high precision (r = 0.907) but reduced accuracy (C_b = 0.956)---a systematic scale error (slope = 1.21) that could potentially be corrected by algorithmic recalibration of the gain factor
- **Device B**: good accuracy (C_b = 0.995) but poor precision (r = 0.782)---inherent measurement variability that cannot be corrected by calibration

This distinction is clinically and developmentally important. For Device A, a firmware update adjusting the algorithm's gain factor could substantially improve agreement, potentially bringing the PE well below 30%. For Device B, fundamental hardware or signal processing improvements would be necessary, as the error is stochastic rather than systematic. The Bland-Altman analysis alone cannot differentiate these scenarios, yet the CCC decomposition immediately identifies the nature of each device's limitation and the appropriate corrective strategy.

## Why Now? Eight Years After Odor et al.

Several developments since the publication of Odor et al. [8] in 2017 strengthen the case for incorporating the CCC:

1. **Proliferation of non-invasive devices**: The market for non-invasive CO monitors has expanded considerably, with finger-cuff (ClearSight/VitaWave), bioimpedance/bioreactance (NICOM/Starling), electrical cardiometry (ICON), and pulse decomposition analysis (VitalStream) devices all receiving regulatory clearance [11-13]. The diversity of measurement principles makes standardised, comprehensive validation more important than ever.

2. **Regulatory implications**: The FDA 510(k) pathway for these devices requires demonstration of substantial equivalence, but the specific statistical methods for validation are not prescribed [14]. Published validation studies overwhelmingly rely on BA analysis and PE, with polar plots for trending. A consensus recommendation to include CCC could influence both study design and regulatory expectations.

3. **Persistent methodological inconsistency**: Recent meta-analyses and systematic reviews continue to identify inconsistency in how validation results are reported across studies [15]. Adding the CCC as a standardised metric---with established benchmarks (e.g., poor < 0.90, moderate 0.90-0.95, good 0.95-0.99, excellent > 0.99, adapted from McBride [16])---would facilitate cross-study comparison.

4. **Computational accessibility**: The CCC is trivially calculated from raw paired data using widely available statistical software (R package `epiR`, Python `pingouin`, Stata `concord`). No additional data collection beyond what is already required for Bland-Altman analysis is needed.

## Proposed Extended Validation Framework

We propose that the standard CO monitor validation framework be extended from a triad to a quartet:

| Metric | Evaluates | Clinical Question |
|--------|-----------|-------------------|
| **Bland-Altman plot** | Bias, LoA | What is the systematic error and spread of differences? |
| **Percentage error** | Normalised LoA | Is agreement clinically acceptable relative to the reference? |
| **Polar plot** | Trending ability | Does the device track changes in the correct direction? |
| **CCC + concordance plot** | Integrated accuracy x precision | How closely do measurements fall on the line of perfect agreement, and is the error due to bias or noise? |

The CCC should be reported alongside its decomposition (r and C_b), as the individual components provide actionable diagnostic information. The concordance plot should be presented with the 45-degree identity line, the best-fit regression line, and the CCC value annotated.

We emphasise that the CCC is not proposed as a replacement for existing methods but as a complement that fills a specific analytical gap. Each metric in the proposed quartet answers a distinct clinical question, and together they provide a comprehensive characterisation of device performance.

## Conclusion

The current standard framework for CO monitor validation---Bland-Altman analysis, percentage error, and polar plot---has served the field for over two decades. However, it lacks an integrated metric for absolute measurement agreement that simultaneously captures accuracy and precision. Lin's concordance correlation coefficient, with its interpretable decomposition into precision and accuracy components, fills this gap. Given the proliferation of non-invasive CO monitoring technologies and the increasing importance of standardised validation methodology, we recommend that the CCC and concordance plot be adopted as a routine component of CO monitor validation studies.

---

## References

1. Bland JM, Altman DG. Statistical methods for assessing agreement between two methods of clinical measurement. Lancet. 1986;327(8476):307-310. doi:10.1016/S0140-6736(86)90837-8

2. Bland JM, Altman DG. Measuring agreement in method comparison studies. Stat Methods Med Res. 1999;8(2):135-160. doi:10.1177/096228029900800204

3. Critchley LAH, Critchley JAJH. A meta-analysis of studies using bias and precision statistics to compare cardiac output measurement techniques. J Clin Monit Comput. 1999;15(2):85-91. doi:10.1023/A:1009982611386

4. Critchley LA, Lee A, Ho AM-H. A critical review of the ability of continuous cardiac output monitors to measure trends in cardiac output. Anesth Analg. 2010;111(5):1180-1192. doi:10.1213/ANE.0b013e3181f08a5b

5. Critchley LA, Yang XX, Lee A. Assessment of trending ability of cardiac output monitors by polar plot methodology. J Cardiothorac Vasc Anesth. 2011;25(3):536-546. doi:10.1053/j.jvca.2011.01.003

6. Cecconi M, Rhodes A, Poloniecki J, Della Rocca G, Grounds RM. Bench-to-bedside review: the importance of the precision of the reference technique in method comparison studies---with specific reference to the measurement of cardiac output. Crit Care. 2009;13(1):201. doi:10.1186/cc7129

7. Saugel B, Grothe O, Wagner JY. Tracking changes in cardiac output: statistical considerations on the 4-quadrant plot and the polar plot methodology. Anesth Analg. 2015;121(2):514-524. doi:10.1213/ANE.0000000000000725

8. Odor PM, Bampoe S, Cecconi M. Cardiac output monitoring: validation studies---how results should be presented. Curr Anesthesiol Rep. 2017;7(4):410-415. doi:10.1007/s40140-017-0239-0

9. Lin LI. A concordance correlation coefficient to evaluate reproducibility. Biometrics. 1989;45(1):255-268. doi:10.2307/2532051

10. Lin LI. A note on the concordance correlation coefficient. Biometrics. 2000;56(1):324-325. doi:10.1111/j.0006-341X.2000.00324.x

11. Ameloot K, Palmers PJ, Malbrain MLNG. The accuracy of noninvasive cardiac output and pressure measurements with finger cuff: a concise review. Curr Opin Crit Care. 2015;21(3):232-239. doi:10.1097/MCC.0000000000000198

12. Squara P, Denjean D, Estagnasie P, Brusset A, Dib JC, Dubois C. Noninvasive cardiac output monitoring (NICOM): a clinical validation. Intensive Care Med. 2007;33(7):1191-1194. doi:10.1007/s00134-007-0640-0

13. Song W, Guo J, Cao D, et al. Comparison of noninvasive electrical cardiometry and transpulmonary thermodilution for cardiac output measurement in critically ill patients: a prospective observational study. BMC Anesthesiol. 2025;25:123. doi:10.1186/s12871-025-03005-1

14. U.S. Food and Drug Administration. Premarket Notification 510(k). https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/premarket-notification-510k. Accessed March 2026.

15. Joosten A, Desebbe O, Suehiro K, et al. Accuracy and precision of non-invasive cardiac output monitoring devices in perioperative medicine: a systematic review and meta-analysis. Br J Anaesth. 2017;118(3):298-310. doi:10.1093/bja/aew461

16. McBride GB. A proposal for strength-of-agreement criteria for Lin's concordance correlation coefficient. NIWA Client Report HAM2005-062. 2005.

---

## Supplementary Note: Software Implementation

The CCC can be calculated in common statistical environments:

**R**:
```r
library(epiR)
result <- epi.ccc(method1, method2, ci = "z-transform", conf.level = 0.95)
# Returns: rho.c (CCC), s.shift (scale shift), l.shift (location shift),
#          C.b (bias correction factor), r (Pearson r)
```

**Python**:
```python
import pingouin as pg
# or manually:
import numpy as np

def concordance_cc(y1, y2):
    """Lin's Concordance Correlation Coefficient with decomposition."""
    mean1, mean2 = np.mean(y1), np.mean(y2)
    var1, var2 = np.var(y1, ddof=1), np.var(y2, ddof=1)
    sd1, sd2 = np.std(y1, ddof=1), np.std(y2, ddof=1)
    cor = np.corrcoef(y1, y2)[0, 1]  # Pearson r (precision)
    # Bias correction factor (accuracy)
    c_b = (2 * sd1 * sd2) / (var1 + var2 + (mean1 - mean2)**2)
    # CCC = r * C_b
    ccc = cor * c_b
    return {'ccc': ccc, 'pearson_r': cor, 'C_b': c_b}
```

**Stata**:
```stata
concord method1 method2, summary
```

---

*Conflicts of Interest*: [To be declared]

*Funding*: [To be declared]
