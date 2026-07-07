# Worked Example: Specialty Referral Process (Synthetic)

A complete, reproducible demonstration of TRACE phases R and E on a fictional
outpatient specialty-referral process — the kind of workflow every health system's
intelligent automation program eventually meets: referral intake, insurance
verification, prior authorization, scheduling.

**All data here is synthetic** (`generate_log.py`, seeded, zero PHI). The process
pathologies are deliberately planted so you can watch the toolkit find them.

## Reproduce it

```bash
python3 generate_log.py 400 > referral_log.csv

python3 ../../toolkit/mine.py referral_log.csv --resource resource --top 8 \
  --end "Visit Completed,Case Closed - No Show,Case Closed - Abandoned" \
  --json mined_report.json

python3 ../../toolkit/conformance.py referral_log.csv \
  --expected "Referral Received,Insurance Verification,Prior Auth Submitted,Prior Auth Approved,Scheduling Call,Appointment Scheduled,Visit Completed" \
  --end "Visit Completed,Case Closed - No Show,Case Closed - Abandoned"
```

The `--end` list is this process's case-boundary definition (its closing
activities). The synthetic log contains only complete cases, so nothing is
excluded here — but on a real extraction it is what keeps in-flight cases from
masquerading as short cycle times and phantom variants. Try it: cut the log at
any date and re-run; the report will tell you what it excluded.

## The miner's output (complete and verbatim)

```
========================================================================
TRACE RECONSTRUCTION REPORT
========================================================================
Cases: 400   Events: 3096   Distinct activities: 14   Distinct variants: 21

DATA QUALITY
  rows read: 3096   blank-case-id rows skipped: 0   exact-duplicate rows dropped: 0
  timestamp granularity: 3096 second
  tied consecutive timestamps: 0 of 2696 (0.0%)
  open (censored) cases excluded from statistics: 0

CYCLE TIME (case start -> case end)
  min 1d 6h   median 17d 3h   p90 24d 0h   max 38d 16h

TOP VARIANTS (the process as it actually runs)
  cases   share   med cycle  path
    139   34.8%    16d 13h   Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     53   13.2%     20d 1h   Referral Received > Insurance Verification > Info Request to Referrer > Info Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     51   12.8%     2d 23h   Referral Received > Insurance Verification > Urgent Override > Scheduling Call > Appointment Scheduled > Visit Completed
     44   11.0%    21d 10h   Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Denied > Prior Auth Resubmitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     25    6.2%     6d 16h   Referral Received > Insurance Verification > Case Closed - Abandoned
     24    6.0%     17d 1h   Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Case Closed - No Show
     11    2.8%    21d 16h   Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Scheduling Call > Appointment Scheduled > Visit Completed
     10    2.5%    16d 23h   Referral Received > Insurance Verification > Info Request to Referrer > Info Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Case Closed - No Show
  (8 variants shown cover 89.2% of cases; 21 variants total)

REWORK (cases where an activity occurs more than once)
     86   21.5%  Insurance Verification
     27    6.8%  Scheduling Call
     11    2.8%  Prior Auth Denied
     11    2.8%  Prior Auth Resubmitted

SLOWEST TRANSITIONS (directly-follows, by median wait)
  NOTE: waits are wall-clock elapsed time (nights/weekends included) and
  include outcome lags (e.g. scheduled -> visit) — read as queues only
  where a queue actually exists.
  count    med wait    p90 wait  transition
     43      9d 19h     14d 21h  Appointment Scheduled -> Case Closed - No Show
    328      8d 19h      15d 1h  Appointment Scheduled -> Visit Completed
     29       7d 8h      9d 16h  Insurance Verification -> Case Closed - Abandoned
    242      4d 16h      6d 11h  Prior Auth Submitted -> Prior Auth Approved
     78      4d 10h      6d 14h  Prior Auth Submitted -> Prior Auth Denied
     78      4d 10h       6d 7h  Prior Auth Resubmitted -> Prior Auth Approved
     11      3d 21h       5d 9h  Prior Auth Resubmitted -> Prior Auth Denied
     86      2d 17h      4d 14h  Info Request to Referrer -> Info Received

HANDOFFS (resource changes per case)
  min 0   median 3   p90 3   max 3
========================================================================
JSON written to mined_report.json
```

## The conformance check (complete and verbatim)

```
========================================================================
TRACE CONFORMANCE REPORT — expected-path mode
========================================================================
Expected path: Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
Cases scored: 400   Open cases excluded: 0
  exact conformance:              139  (34.8%)
  in-order with extra steps:      138  (34.5%)
  in-order but incomplete:         72  (18.0%)  <- exits/abandonment, or censoring if --end unset
  deviant:                         51  (12.8%)

TOP DEVIANT VARIANTS
     51  Referral Received > Insurance Verification > Urgent Override > Scheduling Call > Appointment Scheduled > Visit Completed
========================================================================
```

## How to read it like a TRACE analyst

1. **The documented path is a minority position.** The SOP describes 34.8% of
   reality. That single number reframes the automation conversation from "speed
   up the process" to "which process?"

2. **The only true deviant is the shadow path — and it wins.** The conformance
   breakdown separates exits (18.0% "incomplete" — abandonments and drop-offs)
   from genuine deviation, and what's left is one variant: `Urgent Override`
   (12.8% of cases), which appears in no SOP and completes in a median of
   **3 days versus 16.5 for the happy path**. Before anyone automates prior
   auth, the honest question is what urgent cases prove about whether prior
   auth is needed at all for some referral classes — an *Eliminate/Simplify*
   play that would beat any bot (`/classify`, rungs 1–2).

3. **The rework loop is an upstream data-quality problem.** 21.5% of cases
   repeat Insurance Verification because referrals arrive incomplete.
   Automating verification wouldn't fix that — rung 2 (*Simplify*: fix the
   referral intake form) or rung 4 (*Automate*: validate at submission) attack
   the cause, not the symptom.

4. **Read the transition table critically — the top rows aren't queues.** The
   three slowest "waits" are appointment lead time (scheduled → visit/no-show)
   and time-to-abandonment — outcome lags, not anyone's work queue. The longest
   *actionable* wait inside the workflow is the payer's prior-auth decision
   (median 4d 16h, 242 cases) — and it is **structural**: an internal bot cannot
   compress an external payer's queue. The Economist books that as structural
   cost, not automatable savings. The addressable friction is the loops and
   the abandonment around it.

5. **Exit-state variants are the quiet cost.** 7.2% of referrals are abandoned
   (25 cases straight from verification friction, 4 more after the
   missing-info loop), and another 10.8% end in no-shows (43 cases — the
   transition table's `Appointment Scheduled -> Case Closed - No Show` row —
   spread across seven variants, most below the top-8 cutoff). In a real system that
   is leakage with a revenue number attached. Note what the log can and cannot
   say: the *sequence* (friction, then abandonment) is evidence for a
   hypothesis, not proof of cause — TRACE flags it for the Economist to size
   and the team to test.

6. **The data-quality block is not decoration.** On this synthetic log it's
   clean by construction (second-level timestamps, no ties, no duplicates, no
   open cases). On a real extract, that block is where you learn your
   timestamps are date-only (variant counts become file-order artifacts) or
   that 38% of cases are still in flight — *before* those problems become
   confident wrong conclusions.

Phases T (interviews) and A/C (rates, dispositions) need humans and real
context — this example shows the two phases that run on data alone, which are
also the two you can rehearse before ever touching a production extract.
