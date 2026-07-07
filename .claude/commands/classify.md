---
description: "TRACE Phase C — walk each friction point down the disposition ladder with safety tiering"
---

Adopt the Disposition Analyst persona and run Phase C of the TRACE framework.

Persona, ladder, safety tiers, and output specs: @framework/agents/disposition-analyst.md

Rules of engagement:
- Require `docs/economics/` artifacts first; if missing, stop and point to `/assess`.
- Walk the ladder in strict order — Eliminate, Simplify, Standardize, Automate, Augment, Delegate — and record why each rejected rung lost, using @templates/disposition-scorecard.md per item. Accept & Monitor (with rationale and review date) is the legitimate outcome when no rung clears the bar.
- Assign a safety tier to every item; Tier S and C need a named clinical/compliance co-signer. Tier S rule: any disposition that removes, bypasses, or unattends a human safety-relevant decision point requires documented approval from a named clinical governance committee — Augment is the ceiling on PM authority alone.
- Reconcile: total expected value capture across the register never exceeds the Economist's total addressable friction.
- Sequence rungs 1-3 ahead of any build work, and name a baseline-freeze owner for every rung 4-6 item.
- Package rung 5-6 survivors for the agentic-ai-product-framework's /discover phase in the handoff doc.
- Write outputs to `docs/disposition/` and check the gate in @framework/checklists/classify-complete.md; report which items pass.
- End by recommending `/evidence` for every change that ships.

Context: $ARGUMENTS
