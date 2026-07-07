# TRACE — Process Evidence & Disposition Framework

**Establish what a process actually is, what it actually costs, and what it actually deserves — before anyone builds automation. An agent-driven framework for intelligent automation product managers, with a zero-dependency process-mining toolkit.**

---

## The Problem

Every automation program starts the same way: stakeholders describe a process, someone drafts an ROI slide, and a bot gets built. Then the numbers don't materialize, because the process that got automated was the process as *remembered* — not the process as *run*. The documented path turns out to be a minority of cases; the real cost was in a rework loop nobody mentioned; the bottleneck was external all along; and six weeks after go-live, staff have quietly reverted to the workaround.

TRACE exists to make that sequence impossible. It sits **upstream of any build decision** — including whether to build at all.

## The Five Phases

| Phase | Agent | Command | Core question | Key output |
|:-----:|-------|---------|---------------|------------|
| **T** — Triangulate | Process Archaeologist | `/triangulate` | What are the three versions of this process — documented, perceived, performed — and where do they diverge? | Delta Map |
| **R** — Reconstruct | Process Miner | `/reconstruct` | What does the event log say actually happens? | Reality Report + Variant Atlas |
| **A** — Assess | Process Economist | `/assess` | What does each variant cost — and which friction is addressable vs. structural? | Value Concentration Table |
| **C** — Classify | Disposition Analyst | `/classify` | What does each friction point deserve: Eliminate → Simplify → Standardize → Automate → Augment → Delegate? | Disposition Register |
| **E** — Evidence | Conformance Auditor | `/evidence` | Did the change stick, and did the value arrive? | Conformance Report + Benefits Ledger |

*Trace* is deliberately the process-mining term for one case's path through an event log. The framework's claim: an automation program that cannot produce a trace should not be allowed to produce a bot.

## Two Ideas Doing Most of the Work

**1. The disposition ladder.** Automation is the *last* resort. Every friction point walks the rungs in order — **Eliminate, Simplify, Standardize, Automate, Augment, Delegate** — and stops at the highest rung that solves it. Automating a broken process just produces broken outcomes faster; the ladder forces the "should this step exist at all?" conversation before any build spend. Only rung 5–6 survivors proceed to an agent lifecycle — they map directly into the companion [agentic-ai-product-framework](https://github.com/jerimiahmertz/agentic-ai-product-framework)'s `/discover` → `/score` phases, arriving with evidence packs instead of recollections.

**2. Conformance as the definition of done.** Go-live is a claim. The event log at +30/+60/+90 days is the evidence. Phase E audits every shipped change for the four failure signatures — reversion, displacement, circumvention, erosion — and verifies claimed benefits against observed data only. A change is hardwired when the log says so.

## The Toolkit

`toolkit/` contains working process-mining code with **zero dependencies** — Python 3.6+ standard library only, because the machines this needs to run on (locked-down hospital laptops, client environments) rarely allow `pip install` anything.

```bash
# Reconstruct: variants, rework, bottlenecks, handoffs, cycle times
python3 toolkit/mine.py log.csv --resource resource --json report.json

# Evidence: conformance to the documented path
python3 toolkit/conformance.py log.csv --expected "Step A,Step B,Step C"

# Evidence: did the change stick? (baseline vs. post-change)
python3 toolkit/conformance.py baseline.csv --after after.csv
```

Input is the standard event-log shape: `case_id, activity, timestamp[, resource]` — one row per event. That's extractable from almost any system of record: EHR audit trails, ticketing systems, work queues, RPA logs.

**See it run:** [examples/synthetic-referral/](examples/synthetic-referral/) is a complete, reproducible worked example on a fictional specialty-referral process — including the mined output and how to read it like a TRACE analyst (the documented path turns out to be 34.8% of reality, and the undocumented urgent path is 5× faster).

## Healthcare Design Constraints (built in, not bolted on)

- **PHI-minimal mining.** Extracts are case-ID + activity + timestamp + role, nothing else. Case IDs pseudonymized at extraction; no names, no clinical content, no free text. The data-governance approval path is a Phase T deliverable, not an afterthought.
- **Safety tiering.** Every friction point is tiered before disposition: **Tier S** (errors can reach a patient — floor is *Augment*, and going lower requires clinical governance, not a PM scorecard), **Tier C** (compliance-touching — automation with audit trail and sampling QA), **Tier O** (operational — full ladder).
- **Clinician trust protocol.** Variant data is shown to the people in the flow before it is shown to their leadership, framed as "the process as designed doesn't survive contact with reality" — never "staff aren't following the process." Workarounds are treated as field intelligence, because they usually are.

The framework is healthcare-flavored because that's where it was forged, but nothing in T-R-A-C-E is healthcare-specific — the same five phases run on claims operations, underwriting, title production, or any workflow that leaves timestamps.

## Quick Start

```bash
git clone https://github.com/jerimiahmertz/trace-framework.git
cd trace-framework
claude
# Type: /triangulate  (or start with the worked example: examples/synthetic-referral/)
```

Each phase command loads its agent persona, runs the work conversationally, writes artifacts to `docs/`, and checks its quality gate before advancing. No phase consumes hearsay: `/reconstruct` demands `/triangulate`'s data plan, `/assess` demands mined evidence, `/classify` demands priced friction, `/evidence` demands a frozen baseline.

## Repo Structure

```
trace-framework/
├── .claude/commands/          # /triangulate /reconstruct /assess /classify /evidence
├── framework/
│   ├── agents/                # Five agent personas (one per phase)
│   └── checklists/            # Quality gates between phases
├── toolkit/
│   ├── mine.py                # Zero-dependency process mining
│   └── conformance.py         # Zero-dependency conformance checking
├── templates/                 # Process Evidence Pack, Disposition Scorecard, Conformance Report
├── examples/synthetic-referral/  # Reproducible worked example (synthetic data)
├── docs/                      # Generated artifacts land here (gitignored)
├── CHANGELOG.md
└── LICENSE
```

## Core Principles

1. **The event log is the only witness that doesn't rationalize.** Interviews and SOPs are hypotheses; timestamps are evidence.
2. **The variant, not the process, is the unit of value.** Averages smear the signal; concentration tables find it.
3. **Automation is the last rung, not the first instinct.** Eliminate beats automate every time it's available.
4. **Structural cost is not automatable savings.** An internal bot cannot compress an external party's queue.
5. **Announced ≠ hardwired.** A change exists when the +90-day log says it does.
6. **Credibility compounds.** Conservative estimates, verified benefits, and a never-retroactively-edited ledger are what fund the next bet.

## License

[MIT](LICENSE)

---

*Built by [Jerimiah Mertz](https://github.com/jerimiahmertz) — product leader working at the intersection of AI systems and business strategy. Companion frameworks: [agentic-ai-product-framework](https://github.com/jerimiahmertz/agentic-ai-product-framework) (downstream: build the agents TRACE says deserve to exist) and [the-crucible-method](https://github.com/jerimiahmertz/the-crucible-method).*
