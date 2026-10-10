"""Tests for the worklist selector: filtering, ordering, and filter normalization.

Pure-function tests only — no ledger, no filesystem, no binary. Run with::

    python3 tests/loop/test_worklist.py
"""

from __future__ import annotations

import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from worklist import allowed, main, select, sort_key, source_path, source_root


def entry(module: str, addr: str, kind: str = "function", verify: str = "none",
          name: str = "", group: str = "", block: str = ".text", size: str = "4") -> dict:
    return {"module": module, "addr": addr, "kind": kind, "verify": verify,
            "name": name or f"func_{addr}", "group": group or f"func_{addr}",
            "block": block, "size": size}


class AllowedTests(unittest.TestCase):
    def test_none_and_sentinels_mean_any(self):
        for value in (None, "", "any", "*"):
            self.assertIsNone(allowed(value))

    def test_single_value(self):
        self.assertEqual(allowed("none"), {"none"})

    def test_comma_separated(self):
        self.assertEqual(allowed("none,behaviour"), {"none", "behaviour"})

    def test_iterable_and_empty_iterable(self):
        self.assertEqual(allowed(["a", "b"]), {"a", "b"})
        self.assertIsNone(allowed([]))


class SortKeyTests(unittest.TestCase):
    def test_module_then_addr(self):
        self.assertEqual(sort_key(entry("main", "60000024")), ("main", "60000024"))

    def test_zero_padded_addr_is_lexically_ordered(self):
        addrs = ["60000024", "60000f8c", "601a72e4", "61ffffff"]
        self.assertEqual(sorted(addrs), addrs)


class SelectTests(unittest.TestCase):
    def test_default_keeps_only_pending_functions(self):
        entries = [
            entry("main", "60000024", kind="function", verify="none"),
            entry("main", "60000000", kind="data", verify="none"),
            entry("main", "", kind="external", verify="none"),
            entry("main", "60000028", kind="function", verify="match"),
        ]
        self.assertEqual([e["addr"] for e in select(entries)], ["60000024"])

    def test_deterministic_order_regardless_of_input_order(self):
        entries = [
            entry("main", "601a72e4"),
            entry("main", "60000f8c"),
            entry("main", "60000024"),
        ]
        self.assertEqual([e["addr"] for e in select(entries)],
                         ["60000024", "60000f8c", "601a72e4"])

    def test_does_not_mutate_input(self):
        entries = [entry("main", "60000028"), entry("main", "60000024")]
        before = list(entries)
        select(entries)
        self.assertEqual(entries, before)

    def test_verify_filter_selects_behaviour(self):
        entries = [
            entry("main", "60000024", verify="none"),
            entry("main", "60000028", verify="behaviour"),
        ]
        self.assertEqual([e["addr"] for e in select(entries, verify="behaviour")],
                         ["60000028"])

    def test_verify_any_passes_all_verifies(self):
        entries = [
            entry("main", "60000024", verify="none"),
            entry("main", "60000028", verify="match"),
        ]
        self.assertEqual(len(select(entries, verify="any")), 2)

    def test_kind_any_includes_data_and_externals(self):
        entries = [
            entry("main", "60000000", kind="data"),
            entry("main", "", kind="external"),
            entry("main", "60000024", kind="function"),
        ]
        self.assertEqual(len(select(entries, kind="any")), 3)

    def test_module_filter(self):
        entries = [entry("main", "60000024"), entry("other", "60000024")]
        self.assertEqual([e["module"] for e in select(entries, module="other")], ["other"])

    def test_multiple_modules_as_csv(self):
        entries = [entry("main", "60000024"), entry("other", "60000024"),
                   entry("third", "60000024")]
        got = select(entries, module="main,other")
        self.assertEqual(sorted(e["module"] for e in got), ["main", "other"])

    def test_empty_input(self):
        self.assertEqual(select([]), [])

    def test_drop_predicate_removes_matching_entries(self):
        entries = [entry("main", "60000024"), entry("main", "60000028")]
        got = select(entries, drop=lambda e: e["addr"] == "60000024")
        self.assertEqual([e["addr"] for e in got], ["60000028"])

    def test_key_overrides_the_address_order(self):
        entries = [entry("main", "60000024"), entry("main", "60000028")]
        got = select(entries, key=lambda e: 0 if e["addr"] == "60000028" else 1)
        self.assertEqual([e["addr"] for e in got], ["60000028", "60000024"])

    def test_key_ties_break_on_address_for_determinism(self):
        entries = [entry("main", "60000028"), entry("main", "60000024")]
        got = select(entries, key=lambda e: 0)
        self.assertEqual([e["addr"] for e in got], ["60000024", "60000028"])


