#!/usr/bin/env python3
"""
Generate a synthetic specialty-referral event log for the TRACE worked example.

Entirely fictional data — no PHI, no real institution. The process modeled is a
common healthcare IA target: outpatient specialty referral with insurance
verification and prior authorization. The generator deliberately bakes in the
pathologies TRACE is designed to surface:

- a documented "happy path" that only a minority of cases actually follow
- a prior-auth denial/resubmission rework loop
- an insurance-verification missing-information loop
- a shadow expedited path that skips prior auth (urgent cases)
- abandonment (patients lost before scheduling)
- a wait-time bottleneck between auth submission and decision

Deterministic (seeded) so the committed CSV and mined report stay reproducible.

Usage: python3 generate_log.py [n_cases] > referral_log.csv
"""

import random
import sys
from datetime import datetime, timedelta

SEED = 42
BASE = datetime(2026, 1, 5, 8, 0, 0)

ROLES = {
    "Referral Received": "intake_clerk",
    "Insurance Verification": "intake_clerk",
    "Info Request to Referrer": "intake_clerk",
    "Info Received": "intake_clerk",
    "Prior Auth Submitted": "auth_specialist",
    "Prior Auth Denied": "auth_specialist",
    "Prior Auth Resubmitted": "auth_specialist",
    "Prior Auth Approved": "auth_specialist",
    "Urgent Override": "clinic_manager",
    "Scheduling Call": "scheduler",
    "Appointment Scheduled": "scheduler",
    "Visit Completed": "clinic_ma",
    "Case Closed - No Show": "scheduler",
    "Case Closed - Abandoned": "intake_clerk",
}


def minutes(lo, hi):
    return timedelta(minutes=random.randint(lo, hi))


def days(lo_hours, hi_hours):
    return timedelta(hours=random.randint(lo_hours, hi_hours))


def build_case(case_num):
    events = []
    t = BASE + timedelta(hours=random.randint(0, 2000), minutes=random.randint(0, 59))

    def add(activity, delta):
        nonlocal t
        t += delta
        events.append((t, activity))

    add("Referral Received", timedelta(0))
    roll = random.random()

    # 12% — urgent shadow path: skips prior auth entirely via manager override
    if roll < 0.12:
        add("Insurance Verification", minutes(20, 120))
        add("Urgent Override", minutes(10, 60))
        add("Scheduling Call", minutes(30, 240))
        add("Appointment Scheduled", minutes(5, 20))
        add("Visit Completed", days(24, 96))
        return events

    # 22% — missing-info loop before verification completes
    if roll < 0.34:
        add("Insurance Verification", minutes(20, 120))
        add("Info Request to Referrer", minutes(10, 40))
        add("Info Received", days(24, 120))
        add("Insurance Verification", minutes(15, 60))
    else:
        add("Insurance Verification", minutes(20, 180))

    # 8% of all cases abandon after verification friction
    if random.random() < 0.08:
        add("Case Closed - Abandoned", days(72, 240))
        return events

    add("Prior Auth Submitted", minutes(30, 300))

    # 25% — denial + resubmission rework loop (5% get denied twice)
    if random.random() < 0.25:
        add("Prior Auth Denied", days(48, 168))
        add("Prior Auth Resubmitted", days(8, 72))
        if random.random() < 0.20:
            add("Prior Auth Denied", days(48, 168))
            add("Prior Auth Resubmitted", days(8, 72))
    add("Prior Auth Approved", days(48, 168))  # the bottleneck: payer decision wait

    add("Scheduling Call", days(4, 48))
    # 10% unreachable on first call
    if random.random() < 0.10:
        add("Scheduling Call", days(24, 72))
    add("Appointment Scheduled", minutes(5, 20))

    outcome = random.random()
    if outcome < 0.85:
        add("Visit Completed", days(72, 400))
    else:
        add("Case Closed - No Show", days(72, 400))
    return events


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    random.seed(SEED)
    print("case_id,activity,timestamp,resource")
    for i in range(1, n + 1):
        for ts, activity in build_case(i):
            print("REF-{:04d},{},{},{}".format(i, activity, ts.strftime("%Y-%m-%d %H:%M:%S"), ROLES[activity]))


if __name__ == "__main__":
    main()
