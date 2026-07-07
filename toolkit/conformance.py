#!/usr/bin/env python3
"""
conformance.py — zero-dependency conformance checking for the TRACE framework (E: Evidence).

Two modes:

1. Expected-path mode — how closely does reality follow the documented process?
       python3 conformance.py log.csv --expected "Referral Received,Insurance Verification,Scheduling,Visit Completed"
   Classifies every case as: exact conformance, in-order with extra steps,
   in-order but incomplete (stopped partway — often open/censored or
   abandoned cases), or deviant.

2. Baseline-vs-after mode — did the change stick, or did staff revert?
       python3 conformance.py baseline.csv --after after.csv
   Compares variant distributions and cycle times between two logs. Run this
   at +30/+60/+90 days after any process change; drift back toward old
   variants means the change was announced, not hardwired.

Censoring warning: cases still open at the extraction-window edge masquerade
as short cycle times, phantom "new variants", and false deviance. Pass --end
with your closing activities (from the case-boundary definition) so open
cases are excluded and counted; without it, both modes print an explicit
censoring warning. A process with a 17-day median cycle audited at +30 days
WILL have a large in-flight fraction — handle it or your failure signatures
are artifacts.

Python 3.6+, standard library only. Self-contained by design (helper
functions duplicated from mine.py so each tool is single-file portable —
keep the two in sync via toolkit/test_toolkit.py). Same CSV format as mine.py.
"""

import argparse
import csv
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# ── duplicated from mine.py by design: single-file portability ──────────────

TS_RE = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2})"
    r"(?:[ T](\d{2}:\d{2}(?::\d{2})?)"
    r"(\.\d+)?"
    r"\s*(Z|[+-]\d{2}:?\d{2})?)?\s*$"
)


def parse_ts(value):
    m = TS_RE.match(value or "")
    if not m:
        raise ValueError(
            "Unparseable timestamp: {!r} (expected YYYY-MM-DD HH:MM:SS or ISO 8601)".format(value))
    date_s, time_s, frac, offset = m.groups()
    if not time_s:
        return datetime.strptime(date_s, "%Y-%m-%d"), "date"
    fmt = "%Y-%m-%d %H:%M:%S" if time_s.count(":") == 2 else "%Y-%m-%d %H:%M"
    dt = datetime.strptime(date_s + " " + time_s, fmt)
    if frac:
        dt = dt.replace(microsecond=min(999999, int(round(float(frac) * 1e6))))
    if offset and offset != "Z":
        sign = 1 if offset[0] == "+" else -1
        digits = offset[1:].replace(":", "")
        dt -= sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:] or 0))
    return dt, ("second" if time_s.count(":") == 2 else "minute")


