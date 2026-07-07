#!/usr/bin/env python3
"""
mine.py — zero-dependency process mining for the TRACE framework (R: Reconstruct).

Takes an event log CSV (one row per event) and produces the reconstruction
evidence: data-quality assessment, variants, directly-follows graph, rework
loops, handoffs, and cycle-time statistics.

Runs on Python 3.6+ with the standard library only — no pandas, no installs.
This file is deliberately self-contained: copy this one file to a locked-down
machine and it works.

Usage:
    python3 mine.py log.csv
    python3 mine.py log.csv --case case_id --activity activity --timestamp timestamp
    python3 mine.py log.csv --resource resource --top 15 --json report.json
    python3 mine.py log.csv --end "Visit Completed,Case Closed - No Show"

Accepted timestamp formats: "YYYY-MM-DD HH:MM[:SS]" and ISO 8601 variants
(with 'T' separator, fractional seconds, 'Z' or ±HH:MM offset — offsets are
normalized to UTC). Date-only values are accepted but flagged: within-day
ordering then reflects file order, not reality.

Censoring: cases still open at the edges of your extraction window look like
short cycle times and phantom variants. Pass --end with the comma-separated
closing activities from your case-boundary definition; cases not ending in
one are excluded from statistics and reported as open. Without --end the
report carries an explicit censoring warning.

PHI note: this tool needs only case IDs, activity names, timestamps, and
role names. Pseudonymize case IDs upstream and never feed clinical content,
patient identifiers, or free-text fields into an event log extract. A
pseudonymized event log with timestamps is still PHI under HIPAA — run this
tool inside your approved environment; that is why it has no dependencies.
"""

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

SMALL_N = 8  # medians over fewer cases than this are flagged as unstable

TS_RE = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2})"          # date
    r"(?:[ T](\d{2}:\d{2}(?::\d{2})?)"  # optional time
    r"(\.\d+)?"                          # optional fractional seconds
    r"\s*(Z|[+-]\d{2}:?\d{2})?)?\s*$"    # optional timezone
)


def parse_ts(value):
    """Parse a timestamp string. Returns (datetime, granularity).

    granularity is 'second', 'minute', or 'date'. Timezone-aware values are
    normalized to UTC so mixed-offset extracts stay comparable.
    """
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
    granularity = "second" if time_s.count(":") == 2 else "minute"
    return dt, granularity


def percentile(sorted_values, pct):
    """Nearest-rank percentile on a pre-sorted list: value at ceil(p/100*n)-1."""
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


def load_log(path, case_col, activity_col, ts_col, resource_col=None):
    """Load and validate the log.

    Returns (cases, quality) where cases is {case_id: [(ts, activity, resource), ...]}
    sorted by time, and quality is a dict of data-quality counters.
    """
    cases = defaultdict(list)
    quality = {"rows": 0, "blank_case_rows": 0, "duplicate_rows": 0,
               "granularity": Counter(), "tied_pairs": 0, "sequenced_pairs": 0}
    seen_rows = set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in (case_col, activity_col, ts_col) if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit("Missing column(s) {} — available: {}".format(missing, reader.fieldnames))
        if resource_col and resource_col not in reader.fieldnames:
            sys.exit("Missing resource column {!r} — available: {}".format(resource_col, reader.fieldnames))
        for i, row in enumerate(reader, start=2):
            quality["rows"] += 1
            raw = tuple(row.get(c) for c in (case_col, activity_col, ts_col))
            if any(v is None for v in raw):
                sys.exit("Row {}: malformed row — fewer fields than the header "
                         "(check for unquoted commas or a truncated file)".format(i))
            case_id, activity, ts_raw = (v.strip() for v in raw)
            if not case_id:
                quality["blank_case_rows"] += 1
                continue
            if not activity:
                sys.exit("Row {}: blank activity".format(i))
            try:
                ts, granularity = parse_ts(ts_raw)
            except ValueError as e:
                sys.exit("Row {}: {}".format(i, e))
            quality["granularity"][granularity] += 1
            resource = (row.get(resource_col) or "").strip() if resource_col else None
            key = (case_id, activity, ts, resource)
            if key in seen_rows:
                quality["duplicate_rows"] += 1
                continue
            seen_rows.add(key)
            cases[case_id].append((ts, activity, resource))
    for events in cases.values():
        events.sort(key=lambda e: e[0])
        for (t1, _, _), (t2, _, _) in zip(events, events[1:]):
            quality["sequenced_pairs"] += 1
            if t1 == t2:
                quality["tied_pairs"] += 1
    return dict(cases), quality


def split_complete(cases, end_activities):
    """Split cases into (complete, open) by whether the last event is a closing activity."""
    if not end_activities:
        return cases, {}
    complete, open_cases = {}, {}
    for cid, events in cases.items():
        (complete if events[-1][1] in end_activities else open_cases)[cid] = events
    return complete, open_cases


def analyze(cases):
    variants = Counter()
    variant_durations = defaultdict(list)
    dfg = Counter()
    dfg_waits = defaultdict(list)
    rework = Counter()
    handoff_counts = []
    cycle_times = []
    activity_counts = Counter()

    for events in cases.values():
        seq = tuple(a for _, a, _ in events)
        variants[seq] += 1
        activity_counts.update(seq)

        duration = (events[-1][0] - events[0][0]).total_seconds()
        cycle_times.append(duration)
        variant_durations[seq].append(duration)

        for act, n in Counter(seq).items():
            if n > 1:
                rework[act] += 1

        for (t1, a1, _), (t2, a2, _) in zip(events, events[1:]):
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


