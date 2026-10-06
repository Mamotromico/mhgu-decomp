"""Tests for the resync aligner: the gallop match length and small align sequences.

    python3 tests/nso/test_text_align.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "nso"))

from text_align import align, match_len

WINDOW = 1 << 16


class MatchLenTests(unittest.TestCase):
    def test_full_match_spanning_a_step_boundary(self):
        # Regression: a final truncated window used to overshoot n (256 for 200 bytes).
        data = b"a" * 200
        self.assertEqual(match_len(data, data, 0, 0), 200)

    def test_common_prefix_of_the_shorter(self):
        self.assertEqual(match_len(b"a" * 100, b"a" * 200, 0, 0), 100)

    def test_no_match(self):
        self.assertEqual(match_len(b"abc", b"xyz", 0, 0), 0)

    def test_respecting_the_start_offset(self):
        self.assertEqual(match_len(b"xxABC", b"yyABC", 2, 2), 3)


class AlignTests(unittest.TestCase):
    def events(self, a: bytes, b: bytes, min_match: int = 1) -> list[tuple[str, int]]:
        return [(e["type"], e["len"]) for e in align(a, b, min_match, WINDOW)]

    def test_identical_has_no_events(self):
        data = b"a" * 200
        self.assertEqual(align(data, data, 32, WINDOW), [])

    def test_insertion(self):
        self.assertEqual(self.events(b"ABCDEFGH", b"ABCDXXEFGH"), [("insert", 2)])

    def test_deletion(self):
        self.assertEqual(self.events(b"ABCDXXEFGH", b"ABCDEFGH"), [("delete", 2)])

    def test_substitution_in_place(self):
        events = align(b"ABCDEFGH", b"ABCDXFGH", 1, WINDOW)
        self.assertEqual(events, [{"type": "substitute", "a": 4, "b": 4, "len": 1}])

    def test_common_prefix_is_one_insertion(self):
        self.assertEqual(self.events(b"a" * 100, b"a" * 200), [("insert", 100)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
