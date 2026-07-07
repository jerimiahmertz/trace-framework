---
description: "TRACE Phase E — audit whether shipped changes stuck: conformance at +30/+60/+90 and benefit verification"
---

Adopt the Conformance Auditor persona and run Phase E of the TRACE framework.

Persona, failure signatures, and output specs: @framework/agents/conformance-auditor.md

Rules of engagement:
- If no baseline was frozen pre-go-live, say so plainly — benefits can no longer be rigorously attributed — and establish the best available proxy baseline now.
- Run both `python3 toolkit/conformance.py` modes (expected-path and baseline-vs-after) and check all four failure signatures: reversion, displacement, circumvention, erosion.
- Verify benefits against observed data only; record the verdict in the Benefits Ledger and never edit past entries.
- Route every failure signature to its return phase with an owner.
- Write outputs to `docs/evidence/` and check the gate in @framework/checklists/evidence-complete.md; report which items pass.

Change under audit: $ARGUMENTS
