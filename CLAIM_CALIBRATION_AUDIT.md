# Claim calibration audit — Public Health manuscript

Method: the generated `ph_manuscript_en.docx` text was extracted and scanned
line-by-line for causal, over-strong, or design-inconsistent language. Numbers
below refer to the shipped wording; all hits were inspected, not just counted.

## Banned/over-strong patterns — scan results

| Pattern searched | Hits | Verdict |
|---|---|---|
| `causes` / `caused` / `drives` / `leads to` / `prevents` | 0 in claims | pass |
| `confirms` / `proves` / `proves` / `demonstrates` / `definitively` | 0 | pass |
| `supports policy` (unqualified) | 0 | pass |
| `flight` / `flee` / `specialty flight` | 0 (only benign "several-fold") | pass |
| `no effect` as substantive claim | 0 (appears only in "no evidence of an effect" framings) | pass |
| `structural policy effect` (old HPT JOCS-CP wording) | 0 | removed |
| `pre-specified` / `a priori` margin claims | 0 | now "specified for the present analysis" |
| `null` | 8 — all methodological ("null hypothesis", "one-sided nulls") | pass |
| `should` | 4 — all conditional/hedged ("planning should not assume...", "future research should link...") | acceptable |

## Design-claim consistency

- All association claims use "associated/not associated" or "exposure–change
  association" vocabulary; "effect" is used only when naming the estimand or
  referencing the literature.
- JOCS-CP everywhere described as "exploratory", "cannot isolate the
  compensation scheme from contemporaneous obstetric policies or secular
  change", "contextual association rather than a causal estimate".
- Ecological limitation explicit: "cannot infer individual career decisions";
  abstract Conclusions repeat this.
- Equivalence framed as bounding within specified margins; the ±1% hospital
  non-equivalence result is retained and discussed.
- Policy implications are conditional and restrained: "should not assume that
  reducing routine civil-litigation exposure alone will materially increase
  specialty supply"; no-fault named only as "may be worth evaluating", with the
  design's inability to demonstrate superiority stated.
- No individual-level causal claims; no fabricated statistics; every number in
  the text is generated from `results/reanalysis_results.json` at build time
  (assertions in `build_ph_submission.py` would raise otherwise).

## Data/claims consistency spot check (against results/reanalysis_results.json)

- Physician growth: coef −0.0009, 95% CI −0.0043 to +0.0025, p=0.56 — matches.
- Hospital growth: p=0.90 — matches.
- ±1% physician equivalence: TOST p=0.023, point −0.21%, 90% CI −0.84% to
  +0.42% — matches.
- ±2% hospital equivalence: p=0.002; ±1% hospital not equivalent (p=0.059) —
  matches.
- JOCS-CP: hospitals coef +0.0242, p=0.013 — matches; described as exploratory.
- 12 specialties, 2008–2024, 9 biennial waves, n=96 — matches.

## Conclusion

No sentence in the current manuscript overstates what an ecological,
specialty-level panel with researcher-specified margins can support. No
wording changes required beyond those already implemented in the Public Health
repositioning.

## Finishing-pass update (v2)

Title-only wording change (service-capacity terminology); no claim sentence altered. Re-scan after rebuild: no banned patterns introduced.
