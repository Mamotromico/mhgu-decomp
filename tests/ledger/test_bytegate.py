#!/usr/bin/env python3
"""Regression tests for the byte gate's comparison rule.

The rule this pins down is the fix for the partition-vs-body defect: the ledger's ``size``
is the block *partition* (bytes to the next cut point), which over-covers a function whose
trailing region was never cut (``func_601a72e4``/``new_b``: a 60 B body in a 1368 B
partition). ``compare_body`` compares the compiled body over its own length, treats the
partition as an upper bound, and exposes ``--body`` as an authoritative override.

Pure-function tests only — no clang, no Ghidra, no ledger, no binary. Run with::

    python3 tests/ledger/test_bytegate.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# The ledger tools are plain scripts (no package), so put their directory on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from bytegate import compare_body


class CompareBodyTests(unittest.TestCase):
    # A synthetic block; the "function" lives at offset 0x10. Bytes are arbitrary but
    # deterministic so a wrong slice is easy to spot.
    BLOCK = bytes((0xA0 + i) & 0xFF for i in range(0x1000))
    OFF = 0x10

    def original(self, n: int) -> bytes:
        return self.BLOCK[self.OFF:self.OFF + n]

    # --- the default rule: body length, partition as an upper bound -------------------

    def test_exact_body_filling_partition_matches(self):
        body = self.original(0x40)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 0x40, None)
        self.assertTrue(ok)
        self.assertEqual(ref, body)
        self.assertEqual(status, "match")

    def test_short_body_in_over_covering_partition_is_a_match(self):
        # new_b's shape: a 60 B body in a 1368 B partition.
        body = self.original(60)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, None)
        self.assertTrue(ok)
        self.assertEqual(ref, body)
        self.assertEqual(status, "short-body")

    def test_short_body_with_wrong_bytes_is_a_mismatch(self):
        body = bytearray(self.original(60))
        body[10] ^= 0xFF
        ok, ref, status = compare_body(bytes(body), self.BLOCK, self.OFF, 1368, None)
        self.assertFalse(ok)
        self.assertEqual(len(ref), 60)
        self.assertEqual(status, "mismatch")

    def test_candidate_longer_than_partition_is_too_long(self):
        body = self.original(200)
        ok, _ref, status = compare_body(body, self.BLOCK, self.OFF, 100, None)
        self.assertFalse(ok)
        self.assertEqual(status, "too-long")

    def test_empty_candidate_is_rejected(self):
        # The guard that stops a stub from matching by vacuous prefix equality.
        ok, ref, status = compare_body(b"", self.BLOCK, self.OFF, 1368, None)
        self.assertFalse(ok)
        self.assertEqual(ref, b"")
        self.assertEqual(status, "empty-body")

    # --- the authoritative --body override --------------------------------------------

    def test_body_override_exact_match(self):
        body = self.original(60)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, 60)
        self.assertTrue(ok)
        self.assertEqual(ref, body)
        self.assertEqual(status, "match")

    def test_body_override_rejects_a_truncated_body(self):
        # Under the default rule a 40 B prefix would pass; with --body it must not.
        body = self.original(40)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, 60)
        self.assertFalse(ok)
        self.assertEqual(len(ref), 60)
        self.assertEqual(status, "body-length")

    def test_body_override_wrong_bytes_is_a_mismatch(self):
        body = bytearray(self.original(60))
        body[0] ^= 0xFF
        ok, _ref, status = compare_body(bytes(body), self.BLOCK, self.OFF, 1368, 60)
        self.assertFalse(ok)
        self.assertEqual(status, "mismatch")


if __name__ == "__main__":
    unittest.main(verbosity=2)
