"""Tests for the attempt log: ids, parent links, candidate blobs, containment, and the
incremental index (indexed answers must equal full-scan answers; stale/corrupt/truncated
state must self-heal). Run with::

    python3 tests/loop/test_attempts.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

import attempts
from attempts import (
    INDEX_VERSION,
    AttemptError,
    append,
    attempt_counts,
    build_index,
    candidate_relpath,
    latest_for,
    load_index,
    main,
    next_id,
    parent_for,
    read_attempts,
    record_at,
    records_by_id,
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


class CorruptLogTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_read_reports_a_corrupt_line(self):
        (self.store / "log.jsonl").write_text('{"id": 1}\nnot json\n')
        with self.assertRaises(AttemptError) as ctx:
            read_attempts(self.store / "log.jsonl")
        self.assertIn("corrupt attempt log", str(ctx.exception))

    def test_cli_exits_nonzero_on_a_corrupt_log(self):
        (self.store / "log.jsonl").write_text("nonsense\n")
        self.assertEqual(main(["--store", str(self.store)]), 2)

    def test_append_requires_module_and_addr(self):
        with self.assertRaises(AttemptError):
            append(self.store, {})


class IndexEquivalenceTests(unittest.TestCase):
    """The index is a cache: every answer it gives must equal a full scan of the log."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def seed(self) -> list[dict]:
        for addr, outcomes in [("aaaa0001", ["mismatch", "error", "mismatch"]),
                               ("aaaa0002", ["match"]),
                               ("aaaa0003", [])]:
            for outcome in outcomes:
                append(self.store, {"module": "main", "addr": addr, "outcome": outcome})
        # Same addr under another module — keys must stay distinct.
        append(self.store, {"module": "other", "addr": "aaaa0001"})
        return read_attempts(self.store / "log.jsonl")

    def test_counts_match_full_scan(self):
        records = self.seed()
        expected: dict[tuple[str, str], int] = {}
        for r in records:
            key = (r["module"], r["addr"])
            expected[key] = expected.get(key, 0) + 1
        self.assertEqual(attempt_counts(self.store), expected)

    def test_latest_for_matches_reverse_scan_for_every_entry(self):
        records = self.seed()
        expected: dict[tuple[str, str], dict] = {}
        for r in reversed(records):
            expected.setdefault((r["module"], r["addr"]), r)
        for key, record in expected.items():
            self.assertEqual(latest_for(self.store / "log.jsonl", *key), record)
        self.assertIsNone(latest_for(self.store / "log.jsonl", "main", "aaaa0009"))

    def test_records_by_id_matches_scan_and_omits_unknown_ids(self):
        records = self.seed()
        by_id = records_by_id(self.store, [r["id"] for r in records])
        self.assertEqual(by_id, {r["id"]: r for r in records})
        self.assertEqual(records_by_id(self.store, [9999]), {})
        self.assertEqual(records_by_id(self.store, [None, 1, None])[1], records[0])

    def test_next_id_and_parent_still_agree_with_a_scan_after_a_rebuild(self):
        self.seed()
        (self.store / "index.json").unlink()               # force the slow path
        records = read_attempts(self.store / "log.jsonl")
        added = append(self.store, {"module": "main", "addr": "aaaa0001"})
        self.assertEqual(added["id"], next_id(records))
        self.assertEqual(added["parent"], parent_for(records, "main", "aaaa0001"))

    def test_a_from_scratch_build_matches_incremental_appends(self):
        self.seed()
        built = build_index(self.store / "log.jsonl")
        saved = json.loads((self.store / "index.json").read_text())
        for key in ("next_id", "entries", "id_offsets", "log"):
            self.assertEqual(built[key], saved[key], key)


