"""Tests for the near-miss bank: closeness, the eval pin, and the strictly-improving upsert.

    python3 tests/loop/test_nearmiss.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from nearmiss import (
    METRIC,
    best,
    closeness,
    empty_bank,
    eval_pin,
    key,
    load_bank,
    main,
    record,
    save_bank,
    upsert,
)


class ClosenessTests(unittest.TestCase):
    def test_lower_is_better_pair(self):
        self.assertEqual(closeness(3, 58, 60), [2, 3])

    def test_length_delta_is_absolute(self):
        self.assertEqual(closeness(0, 40, 60), [20, 0])
        self.assertEqual(closeness(0, 80, 60), [20, 0])

    def test_length_error_outranks_divergences(self):
        # A same-length candidate beats a shorter one with fewer differing bytes.
        self.assertLess(closeness(40, 60, 60), closeness(8, 8, 60))


class EvalPinTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def write(self, text: str) -> Path:
        path = self.tmp / "toolchain.json"
        path.write_text(text)
        return path

    def test_deterministic(self):
        path = self.write('{"clang": "clang"}')
        self.assertEqual(eval_pin(path), eval_pin(path))

    def test_changes_with_toolchain_content(self):
        self.assertNotEqual(eval_pin(self.write("a")), eval_pin(self.write("b")))

    def test_depends_on_metric_definition(self):
        self.assertIn("closeness", METRIC)

    def test_missing_toolchain_raises_value_error(self):
        with self.assertRaises(ValueError):
            eval_pin(self.tmp / "missing.json")


class KeyTests(unittest.TestCase):
    def test_key(self):
        self.assertEqual(key("main", "601a72e4"), "main:601a72e4")


class UpsertTests(unittest.TestCase):
    PIN = "pin-a"

    def test_new_record_is_stored(self):
        bank, result = upsert(empty_bank(), "main", "a", [3, 1], self.PIN)
        self.assertTrue(result["updated"])
        self.assertEqual(result["reason"], "new")
        rec = best(bank, "main", "a", self.PIN)
        assert rec is not None
        self.assertEqual(rec["closeness"], [3, 1])

    def test_improvement_replaces(self):
        bank, _ = upsert(empty_bank(), "main", "a", [5, 2], self.PIN)
        bank, result = upsert(bank, "main", "a", [3, 0], self.PIN)
        self.assertTrue(result["updated"])
        self.assertEqual(result["reason"], "improved")
        rec = best(bank, "main", "a", self.PIN)
        assert rec is not None
        self.assertEqual(rec["closeness"], [3, 0])

    def test_equal_or_worse_is_kept(self):
        bank, _ = upsert(empty_bank(), "main", "a", [3, 0], self.PIN)
        bank, result = upsert(bank, "main", "a", [3, 0], self.PIN)   # equal
        self.assertFalse(result["updated"])
        bank, result = upsert(bank, "main", "a", [4, 0], self.PIN)   # worse
        self.assertFalse(result["updated"])
        self.assertEqual(result["reason"], "not-improved")
        rec = best(bank, "main", "a", self.PIN)
        assert rec is not None
        self.assertEqual(rec["closeness"], [3, 0])

    def test_different_pin_is_not_comparable_and_warns(self):
        bank, _ = upsert(empty_bank(), "main", "a", [1, 0], "pin-a")
        self.assertIsNone(best(bank, "main", "a", "pin-b"))  # incomparable
        bank, result = upsert(bank, "main", "a", [9, 9], "pin-b")
        self.assertTrue(result["updated"])
        self.assertEqual(result["reason"], "re-pinned")
        self.assertIn("pin changed", result["warn"])

    def test_extra_fields_are_stored(self):
        bank, _ = upsert(empty_bank(), "main", "a", [3, 0], self.PIN, name="func_a",
                         attempt_id=7)
        rec = best(bank, "main", "a", self.PIN)
        assert rec is not None
        self.assertEqual((rec["name"], rec["attempt_id"]), ("func_a", 7))


class BankIoTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "bank.json"

    def tearDown(self):
        self._dir.cleanup()

    def test_missing_bank_is_empty(self):
        self.assertEqual(load_bank(self.path), {"metric": METRIC, "records": {}})

    def test_corrupt_bank_raises_value_error(self):
        self.path.write_text("{not json")
        with self.assertRaises(ValueError):
            load_bank(self.path)

    def test_cli_exits_nonzero_on_a_corrupt_bank(self):
        self.path.write_text("bad")
        self.assertEqual(main(["--bank", str(self.path)]), 2)

    def test_save_load_round_trip(self):
        bank, _ = upsert(empty_bank(), "main", "a", [2, 1], "p")
        save_bank(self.path, bank)
        self.assertEqual(load_bank(self.path), bank)

    def test_save_is_deterministic(self):
        bank, _ = upsert(empty_bank(), "main", "a", [2, 1], "p")
        save_bank(self.path, bank)
        first = self.path.read_text()
        save_bank(self.path, bank)
        self.assertEqual(self.path.read_text(), first)

    def test_record_persists_only_improvements(self):
        record(self.path, "main", "a", [3, 0], "p")
        rec = best(load_bank(self.path), "main", "a", "p")
        assert rec is not None
        self.assertEqual(rec["closeness"], [3, 0])
        result = record(self.path, "main", "a", [4, 0], "p")
        self.assertFalse(result["updated"])
        rec = best(load_bank(self.path), "main", "a", "p")
        assert rec is not None
        self.assertEqual(rec["closeness"], [3, 0])

    def test_record_warns_on_pin_change(self):
        record(self.path, "main", "a", [1, 0], "p1")
        result = record(self.path, "main", "a", [2, 0], "p2")
        self.assertTrue(result["updated"])
        self.assertIn("pin changed", result["warn"])

    def test_record_resets_on_metric_change(self):
        save_bank(self.path, {"metric": "old/v0", "records": {"main:a": {"closeness": [1, 0]}}})
        record(self.path, "main", "a", [5, 5], "p")
        self.assertEqual(load_bank(self.path)["metric"], METRIC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
