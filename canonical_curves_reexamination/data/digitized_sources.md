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

## #2 Laffer Curve — `laffer_real.csv`
- Sources (OECD, latest common year = 2022 cross-section, matched on ISO3):
  - x = top (statutory) personal income tax rate: OECD Tax Database, Table I.7
    ("Top statutory personal income tax rates"), series TAX=PERS_ITAX (combined
    central + sub-central), fetched from the OECD SDMX-JSON endpoint
    (dataset TABLE_I7).
  - y = total tax revenue as % of GDP: OECD Global Revenue Statistics
    (Data Explorer dataflow DSD_REV_COMP_GLOBAL@DF_RSGLOBAL; MEASURE=TAX_REV,
    SECTOR=S13 general government, STANDARD_REVENUE=_T total tax,
    UNIT_MEASURE=PT_B1GQ % of GDP).
- 29 OECD countries with both variables for 2022. Replaces the previous
  26 hand-transcribed OECD-2022 values (which mixed years/definitions, e.g. a
  central-only US top rate and older tax-revenue figures).
- x = top marginal PIT rate (%); y = total tax revenue (% of GDP).

## #11 Great Gatsby Curve — `great_gatsby_real.csv` (reconstruction)
- This is a modern public-data RECONSTRUCTION, not a replication of Corak's
  (2013) original figure. Matched on ISO3.
  - y = intergenerational income elasticity (IGE, father-son): World Bank
    Global Database on Intergenerational Mobility (GDIM), income mobility
    dataset (Munoz, Ercio & Roy van der Weide 2025, "Intergenerational income
    mobility around the world: A new database", WB Policy Research WP 11166),
    file `IGE_Munoz_VanderWeide_June2025.dta` (87 economies). Downloaded from
    the WB Development Data Hub (dataset 0066878).
  - x = Gini index: Our World in Data `economic-inequality-gini-index`
    (source: World Bank Poverty and Inequality Platform), most recent year
    2000-2022 per country, rescaled to 0-100.
- 83 economies with both variables. Replaces 23 hand-entered Gini/IGE values.
- IGE per-country literature source is retained in the CSV (`ige_source`).

## #32 HANPP vs Development — `hanpp_real.csv` (zonal aggregation of grids)
- Source: Haberl, H., K.-H. Erb, F. Krausmann, V. Gaube, A. Bondeau, C. Plutzar,
  S. Gingrich, W. Lucht & M. Fischer-Kowalski (2007) "Quantifying and mapping
  the human appropriation of net primary production in Earth's terrestrial
  ecosystems." PNAS 104(31):12942-12947 (doi:10.1073/pnas.0704243104).
- Haberl 2007 does NOT publish a country-level HANPP table — only gridded data
  (year 2000) and regional aggregates. Country values here are COMPUTED by
  zonal aggregation of the official 5-arc-minute grids from the Global HANPP
  Data package (all_grids.zip):
    country HANPP% = 100 * Σ(HANPP_gCm2 · area) / Σ(NPP0_gCm2 · area)
  over the country's land cells (cos-latitude area weights), using grids
  `thanpppallgcm` (HANPP, gC/m²/yr) and `tn0_all_gcm` (NPP0, gC/m²/yr).
  Country boundaries: Natural Earth 1:110m admin-0 (ISO_A3).
- x = GDP per capita PPP (OWID / World Bank), year 2000, matched on ISO3.
- 156 countries. Replaces 25 hand-entered HANPP/GDP values. Negative HANPP for
  a few arid, heavily-irrigated countries (e.g. EGY, Gulf states) is a genuine
  result of the aggregation (NPP0 near zero), retained rather than dropped.

## #48 Putnam Social Capital — `putnam_real.csv` (European proxy)
- PROXY reconstruction (not a replication of Putnam's US-community measures),
  matched on ISO3:
  - x = daily time watching television and video (hours): Eurostat Harmonised
    European Time Use Surveys (HETUS), dataset `tus_00age`, activity code
    AC82 "Television and video", unit TIME_SP (mean time, total sex/age),
    most recent survey round per country (2000 or 2010).
  - y = generalized trust (% agreeing "most people can be trusted"): Our World
    in Data `self-reported-trust-attitudes` (World Values Survey / integrated
    surveys), value from the year nearest the TV survey (recorded per row).
- 22 European countries. Replaces 25 hand-entered TV-hours/trust values.
  Coverage is European only; labelled as a proxy, not a Putnam replication.

## #27 Replacement Migration Curve — `replacement_migration_real.csv` (UN model output, transcribed)
- Source (values are UN MODEL OUTPUTS, not empirical observations):
  United Nations, Population Division (2000/2001) "Replacement Migration: Is
  It a Solution to Declining and Ageing Populations?" (ST/ESA/SER.A/206).
  PDF: https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/files/documents/2020/Jan/un_2001_replacementmigration.pdf
- Transcribed exactly from two report tables:
  - x = TFR gap = 2.1 - TFR(1995-2000), TFR from Table IV.1 "Total fertility
    rates, 1950 to 2050" (p.23), column 1995-2000 (based on the UN 1998
    Revision medium variant).
  - y = Table IV.6 "Average annual net number of migrants between 2000 and
    2050, per million inhabitants in 2000" (p.25), Scenario IV = migration
    required to keep the working-age population (15-64) constant.
- 8 study countries (France, Germany, Italy, Japan, Republic of Korea, Russian
  Federation, United Kingdom, United States). The two regional aggregates
  (Europe, European Union) are stored in the CSV but excluded from the curve
  to avoid double-counting member countries. Replaces 25 hand-invented values
  (the UN report only studied 8 countries + 2 regions).
