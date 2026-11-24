"""Tests for the benchmark: cohort feature detection, stratified sampling, the
dev/holdout split, and the digest/round-trip. All synthetic — no ROM, no Ghidra. Run with::

    python3 tests/loop/test_benchmark.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import benchmark
from benchmark import (
    COHORT_ORDER,
    assign_split,
    build_document,
    cohorts_for,
    document_digest,
    has_conditional_branch,
    has_fp_neon,
    has_preindexed_writeback,
    load_document,
    save_document,
    size_bucket,
    stratified_sample,
    verify_document,
)


def w(word: int) -> bytes:
    return word.to_bytes(4, "little")


def body(*words: int) -> bytes:
    return b"".join(w(x) for x in words)


# Common A32 words (cond=E unless noted).
MOV_R0_1 = 0xE3A00001          # mov r0, #1
BX_LR = 0xE12FFF1E             # bx lr
ADR_R0 = 0xE28F0000            # add r0, pc, #0 (jump-table suspect: not gateable)


def bl(imm24: int) -> int:
    return 0xEB000000 | (imm24 & 0xFFFFFF)


def ldr_pc(rd: int, imm: int = 0) -> int:
    return 0xE59F0000 | (rd << 12) | imm


def entry(addr: str, kind: str = "function", verify: str = "none",
          size: int = 16) -> dict:
    return {"module": "main", "addr": addr, "name": f"func_{addr}", "kind": kind,
            "verify": verify, "size": str(size)}


class SizeBucketTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(size_bucket(4), "<=16B")
        self.assertEqual(size_bucket(16), "<=16B")
        self.assertEqual(size_bucket(20), "17-32B")
        self.assertEqual(size_bucket(32), "17-32B")
        self.assertEqual(size_bucket(64), "33-64B")
        self.assertEqual(size_bucket(68), ">64B")


class FeatureTests(unittest.TestCase):
    def test_a_plain_leaf(self):
        tags = cohorts_for(entry("60000000"), body(MOV_R0_1, BX_LR), set())
        self.assertEqual(tags, ["<=16B", "leaf"])

    def test_a_call_is_not_a_leaf(self):
        self.assertIn("calls", cohorts_for(entry("60000000"), body(bl(0), BX_LR), set()))

    def test_a_pool_load_is_tagged(self):
        self.assertIn("pool", cohorts_for(entry("60000000"), body(ldr_pc(0), BX_LR), set()))

    def test_a_preindexed_writeback_is_detected(self):
        # str r1, [r0, #0x18]!  (P=1, W=1)
        self.assertTrue(has_preindexed_writeback(body(0xE5A01018)))
        # The same store without writeback is not.
        self.assertFalse(has_preindexed_writeback(body(0xE5801018)))
        # A post-indexed form (P=0) is not pre-indexed.
        self.assertFalse(has_preindexed_writeback(body(0xE4801018)))

    def test_vfp_neon_words_are_detected(self):
        # vldr s0, [r0] — coprocessor transfer class 110.
        self.assertTrue(has_fp_neon(body(0xED900A00)))
        # A NEON data-processing word (cond=1111).
        self.assertTrue(has_fp_neon(body(0xF4A00100)))
        self.assertFalse(has_fp_neon(body(MOV_R0_1, BX_LR)))

    def test_a_conditional_branch_is_control_flow(self):
        self.assertTrue(has_conditional_branch(body(0x1A000000)))   # bne
        self.assertFalse(has_conditional_branch(body(0xEA000000)))  # b (AL)

    def test_a_bl_to_an_import_stub_is_tagged(self):
        # BL at +0 from 0x60000010 with imm 0 targets 0x60000018 — a stub address.
        addr = "60000010"
        stub = {0x60000018}
        self.assertIn("import_call", cohorts_for(entry(addr), body(bl(0), BX_LR), stub))
        self.assertNotIn("import_call", cohorts_for(entry(addr), body(bl(4), BX_LR), stub))

    def test_a_conditional_return_is_the_known_hard_tag(self):
        self.assertIn("guard", cohorts_for(entry("60000000"), body(0x112FFF1E), set()))


class SampleTests(unittest.TestCase):
    def _candidates(self, spec: dict[str, list[str]]):
        return [{"module": "main", "addr": a, "name": f"func_{a}", "cohorts": tags}
                for a, tags in sorted(spec.items())]

    def test_every_cohort_is_covered_before_untagged_entries_repeat(self):
        # 40 plain 16B leaves and one fpneon entry: the round-robin must pick the fpneon
        # entry (a different address would not do — assert it is in the sample).
        spec = {f"{0x60000000 + i * 4:08x}": ["<=16B", "leaf"] for i in range(40)}
        spec["60001000"] = ["<=16B", "leaf", "fpneon"]
        picked = stratified_sample(self._candidates(spec), 10)
        self.assertIn("60001000", {c["addr"] for c in picked})
        self.assertEqual(len(picked), 10)

    def test_the_sample_is_deterministic(self):
        spec = {f"{0x60000000 + i * 4:08x}": ["<=16B", "leaf"] for i in range(30)}
        a = stratified_sample(self._candidates(spec), 12)
        b = stratified_sample(self._candidates(spec), 12)
        self.assertEqual([c["addr"] for c in a], [c["addr"] for c in b])

    def test_a_smaller_sample_is_a_prefix_of_the_larger(self):
        spec = {f"{0x60000000 + i * 4:08x}": ["<=16B", "leaf"] for i in range(30)}
        small = stratified_sample(self._candidates(spec), 8)
        large = stratified_sample(self._candidates(spec), 20)
        self.assertEqual([c["addr"] for c in small],
                         [c["addr"] for c in large][:len(small)])

    def test_more_than_eligible_selects_everything(self):
        spec = {f"{0x60000000 + i * 4:08x}": ["<=16B", "leaf"] for i in range(5)}
        self.assertEqual(len(stratified_sample(self._candidates(spec), 400)), 5)


class SplitTests(unittest.TestCase):
    def test_deterministic_and_partitioned(self):
        modules = [("main", f"{0x60000000 + i * 4:08x}") for i in range(200)]
        splits = {assign_split(m, a, "v1", 0.2) for m, a in modules}
        self.assertEqual(splits, {"dev", "holdout"})
        again = [assign_split(m, a, "v1", 0.2) for m, a in modules]
        first = [assign_split(m, a, "v1", 0.2) for m, a in modules]
        self.assertEqual(again, first)
        holdouts = sum(1 for m, a in modules if assign_split(m, a, "v1", 0.2) == "holdout")
        self.assertGreater(holdouts, 5)
        self.assertLess(holdouts, 80)

    def test_a_fraction_of_zero_is_all_dev(self):
        self.assertEqual(assign_split("main", "60000000", "v1", 0.0), "dev")


class DocumentTests(unittest.TestCase):
    INPUTS = {"ledger_sha256": "abc", "inventory_sha256": "def",
              "toolchain_sha256": "ghi", "eval_pin": "547b", "gate_version": "bytegate/v4",
              "nso": {"path": "/rom/main.nso", "size": 1, "mtime_ns": 2}}

    def _ledger(self):
        return [
            entry("60000000"),                                  # plain 8B leaf
            entry("60000008"),                                  # pool reader
            entry("60000010", verify="match"),                  # matched: excluded
            entry("60000018", kind="import-stub", size=12),     # stub: excluded
            entry("60000020", kind="external", size=0),         # external: excluded
            entry("60000028"),                                  # jump-table suspect (not gateable)
        ]

    def _text(self):
        bodies = {
            "60000000": body(MOV_R0_1, BX_LR),
            "60000008": body(ldr_pc(0), BX_LR),
            "60000028": body(ADR_R0, BX_LR),
        }
        blob = bytearray()
        for addr, b in sorted(bodies.items()):
            off = int(addr, 16) - 0x60000000
            blob[off:off + len(b)] = b
        return bytes(blob)

    def test_population_filters_and_counts(self):
        sizes = {a: 8 for a in ("60000000", "60000008", "60000028")}
        doc = build_document(name="t", entries=self._ledger(), text=self._text(),
                             sizes=sizes, inputs=dict(self.INPUTS), total=400,
                             holdout_fraction=0.2, salt="t", now="2026-11-24T00:00:00+00:00")
        self.assertTrue(verify_document(doc))
        addrs = {e["addr"] for e in doc["entries"]}
        self.assertEqual(addrs, {"60000000", "60000008"})   # gateable + unmatched only
        self.assertEqual(doc["counts"]["eligible"], 2)
        self.assertEqual(doc["counts"]["selected"], 2)
        self.assertEqual(doc["counts"]["dev"] + doc["counts"]["holdout"], 2)
        self.assertEqual(doc["counts"]["cohorts"]["pool"], 1)
        self.assertEqual(doc["counts"]["cohorts"]["leaf"], 2)   # neither body calls

    def test_the_digest_covers_the_content(self):
        sizes = {"60000000": 8, "60000008": 8, "60000028": 8}
        doc = build_document(name="t", entries=self._ledger(), text=self._text(),
                             sizes=sizes, inputs=dict(self.INPUTS), total=400,
                             holdout_fraction=0.2, salt="t", now="2026-11-24T00:00:00+00:00")
        self.assertTrue(verify_document(doc))
        doc["entries"][0]["split"] = "holdout"
        self.assertFalse(verify_document(doc))
        self.assertNotEqual(document_digest(doc), doc["digest"])

    def test_save_load_round_trip_and_corruption(self):
        sizes = {"60000000": 8, "60000008": 8, "60000028": 8}
        doc = build_document(name="t", entries=self._ledger(), text=self._text(),
                             sizes=sizes, inputs=dict(self.INPUTS), total=400,
                             holdout_fraction=0.2, salt="t", now="2026-11-24T00:00:00+00:00")
        with tempfile.TemporaryDirectory() as td:
            path = save_document(Path(td), doc)
            loaded = load_document(Path(td), "t")
            self.assertEqual(loaded["digest"], doc["digest"])
            broken = json.loads(path.read_text())
            broken["counts"]["selected"] = 99
            path.write_text(json.dumps(broken))
            with self.assertRaises(ValueError):
                load_document(Path(td), "t")

    def test_a_missing_benchmark_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                load_document(Path(td), "nope")


if __name__ == "__main__":
    unittest.main()
