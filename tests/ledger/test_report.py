"""Tests for the decomp.dev/objdiff report exporter (``tools/ledger/report.py``).

The exporter is the published-number surface, so these pin its contract: the shared
predicate drives every field, externals/zero-size leave the denominator, ``behaviour`` is
not a match, and code/data/units/categories split exactly as the docs describe.

Pure functions + temp files — no clang, no Ghidra, no binary. Run with::

    python3 tests/ledger/test_report.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from report import (REPORT_VERSION, build as _build, linked_entries,
                    main as report_main, verified_extents)
from ledgerlib import LEDGER_COLUMNS

HEADER = "\t".join(LEDGER_COLUMNS)
MEASURE_FIELDS = {
    "fuzzy_match_percent", "total_code", "matched_code", "matched_code_percent",
    "total_data", "matched_data", "matched_data_percent", "total_functions",
    "matched_functions", "matched_functions_percent", "complete_code",
    "complete_code_percent", "complete_data", "complete_data_percent", "total_units",
    "complete_units",
}


def entry(**over) -> dict:
    """One ledger entry (all columns) with ``over`` applied."""
    base = {
        "module": "main", "addr": "60000000", "kind": "function",
        "name": "func_60000000", "block": ".text", "group": "func_60000000",
        "size": "4", "name_class": "generated", "bind": "", "guess": "0",
        "verify": "none", "gate": "", "review": "generated", "enroll": "rombytes",
    }
    base.update(over)
    return base


def build(entries: list[dict], include_units: bool = False,
          linked: set[tuple[str, str]] | None = None,
          extents: dict[tuple[str, str], int] | None = None) -> dict:
    """Test convenience: old partition-sized cases get an explicit extent map."""
    if extents is None:
        extents = {(e["module"], e["addr"]): int(e["size"]) for e in entries
                   if e["verify"] == "match" and e["kind"] in ("function", "data")}
    return _build(entries, include_units=include_units, linked=linked, extents=extents)


class ReportTests(unittest.TestCase):
    def test_version_is_current_objdiff_version(self):
        self.assertEqual(REPORT_VERSION, 2)
        self.assertEqual(build([])["version"], 2)

    def test_measures_split_code_data_and_matched(self):
        entries = [
            entry(name="A", group="A", size="8", verify="match", enroll="complete"),
            entry(addr="60000008", name="B", group="B", size="4"),
            entry(addr="6000000c", name="C", group="C", kind="data", block=".rodata",
                  size="16", verify="match", enroll="complete"),
        ]
        m = build(entries)["measures"]
        self.assertEqual(m["total_code"], 12)
        self.assertEqual(m["matched_code"], 8)
        self.assertEqual(m["total_functions"], 2)
        self.assertEqual(m["matched_functions"], 1)
        self.assertEqual(m["total_data"], 16)
        self.assertEqual(m["matched_data"], 16)
        self.assertAlmostEqual(m["matched_code_percent"], 8 / 12 * 100)
        # fuzzy has no partial credit: it equals the code match percent
        self.assertEqual(m["fuzzy_match_percent"], m["matched_code_percent"])

    def test_externals_and_zero_size_leave_the_denominator(self):
        entries = [
            entry(name="A", group="A", size="8", verify="match"),
            entry(kind="external", name="nn::foo", block="", group="", size="",
                  name_class="discovered", bind="GLOBAL", enroll=""),
            entry(addr="60000008", name="Z", group="Z", size="0"),
        ]
        m = build(entries)["measures"]
        self.assertEqual(m["total_functions"], 1)
        self.assertEqual(m["total_code"], 8)
        self.assertEqual(build(entries, include_units=True)["units"][0]["name"], "A")

    def test_units_are_omitted_by_default(self):
        entries = [entry(name="A", group="A", size="8", verify="match")]
        report = build(entries)
        self.assertNotIn("units", report)
        self.assertIn("categories", report)
        self.assertEqual(report["measures"]["total_units"], 1)

    def test_behaviour_is_not_a_match(self):
        entries = [entry(name="A", group="A", size="8", verify="behaviour")]
        m = build(entries)["measures"]
        self.assertEqual(m["matched_code"], 0)
        self.assertEqual(m["total_code"], 8)

    def test_complete_tracks_the_enroll_axis(self):
        entries = [
            entry(name="A", group="A", size="8", verify="match", enroll="complete"),
            entry(addr="60000008", name="B", group="B", size="4", verify="match"),
        ]
        m = build(entries)["measures"]
        self.assertEqual(m["complete_code"], 8)
        self.assertAlmostEqual(m["complete_code_percent"], 8 / 12 * 100)

    def test_a_link_result_replaces_the_enroll_axis(self):
        # The build's verdict is authoritative: A was verified in the image, B was not,
        # even though neither is enrolled as complete.
        entries = [
            entry(name="A", group="A", size="8", verify="match"),
            entry(addr="60000008", name="B", group="B", size="4", verify="match"),
        ]
        m = build(entries, linked={("main", "60000000")})["measures"]
        self.assertEqual(m["matched_code"], 12)
        self.assertEqual(m["complete_code"], 8)
        self.assertAlmostEqual(m["complete_code_percent"], 8 / 12 * 100)

    def test_link_result_does_not_link_an_unmatched_entry(self):
        entries = [entry(name="A", group="A", size="8", verify="none")]
        m = build(entries, linked={("main", "60000000")})["measures"]
        self.assertEqual(m["complete_code"], 0)

    def test_linked_entries_parses_a_link_report(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "link.json"
            path.write_text(json.dumps({"linked": ["main:60000288", "main:6000029c"]}))
            self.assertEqual(linked_entries(path),
                             {("main", "60000288"), ("main", "6000029c")})

    def test_linked_entries_rejects_a_malformed_key(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "link.json"
            path.write_text(json.dumps({"linked": ["60000288"]}))
            with self.assertRaises(ValueError):
                linked_entries(path)

    def test_units_are_groups_and_categories_are_modules(self):
        entries = [
            entry(name="A", group="A", size="8", verify="match", enroll="complete"),
            entry(addr="60000008", name="B", group="A", size="4"),
            entry(addr="6000000c", name="C", group="C", kind="data", block=".rodata",
                  size="16", verify="match", enroll="complete"),
        ]
        r = build(entries, include_units=True)
        self.assertEqual([u["name"] for u in r["units"]], ["A", "C"])
        self.assertEqual(r["measures"]["total_units"], 2)
        # unit A is half-enrolled -> not complete; unit C is -> complete
        self.assertEqual(r["measures"]["complete_units"], 1)
        self.assertFalse(r["units"][0]["metadata"]["complete"])
        self.assertTrue(r["units"][1]["metadata"]["complete"])
        self.assertEqual([c["id"] for c in r["categories"]], ["main"])
        self.assertEqual(r["categories"][0]["measures"]["total_code"], 12)

    def test_function_items_carry_sizes_and_virtual_address(self):
        entries = [entry(name="A", group="A", size="8", addr="60000008",
                         verify="match")]
        unit = build(entries, include_units=True)["units"][0]
        self.assertEqual(unit["functions"][0]["size"], 8)
        self.assertEqual(unit["functions"][0]["fuzzy_match_percent"], 100.0)
        self.assertEqual(unit["functions"][0]["metadata"]["virtual_address"], 0x60000008)

    def test_verified_body_is_not_charged_for_its_whole_partition(self):
        entries = [entry(name="A", group="A", size="1368", verify="match",
                         enroll="complete")]
        extents = {("main", "60000000"): 60}
        r = build(entries, include_units=True, extents=extents)
        m = r["measures"]
        self.assertEqual(m["total_code"], 1368)
        self.assertEqual(m["matched_code"], 60)
        self.assertEqual(m["complete_code"], 60)
        self.assertEqual(m["matched_functions"], 1)
        self.assertAlmostEqual(m["matched_code_percent"], 60 / 1368 * 100)
        self.assertEqual(r["categories"][0]["measures"]["matched_code"], 60)
        self.assertEqual(r["units"][0]["measures"]["matched_code"], 60)
        self.assertEqual(r["units"][0]["functions"][0]["size"], 60)

        unlinked = build(entries, linked=set(), extents=extents)["measures"]
        linked = build(entries, linked={("main", "60000000")}, extents=extents)["measures"]
        self.assertEqual(unlinked["matched_code"], 60)
        self.assertEqual(unlinked["complete_code"], 0)
        self.assertEqual(linked["matched_code"], 60)
        self.assertEqual(linked["complete_code"], 60)

    def test_a_matched_row_without_a_valid_extent_is_rejected(self):
        matched = entry(name="A", group="A", size="1368", verify="match")
        with self.assertRaisesRegex(ValueError, "missing verified extent"):
            _build([matched])
        with self.assertRaisesRegex(ValueError, "does not fit partition"):
            _build([matched], extents={("main", "60000000"): 1369})

    def test_extent_derivation_covers_functions_data_and_materialized_gaps(self):
        entries = [
            entry(name="A", group="A", size="1368", verify="match"),
            entry(addr="60001000", name="D_data", group="D_data", kind="data",
                  block=".rodata", size="32", verify="match"),
            entry(addr="60002000", name="D_gap", group="D_gap", kind="data",
                  block=".rodata", size="48", verify="match"),
        ]
        inventory = {"60000000": ("function", 60), "60001000": ("data", 24)}
        extents = verified_extents(entries, bytes(60), inventory, {"60002000"})
        self.assertEqual(extents, {
            ("main", "60000000"): 60,
            ("main", "60001000"): 24,
            ("main", "60002000"): 48,
        })

    def test_extent_derivation_rejects_missing_inventory_rows(self):
        matched_function = entry(name="A", group="A", size="60", verify="match")
        with self.assertRaisesRegex(ValueError, "no function instruction extent"):
            verified_extents([matched_function], bytes(60), {}, set())
        matched_data = entry(name="D", group="D", kind="data", size="60",
                             verify="match")
        with self.assertRaisesRegex(ValueError, "no data extent"):
            verified_extents([matched_data], None, {}, set())

    def test_empty_ledger_is_100_percent_by_objdiff_convention(self):
        m = build([])["measures"]
        self.assertEqual(m["matched_code_percent"], 100.0)
        self.assertEqual(m["complete_code_percent"], 100.0)


class CliTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def _ledger(self, rows: list[dict]) -> Path:
        p = self.tmp / "ledger.tsv"
        lines = [HEADER]
        for r in rows:
            lines.append("\t".join(r[c] for c in LEDGER_COLUMNS))
        p.write_text("\n".join(lines) + "\n")
        return p

    def test_out_writes_a_parseable_v2_report(self):
        ledger = self._ledger([entry(name="A", group="A", size="8", verify="match")])
        out = self.tmp / "nested" / "report.json"
        extents = {("main", "60000000"): 8}
        with mock.patch("report.load_verified_extents", return_value=extents):
            with contextlib.redirect_stderr(io.StringIO()):
                rc = report_main(["--ledger", str(ledger), "--out", str(out)])
        self.assertEqual(rc, 0)
        report = json.loads(out.read_text())
        self.assertEqual(report["version"], 2)
        self.assertEqual(set(report), {"measures", "version", "categories"})
        self.assertEqual(set(report["measures"]), MEASURE_FIELDS)
        self.assertEqual(set(report["categories"][0]["measures"]), MEASURE_FIELDS)
        self.assertEqual(report["measures"]["matched_code"], 8)

    def test_missing_ledger_is_a_usage_error(self):
        rc = report_main(["--ledger", str(self.tmp / "nope.tsv")])
        self.assertEqual(rc, 2)

    def test_an_extent_error_is_a_usage_error(self):
        ledger = self._ledger([entry(name="A", group="A", size="8", verify="match")])
        err = io.StringIO()
        with mock.patch("report.load_verified_extents",
                        side_effect=ValueError("missing verified extent")):
            with contextlib.redirect_stderr(err):
                rc = report_main(["--ledger", str(ledger), "--compact"])
        self.assertEqual(rc, 2)
        self.assertIn("missing verified extent", err.getvalue())

    def test_stdout_is_valid_json(self):
        ledger = self._ledger([entry(name="A", group="A", size="8")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = report_main(["--ledger", str(ledger), "--compact"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["version"], 2)


if __name__ == "__main__":
    unittest.main()
