"""Tests for the ledger reconcile tool (reviewed boundary overrides).

Pure in-memory application + a temp override file — no clang, no Ghidra, no binary. Run::

    python3 tests/ledger/test_reconcile.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from reconcile import Override, ReconcileError, apply_overrides, read_overrides, serialize


def erow(addr: int, size: int, *, kind: str = "function", verify: str = "none") -> dict:
    name = f"{'func' if kind == 'function' else 'D'}_{addr:08x}"
    return {"module": "main", "addr": f"{addr:08x}", "kind": kind, "name": name,
            "block": ".text", "group": name, "size": str(size), "name_class": "generated",
            "bind": "", "guess": "0", "verify": verify, "review": "generated",
            "enroll": "rombytes"}


def ov(start: int, end: int, *cuts: tuple[int, str]) -> Override:
    return Override("main", ".text", start, end, tuple(cuts))


class ReadOverridesTests(unittest.TestCase):
    def test_missing_file_is_empty(self):
        self.assertEqual(read_overrides(Path("/no/such/overrides.tsv")), [])

    def test_parses_a_region_skipping_comments(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.tsv"
            p.write_text("module\tblock\tstart\tend\tcuts\n"
                         "# a comment\n"
                         "main\t.text\t1000\t2000\t1000:function,1500:data\n")
            self.assertEqual(read_overrides(p),
                             [Override("main", ".text", 0x1000, 0x2000,
                                       ((0x1000, "function"), (0x1500, "data")))])

    def test_bad_header_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.tsv"
            p.write_text("module\tblock\tstart\tend\n")
            with self.assertRaises(ReconcileError):
                read_overrides(p)

    def test_first_cut_must_equal_start(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.tsv"
            p.write_text("module\tblock\tstart\tend\tcuts\nmain\t.text\t1000\t2000\t1100:function\n")
            with self.assertRaises(ReconcileError):
                read_overrides(p)

    def test_cut_outside_range_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "o.tsv"
            p.write_text("module\tblock\tstart\tend\tcuts\nmain\t.text\t1000\t2000\t1000:function,2000:function\n")
            with self.assertRaises(ReconcileError):
                read_overrides(p)


class ApplyOverridesTests(unittest.TestCase):
    def test_merge_collapses_fragments(self):
        entries = [erow(0x1000, 0x10), erow(0x1010, 0x10), erow(0x1020, 0x10)]
        new, changes = apply_overrides(entries, [ov(0x1000, 0x1020, (0x1000, "function"))])
        self.assertEqual([e["addr"] for e in new], ["00001000", "00001020"])
        self.assertEqual(new[0]["size"], str(0x20))              # absorbed the second row
        self.assertEqual(new[0]["name"], "func_00001000")        # carried, not regenerated
        self.assertEqual(changes[0]["removed"], ["00001000", "00001010"])
        self.assertEqual(changes[0]["carried"], ["00001000"])
        self.assertEqual(changes[0]["added"], [])

    def test_split_creates_a_generated_boundary(self):
        entries = [erow(0x1000, 0x20), erow(0x1020, 0x08)]
        new, changes = apply_overrides(
            entries, [ov(0x1000, 0x1020, (0x1000, "function"), (0x1010, "function"))])
        self.assertEqual([e["addr"] for e in new], ["00001000", "00001010", "00001020"])
        self.assertEqual([e["size"] for e in new[:2]], [str(0x10), str(0x10)])
        self.assertEqual(new[1]["name"], "func_00001010")
        self.assertEqual(new[1]["kind"], "function")
        self.assertEqual(changes[0]["added"], ["00001010"])

    def test_a_carried_row_keeps_its_status_and_name(self):
        entries = [erow(0x1000, 0x10, verify="match")] + [erow(0x1010, 0x10)]
        entries[0]["name"], entries[0]["name_class"] = "the_real_one", "discovered"
        new, _ = apply_overrides(entries, [ov(0x1000, 0x1010, (0x1000, "function"))])
        self.assertEqual(new[0]["verify"], "match")
        self.assertEqual(new[0]["name"], "the_real_one")
        self.assertEqual(new[0]["size"], str(0x10))

    def test_dropping_authored_status_is_refused_without_force(self):
        entries = [erow(0x1000, 0x10), erow(0x1010, 0x10, verify="match"), erow(0x1020, 0x10)]
        with self.assertRaises(ReconcileError):
            apply_overrides(entries, [ov(0x1000, 0x1020, (0x1000, "function"))])
        new, _ = apply_overrides(entries, [ov(0x1000, 0x1020, (0x1000, "function"))], force=True)
        self.assertEqual([e["addr"] for e in new], ["00001000", "00001020"])

    def test_start_must_be_an_existing_entry(self):
        entries = [erow(0x1000, 0x10), erow(0x1020, 0x10)]
        with self.assertRaises(ReconcileError):
            apply_overrides(entries, [ov(0x1010, 0x1020, (0x1010, "function"))])

    def test_end_must_be_an_existing_entry(self):
        entries = [erow(0x1000, 0x20)]
        with self.assertRaises(ReconcileError):
            apply_overrides(entries, [ov(0x1000, 0x1020, (0x1000, "function"))])

    def test_kind_change_on_a_carried_row_is_refused(self):
        entries = [erow(0x1000, 0x10, kind="function"), erow(0x1010, 0x10)]
        with self.assertRaises(ReconcileError):
            apply_overrides(entries, [ov(0x1000, 0x1010, (0x1000, "data"))])

    def test_serialize_round_trips(self):
        entries = [erow(0x1000, 0x10), erow(0x1010, 0x10)]
        self.assertEqual(serialize(entries).count("\n"), 3)      # header + 2 rows


if __name__ == "__main__":
    unittest.main()
