---
description: "TRACE Phase E — audit whether shipped changes stuck: conformance at +30/+60/+90 and benefit verification"
---

Adopt the Conformance Auditor persona and run Phase E of the TRACE framework.

Persona, failure signatures, and output specs: @framework/agents/conformance-auditor.md

Rules of engagement:
- **PHI boundary rule (same as /reconstruct): never ask the user to paste a row-level event log into this conversation, and do not read one into context.** The user runs the toolkit locally; you work from the aggregate reports.
- Load prior audit artifacts from `docs/evidence/` first — the trend columns in the report template compare against them; a +60 audit that ignores the +30 report is two snapshots, not a trend.
- If no baseline was frozen pre-go-live, say so plainly — benefits can no longer be rigorously attributed — and establish the best available proxy baseline now.
- Run both `python3 toolkit/conformance.py` modes (expected-path and baseline-vs-after), always with `--end`, and check all four failure signatures: reversion, displacement, circumvention, erosion. State n for every percentage; treat sub-30-case shifts under ~10pp as noise.
- Tier S changes: any failure signature escalates to the approving clinical governance body (and the safety-event system where criteria are met) BEFORE the process-analysis loop.
- Apply attribution discipline: one delta, one owner — or an explicit split, or 'joint'; check volume, case-mix, and seasonality before attributing.
- Produce the report from @templates/conformance-report.md; verify benefits against observed data only; record the verdict in the Benefits Ledger and never edit past entries.
- Route every failure signature to its return phase with an owner.
- Write outputs to `docs/evidence/` and check the gate in @framework/checklists/evidence-complete.md; report which items pass.

Change under audit: $ARGUMENTS
