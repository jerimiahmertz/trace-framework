#!/usr/bin/env python3
"""
Unit tests for the TRACE toolkit. Stdlib only.

Run:  python3 -m unittest discover toolkit  (from repo root)
  or: python3 toolkit/test_toolkit.py

Also guards the deliberate duplication between mine.py and conformance.py:
their shared helpers must behave identically.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conformance
import mine


class TestPercentile(unittest.TestCase):
    """Nearest-rank definition: value at index ceil(p/100 * n) - 1."""

    def test_median_of_two_is_the_lower(self):
        self.assertEqual(mine.percentile([1, 100], 50), 1)

    def test_median_of_ten(self):
        self.assertEqual(mine.percentile(list(range(1, 11)), 50), 5)

    def test_p90_of_ten(self):
        self.assertEqual(mine.percentile(list(range(1, 11)), 90), 9)

    def test_p100_is_max(self):
        self.assertEqual(mine.percentile([3, 7, 9], 100), 9)

    def test_single_element(self):
        self.assertEqual(mine.percentile([42], 50), 42)

    def test_empty(self):
        self.assertIsNone(mine.percentile([], 50))

    def test_conformance_copy_matches(self):
        for n in (1, 2, 3, 4, 5, 10, 20, 400):
            vals = list(range(n))
            for p in (25, 50, 75, 90, 100):
                self.assertEqual(mine.percentile(vals, p), conformance.percentile(vals, p),
                                 "drift between mine.py and conformance.py at n={} p={}".format(n, p))


class TestParseTs(unittest.TestCase):
    def test_basic(self):
        dt, g = mine.parse_ts("2026-01-05 08:30:00")
        self.assertEqual(dt, datetime(2026, 1, 5, 8, 30, 0))
        self.assertEqual(g, "second")

    def test_iso_t_separator(self):
        dt, _ = mine.parse_ts("2026-01-05T08:30:00")
        self.assertEqual(dt, datetime(2026, 1, 5, 8, 30, 0))

    def test_fractional_seconds(self):
        dt, _ = mine.parse_ts("2026-01-05 08:30:00.123456")
        self.assertEqual(dt.microsecond, 123456)

    def test_zulu(self):
        dt, _ = mine.parse_ts("2026-01-05T08:30:00Z")
        self.assertEqual(dt, datetime(2026, 1, 5, 8, 30, 0))

    def test_offset_normalized_to_utc(self):
        dt, _ = mine.parse_ts("2026-01-05T08:30:00-05:00")
        self.assertEqual(dt, datetime(2026, 1, 5, 13, 30, 0))
        dt2, _ = mine.parse_ts("2026-01-05T08:30:00+0100")
        self.assertEqual(dt2, datetime(2026, 1, 5, 7, 30, 0))

    def test_date_only_flagged(self):
        dt, g = mine.parse_ts("2026-01-05")
        self.assertEqual(g, "date")

    def test_minute_granularity(self):
        _, g = mine.parse_ts("2026-01-05 08:30")
        self.assertEqual(g, "minute")

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            mine.parse_ts("05/01/2026 08:30")

    def test_conformance_copy_matches(self):
        for s in ("2026-01-05 08:30:00", "2026-01-05T08:30:00Z", "2026-01-05T08:30:00.5-05:00", "2026-01-05"):
            self.assertEqual(mine.parse_ts(s), conformance.parse_ts(s))


class TestConformanceLogic(unittest.TestCase):
    EXPECTED = ("A", "B", "C")

    def test_in_order_exact(self):
        self.assertTrue(conformance.in_order(("A", "B", "C"), self.EXPECTED))

    def test_in_order_with_extras(self):
        self.assertTrue(conformance.in_order(("A", "X", "B", "Y", "C"), self.EXPECTED))

    def test_out_of_order(self):
        self.assertFalse(conformance.in_order(("B", "A", "C"), self.EXPECTED))

    def test_incomplete_prefix(self):
        self.assertTrue(conformance.in_order_prefix(("A", "B"), self.EXPECTED))
        self.assertTrue(conformance.in_order_prefix(("A", "X", "B"), self.EXPECTED))

    def test_prefix_rejects_complete(self):
        self.assertFalse(conformance.in_order_prefix(("A", "B", "C"), self.EXPECTED))

    def test_prefix_rejects_out_of_order_remnant(self):
        # C appears before B was reached — deviant, not incomplete
        self.assertFalse(conformance.in_order_prefix(("A", "C"), self.EXPECTED))

    def test_prefix_rejects_no_match(self):
        self.assertFalse(conformance.in_order_prefix(("X", "Y"), self.EXPECTED))


class TestLoadLog(unittest.TestCase):
    def _write(self, content):
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_duplicates_dropped_and_counted(self):
        path = self._write("case_id,activity,timestamp\n"
                           "C1,Start,2026-01-05 08:00:00\n"
                           "C1,Start,2026-01-05 08:00:00\n"
                           "C1,End,2026-01-05 09:00:00\n")
        cases, quality = mine.load_log(path, "case_id", "activity", "timestamp")
        self.assertEqual(len(cases["C1"]), 2)
        self.assertEqual(quality["duplicate_rows"], 1)

    def test_blank_case_id_skipped_and_counted(self):
        path = self._write("case_id,activity,timestamp\n"
                           ",Start,2026-01-05 08:00:00\n"
                           "C1,Start,2026-01-05 08:00:00\n")
        cases, quality = mine.load_log(path, "case_id", "activity", "timestamp")
        self.assertEqual(list(cases), ["C1"])
        self.assertEqual(quality["blank_case_rows"], 1)

    def test_ragged_row_exits_with_row_number(self):
        path = self._write("case_id,activity,timestamp\nC1,Start\n")
        with self.assertRaises(SystemExit) as ctx:
            mine.load_log(path, "case_id", "activity", "timestamp")
        self.assertIn("Row 2", str(ctx.exception))

    def test_tie_counting(self):
        path = self._write("case_id,activity,timestamp\n"
                           "C1,Start,2026-01-05 08:00:00\n"
                           "C1,Mid,2026-01-05 08:00:00\n"
                           "C1,End,2026-01-05 09:00:00\n")
        _, quality = mine.load_log(path, "case_id", "activity", "timestamp")
        self.assertEqual(quality["tied_pairs"], 1)
        self.assertEqual(quality["sequenced_pairs"], 2)


class TestConformanceLoadParity(unittest.TestCase):
    """conformance.py must share mine.py's loading semantics."""

    def _write(self, content):
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        f.write(content)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_duplicates_dropped(self):
        path = self._write("case_id,activity,timestamp\n"
                           "C1,Start,2026-01-05 08:00:00\n"
                           "C1,Start,2026-01-05 08:00:00\n"
                           "C1,End,2026-01-05 09:00:00\n")
        cases = conformance.load_log(path, "case_id", "activity", "timestamp")
        self.assertEqual(len(cases["C1"]), 2)

    def test_blank_activity_exits(self):
        path = self._write("case_id,activity,timestamp\nC1,,2026-01-05 08:00:00\n")
        with self.assertRaises(SystemExit) as ctx:
            conformance.load_log(path, "case_id", "activity", "timestamp")
        self.assertIn("blank activity", str(ctx.exception))

    def test_end_vocabulary_guard(self):
        cases = {"C1": [(datetime(2026, 1, 5), "Start"), (datetime(2026, 1, 6), "End")]}
        with self.assertRaises(SystemExit) as ctx:
            conformance.check_end_vocabulary(cases, {"End", "Closd"}, "test.csv")
        self.assertIn("Closd", str(ctx.exception))
        conformance.check_end_vocabulary(cases, {"End"}, "test.csv")  # must not raise


