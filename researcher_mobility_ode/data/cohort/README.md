# Cohort data provenance

The files in this directory are derived from the OpenAlex API (`subfields/1702`, Artificial Intelligence, career-start years 2000–2023) using `src/cohort_extraction.py`.

- `raw_sampled_works.json` – a stratified random sample of works used to seed the author cohort.
- `cohort.csv` – author-level cohort (career dates, civilisation grouping, `origin_group`, and state flags used for rate estimation).
- `transition_rates.csv` – transition-rate point estimates computed from `cohort.csv`.

## Manual correction in `cohort.csv`

One author (row 239, `Ignazio Stanganelli`, OpenAlex `A5061353810`) was assigned to `United States` by the automatic `classify_author` majority-vote rule. Inspection of the sampled works and the country-to-civilisation mapping showed that the author's earliest affiliation was in Italy (`IT`), which maps to `Continental Europe`. The `origin_group` cell was therefore corrected to `Continental Europe` and `origin_year` was set to the earliest observed Italian affiliation year. This is the only hand-edited value in the committed cohort file; it is documented here so that future re-extractions can audit the decision.