class SourcePathTests(unittest.TestCase):
    def test_path_is_module_group_cpp(self):
        e = entry("main", "60000024", group="func_60000024")
        self.assertEqual(source_path(e, Path("/r/src")),
                         Path("/r/src/main/func_60000024.cpp"))

    def test_merged_tu_shares_a_path(self):
        a = entry("main", "60000024", group="grp")
        b = entry("main", "60000028", group="grp")
        self.assertEqual(source_path(a, Path("/r/src")), source_path(b, Path("/r/src")))


class SourceRootTests(unittest.TestCase):
    def test_missing_config_falls_back(self):
        missing = Path(tempfile.mkdtemp()) / "nope.json"
        self.assertEqual(source_root(missing), "src")

    def test_value_read_from_config(self):
        path = Path(tempfile.mkdtemp()) / "build.json"
        path.write_text('{"source_root": "code"}')
        self.assertEqual(source_root(path), "code")

    def test_malformed_config_falls_back(self):
        path = Path(tempfile.mkdtemp()) / "build.json"
        path.write_text("{not json")
        self.assertEqual(source_root(path), "src")


class MainJsonLimitTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.ledger = Path(self._dir.name) / "ledger.tsv"
        rows = ["module\taddr\tkind\tverify"]
        for i in range(25):
            rows.append(f"main\t6000{i:04x}\tfunction\tnone")
        self.ledger.write_text("\n".join(rows) + "\n")

    def tearDown(self):
        self._dir.cleanup()

    def _run(self, argv: list[str]) -> list:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(["--ledger", str(self.ledger), "--json", *argv])
        self.assertEqual(rc, 0)
        return json.loads(out.getvalue())

    def test_json_emits_the_whole_queue_by_default(self):
        self.assertEqual(len(self._run([])), 25)

    def test_explicit_limit_still_applies(self):
        self.assertEqual(len(self._run(["--limit", "5"])), 5)


class MainOrderTests(unittest.TestCase):
    """``--order easiest`` ranks call-free functions first, via the injected complexity key."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        d = Path(self._dir.name)
        self.ledger = d / "ledger.tsv"
        self.ledger.write_text("module\taddr\tkind\tverify\tsize\n"
                               "main\t60000000\tfunction\tnone\t4\n"
                               "main\t60000004\tfunction\tnone\t4\n")
        self.inv = d / "inventory.tsv"
        self.inv.write_text("60000000\tfunction\t4\tF\t.text\n"
                            "60000004\tfunction\t4\tF\t.text\n")

    def tearDown(self):
        self._dir.cleanup()

    def test_easiest_ranks_call_free_first(self):
        # 0x60000000: mov r0,r0 (call-free); 0x60000004: bl (has a call).
        text = struct.pack("<I", 0xE1A00000) + struct.pack("<I", 0xEB000000)
        out = io.StringIO()
        with mock.patch("worklist.complexity.load_text", return_value=text):
            with contextlib.redirect_stdout(out):
                rc = main(["--ledger", str(self.ledger), "--inventory", str(self.inv),
                           "--order", "easiest", "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual([e["addr"] for e in json.loads(out.getvalue())],
                         ["60000000", "60000004"])

    def test_order_easiest_degrades_to_addr_without_the_image(self):
        out = io.StringIO()
        with mock.patch("worklist.complexity.load_text", return_value=None):
            with contextlib.redirect_stdout(out):
                rc = main(["--ledger", str(self.ledger), "--order", "easiest", "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual([e["addr"] for e in json.loads(out.getvalue())],
                         ["60000000", "60000004"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
