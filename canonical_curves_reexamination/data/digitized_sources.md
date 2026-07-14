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

## #36 Ebbinghaus Forgetting Curve — `ebbinghaus_real.csv`
- Source: Ebbinghaus H (1885) "Über das Gedächtnis" / Ruger & Bussenius (1913)
  translation "Memory: A Contribution to Experimental Psychology", Chapter VII,
  Sections 28-29 (public domain). Transcribed from the original savings table
  (verifiable at Wikisource and psychclassics.yorku.ca/Ebbinghaus/memory7.htm).
- Values (X = hours after learning, Q = % savings retained):
  0.33h→58.2, 1h→44.2, 8.8h→35.8, 24h→33.7, 48h→27.8, 144h→25.4, 744h→21.1.
- x = log(time in hours); y = retention (savings %). Not extrapolated — exactly
  the 7 intervals Ebbinghaus reported.

## #29 Species-Area Curve — `species_area_real.csv`
- Source: M. P. Johnson & P. H. Raven (1973) "Species number and endemism: The
  Galápagos Archipelago revisited." Science 179(4076):893-895. Distributed as the
  `gala` dataset in the R `faraway` package (extracted from the CRAN source
  tarball `faraway/data/gala.rda`).
- 30 Galápagos islands: island area (km²) and number of plant species.
- x = log₁₀(Area, km²); y = log₁₀(Species). Replaces the previous invented
  "representative" bird-species counts for Caribbean/global islands.

## #41 Kleiber's Law — `kleiber_real.csv`
- Source: AnAge database, build 14 (Human Ageing Genomic Resources; Tacutu et
  al. 2018 Nucleic Acids Res 46:D1083-D1090), fields "Metabolic rate (W)" and
  "Body mass (g)", downloaded from https://genomics.senescence.info/species/.
- Restricted to Class Mammalia with both fields present and >0 → 422 species.
  Body mass converted g→kg. This is a modern real-data test of Kleiber's law
  (not Kleiber's 1932 domestic-animal table, whose scanned original is not
  reliably machine-readable); the source is labelled accordingly.
- x = log₁₀(Body mass, kg); y = log₁₀(BMR, W). Replaces 22 hand-entered values.

## #45 Duverger's Law — `duverger_real.csv`
- Source: Nils-Christian Bormann & Matt Golder, Democratic Electoral Systems
  (DES) dataset, version 5.0 (Bormann & Golder 2022 Electoral Studies 78;
  Bormann & Kaftan 2024 Open Research Europe 4:73). Downloaded
  `es_data-v50.zip` from https://mattgolder.com/elections.
- Legislative elections with tier-1 average district magnitude and effective
  number of electoral parties (enep, Laakso-Taagepera) both present → 1660
  elections. Replaces 30 hand-entered country values.
- x = log(district magnitude + 1); y = effective number of electoral parties.
