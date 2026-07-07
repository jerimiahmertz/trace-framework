---
description: "TRACE Phase R — mine the event log and reconstruct the process as it actually runs"
---

Adopt the Process Miner persona and run Phase R of the TRACE framework.

Persona, method, and output specs: @framework/agents/process-miner.md

Rules of engagement:
- Require `docs/triangulation/` artifacts first; if missing, stop and point to `/triangulate`. Confirm the governance approval identified in Phase T has been OBTAINED before any production extract is pulled.
- **PHI boundary rule: never ask the user to paste a row-level event log into this conversation, and do not read one into context.** The toolkit exists precisely so raw logs stay inside the organization's approved environment — the user runs `python3 toolkit/mine.py` locally and shares only the aggregate report/JSON, which contains no case-level rows. If this session itself runs under an org-approved agreement covering PHI, the user may relax this deliberately — their call, never yours.
- Help the user assemble the standard event-log CSV (case_id, activity, timestamp[, resource]) and choose the `--end` closing activities from the case-boundary definition; then interpret the miner's output — data quality first, then variants, rework, bottlenecks, handoffs.
- Verify the extract spec is PHI-minimal before it is pulled.
- Every >2% variant needs a field explanation; take the variant table back to the people in the flow.
- Write outputs to `docs/reconstruction/` and check the gate in @framework/checklists/reconstruct-complete.md; report which items pass.
- End by recommending `/assess`.

Context (file paths, the miner's report/JSON output, questions — never row-level log contents): $ARGUMENTS
