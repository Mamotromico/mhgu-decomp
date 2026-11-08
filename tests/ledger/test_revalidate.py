"""Tests for the candidate-toolchain re-validation tool (``tools/ledger/revalidate.py``).

These pin the contract that makes a pin change reviewable: the selection is exactly the
matched functions, a result is a regression iff the gate did not accept it, the summary
is deterministic, and a missing gate report is an ``error`` (never a silent match).

Pure functions + temp files — no clang, no Ghidra, no binary. Run with::

    python3 tests/ledger/test_revalidate.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import revalidate


def entry(**over) -> dict:
    base = {
        "module": "main", "addr": "60000000", "kind": "function",
        "name": "func_60000000", "block": ".text", "group": "func_60000000",
        "size": "4", "verify": "match",
    }
    base.update(over)
    return base


class SelectTests(unittest.TestCase):
    def test_keeps_only_matched_functions(self):
        rows = [entry(addr="60000000"), entry(addr="60000004", verify="none"),
                entry(addr="60000008", kind="data"), entry(addr="6000000c", verify="behaviour")]
        got = revalidate.selected(rows)
        self.assertEqual([e["addr"] for e in got], ["60000000"])

    def test_orders_by_module_then_addr(self):
        rows = [entry(addr="60000010"), entry(addr="60000004"),
                entry(addr="50000000", module="other")]
        got = revalidate.selected(rows)
        self.assertEqual([(e["module"], e["addr"]) for e in got],
                         [("main", "60000004"), ("main", "60000010"),
                          ("other", "50000000")])

    def test_module_filter_and_limit(self):
        rows = [entry(addr="60000004"), entry(addr="60000008"),
                entry(addr="6000000c", module="other")]
        self.assertEqual([e["addr"] for e in revalidate.selected(rows, module="main")],
                         ["60000004", "60000008"])
        self.assertEqual([e["addr"] for e in revalidate.selected(rows, limit=1)],
                         ["60000004"])


class SummarizeTests(unittest.TestCase):
    def test_counts_match_by_ok_not_status(self):
        results = [{"ok": True, "status": "match"},
                   {"ok": True, "status": "short-body"},
                   {"ok": False, "status": "mismatch"},
                   {"ok": False, "status": "mismatch"},
                   {"ok": False, "status": None}]
        self.assertEqual(revalidate.summarize(results),
                         {"match": 2, "mismatch": 2, "error": 1})

    def test_format_counts_puts_match_first(self):
        self.assertEqual(revalidate.format_counts({"mismatch": 3, "match": 10}),
                         "match=10, mismatch=3")


class RegressionTests(unittest.TestCase):
    def test_excludes_matches_and_keeps_actionable_fields(self):
        results = [
            {"module": "main", "addr": "60000004", "name": "func_60000004",
             "ok": True, "status": "match", "diff_count": 0},
            {"module": "main", "addr": "60000008", "name": "func_60000008",
             "ok": False, "status": "mismatch", "diff_count": 2, "rc": 1,
             "diff_words": [{"offset": 4, "got": "00000000", "want": "11111111"}]},
        ]
        regs = revalidate.regressions(results)
        self.assertEqual(len(regs), 1)
        r = regs[0]
        self.assertEqual((r["addr"], r["status"], r["diff_count"], r["rc"]),
                         ("60000008", "mismatch", 2, 1))
        self.assertEqual(r["diff_words"][0]["offset"], 4)


class ResultFromReportTests(unittest.TestCase):
    def test_report_is_normalized(self):
        e = entry(addr="60000008")
        rep = {"ok": False, "status": "too-long", "diff_count": 5,
               "diff_words": [{"offset": 0, "got": "aa", "want": "bb"}]}
        r = revalidate.result_from_report(e, rep, rc=1)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "too-long")
        self.assertEqual(r["diff_count"], 5)
        self.assertEqual(r["rc"], 1)

    def test_missing_report_is_an_error_with_detail(self):
        e = entry()
        r = revalidate.result_from_report(e, None, rc=3, output="x" * 1000)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["rc"], 3)
        self.assertLessEqual(len(r["detail"]), 400)

    def test_report_ok_wins(self):
        e = entry()
        r = revalidate.result_from_report(e, {"ok": True, "status": "match"}, rc=0)
        self.assertTrue(r["ok"])


class ReportTests(unittest.TestCase):
    def test_build_report_shape(self):
        results = [{"module": "main", "addr": "60000000", "name": "func_60000000",
                    "ok": True, "status": "match", "diff_count": 0, "rc": 0}]
        rep = revalidate.build_report("config/x.json", "/opt/clang/bin/clang",
                                      "clang version 4.0.1", results)
        self.assertEqual(rep["total"], 1)
        self.assertEqual(rep["counts"], {"match": 1})
        self.assertEqual(rep["regressions"], [])
        self.assertEqual(rep["clang"], "/opt/clang/bin/clang")

    def test_write_tsv_skips_matches(self):
        results = [
            {"addr": "60000000", "name": "a", "ok": True, "status": "match", "rc": 0,
             "diff_count": 0},
            {"addr": "60000004", "name": "b", "ok": False, "status": "mismatch", "rc": 1,
             "diff_count": 2},
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.tsv"
            revalidate.write_tsv(p, results)
            lines = p.read_text().splitlines()
        self.assertEqual(lines[0], "addr\tname\tstatus\tdiff_count\trc")
        self.assertEqual(len(lines), 2)
        self.assertIn("mismatch", lines[1])


class WriteRefBinTests(unittest.TestCase):
    def test_name_carries_block_start(self):
        with tempfile.TemporaryDirectory() as d:
            p = revalidate.write_ref_bin(b"\x00\x01", Path(d))
            self.assertEqual(p.name, ".text_60000000.bin")
            self.assertEqual(p.read_bytes(), b"\x00\x01")


class RemapIncludeTests(unittest.TestCase):
    def test_missing_libcxx_path_follows_the_override(self):
        with tempfile.TemporaryDirectory() as d:
            prefix = Path(d)
            (prefix / "bin").mkdir()
            inc = prefix / "include" / "c++" / "v1"
            inc.mkdir(parents=True)
            clang = str(prefix / "bin" / "clang")
            cflags = ["-target", "armv8a-none-eabi", "-isystem",
                      "/opt/clang-4.0.1/include/c++/v1", "-O2"]
            out = revalidate.remap_include_flags(cflags, clang)
            self.assertEqual(out[3], str(inc))
            self.assertEqual(out[0], "-target")

    def test_existing_path_is_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            prefix = Path(d)
            (prefix / "bin").mkdir()
            (prefix / "include" / "c++" / "v1").mkdir(parents=True)
            existing = prefix / "real" / "include" / "c++" / "v1"
            existing.mkdir(parents=True)
            cflags = ["-isystem", str(existing)]
            out = revalidate.remap_include_flags(cflags, str(prefix / "bin" / "clang"))
            self.assertEqual(out[1], str(existing))

    def test_bare_name_is_not_remapped(self):
        cflags = ["-isystem", "/nope/include/c++/v1"]
        self.assertEqual(revalidate.remap_include_flags(cflags, "clang"), cflags)


class EffectiveProfileTests(unittest.TestCase):
    def test_clang_override_is_written_without_touching_source(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "base.json"
            src.write_text(json.dumps({"clang": "/original/clang", "cflags": []}))
            work = Path(d) / "work"
            work.mkdir()
            tmp, data = revalidate.effective_profile(src, "/local/clang", work)
            self.assertEqual(data["clang"], "/local/clang")
            self.assertNotEqual(tmp, src)
            self.assertEqual(json.loads(tmp.read_text())["clang"], "/local/clang")
            self.assertEqual(json.loads(src.read_text())["clang"], "/original/clang")


if __name__ == "__main__":
    unittest.main()
