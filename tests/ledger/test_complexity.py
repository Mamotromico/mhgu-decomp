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

from complexity import (
    BASE_ADDR,
    any_pool_reference,
    body_of,
    branches_out,
    has_adr,
    has_call,
    has_literal_pool,
    has_pool_load,
    is_call,
    load_blocks,
    make_key,
    score,
)


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
    def test_clean_sorts_before_pool_sorts_before_branch(self):
        clean = score(word(0xE1A00000), 4)   # mov r0, r0
        pool = score(word(0xE59F0010), 4)    # ldr r0, [pc, #0x10]
        branch = score(word(0xEB000000), 4)  # bl
        self.assertLess(clean, pool)
        self.assertLess(pool, branch)

    def test_smaller_sorts_before_larger_within_a_class(self):
        self.assertLess(score(word(0xE1A00000), 4),
                        score(word(0xE1A00000) * 3, 12))

    def test_unreadable_sorts_last(self):
        self.assertGreater(score(None, 4), score(word(0xEB000000), 4))

    def test_unreadable_uses_the_given_size(self):
        self.assertEqual(score(None, 384), (3, 384))

    def test_resolution_lifts_a_constant_pool_to_tier_0(self):
        # A pool load whose word is a plain constant: resolved clean -> tier 0.
        self.assertEqual(score(word(0xE59F0010), 4, resolve=lambda b: False), (0, 4))

    def test_resolution_drops_an_address_pool_to_tier_2(self):
        self.assertEqual(score(word(0xE59F0010), 4, resolve=lambda b: True), (2, 4))

    def test_adr_stays_a_suspect_at_tier_1_under_resolution(self):
        self.assertEqual(score(word(0xE28F0004), 4, resolve=lambda b: False), (1, 4))


class BranchesOutTests(unittest.TestCase):
    def test_bl_is_outbound(self):
        self.assertTrue(branches_out(word(0xEB000000)))

    def test_internal_branch_is_not_outbound(self):
        # b +8 lands on the third word of a 12-byte body -> stays inside.
        body = word(0xEA000000) + word(0xE1A00000) + word(0xE1A00000)
        self.assertFalse(branches_out(body))

    def test_forward_branch_past_the_end_is_outbound(self):
        body = word(0xEA000400) + word(0xE1A00000)
        self.assertTrue(branches_out(body))

    def test_backward_branch_before_the_start_is_outbound(self):
        body = word(0xEAFFFFFC) + word(0xE1A00000)
        self.assertTrue(branches_out(body))

    def test_call_free_internal_loop_is_not_outbound(self):
        body = word(0xE1A00000) + word(0xEAFFFFFD)  # b back into the body
        self.assertFalse(branches_out(body))


class LiteralPoolTests(unittest.TestCase):
    def test_ldr_from_pc_positive_is_a_pool_load(self):
        self.assertTrue(has_pool_load(word(0xE59F0010)))
        self.assertTrue(has_literal_pool(word(0xE59F0010)))

    def test_ldr_from_pc_negative_is_a_pool_load(self):
        self.assertTrue(has_pool_load(word(0xE51F0010)))

    def test_add_pc_is_an_adr_not_a_pool_load(self):
        self.assertTrue(has_adr(word(0xE28F0004)))
        self.assertFalse(has_pool_load(word(0xE28F0004)))
        self.assertTrue(has_literal_pool(word(0xE28F0004)))

    def test_ldr_from_a_register_is_neither(self):
        self.assertFalse(has_literal_pool(word(0xE5910004)))

    def test_mov_is_neither(self):
        self.assertFalse(has_literal_pool(word(0xE1A00000)))


class AnyPoolReferenceTests(unittest.TestCase):
    """``ldr rd,[pc,...]`` pool words are resolved (absolute *or* PC-relative) on the image."""

    def _text(self, literal: int) -> bytes:
        # 0x60000000: ldr r0,[pc,#0] -> pool word at 0x60000008; filler; the word itself.
        return word(0xE59F0000) + word(0xE1A00000) + word(literal)

    def _in(self, ranges):
        return lambda v: any(lo <= v < hi for lo, hi in ranges)

    def test_absolute_address_word_is_a_reference(self):
        text = self._text(0x6172F000)
        self.assertTrue(any_pool_reference(text[:4], "60000000", text,
                                           self._in([(0x6172F000, 0x61800000)])))

    def test_pc_relative_offset_word_is_a_reference(self):
        # The PIC GOT idiom: the word is an offset; pc + word lands in .data.
        text = self._text(0x0181C5E4)
        self.assertTrue(any_pool_reference(text[:4], "60000000", text,
                                           self._in([(0x6172F000, 0x61840000)])))

    def test_constant_word_is_not_a_reference(self):
        text = self._text(0x12345678)  # neither it nor pc + it is in the image
        self.assertFalse(any_pool_reference(text[:4], "60000000", text,
                                            self._in([(0x6172F000, 0x61800000)])))

    def test_negative_pc_offset_resolves(self):
        # Pool word at 0x60000000; ldr r0,[pc,#-0x10] at 0x60000008 -> resolves back to it.
        text = word(0x6172F000) + word(0xE1A00000) + word(0xE51F0010)
        self.assertTrue(any_pool_reference(text[8:12], "60000008", text,
                                           self._in([(0x60000000, 0x61800000)])))


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

    def test_orders_clean_small_first(self):
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

    def test_blocks_resolve_a_constant_pool_to_tier_0(self):
        text = word(0xE59F0000) + word(0xE1A00000) + word(0x12345678)
        key = make_key(text, {"60000000": 4}, [(0x6172F000, 0x61800000)])
        self.assertEqual(key({"addr": "60000000", "size": "4"}), (0, 4))

    def test_blocks_drop_an_address_pool_to_tier_2(self):
        text = word(0xE59F0000) + word(0xE1A00000) + word(0x6172F000)
        key = make_key(text, {"60000000": 4}, [(0x6172F000, 0x61800000)])
        self.assertEqual(key({"addr": "60000000", "size": "4"}), (2, 4))


class LoadBlocksTests(unittest.TestCase):
    def test_parses_hex_ranges(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "inventory.blocks.tsv"
            p.write_text("block\tclass\taddr\tsize\n"
                         ".text\tcontent\t60000000\t100\n"
                         ".bss\tcontent\t6184b000\t10\n")
            self.assertEqual(load_blocks(p),
                             [(0x60000000, 0x60000100), (0x6184B000, 0x6184B010)])

    def test_missing_file_is_empty(self):
        self.assertEqual(load_blocks(Path("/no/such/inventory.blocks.tsv")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
