"""Tests for the fragment lint's A32 primitives (no image, no Ghidra).

Run::

    python3 tests/ledger/test_fragments.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from fragments import (branch_targets, classify, has_exit, is_prologue, pool_offsets,
                       writes_pc)


def words(*ws: int) -> bytes:
    return b"".join(w.to_bytes(4, "little") for w in ws)


class PrologueTests(unittest.TestCase):
    def test_push_is_a_prologue(self):
        self.assertTrue(is_prologue(0xE92D4FF0))       # push {r4-r9, sl, fp, lr}
        self.assertTrue(is_prologue(0xE92D4000))       # push {lr}

    def test_other_instructions_are_not(self):
        self.assertFalse(is_prologue(0xE3A01000))      # mov r1, #0
        self.assertFalse(is_prologue(0xE8BD8FF0))      # pop {…, pc}


class WritesPcTests(unittest.TestCase):
    def test_returns_write_pc(self):
        self.assertTrue(writes_pc(0xE12FFF1E))         # bx lr
        self.assertTrue(writes_pc(0xE8BD8FF0))         # pop {r4-r9, sl, fp, pc}
        self.assertTrue(writes_pc(0xE8BD8070))         # pop {r4, r5, r6, pc}
        self.assertTrue(writes_pc(0xE1A0F00E))         # mov pc, lr
        self.assertTrue(writes_pc(0xE59FF004))         # ldr pc, [pc, #4]

    def test_ordinary_instructions_do_not(self):
        self.assertFalse(writes_pc(0xE3A01000))        # mov r1, #0
        self.assertFalse(writes_pc(0xE1A00005))        # mov r0, r5
        self.assertFalse(writes_pc(0xEB000000))        # bl (a call, not a return)

    def test_condition_never_is_not_an_instruction(self):
        self.assertFalse(writes_pc(0xF12FFF1E))


class PoolOffsetTests(unittest.TestCase):
    def test_pc_relative_load_targets_a_pool_word(self):
        self.assertEqual(pool_offsets(words(0xE59F0000, 0xEA000000, 0x2AEF0000)), {8})

    def test_out_of_range_literal_is_not_a_pool_word(self):
        self.assertEqual(pool_offsets(words(0xE59F0FFF, 0xEA000000)), set())


class HasExitTests(unittest.TestCase):
    def test_a_return_is_an_exit(self):
        self.assertTrue(has_exit(words(0xE3A01000, 0xE12FFF1E)))

    def test_a_tail_call_is_an_exit(self):
        # pop {r4, lr}; b <far outside>  — the sibling-call epilogue
        self.assertTrue(has_exit(words(0xE8BD4010, 0xEA0003FF)))

    def test_a_noreturn_tail_is_an_exit(self):
        self.assertTrue(has_exit(words(0xE1A00004, 0xEB000000)))    # mov; bl (last code)

    def test_a_pool_word_does_not_hide_a_noreturn_tail(self):
        # ldr r0, [pc, #0]; bl <callee>; <pool word>
        self.assertTrue(has_exit(words(0xE59F0000, 0xEB000000, 0x2AEF0000)))

    def test_straight_line_code_with_no_exit_is_a_fragment(self):
        self.assertFalse(has_exit(words(0xE3A01000, 0xE3A02000)))   # mov; mov


class BranchTargetsTests(unittest.TestCase):
    def test_bl_and_b_targets_are_collected(self):
        text = words(0x00000000, 0xEB000000, 0xEA000000)   # pad; bl +0; b +0
        bl, b = branch_targets(text)
        self.assertEqual(bl, {0x6000000C})                 # 0x60000004 + 8
        self.assertEqual(b, {0x60000010})                  # 0x60000008 + 8


class ClassifyTests(unittest.TestCase):
    def _entry(self, addr: int, size: int) -> dict:
        return {"module": "main", "addr": f"{addr:08x}", "kind": "function", "block": ".text",
                "name": f"func_{addr:08x}", "size": str(size)}

    def test_a_fragment_with_no_exit_is_flagged(self):
        text = words(0xE3A01000, 0xE3A02000)                # mov; mov, no return
        entries = [self._entry(0x60000000, 8)]
        findings = classify(entries, text, bl_targets=set())
        self.assertEqual([f.reasons for f in findings], [["no-exit", "no-entry-signal"]])

    def test_a_real_leaf_with_a_return_and_a_bl_target_is_clean(self):
        text = words(0xE1A00000, 0xE12FFF1E)                # nop; bx lr
        entries = [self._entry(0x60000000, 8)]
        self.assertEqual(classify(entries, text, bl_targets={0x60000000}), [])


if __name__ == "__main__":
    unittest.main()
