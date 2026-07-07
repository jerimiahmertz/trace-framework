# Conformance Report

> Produced by `/evidence` at each audit date (+30/+60/+90 days, then quarterly).

## Change under audit: [Name]

**Went live:** [date] | **Audit date:** [+30 / +60 / +90 / quarterly]
**Baseline frozen:** [date, artifact refs] | **Expected path:** [ordered activity list]
**Closing activities (`--end`):** [list] | **Open cases excluded this window:** [n]
**Cases scored (n):** [n — if < 30, mark percentage shifts under ~10pp as noise]

---

### Conformance
Sources: expected-path mode per window; median cycle and variant shift from baseline-vs-after mode. Baseline and prior-audit columns come from the frozen baseline and earlier reports in `docs/evidence/`.

| Measure | Baseline | Prior audit | This audit | Trend |
|---------|---------:|------------:|-----------:|-------|
| Exact conformance | | | | |
| In-order with extra steps | | | | |
| In-order but incomplete (exits) | | | | |
| Deviant | | | | |
| Median cycle time (complete cases) | | | | |

### Failure signature check

| Signature | Detected? | Evidence | Response |
|-----------|-----------|----------|----------|
| Reversion (old variants regaining share) | | | |
| Displacement (new queue downstream — from post-change mine.py transition table vs. baseline) | | | |
| Circumvention (new shadow variant around the change) | | | |
| Erosion (gains decaying month over month) | | | |

### Benefit verification

| Claimed (Disposition Register) | Observed (log + rates) | Variance | Verdict |
|--------------------------------|------------------------|----------|---------|
| | | | realized / partial / not realized / too early |

**Basis for observed figure:** [observed volume × observed cycle delta × sourced rate — never projections]

### Routing

| Finding | Return phase | Owner | Due |
|---------|-------------|-------|-----|

**Benefits Ledger updated:** [ ] yes — entry [ref]. Past entries never edited.