def quality_section(quality, n_open, end_given):
    lines = []
    w = lines.append
    w("DATA QUALITY")
    w("  rows read: {}   blank-case-id rows skipped: {}   exact-duplicate rows dropped: {}".format(
        quality["rows"], quality["blank_case_rows"], quality["duplicate_rows"]))
    gran = quality["granularity"]
    w("  timestamp granularity: {}".format(
        ", ".join("{} {}".format(n, g) for g, n in gran.most_common()) or "n/a"))
    tie_pct = 100.0 * quality["tied_pairs"] / quality["sequenced_pairs"] if quality["sequenced_pairs"] else 0.0
    w("  tied consecutive timestamps: {} of {} ({:.1f}%)".format(
        quality["tied_pairs"], quality["sequenced_pairs"], tie_pct))
    if gran.get("date"):
        w("  ⚠ date-only timestamps present: within-day ordering reflects FILE ORDER,")
        w("    not reality — variant and transition counts may be artifacts.")
    if tie_pct > 5.0:
        w("  ⚠ >5% tied timestamps: ordering of tied events is arbitrary; treat")
        w("    fine-grained variant distinctions with suspicion.")
    if end_given:
        w("  open (censored) cases excluded from statistics: {}".format(n_open))
    else:
        w("  ⚠ no --end given: cases truncated by the extraction window are counted")
        w("    as if complete — cycle times bias short and phantom 'variants' appear.")
        w("    Pass --end \"Closing Activity A,Closing Activity B\" from your case-boundary definition.")
    return lines


def report(cases, a, top, quality, n_open, end_given):
    n_cases = len(cases)
    n_events = sum(len(v) for v in cases.values())
    lines = []
    w = lines.append

    w("=" * 72)
    w("TRACE RECONSTRUCTION REPORT")
    w("=" * 72)
    w("Cases: {}   Events: {}   Distinct activities: {}   Distinct variants: {}".format(
        n_cases, n_events, len(a["activity_counts"]), len(a["variants"])))
    w("")
    lines.extend(quality_section(quality, n_open, end_given))

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
    small_n_flag = False
    for seq, count in a["variants"].most_common(top):
        cum += count
        med = percentile(sorted(a["variant_durations"][seq]), 50)
        marker = "*" if count < SMALL_N else " "
        small_n_flag = small_n_flag or count < SMALL_N
        w("  {:>5}  {:>5.1f}%  {:>9}{}  {}".format(
            count, 100.0 * count / n_cases, fmt_duration(med), marker, " > ".join(seq)))
    w("  ({} variants shown cover {:.1f}% of cases; {} variants total)".format(
        min(top, len(a["variants"])), 100.0 * cum / n_cases, len(a["variants"])))
    if small_n_flag:
        w("  * fewer than {} cases — median is unstable, treat as anecdote".format(SMALL_N))

    w("")
    w("REWORK (cases where an activity occurs more than once)")
    if a["rework"]:
        for act, n in a["rework"].most_common(top):
            w("  {:>5}  {:>5.1f}%  {}".format(n, 100.0 * n / n_cases, act))
    else:
        w("  none detected")

    w("")
    w("SLOWEST TRANSITIONS (directly-follows, by median wait)")
    w("  NOTE: waits are wall-clock elapsed time (nights/weekends included) and")
    w("  include outcome lags (e.g. scheduled -> visit) — read as queues only")
    w("  where a queue actually exists.")
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


def to_json(cases, a, quality, n_open):
    n_cases = len(cases)
    ct = sorted(a["cycle_times"])
    return {
        "cases": n_cases,
        "events": sum(len(v) for v in cases.values()),
        "open_cases_excluded": n_open,
        "data_quality": {
            "rows": quality["rows"],
            "blank_case_rows": quality["blank_case_rows"],
            "duplicate_rows": quality["duplicate_rows"],
            "granularity": dict(quality["granularity"]),
            "tied_pairs": quality["tied_pairs"],
            "sequenced_pairs": quality["sequenced_pairs"],
        },
        "activities": dict(a["activity_counts"]),
        "cycle_time_seconds": {"min": ct[0], "median": percentile(ct, 50),
                               "p90": percentile(ct, 90), "max": ct[-1]},
        "variants": [
            {"path": list(seq), "cases": count, "share": count / n_cases,
             "median_cycle_seconds": percentile(sorted(a["variant_durations"][seq]), 50),
             "small_n": count < SMALL_N}
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
    p.add_argument("--end", default=None,
                   help="comma-separated closing activities; cases not ending in one are excluded as open/censored")
    p.add_argument("--top", type=int, default=10, help="rows per section (default 10)")
    p.add_argument("--json", dest="json_out", default=None, help="also write full results to JSON")
    args = p.parse_args()

    all_cases, quality = load_log(args.log, args.case, args.activity, args.timestamp, args.resource)
    if not all_cases:
        sys.exit("No cases found in {}".format(args.log))
    end_activities = set(s.strip() for s in args.end.split(",") if s.strip()) if args.end else None
    if end_activities:
        vocab = set()
        for events in all_cases.values():
            vocab.update(a for _, a, _ in events)
        unknown = end_activities - vocab
        if unknown:
            sys.exit("--end activities not found in the log: {} — log vocabulary: {}".format(
                sorted(unknown), sorted(vocab)))
    cases, open_cases = split_complete(all_cases, end_activities)
    if not cases:
        sys.exit("All {} cases are open (none end in {}) — check your --end list.".format(
            len(all_cases), sorted(end_activities)))
    a = analyze(cases)
    print(report(cases, a, args.top, quality, len(open_cases), end_activities is not None))
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(to_json(cases, a, quality, len(open_cases)), f, indent=2)
        print("JSON written to {}".format(args.json_out))


if __name__ == "__main__":
    main()
