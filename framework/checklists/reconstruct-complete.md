# Reconstruction Complete Checklist

> Quality gate: must pass before advancing to `/assess`

- [ ] Governance approval for the extract OBTAINED (not merely identified) before production data was pulled
- [ ] Case boundary and activity vocabulary defined and documented
- [ ] Event log assembled in standard format; PHI-minimal verified
- [ ] Data-quality block reviewed: timestamp granularity, tied timestamps, duplicates — caveats carried into the Reality Report
- [ ] Open/censored cases excluded via --end and their count reported
- [ ] toolkit/mine.py run; report and JSON committed to the record
- [ ] Variant concentration headline stated (documented path's actual share)
- [ ] Every >2% variant has a field explanation (legitimate vs. accidental)
- [ ] Rework loops and bottlenecks identified with median/p90 waits
- [ ] Bottlenecks classified internal vs. external
- [ ] Delta map updated with quantified evidence
- [ ] `docs/reconstruction/` artifacts exist and are complete
