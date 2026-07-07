# Evidence Complete Checklist

> Quality gate: applies to every shipped change, at every audit date

- [ ] Baseline frozen before go-live (log + mined report + value claim)
- [ ] Audit calendar set: +30/+60/+90 days, then quarterly
- [ ] Both conformance modes run (expected-path and baseline-vs-after), each with --end; open-case exclusions reported
- [ ] Sample size stated for every percentage; sub-30-case shifts under ~10pp treated as noise, not signal
- [ ] Four failure signatures checked: reversion, displacement, circumvention, erosion
- [ ] Tier S failure signatures escalated to the approving clinical governance body (and safety-event system where criteria met) before process analysis
- [ ] Attribution discipline applied: each observed delta attributed to one change, split explicitly, or reported as joint; volume/case-mix/seasonality checked
- [ ] Report produced from the Conformance Report template, with prior audits loaded for the trend columns
- [ ] Benefits verified against observed volumes and cycle deltas only
- [ ] Verdict recorded: realized / partial / not realized / too early
- [ ] Failure signatures routed to their return phase with an owner
- [ ] Benefits Ledger updated; never edited retroactively
