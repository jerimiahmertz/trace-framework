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
python3 ../../toolkit/mine.py referral_log.csv --resource resource --top 8
python3 ../../toolkit/conformance.py referral_log.csv \
  --expected "Referral Received,Insurance Verification,Prior Auth Submitted,Prior Auth Approved,Scheduling Call,Appointment Scheduled,Visit Completed"
```

## What the miner finds (actual output)

```
Cases: 400   Events: 3096   Distinct activities: 14   Distinct variants: 21

CYCLE TIME (case start -> case end)
  min 1d 6h   median 17d 3h   p90 24d 0h   max 38d 16h

TOP VARIANTS (the process as it actually runs)
  cases   share   med cycle  path
    139   34.8%     16d 13h  Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     53   13.2%      20d 1h  Referral Received > Insurance Verification > Info Request to Referrer > Info Received > Insurance Verification > Prior Auth Submitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     51   12.8%      2d 23h  Referral Received > Insurance Verification > Urgent Override > Scheduling Call > Appointment Scheduled > Visit Completed
     44   11.0%     21d 10h  Referral Received > Insurance Verification > Prior Auth Submitted > Prior Auth Denied > Prior Auth Resubmitted > Prior Auth Approved > Scheduling Call > Appointment Scheduled > Visit Completed
     25    6.2%      6d 16h  Referral Received > Insurance Verification > Case Closed - Abandoned
     ...

REWORK (cases where an activity occurs more than once)
     86   21.5%  Insurance Verification
     27    6.8%  Scheduling Call
     11    2.8%  Prior Auth Denied

SLOWEST TRANSITIONS (directly-follows, by median wait)
    242      4d 17h      6d 11h  Prior Auth Submitted -> Prior Auth Approved
     86      2d 18h      4d 14h  Info Request to Referrer -> Info Received
```

And the conformance check against the documented path:

```
  exact conformance:            139  (34.8%)
  in-order with extra steps:    138  (34.5%)
  deviant:                      123  (30.8%)
```

## How to read it like a TRACE analyst

1. **The documented path is a minority position.** The SOP describes 34.8% of reality. That single number reframes the automation conversation from "speed up the process" to "which process?"
2. **The shadow path is the most interesting variant.** The `Urgent Override` path (12.8% of cases) appears in no SOP — and it completes in **3 days versus 17**. Before anyone automates prior auth, the honest question is: what do urgent cases know that routine cases don't? (In `/classify` terms: is there an *Eliminate* or *Simplify* play on prior auth for some referral classes that beats any bot?)
3. **The rework loop is an upstream data-quality problem.** 21.5% of cases repeat Insurance Verification because information arrives incomplete. Automating verification wouldn't fix that — rung 2 (*Simplify*: fix the referral intake form) or rung 4 (*Automate*: validate at submission) attack the cause.
4. **The bottleneck is structural.** The longest internal wait is the payer's auth decision (median 4d 17h). An internal bot cannot compress an external payer's queue — the Economist would book that as structural cost, not automatable savings. The addressable plays are the loops and the abandonment friction around it.
5. **Exit-state variants are the quiet cost.** 6.2% of referrals are abandoned after verification friction — in a real system, that's leakage with a revenue number attached. Note the sequence is evidence for a hypothesis, not proof of cause; TRACE flags it for the Economist to size and the team to test.

Phases T (interviews) and A/C (rates, dispositions) need humans and real context — this example shows the two phases that run on data alone, which are also the two you can rehearse before ever touching a production extract.
