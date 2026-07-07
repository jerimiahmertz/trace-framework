# Changelog

## v1.0 — 2026-07-06

Initial public release.

- Five-phase framework: Triangulate → Reconstruct → Assess → Classify → Evidence, each owned by an agent persona with a quality gate and a Claude Code slash command
- The disposition ladder (Eliminate → Simplify → Standardize → Automate → Augment → Delegate) with healthcare safety tiering (S/C/O)
- Zero-dependency process-mining toolkit (Python 3.6+ stdlib only): `mine.py` (variants, DFG, rework, handoffs, cycle times) and `conformance.py` (expected-path and baseline-vs-after modes)
- Conformance-as-definition-of-done: +30/+60/+90-day audits, four failure signatures (reversion, displacement, circumvention, erosion), benefits verified against observed data only
- Templates: Process Evidence Pack, Disposition Scorecard, Conformance Report
- Reproducible worked example on synthetic specialty-referral data (seeded generator, zero PHI)
- Designed as the upstream companion to [agentic-ai-product-framework](https://github.com/jerimiahmertz/agentic-ai-product-framework): rung 5–6 disposition survivors feed its `/discover` → `/score` phases
