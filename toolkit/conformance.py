#!/usr/bin/env python3
"""
conformance.py — zero-dependency conformance checking for the TRACE framework (E: Evidence).

Two modes:

1. Expected-path mode — how closely does reality follow the documented process?
       python3 conformance.py log.csv --expected "Referral Received,Insurance Verification,Scheduling,Visit Completed"
   Reports the share of cases that conform exactly, conform with extra steps
   (documented path present in order, other activities interleaved), or deviate.

2. Baseline-vs-after mode — did the change stick, or did staff revert?
       python3 conformance.py baseline.csv --after after.csv
   Compares variant distributions and cycle times between two logs. Run this
   at +30/+60/+90 days after any process change; drift back toward old
   variants means the change was announced, not hardwired.

Python 3.6+, standard library only. Same CSV format as mine.py.
"""

import argparse
import sys
from collections import Counter

from mine import load_log, percentile, fmt_duration


def case_paths(cases):
    return {cid: tuple(a for _, a, _ in events) for cid, events in cases.items()}


def in_order(path, expected):
    """True if all expected activities appear in path in order (gaps allowed)."""
    it = iter(path)
    return all(any(step == x for x in it) for step in expected)


def cycle_times(cases):
    return sorted((events[-1][0] - events[0][0]).total_seconds() for events in cases.values())


def expected_mode(cases, expected):
    paths = case_paths(cases)
    n = len(paths)
    exact = sum(1 for p in paths.values() if p == expected)
    ordered = sum(1 for p in paths.values() if p != expected and in_order(p, expected))
    deviant = n - exact - ordered

    print("=" * 72)
    print("TRACE CONFORMANCE REPORT — expected-path mode")
    print("=" * 72)
    print("Expected path: {}".format(" > ".join(expected)))
    print("Cases: {}".format(n))
    print("  exact conformance:          {:>5}  ({:.1f}%)".format(exact, 100.0 * exact / n))
    print("  in-order with extra steps:  {:>5}  ({:.1f}%)".format(ordered, 100.0 * ordered / n))
    print("  deviant:                    {:>5}  ({:.1f}%)".format(deviant, 100.0 * deviant / n))

    if deviant:
        print("")
        print("TOP DEVIANT VARIANTS")
        dev = Counter(p for p in paths.values() if p != expected and not in_order(p, expected))
        for path, count in dev.most_common(10):
            print("  {:>5}  {}".format(count, " > ".join(path)))
    print("=" * 72)


def compare_mode(base_cases, after_cases):
    bp, ap = case_paths(base_cases), case_paths(after_cases)
    bv, av = Counter(bp.values()), Counter(ap.values())
    nb, na = len(bp), len(ap)

    print("=" * 72)
    print("TRACE CONFORMANCE REPORT — baseline vs after")
    print("=" * 72)
    print("{:<12} {:>8} {:>10} {:>10}".format("", "cases", "variants", "med cycle"))
    bct, act_ = cycle_times(base_cases), cycle_times(after_cases)
    print("{:<12} {:>8} {:>10} {:>10}".format("baseline", nb, len(bv), fmt_duration(percentile(bct, 50))))
    print("{:<12} {:>8} {:>10} {:>10}".format("after", na, len(av), fmt_duration(percentile(act_, 50))))

    print("")
    print("VARIANT SHIFT (share of cases, baseline -> after)")
    print("  {:>8} {:>8} {:>8}  {}".format("base", "after", "delta", "path"))
    all_variants = sorted(set(bv) | set(av),
                          key=lambda v: max(bv.get(v, 0) / nb, av.get(v, 0) / na), reverse=True)
    for v in all_variants[:12]:
        b_share = 100.0 * bv.get(v, 0) / nb
        a_share = 100.0 * av.get(v, 0) / na
        print("  {:>7.1f}% {:>7.1f}% {:>+7.1f}%  {}".format(b_share, a_share, a_share - b_share, " > ".join(v)))

    gone = [v for v in bv if v not in av]
    new = [v for v in av if v not in bv]
    print("")
    print("Variants eliminated: {}   Variants newly appeared: {}".format(len(gone), len(new)))
    print("=" * 72)


def main():
    p = argparse.ArgumentParser(description="Zero-dependency conformance checking (TRACE: Evidence)")
    p.add_argument("log", help="event log CSV (baseline in compare mode)")
    p.add_argument("--expected", default=None, help="comma-separated expected activity path")
    p.add_argument("--after", default=None, help="post-change event log CSV for comparison")
    p.add_argument("--case", default="case_id")
    p.add_argument("--activity", default="activity")
    p.add_argument("--timestamp", default="timestamp")
    args = p.parse_args()

    if bool(args.expected) == bool(args.after):
        sys.exit("Choose exactly one mode: --expected \"A,B,C\" or --after other_log.csv")

    cases = load_log(args.log, args.case, args.activity, args.timestamp)
    if args.expected:
        expected = tuple(s.strip() for s in args.expected.split(",") if s.strip())
        expected_mode(cases, expected)
    else:
        after = load_log(args.after, args.case, args.activity, args.timestamp)
        compare_mode(cases, after)


if __name__ == "__main__":
    main()
