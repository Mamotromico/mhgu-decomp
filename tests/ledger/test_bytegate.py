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

from bytegate import compare_body, gate_result, should_color


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


class GateResultTests(unittest.TestCase):
    """The machine-readable result the near-miss bank consumes."""

    def result(self, cand, ref, ok=True, status="match", body=60, partition=1368):
        return gate_result("main", "601a72e4", "func_601a72e4", cand, ref, ok, status,
                           body, partition, has_reloc=False)

    def test_exact_match_has_no_divergences(self):
        r = self.result(b"abcd", b"abcd")
        self.assertEqual((r["diff_count"], r["first_diff"]), (0, None))
        self.assertEqual((r["cand_len"], r["ref_len"]), (4, 4))
        self.assertEqual(r["partition"], 1368)

    def test_counts_divergences_and_first_offset(self):
        r = self.result(b"abXdYf", b"abcccf")
        self.assertEqual(r["diff_count"], 3)
        self.assertEqual(r["first_diff"], 2)

    def test_span_is_the_shorter_length(self):
        r = self.result(b"abcd", b"abcdef")
        self.assertEqual(r["diff_count"], 0)
        self.assertEqual((r["cand_len"], r["ref_len"]), (4, 6))

    def test_carries_status_and_identity(self):
        r = self.result(b"abcd", b"abce", ok=False, status="mismatch")
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "mismatch")
        self.assertEqual(r["name"], "func_601a72e4")


class ShouldColorTests(unittest.TestCase):
    """Colour is suppressed for --no-color, NO_COLOR, or non-TTY output."""

    class Stream:
        def __init__(self, tty: bool):
            self._tty = tty

        def isatty(self) -> bool:
            return self._tty

    def test_tty_without_overrides_colours(self):
        self.assertTrue(should_color(False, self.Stream(True), {}))

    def test_no_color_flag_wins(self):
        self.assertFalse(should_color(True, self.Stream(True), {}))

    def test_no_color_env_wins(self):
        self.assertFalse(should_color(False, self.Stream(True), {"NO_COLOR": "1"}))

    def test_non_tty_is_plain(self):
        self.assertFalse(should_color(False, self.Stream(False), {}))

    def test_stream_without_isatty_is_plain(self):
        self.assertFalse(should_color(False, object(), {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
