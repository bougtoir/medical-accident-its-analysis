# Reference Verification Audit Report

**Generated:** 2026-06-11T01:42:10Z
**Method:** Articles → Crossref API | Books → Open Library API | URLs → HTTP reachability
**Source:** `scripts/create_perspective_docx.py` REFERENCES list
**Total references:** 26

## Summary

| Status | Count | Meaning |
|--------|-------|---------|
| MATCH | 25 | Verified correct (INFO-level notes only) |
| WARNING | 0 | Possible metadata error (year/vol/pages) |
| CRITICAL_MISMATCH | 1 | Crossref found different paper — likely wrong ref |
| UNVERIFIED | 0 | Could not verify (book, API miss) |

### Severity Legend

- **CRITICAL**: Title or first-author mismatch → Crossref matched a different paper
- **WARNING**: Volume, pages, or year (>1yr diff) discrepancy → needs manual check
- **INFO**: Journal abbreviation vs full name, year +/-1 → acceptable/expected

## Issues Requiring Attention

### 🚨 Ref 26: CRITICAL_MISMATCH

**Manuscript:** Karagiannis P, Takahashi K, Saito M, et al. Induced pluripotent stem cells and their use in human models of disease and development. Physiol Rev. 2019;99(1):79–114.

**Crossref DOI:** https://doi.org/10.1007/978-981-13-3672-0_1
**Crossref title:** Clinical Potential of Induced Pluripotent Stem Cells
**Crossref authors:** Karagiannis P
**Crossref journal:** Current Human Cell Research and Applications
**Crossref year;vol(issue):pages:** 2019;():3-12

**Issues:**
- [CRITICAL] Title mismatch (overlap=38%): MS='Induced pluripotent stem cells and their use in human models of disease and deve' vs CR='Clinical Potential of Induced Pluripotent Stem Cells'
- [WARNING] Pages: MS=79–114 vs Crossref=3-12
- [INFO] Journal name difference: MS='Physiol Rev' vs Crossref='Current Human Cell Research and Applications'

---

## All Results (Quick View)

| # | Status | First Author | Year | Notes |
|---|--------|--------------|------|-------|
| 1 | MATCH | Kirkeby A | 2025 |  |
| 2 | MATCH | Yamanaka S | 2020 |  |
| 3 | MATCH | Volpato V | 2018 |  |
| 4 | MATCH | Volpato V | 2020 |  |
| 5 | MATCH | Ortmann D | 2017 |  |
| 6 | MATCH | Cai J | 2025 |  |
| 7 | MATCH | Agarwal N | 2017 |  |
| 8 | MATCH | Panina Y | 2020 |  |
| 9 | MATCH | McCreery KP | 2024 |  |
| 10 | MATCH | Sato S | 2023 |  |
| 11 | MATCH | Ameneiro C | 2020 |  |
| 12 | MATCH | Golan K | 2019 |  |
| 13 | MATCH | Bi S | 2020 |  |
| 14 | MATCH | Chui JS | 2024 |  |
| 15 | MATCH | Mizuno M | 2020 |  |
| 16 | MATCH | Klein SG | 2022 |  |
| 17 | MATCH | Czyz J | 2004 |  |
| 18 | MATCH | Diatroptova MA | 2022 |  |
| 19 | MATCH | Leathersich SJ | 2023 |  |
| 20 | MATCH | Wang C | 2025 |  |
| 21 | MATCH | Braga DPdA | 2025 |  |
| 22 | MATCH | Deng Q | 2025 |  |
| 23 | MATCH | Wang J | 1992 |  |
| 24 | MATCH | Barrett T | 2012 |  |
| 25 | MATCH | ? | ? |  |
| 26 | CRITICAL_MISMATCH | Karagiannis P | 2019 | Title mismatch (overlap=38%): MS='Induced pluripot; Pages: M |

## Methodology

1. Each reference is parsed to extract: first author surname, title, year, volume, pages
2. Reference type detected: article → Crossref API, book → Open Library API, URL → HTTP check
3. **Articles**: Crossref queried with `query.bibliographic` + `query.author`; metadata compared
4. **Books**: Open Library queried with title + author; title/author/year compared
5. **URLs**: HTTP HEAD request to verify reachability (status code < 400)
6. Issues classified by severity: CRITICAL > WARNING > INFO
7. Journal abbreviation differences (NLM vs full name) classified as INFO (acceptable)
8. Article IDs (e.g., 'deaf008', 'e201900534') recognized as valid page identifiers
9. Year differences of exactly +/-1 classified as INFO (online-first vs print)

### Limitations

- Crossref coverage is not 100% (some older/non-English journals may be missing)
- Open Library coverage varies; some books may not have entries
- URL reachability may be affected by geoblocking, authentication, or temporary outages
- Author name transliterations may differ between databases
- This script verifies metadata accuracy, NOT whether the citation supports the claim in text
- A MATCH status means the API confirmed the work exists with matching metadata —
  it does NOT verify the full author list beyond the first author

### Reproducibility

Re-run: `python scripts/verify_references.py`

Results are deterministic for a given REFERENCES list and Crossref database state.
Crossref metadata may be updated over time (corrections, retractions).
Commit the JSON/MD reports as audit artifacts alongside the manuscript.