def percentile(sorted_values, pct):
    if not sorted_values:
        return None
    n = len(sorted_values)
    if float(pct).is_integer():
        rank = -(-int(pct) * n // 100)  # exact integer ceil — no FP edge cases
    else:
        rank = int(math.ceil(pct / 100.0 * n))
    return sorted_values[max(0, min(n - 1, rank - 1))]


def fmt_duration(seconds):
    if seconds is None:
        return "n/a"
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return "{}d {}h".format(days, hours)
    if hours:
        return "{}h {}m".format(hours, minutes)
    return "{}m".format(minutes)


def load_log(path, case_col, activity_col, ts_col):
    """Same loading semantics as mine.py: blank-activity rows are an error,
    exact-duplicate rows are dropped (and noted), blank-case-id rows skipped."""
    cases = defaultdict(list)
    blank_case = duplicates = 0
    seen_rows = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in (case_col, activity_col, ts_col) if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit("{}: missing column(s) {} — available: {}".format(path, missing, reader.fieldnames))
        for i, row in enumerate(reader, start=2):
            raw = tuple(row.get(c) for c in (case_col, activity_col, ts_col))
            if any(v is None for v in raw):
                sys.exit("{} row {}: malformed row — fewer fields than the header".format(path, i))
            case_id, activity, ts_raw = (v.strip() for v in raw)
            if not case_id:
                blank_case += 1
                continue
            if not activity:
                sys.exit("{} row {}: blank activity".format(path, i))
            try:
                ts, _ = parse_ts(ts_raw)
            except ValueError as e:
                sys.exit("{} row {}: {}".format(path, i, e))
            key = (case_id, activity, ts)
            if key in seen_rows:
                duplicates += 1
                continue
            seen_rows.add(key)
            cases[case_id].append((ts, activity))
    if not cases:
        sys.exit("No cases found in {}".format(path))
    if blank_case or duplicates:
        print("note: {}: {} blank-case-id rows skipped, {} exact-duplicate rows dropped".format(
            path, blank_case, duplicates))
    for events in cases.values():
        events.sort(key=lambda e: e[0])
    return dict(cases)


def check_end_vocabulary(cases, end_activities, label):
    """A typo in --end silently reclassifies real closers as open — refuse it."""
    if not end_activities:
        return
    vocab = set(a for events in cases.values() for _, a in events)
    unknown = end_activities - vocab
    if unknown:
        sys.exit("--end activities not found in {}: {} — log vocabulary: {}".format(
            label, sorted(unknown), sorted(vocab)))

# ── conformance logic ────────────────────────────────────────────────────────


def case_paths(cases):
    return {cid: tuple(a for _, a in events) for cid, events in cases.items()}


def split_complete(paths, end_activities):
    if not end_activities:
        return paths, {}
    complete, open_ = {}, {}
    for cid, p in paths.items():
        (complete if p[-1] in end_activities else open_)[cid] = p
    return complete, open_


def in_order(path, expected):
    """True if all expected activities appear in path in order (gaps allowed)."""
    it = iter(path)
    return all(any(step == x for x in it) for step in expected)


def in_order_prefix(path, expected):
    """Steps matched greedily from the front of expected; True if the path
    follows the expected order but stops before completing it."""
    idx = 0
    for act in path:
        if idx < len(expected) and act == expected[idx]:
            idx += 1
    if idx == 0 or idx >= len(expected):
        return False
    remaining = set(expected[idx:])
    return not any(act in remaining for act in path)


def cycle_times(cases):
    return sorted((events[-1][0] - events[0][0]).total_seconds() for events in cases.values())


def check_vocabulary(paths, expected):
    vocab = set(a for p in paths.values() for a in p)
    missing = [e for e in expected if e not in vocab]
    if missing:
        print("⚠ WARNING: expected activities never occur in this log: {}".format(missing))
        print("  Log vocabulary: {}".format(sorted(vocab)))
        print("  A typo or naming mismatch here makes every case look deviant. Fix before trusting results.")
        print("")


def censoring_warning(end_given):
    if not end_given:
        print("⚠ WARNING: no --end given. Open/censored cases at the extraction-window")
        print("  edge appear as short cycles, phantom variants, and false deviance.")
        print("  Pass --end \"Closing Activity A,Closing Activity B\" to exclude them.")
        print("")


def expected_mode(cases, expected, end_activities):
    paths = case_paths(cases)
    paths, open_ = split_complete(paths, end_activities)
    if not paths:
        sys.exit("All cases are open (none end in {}) — nothing to score.".format(sorted(end_activities)))
    check_vocabulary(paths, expected)
    n = len(paths)
    exact = sum(1 for p in paths.values() if p == expected)
    ordered = sum(1 for p in paths.values() if p != expected and in_order(p, expected))
    incomplete = sum(1 for p in paths.values()
                     if p != expected and not in_order(p, expected) and in_order_prefix(p, expected))
    deviant = n - exact - ordered - incomplete

    print("=" * 72)
    print("TRACE CONFORMANCE REPORT — expected-path mode")
    print("=" * 72)
    print("Expected path: {}".format(" > ".join(expected)))
    print("Cases scored: {}   Open cases excluded: {}".format(n, len(open_)))
    print("  exact conformance:            {:>5}  ({:.1f}%)".format(exact, 100.0 * exact / n))
    print("  in-order with extra steps:    {:>5}  ({:.1f}%)".format(ordered, 100.0 * ordered / n))
    print("  in-order but incomplete:      {:>5}  ({:.1f}%)  <- exits/abandonment, or censoring if --end unset".format(
        incomplete, 100.0 * incomplete / n))
    print("  deviant:                      {:>5}  ({:.1f}%)".format(deviant, 100.0 * deviant / n))

    if deviant:
        print("")
        print("TOP DEVIANT VARIANTS")
        dev = Counter(p for p in paths.values()
                      if p != expected and not in_order(p, expected) and not in_order_prefix(p, expected))
        for path, count in dev.most_common(10):
            print("  {:>5}  {}".format(count, " > ".join(path)))
    print("=" * 72)


def compare_mode(base_cases, after_cases, end_activities):
    bp, ap = case_paths(base_cases), case_paths(after_cases)
    bp, b_open = split_complete(bp, end_activities)
    ap, a_open = split_complete(ap, end_activities)
    if not bp or not ap:
        sys.exit("A log has zero complete cases after the --end filter — nothing to compare.")
    bv, av = Counter(bp.values()), Counter(ap.values())
    nb, na = len(bp), len(ap)
    b_complete = {cid: base_cases[cid] for cid in bp}
    a_complete = {cid: after_cases[cid] for cid in ap}

    print("=" * 72)
    print("TRACE CONFORMANCE REPORT — baseline vs after")
    print("=" * 72)
    print("{:<12} {:>8} {:>8} {:>10} {:>10}".format("", "cases", "open", "variants", "med cycle"))
    bct, act_ = cycle_times(b_complete), cycle_times(a_complete)
    print("{:<12} {:>8} {:>8} {:>10} {:>10}".format(
        "baseline", nb, len(b_open), len(bv), fmt_duration(percentile(bct, 50))))
    print("{:<12} {:>8} {:>8} {:>10} {:>10}".format(
        "after", na, len(a_open), len(av), fmt_duration(percentile(act_, 50))))
    if min(nb, na) < 30:
        print("⚠ small sample ({} vs {} cases): percentage-point shifts below ~10pp".format(nb, na))
        print("  are within noise at this n — do not act on them alone.")

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
    if new and not end_activities:
        prefixes = sum(1 for v in new if any(b[:len(v)] == v for b in bv))
        if prefixes:
            print("⚠ {} of the {} 'new' variants are truncated prefixes of baseline variants —".format(prefixes, len(new)))
            print("  almost certainly open cases cut by the extraction window, not new behavior.")
    print("=" * 72)


def main():
    p = argparse.ArgumentParser(description="Zero-dependency conformance checking (TRACE: Evidence)")
    p.add_argument("log", help="event log CSV (baseline in compare mode)")
    p.add_argument("--expected", default=None, help="comma-separated expected activity path")
    p.add_argument("--after", default=None, help="post-change event log CSV for comparison")
    p.add_argument("--end", default=None,
                   help="comma-separated closing activities; cases not ending in one are excluded as open/censored")
    p.add_argument("--case", default="case_id")
    p.add_argument("--activity", default="activity")
    p.add_argument("--timestamp", default="timestamp")
    args = p.parse_args()

    if bool(args.expected) == bool(args.after):
        sys.exit("Choose exactly one mode: --expected \"A,B,C\" or --after other_log.csv")

    end_activities = set(s.strip() for s in args.end.split(",") if s.strip()) if args.end else None
    censoring_warning(end_activities is not None)
    cases = load_log(args.log, args.case, args.activity, args.timestamp)
    check_end_vocabulary(cases, end_activities, args.log)
    if args.expected:
        expected = tuple(s.strip() for s in args.expected.split(",") if s.strip())
        if not expected:
            sys.exit("--expected is empty")
        expected_mode(cases, expected, end_activities)
    else:
        after = load_log(args.after, args.case, args.activity, args.timestamp)
        check_end_vocabulary(after, end_activities, args.after)
        compare_mode(cases, after, end_activities)


if __name__ == "__main__":
    main()
