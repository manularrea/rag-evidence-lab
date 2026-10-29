# Changelog

## 0.2.0 — 2026-10-28

Community release. Thanks to @HarshRajSinghania (#9) and @soyeladice-svg (#10).

### Added

- LangChain RetrievalQA exporter recipe, synthetic fixture, and CLI walkthrough
  (`examples/recipes`). Source IDs are sanitized to the cases schema; citations
  are never invented. Compatibility is tested against a synthetic
  LangChain-shaped export, not an installed LangChain version. (#9)

### Changed

- Numeric comparison normalizes unambiguous grouping (spaces, NBSP, narrow
  NBSP, repeated groups, mixed English/Spanish decimal-plus-group layouts).
  Ambiguous single-separator forms such as `1.234` or `1,000` are compared as
  literals instead of being guessed; leading-zero decimals such as `0.125`
  stay fractional. (#10)

### Upgrade notes

- Flag counts can change for the same input: some formatting-only numeric
  flags disappear, and `1,000` / `1.000` versus `1000` is now flagged for
  review. Regenerate baseline reports with 0.2.0 before comparing candidates;
  baseline and candidate must come from the same inspector version.
- Report `schema_version` is unchanged (`1`).

## 0.1.0 — 2026-09-30

- Offline citation and numeric-literal checks for exported RAG answers.
- Explainable lexical-overlap signals with documented semantic limitations.
- Portable, escaped HTML and machine-readable JSON reports.
- Absolute flagged-claim budgets and per-case baseline regression checks.
- Synthetic English/Spanish examples, unit tests, and GitHub Actions CI.

Initial prototype. Not a production factuality benchmark or certification tool.
