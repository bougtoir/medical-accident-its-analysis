# Frozen public source data

These files are the exact public-data vintage used to produce the archived manuscript results. They are committed so a third party can reproduce the paper without relying on mutable provider APIs.

- `pwt1001_selected.csv`: Penn World Table 10.01 extract (DOI `10.34894/QT5BCC`).
- `world_bank_indicators.csv`: WDI R&D expenditure and World Bank Changing Wealth of Nations indicators.
- `oecd/gfcf_by_asset_full.csv`: OECD GFCF-by-asset observations used to construct the observable tempo measure.
- `manifest.json`: source URLs, transformations, licenses, row counts, and SHA-256 checksums.

The files contain public macroeconomic aggregates only. No observations are simulated or manually created. `scripts/verify_source_data.py` validates every committed byte against the manifest. `scripts/fetch_source_data.py` independently downloads the current PWT and World Bank releases and compares them with the frozen vintage. Live APIs can be revised, so reproduction always uses the committed inputs; refreshing data creates a new research vintage and requires re-validating every result.

The OECD file intentionally preserves the source order and duplicate asset-country-year rows used in the published computation. The analysis converts each country-year group to a dictionary, so the final row for an asset is selected. Changing the OECD vintage or deduplication rule can change `M_obs` and is therefore not done silently.
