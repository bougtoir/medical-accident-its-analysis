# Digitized / transcribed source data

Curves whose data cannot be fetched from a public API are taken directly from the
original published figure/table. Each entry records the paper, DOI, the specific
table/figure, and how the values were obtained. Values are transcribed exactly as
published (no rounding beyond the source) or extracted from the figure with
WebPlotDigitizer. These are stored in `data/*_real.csv` and read by
`scripts/data_additional_real.py`.

## #21 BMI-Mortality J-Curve — `bmi_mortality_real.csv`
- Source: The Global BMI Mortality Collaboration (2016). "Body-mass index and
  all-cause mortality: individual-participant-data meta-analysis of 239
  prospective studies in four continents." Lancet 388(10046):776-786.
  DOI: 10.1016/S0140-6736(16)30175-1 (Open Access, CC BY).
- Values: primary prespecified analysis — never-smokers without chronic disease
  at baseline, excluding the first 5 years of follow-up; study/age/sex-adjusted
  hazard ratios relative to BMI 22.5-<25.0 kg/m². The nine finer BMI groups and
  their HRs (95% CI) are stated verbatim in the Abstract/Findings and Table 2.
- Transcription (not figure digitization): HRs read from the reported numbers.
- x = BMI category midpoint (kg/m²); y = all-cause mortality hazard ratio.
