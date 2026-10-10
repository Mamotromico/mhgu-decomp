"""Tests for the easy-first difficulty key: call detection, scoring, and the selector key.

Pure-function tests only — no ledger, no filesystem, no binary. Run with::

    python3 tests/ledger/test_complexity.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from complexity import BASE_ADDR, body_of, has_call, is_call, make_key, score


def word(value: int) -> bytes:
    return struct.pack("<I", value)


class IsCallTests(unittest.TestCase):
    def test_bl_unconditional_is_a_call(self):
        self.assertTrue(is_call(0xEB000000))

    def test_bl_conditional_is_a_call(self):
        self.assertTrue(is_call(0x0B000000))  # BL{cond=EQ}

    def test_plain_branch_is_not_a_call(self):
        self.assertFalse(is_call(0xEA000000))  # B, no link

    def test_blx_immediate_is_a_call(self):
        self.assertTrue(is_call(0xFA000000))
        self.assertTrue(is_call(0xFB000000))

    def test_blx_register_is_a_call(self):
        self.assertTrue(is_call(0xE12FFF30))  # blx r0

    def test_bx_lr_is_not_a_call(self):
        self.assertFalse(is_call(0xE12FFF1E))  # return

    def test_data_and_moves_are_not_calls(self):
        for w in (0x00000000, 0xE59F0000, 0xE1A00000, 0xE92D4800):
            self.assertFalse(is_call(w), hex(w))


class HasCallTests(unittest.TestCase):
    def test_finds_a_call_anywhere(self):
        body = word(0xE1A00000) + word(0xEB000010) + word(0xE12FFF1E)
        self.assertTrue(has_call(body))

    def test_call_free_body(self):
        body = word(0xE92D4800) + word(0xE1A00000) + word(0xE8BD8800)
        self.assertFalse(has_call(body))

    def test_empty_body_is_call_free(self):
        self.assertFalse(has_call(b""))


class ScoreTests(unittest.TestCase):
    def test_call_free_sorts_before_call(self):
        self.assertLess(score(word(0xE1A00000), 4), score(word(0xEB000000), 4))

    def test_smaller_sorts_before_larger_within_a_class(self):
        self.assertLess(score(word(0xE1A00000), 4),
                        score(word(0xE1A00000) * 3, 12))

    def test_unreadable_sorts_last(self):
        self.assertGreater(score(None, 4), score(word(0xEB000000), 4))

    def test_unreadable_uses_the_given_size(self):
        self.assertEqual(score(None, 384), (2, 384))


class BodyOfTests(unittest.TestCase):
    def test_slices_at_the_offset(self):
        text = b"AAAABBBB"
        self.assertEqual(body_of(text, f"{BASE_ADDR + 4:08x}", 4), b"BBBB")

    def test_out_of_range_is_none(self):
        self.assertIsNone(body_of(b"AAAA", f"{BASE_ADDR + 4:08x}", 4))
        self.assertIsNone(body_of(b"AAAA", "not-hex", 4))

    def test_non_positive_size_is_none(self):
        self.assertIsNone(body_of(b"AAAA", f"{BASE_ADDR:08x}", 0))


class MakeKeyTests(unittest.TestCase):
    def _text(self) -> bytes:
        # 0x00: call-free (4B); 0x04: call-free (8B); 0x0c: has a BL.
        return (word(0xE1A00000)
                + word(0xE1A00000) + word(0xE1A00000)
                + word(0xEB000000))

    def test_orders_call_free_small_first(self):
        text = self._text()
        sizes = {"60000000": 4, "60000004": 8, "6000000c": 4}
        key = make_key(text, sizes)
        entries = [{"addr": "6000000c", "size": "4"},
                   {"addr": "60000004", "size": "8"},
                   {"addr": "60000000", "size": "4"}]
        self.assertEqual([e["addr"] for e in sorted(entries, key=key)],
                         ["60000000", "60000004", "6000000c"])

    def test_missing_size_falls_back_to_ledger_partition(self):
        text = self._text()
        key = make_key(text, {})  # no inventory sizes
        self.assertEqual(key({"addr": "60000000", "size": "4"}), (0, 4))


if __name__ == "__main__":
    unittest.main(verbosity=2)
