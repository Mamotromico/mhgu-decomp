"""Tests for the attempt log: ids, parent links, candidate blobs, containment. Run with::

    python3 tests/loop/test_attempts.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from attempts import (
    AttemptError,
    append,
    candidate_relpath,
    latest_for,
    next_id,
    parent_for,
    read_attempts,
    safe_component,
)


class SafeComponentTests(unittest.TestCase):
    def test_accepts_a_normal_component(self):
        self.assertEqual(safe_component("func_601a72e4"), "func_601a72e4")

    def test_rejects_traversal_and_separators(self):
        for bad in ("a/b", "a\\b", "..", ".", ""):
            with self.assertRaises(AttemptError):
                safe_component(bad)


class CandidateRelpathTests(unittest.TestCase):
    def test_layout(self):
        self.assertEqual(candidate_relpath("main", "601a72e4", 3),
                         Path("main/601a72e4/003.cpp"))


class RecordMathTests(unittest.TestCase):
    def test_next_id_on_empty_and_filled(self):
        self.assertEqual(next_id([]), 1)
        self.assertEqual(next_id([{"id": 1}, {"id": 4}, {"id": 2}]), 5)

    def test_parent_is_the_last_matching_attempt(self):
        records = [{"id": 1, "module": "main", "addr": "a"},
                   {"id": 2, "module": "main", "addr": "b"},
                   {"id": 3, "module": "main", "addr": "a"}]
        self.assertEqual(parent_for(records, "main", "a"), 3)
        self.assertIsNone(parent_for(records, "main", "c"))


class AppendTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_first_attempt_has_no_parent_and_writes_blob(self):
        rec = append(self.store, {"module": "main", "addr": "601a72e4", "outcome": "mismatch"},
                     candidate_text="int f(){}", now="2020-01-01T00:00:00+00:00")
        self.assertEqual(rec["id"], 1)
        self.assertIsNone(rec["parent"])
        self.assertEqual(rec["timestamp"], "2020-01-01T00:00:00+00:00")
        self.assertEqual(rec["candidate"], "main/601a72e4/001.cpp")
        self.assertEqual((self.store / rec["candidate"]).read_text(), "int f(){}")

    def test_second_attempt_links_to_the_first(self):
        append(self.store, {"module": "main", "addr": "601a72e4"})
        second = append(self.store, {"module": "main", "addr": "601a72e4"})
        self.assertEqual(second["id"], 2)
        self.assertEqual(second["parent"], 1)

    def test_different_entry_starts_a_new_tree(self):
        append(self.store, {"module": "main", "addr": "601a72e4"})
        other = append(self.store, {"module": "main", "addr": "60000f8c"})
        self.assertEqual(other["id"], 2)
        self.assertIsNone(other["parent"])

    def test_explicit_parent_is_respected(self):
        rec = append(self.store, {"module": "main", "addr": "601a72e4", "parent": 99})
        self.assertEqual(rec["parent"], 99)

    def test_log_is_append_only_and_readable(self):
        append(self.store, {"module": "main", "addr": "601a72e4"})
        append(self.store, {"module": "main", "addr": "601a72e4"})
        records = read_attempts(self.store / "log.jsonl")
        self.assertEqual([r["id"] for r in records], [1, 2])

    def test_missing_log_reads_empty(self):
        self.assertEqual(read_attempts(self.store / "nope.jsonl"), [])

    def test_latest_for(self):
        append(self.store, {"module": "main", "addr": "601a72e4"})
        append(self.store, {"module": "main", "addr": "601a72e4"})
        found = latest_for(self.store / "log.jsonl", "main", "601a72e4")
        assert found is not None
        self.assertEqual(found["id"], 2)
        self.assertIsNone(latest_for(self.store / "log.jsonl", "main", "60000f8c"))

    def test_unsafe_ledger_component_is_refused(self):
        with self.assertRaises(AttemptError):
            append(self.store, {"module": "main", "addr": "../evil"}, candidate_text="x")


if __name__ == "__main__":
    unittest.main(verbosity=2)
