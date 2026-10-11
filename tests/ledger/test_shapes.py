"""Tests for the A32 shape decoder: golden vectors, register normalization, conditions.

The vectors are **assembler-derived**: each word was emitted by the pinned clang
(``clang -target armv8a-none-eabi``) from the mnemonic in the comment, so a failure here means
the decoder disagrees with the real toolchain, not with a hand-guessed byte. The corpus
cross-check (a handful of functions disassembled by Ghidra) caught the condition-table bug
guarded by :class:`ConditionTests`.

Pure functions only — no ledger, no filesystem, no binary. Run with::

    python3 tests/ledger/test_shapes.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from shapes import decode, histogram, render_sig, signature


def word(value: int) -> bytes:
    return struct.pack("<I", value)


# (word, expected) pairs, each word assembled by the pinned clang from `expected`'s shape.
# Immediates and offsets are collapsed to '#'; registers are kept.
_VECTORS = [
    (0xE12FFF1E, "bx lr"),
    (0xE1A0F00E, "mov pc,lr"),
    (0xE1A00001, "mov r0,r1"),
    (0xE3A004FF, "mov r0,#"),
    (0xE3A00008, "mov r0,#"),
    (0xE3E00000, "mvn r0,#"),
    (0xE5900004, "ldr r0,[r0,#]"),
    (0xE5801008, "str r1,[r0,#]"),
    (0xE5D10002, "ldrb r0,[r1,#]"),
    (0xE5C32001, "strb r2,[r3,#]"),
    (0xE1D20BB0, "ldrh r0,[r2,#]"),
    (0xE19200B0, "ldrh r0,[r2,r0]"),
    (0xE1D100D3, "ldrsb r0,[r1,#]"),
    (0xE19100F2, "ldrsh r0,[r1,r2]"),
    (0xE92D4030, "push {r4,r5,lr}"),
    (0xE8BD8030, "pop {r4,r5,pc}"),
    (0xE3500000, "cmp r0,#"),
    (0xE1500001, "cmp r0,r1"),
    (0xE1300001, "teq r0,r1"),
    (0xE0800001, "add r0,r0,r1"),
    (0xE2900001, "adds r0,r0,#"),
    (0xE2400001, "sub r0,r0,#"),
    (0xE0010002, "and r0,r1,r2"),
    (0xE3800001, "orr r0,r0,#"),
    (0xE0200001, "eor r0,r0,r1"),
    (0xE0000291, "mul r0,r1,r2"),
    (0xE0203291, "mla r0,r1,r2,r3"),
    (0xE0810392, "umull r0,r1,r2,r3"),
    (0xE16F0F11, "clz r0,r1"),
    (0xE3010234, "movw r0,#"),
    (0xE3450678, "movt r0,#"),
    (0xE59F0004, "ldr r0,[pc,#]"),          # literal-pool load
    (0xE28F0004, "add r0,pc,#"),            # ADR
    (0xE1A00101, "mov r0,r1,lsl #"),
    (0xE1A00251, "mov r0,r1,asr r2"),
    (0xE7910102, "ldr r0,[r1,r2,lsl #]"),
    (0xE12FFF13, "bx r3"),
    (0xE12FFF33, "blx r3"),
]


class GoldenVectorTests(unittest.TestCase):
    def test_assembler_vectors(self):
        for w, want in _VECTORS:
            with self.subTest(word=f"{w:08X}"):
                self.assertEqual(decode(w), want)

    def test_lsl_zero_is_a_plain_move(self):
        self.assertEqual(decode(0xE1A00001), "mov r0,r1")   # mov r0, r1, lsl #0


class ConditionTests(unittest.TestCase):
    """The condition table must map each 4-bit code to one canonical mnemonic (CS==HS, CC==LO).

    A wrong table shifted every code after CC, so ``bxls`` decoded as ``bxvc`` — Ghidra's dump of
    a real function caught it. These pin the whole table through a single shape (bx).
    """

    def test_condition_suffixes(self):
        # cond in bits 31:28; bx lr = 0x?12FFF1E.
        cases = {0x00: "eq", 0x10: "ne", 0x20: "cs", 0x30: "cc", 0x40: "mi", 0x50: "pl",
                 0x60: "vs", 0x70: "vc", 0x80: "hi", 0x90: "ls", 0xA0: "ge", 0xB0: "lt",
                 0xC0: "gt", 0xD0: "le"}
        for high, suffix in cases.items():
            with self.subTest(cond=suffix):
                self.assertEqual(decode((0xE12FFF1E & 0x0FFFFFFF) | (high << 24)),
                                 f"bx{suffix} lr")

    def test_al_has_no_suffix(self):
        self.assertEqual(decode(0xE12FFF1E), "bx lr")

    def test_conditional_mov_keeps_both_suffixes(self):
        self.assertEqual(decode(0x03A00000), "moveq r0,#")
        self.assertEqual(decode(0x13A00000), "movne r0,#")


class SignatureTests(unittest.TestCase):
    def test_one_token_per_word(self):
        body = word(0xE3A00000) + word(0xE12FFF1E)
        self.assertEqual(signature(body), ("mov r0,#", "bx lr"))

    def test_trailing_partial_word_is_ignored(self):
        body = word(0xE12FFF1E) + b"\xaa\xbb"
        self.assertEqual(signature(body), ("bx lr",))

    def test_render_joins_with_semicolons(self):
        self.assertEqual(render_sig(("mov r0,#", "bx lr")), "mov r0,#; bx lr")


class HistogramTests(unittest.TestCase):
    def test_counts_exact_signatures(self):
        a = ("mov r0,#", "bx lr")
        b = ("bx lr",)
        counts = histogram([a, a, b])
        self.assertEqual(counts[a], 2)
        self.assertEqual(counts[b], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
