#!/usr/bin/env python3
"""
mine.py — zero-dependency process mining for the TRACE framework (R: Reconstruct).

Takes an event log CSV (one row per event) and produces the reconstruction
evidence: variants, directly-follows graph, rework loops, handoffs, and
cycle-time statistics.

Runs on Python 3.6+ with the standard library only — no pandas, no installs.
Designed to run on locked-down machines where you cannot install anything.

Usage:
    python3 mine.py log.csv
    python3 mine.py log.csv --case case_id --activity activity --timestamp timestamp
    python3 mine.py log.csv --resource resource --top 15 --json report.json

Expected timestamp format: "YYYY-MM-DD HH:MM:SS" (or ISO 8601 with 'T').

PHI note: this tool needs only case IDs, activity names, timestamps, and
role names. Pseudonymize case IDs upstream and never feed clinical content,
patient identifiers, or free-text fields into an event log extract.
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime

TS_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")


def parse_ts(value):
    value = value.strip()
    for fmt in TS_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError("Unparseable timestamp: {!r} (expected YYYY-MM-DD HH:MM:SS)".format(value))


def percentile(sorted_values, pct):
    """Nearest-rank percentile on a pre-sorted list."""
    if not sorted_values:
        return None
    k = max(0, min(len(sorted_values) - 1, int(round(pct / 100.0 * len(sorted_values) + 0.5)) - 1))
    return sorted_values[k]


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


def load_log(path, case_col, activity_col, ts_col, resource_col=None):
    """Return {case_id: [(ts, activity, resource), ...]} sorted by time."""
    cases = defaultdict(list)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in (case_col, activity_col, ts_col) if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit("Missing column(s) {} — available: {}".format(missing, reader.fieldnames))
        if resource_col and resource_col not in reader.fieldnames:
            sys.exit("Missing resource column {!r} — available: {}".format(resource_col, reader.fieldnames))
        for i, row in enumerate(reader, start=2):
            try:
                ts = parse_ts(row[ts_col])
            except ValueError as e:
                sys.exit("Row {}: {}".format(i, e))
            resource = row[resource_col].strip() if resource_col else None
            cases[row[case_col].strip()].append((ts, row[activity_col].strip(), resource))
    for events in cases.values():
        events.sort(key=lambda e: e[0])
    return dict(cases)


def analyze(cases):
    variants = Counter()
    variant_durations = defaultdict(list)
    dfg = Counter()                      # (a, b) -> count
    dfg_waits = defaultdict(list)        # (a, b) -> [seconds]
    rework = Counter()                   # activity -> cases with repeats
    handoff_counts = []                  # per-case resource changes
    cycle_times = []                     # per-case seconds
    activity_counts = Counter()

    for events in cases.values():
        seq = tuple(a for _, a, _ in events)
        variants[seq] += 1
        activity_counts.update(seq)

        duration = (events[-1][0] - events[0][0]).total_seconds()
        cycle_times.append(duration)
        variant_durations[seq].append(duration)

        seen = Counter(seq)
        for act, n in seen.items():
            if n > 1:
                rework[act] += 1

        for (t1, a1, r1), (t2, a2, r2) in zip(events, events[1:]):
            dfg[(a1, a2)] += 1
            dfg_waits[(a1, a2)].append((t2 - t1).total_seconds())

        resources = [r for _, _, r in events if r]
        if resources:
            handoff_counts.append(sum(1 for x, y in zip(resources, resources[1:]) if x != y))

    return {
        "variants": variants,
        "variant_durations": variant_durations,
        "dfg": dfg,
        "dfg_waits": dfg_waits,
        "rework": rework,
        "handoff_counts": handoff_counts,
        "cycle_times": cycle_times,
        "activity_counts": activity_counts,
    }


def report(cases, a, top):
    n_cases = len(cases)
    n_events = sum(len(v) for v in cases.values())
    lines = []
    w = lines.append

    w("=" * 72)
    w("TRACE RECONSTRUCTION REPORT")
    w("=" * 72)
    w("Cases: {}   Events: {}   Distinct activities: {}   Distinct variants: {}".format(
        n_cases, n_events, len(a["activity_counts"]), len(a["variants"])))

    ct = sorted(a["cycle_times"])
    w("")
    w("CYCLE TIME (case start -> case end)")
    w("  min {}   median {}   p90 {}   max {}".format(
        fmt_duration(ct[0]), fmt_duration(percentile(ct, 50)),
        fmt_duration(percentile(ct, 90)), fmt_duration(ct[-1])))

    w("")
    w("TOP VARIANTS (the process as it actually runs)")
    w("  {:>5}  {:>6}  {:>10}  {}".format("cases", "share", "med cycle", "path"))
    cum = 0
    for seq, count in a["variants"].most_common(top):
        cum += count
        med = percentile(sorted(a["variant_durations"][seq]), 50)
        w("  {:>5}  {:>5.1f}%  {:>10}  {}".format(count, 100.0 * count / n_cases, fmt_duration(med), " > ".join(seq)))
    w("  ({} variants shown cover {:.1f}% of cases; {} variants total)".format(
        min(top, len(a["variants"])), 100.0 * cum / n_cases, len(a["variants"])))

    w("")
    w("REWORK (cases where an activity occurs more than once)")
    if a["rework"]:
        for act, n in a["rework"].most_common(top):
            w("  {:>5}  {:>5.1f}%  {}".format(n, 100.0 * n / n_cases, act))
    else:
        w("  none detected")

    w("")
    w("SLOWEST TRANSITIONS (directly-follows, by median wait)")
    ranked = sorted(a["dfg_waits"].items(),
                    key=lambda kv: percentile(sorted(kv[1]), 50), reverse=True)[:top]
    w("  {:>5}  {:>10}  {:>10}  {}".format("count", "med wait", "p90 wait", "transition"))
    for (x, y), waits in ranked:
        s = sorted(waits)
        w("  {:>5}  {:>10}  {:>10}  {} -> {}".format(
            a["dfg"][(x, y)], fmt_duration(percentile(s, 50)), fmt_duration(percentile(s, 90)), x, y))

    if a["handoff_counts"]:
        h = sorted(a["handoff_counts"])
        w("")
        w("HANDOFFS (resource changes per case)")
        w("  min {}   median {}   p90 {}   max {}".format(
            h[0], percentile(h, 50), percentile(h, 90), h[-1]))

    w("=" * 72)
    return "\n".join(lines)


def to_json(cases, a):
    n_cases = len(cases)
    ct = sorted(a["cycle_times"])
    return {
        "cases": n_cases,
        "events": sum(len(v) for v in cases.values()),
        "activities": dict(a["activity_counts"]),
        "cycle_time_seconds": {"min": ct[0], "median": percentile(ct, 50),
                               "p90": percentile(ct, 90), "max": ct[-1]},
        "variants": [
            {"path": list(seq), "cases": count, "share": count / n_cases,
             "median_cycle_seconds": percentile(sorted(a["variant_durations"][seq]), 50)}
            for seq, count in a["variants"].most_common()
        ],
        "rework": {act: n for act, n in a["rework"].most_common()},
        "dfg": [
            {"from": x, "to": y, "count": c,
             "median_wait_seconds": percentile(sorted(a["dfg_waits"][(x, y)]), 50)}
            for (x, y), c in a["dfg"].most_common()
        ],
    }


def main():
    p = argparse.ArgumentParser(description="Zero-dependency process mining (TRACE: Reconstruct)")
    p.add_argument("log", help="event log CSV")
    p.add_argument("--case", default="case_id")
    p.add_argument("--activity", default="activity")
    p.add_argument("--timestamp", default="timestamp")
    p.add_argument("--resource", default=None, help="optional resource/role column")
    p.add_argument("--top", type=int, default=10, help="rows per section (default 10)")
    p.add_argument("--json", dest="json_out", default=None, help="also write full results to JSON")
    args = p.parse_args()

    cases = load_log(args.log, args.case, args.activity, args.timestamp, args.resource)
    if not cases:
        sys.exit("No cases found in {}".format(args.log))
    a = analyze(cases)
    print(report(cases, a, args.top))
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(to_json(cases, a), f, indent=2)
        print("JSON written to {}".format(args.json_out))


if __name__ == "__main__":
    main()