class TestSplitComplete(unittest.TestCase):
    def test_split(self):
        cases = {
            "C1": [(datetime(2026, 1, 5), "Start", None), (datetime(2026, 1, 6), "End", None)],
            "C2": [(datetime(2026, 1, 5), "Start", None), (datetime(2026, 1, 6), "Mid", None)],
        }
        complete, open_ = mine.split_complete(cases, {"End"})
        self.assertEqual(list(complete), ["C1"])
        self.assertEqual(list(open_), ["C2"])

    def test_no_filter_passthrough(self):
        cases = {"C1": [(datetime(2026, 1, 5), "Start", None)]}
        complete, open_ = mine.split_complete(cases, None)
        self.assertEqual(complete, cases)
        self.assertEqual(open_, {})


class TestCLI(unittest.TestCase):
    """Smoke: both tools run standalone from an arbitrary cwd."""

    def _tool(self, name):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

    def _log(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        f.write("case_id,activity,timestamp\n"
                "C1,Start,2026-01-05 08:00:00\nC1,End,2026-01-05 09:00:00\n"
                "C2,Start,2026-01-05 10:00:00\nC2,End,2026-01-05 12:00:00\n")
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_mine_runs_from_tmp(self):
        r = subprocess.run([sys.executable, self._tool("mine.py"), self._log(), "--end", "End"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tempfile.gettempdir())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"TRACE RECONSTRUCTION REPORT", r.stdout)

    def test_conformance_standalone_from_tmp(self):
        r = subprocess.run([sys.executable, self._tool("conformance.py"), self._log(),
                            "--expected", "Start,End", "--end", "End"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tempfile.gettempdir())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"expected-path mode", r.stdout)

    def test_vocab_mismatch_warns(self):
        r = subprocess.run([sys.executable, self._tool("conformance.py"), self._log(),
                            "--expected", "Start,Endd"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertIn(b"never occur in this log", r.stdout)


if __name__ == "__main__":
    unittest.main()