class IndexHealingTests(unittest.TestCase):
    """Stale fingerprint, corrupt sidecar, external growth, truncation — the index must
    detect each and rebuild from the log, never serve a stale answer."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Path(self._dir.name)
        self.log = self.store / "log.jsonl"
        attempts._CACHE.clear()      # exercise the on-disk index paths, not the cache

    def tearDown(self):
        self._dir.cleanup()

    def test_a_missing_index_is_built_and_saved(self):
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        (self.store / "index.json").unlink()
        attempts._CACHE.clear()          # model a fresh process; the warm cache is valid
        index = load_index(self.store)
        self.assertEqual(index["next_id"], 3)
        self.assertTrue((self.store / "index.json").exists())
        self.assertEqual(latest_for(self.log, "main", "aaaa0001")["id"], 2)

    def test_a_corrupt_index_rebuilds(self):
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        (self.store / "index.json").write_text("{ not json")
        self.assertEqual(latest_for(self.log, "main", "aaaa0001")["id"], 1)

    def test_a_version_mismatch_rebuilds(self):
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        idx_path = self.store / "index.json"
        payload = json.loads(idx_path.read_text())
        payload["version"] = INDEX_VERSION + 1
        idx_path.write_text(json.dumps(payload))
        attempts._CACHE.clear()          # model a fresh process seeing the bumped file
        self.assertEqual(latest_for(self.log, "main", "aaaa0001")["id"], 1)
        self.assertEqual(json.loads(idx_path.read_text())["version"], INDEX_VERSION)

    def test_an_externally_grown_log_invalidates_the_index(self):
        append(self.store, {"module": "main", "addr": "aaaa0001", "outcome": "mismatch"})
        with self.log.open("a") as fh:   # a writer that bypasses the index
            fh.write(json.dumps({"id": 2, "module": "main", "addr": "aaaa0001",
                                 "outcome": "match"}) + "\n")
        latest = latest_for(self.log, "main", "aaaa0001")
        self.assertEqual(latest["id"], 2)
        self.assertEqual(latest["outcome"], "match")
        self.assertEqual(attempt_counts(self.store)[("main", "aaaa0001")], 2)

    def test_a_truncated_log_invalidates_the_index(self):
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        self.log.write_text("")          # e.g. a disk-full close
        self.assertIsNone(latest_for(self.log, "main", "aaaa0001"))
        self.assertEqual(attempt_counts(self.store), {})

    def test_a_corrupt_log_line_raises_through_the_index_path(self):
        self.log.write_text('{"id": 1, "module": "main", "addr": "a"}\nnot json\n')
        with self.assertRaises(AttemptError):
            latest_for(self.log, "main", "a")
        with self.assertRaises(AttemptError):
            attempt_counts(self.store)

    def test_the_in_process_cache_serves_without_rereading_the_sidecar(self):
        append(self.store, {"module": "main", "addr": "aaaa0001", "outcome": "mismatch"})
        load_index(self.store)                        # warm the cache
        (self.store / "index.json").write_text("{ not json")   # sidecar dies…
        self.assertEqual(latest_for(self.log, "main", "aaaa0001")["id"], 1)  # …cache serves
        with self.log.open("a") as fh:                # but an external log change is noticed
            fh.write(json.dumps({"id": 2, "module": "main", "addr": "aaaa0001",
                                 "outcome": "match"}) + "\n")
        self.assertEqual(latest_for(self.log, "main", "aaaa0001")["id"], 2)


class IndexMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.store = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_append_maintains_every_index_field(self):
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        append(self.store, {"module": "main", "addr": "aaaa0001"})
        append(self.store, {"module": "main", "addr": "aaaa0002"})
        index = json.loads((self.store / "index.json").read_text())
        entry = index["entries"]["main/aaaa0001"]
        self.assertEqual((entry["count"], entry["last_id"]), (2, 2))
        self.assertEqual(index["entries"]["main/aaaa0002"]["count"], 1)
        self.assertEqual(index["next_id"], 4)
        self.assertEqual(index["log"]["lines"], 3)
        self.assertEqual(index["log"]["size"], (self.store / "log.jsonl").stat().st_size)
        self.assertEqual(index["log"]["mtime_ns"],
                         (self.store / "log.jsonl").stat().st_mtime_ns)

    def test_every_index_offset_round_trips_to_its_record(self):
        for i in range(5):
            append(self.store, {"module": "main", "addr": f"aaaa000{i % 2}"})
        records = read_attempts(self.store / "log.jsonl")
        index = json.loads((self.store / "index.json").read_text())
        self.assertEqual(len(index["id_offsets"]), len(records))
        for rid, offset in index["id_offsets"].items():
            self.assertEqual(record_at(self.store / "log.jsonl", offset)["id"], int(rid))
        with self.assertRaises(AttemptError):
            record_at(self.store / "log.jsonl", 10 ** 9)

    def test_no_tmp_files_are_left_after_appends(self):
        for _ in range(3):
            append(self.store, {"module": "main", "addr": "aaaa0001"})
        leftovers = [p.name for p in self.store.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
