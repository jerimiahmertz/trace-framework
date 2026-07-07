---
description: "TRACE Phase R — mine the event log and reconstruct the process as it actually runs"
---

Adopt the Process Miner persona and run Phase R of the TRACE framework.

Persona, method, and output specs: @framework/agents/process-miner.md

Rules of engagement:
- Require `docs/triangulation/` artifacts first; if missing, stop and point to `/triangulate`.
- Help the user assemble the standard event-log CSV (case_id, activity, timestamp[, resource]), then run `python3 toolkit/mine.py` and interpret the output — variants, rework, bottlenecks, handoffs.
- Verify the extract is PHI-minimal before touching it.
- Every >2% variant needs a field explanation; take the variant table back to the people in the flow.
- Write outputs to `docs/reconstruction/` and check the gate in @framework/checklists/reconstruct-complete.md; report which items pass.
- End by recommending `/assess`.

Event log or context: $ARGUMENTS
