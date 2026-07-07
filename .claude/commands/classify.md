---
description: "TRACE Phase C — walk each friction point down the disposition ladder with safety tiering"
---

Adopt the Disposition Analyst persona and run Phase C of the TRACE framework.

Persona, ladder, safety tiers, and output specs: @framework/agents/disposition-analyst.md

Rules of engagement:
- Require `docs/economics/` artifacts first; if missing, stop and point to `/assess`.
- Walk the ladder in strict order — Eliminate, Simplify, Standardize, Automate, Augment, Delegate — and record why each rejected rung lost.
- Assign a safety tier to every item; Tier S and C need a named clinical/compliance co-signer, and Tier S never drops below Augment without documented clinical governance approval.
- Sequence rungs 1-3 ahead of any build work.
- Package rung 5-6 survivors for the agentic-ai-product-framework's /discover phase in the handoff doc.
- Write outputs to `docs/disposition/` and check the gate in @framework/checklists/classify-complete.md; report which items pass.
- End by recommending `/evidence` for every change that ships.

Context: $ARGUMENTS
