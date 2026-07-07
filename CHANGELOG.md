# Changelog

## v1.1 — 2026-07-06

Hardening release: a 49-agent adversarial review (five lenses: toolkit correctness, methodology, consistency, healthcare/privacy, first-run UX) produced 44 verified findings; this release addresses all of them.

### Toolkit
- **Fixed** `percentile()` off-by-one: banker's rounding of `round(m+0.5)` picked one rank too high whenever the rank landed on an odd integer (median of 2 items returned the max). Now true nearest-rank via `ceil`; example outputs regenerated
- **Added** censoring control: `--end` (closing activities) excludes and counts in-flight cases in both tools — previously, cutting a log mid-window fabricated a 45% cycle-time "improvement" and phantom variants on identical behavior
- **Added** data-quality assessment to `mine.py`: timestamp granularity (date-only warning — within-day order is file order), tied-timestamp rate, exact-duplicate detection (dropped and counted), blank-case-id handling
- **Added** robust timestamp parsing: ISO 8601 `T`, fractional seconds, `Z`/±offset (normalized to UTC); ragged CSV rows now fail with row-numbered errors
- **Added** conformance classification for "in-order but incomplete" cases (exits/abandonment vs. true deviance), expected-path vocabulary check (typos no longer read as 100% deviant), truncated-prefix detection for "new" variants, empty-log guards, small-sample warnings
- **Changed** `conformance.py` to be fully self-contained (single-file portable, like `mine.py`), with loading semantics matched to `mine.py` (duplicates dropped and noted, blank activities rejected) and an `--end` vocabulary guard so a typo in the closing-activity list fails loudly instead of silently excluding real cases
- **Added** `test_toolkit.py`: 32 stdlib unit tests, including drift guards on the deliberately duplicated helpers

### Methodology
- **Added** Accept & Monitor as a terminal disposition (structural friction and below-threshold items now have a recordable outcome)
- **Tightened** the Tier S rule to name what it blocks: removing, bypassing, or unattending a human safety-relevant decision point requires documented approval from a named clinical governance committee; defined what "clinical governance" operationally means
- **Added** attribution discipline to Phase E (one delta one owner, case-mix/seasonality checks) and Tier S safety escalation ahead of process analysis
- **Added** economics reconciliation rules (friction ledger as atomic record; register capture ≤ total addressable) and sample-size honesty rules across phases
- **Wired** the three templates into the phases that produce them (they were orphaned); the Process Evidence Pack is now Phase A's closing deliverable with the Economist as owner; baseline-freeze ownership is assigned at `/classify`

### Healthcare & privacy
- **Stated plainly** that a pseudonymized event log with timestamps is still PHI; governance approval must be *obtained* (not just identified) before extracts are pulled; sensitive service lines flagged for separate review
- **Added** the raw-log boundary rule: row-level extracts never enter the AI conversation — agents work from the toolkit's aggregate reports
- **Added** the no-individual-performance-management commitment and small-cell attribution rule to the clinician-trust protocol

### Example & docs
- Example outputs regenerated with the fixed toolkit and quoted verbatim (previous version silently pruned rows); bottleneck narrative corrected to distinguish outcome lags from queues; abandonment rate corrected to 7.2% total; `/triangulate` gained an explicit cold-start mode; Windows `py` launcher note

## v1.0 — 2026-07-06

Initial public release.

- Five-phase framework: Triangulate → Reconstruct → Assess → Classify → Evidence, each owned by an agent persona with a quality gate and a Claude Code slash command
- The disposition ladder (Eliminate → Simplify → Standardize → Automate → Augment → Delegate) with healthcare safety tiering (S/C/O)
- Zero-dependency process-mining toolkit (Python 3.6+ stdlib only): `mine.py` (variants, DFG, rework, handoffs, cycle times) and `conformance.py` (expected-path and baseline-vs-after modes)
- Conformance-as-definition-of-done: +30/+60/+90-day audits, four failure signatures (reversion, displacement, circumvention, erosion), benefits verified against observed data only
- Templates: Process Evidence Pack, Disposition Scorecard, Conformance Report
- Reproducible worked example on synthetic specialty-referral data (seeded generator, zero PHI)
- Designed as the upstream companion to [agentic-ai-product-framework](https://github.com/jerimiahmertz/agentic-ai-product-framework): rung 5–6 disposition survivors feed its `/discover` → `/score` phases
