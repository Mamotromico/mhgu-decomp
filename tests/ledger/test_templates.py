"""Tests for the trivial-shape templates: recognition and rendering, pure and offline.

Pure-function tests only — no ledger, no filesystem, no binary, no clang. The gate is what
ultimately verifies a template; here we only pin the deterministic bytes -> source mapping.

    python3 tests/ledger/test_templates.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from templates import propose, propose_rule

BX_LR = 0xE12FFF1E


def word(value: int) -> bytes:
    return struct.pack("<I", value)


def body(*values: int) -> bytes:
    return b"".join(word(v) for v in values)


class VoidTemplateTests(unittest.TestCase):
    def test_bx_lr_renders_an_empty_function(self):
        self.assertEqual(
            propose(body(BX_LR), "func_60001534"),
            'extern "C" void func_60001534(void);\n'
            'extern "C" void func_60001534(void) {}\n')

    def test_non_identifier_symbol_uses_an_asm_binding(self):
        self.assertEqual(
            propose(body(BX_LR), "weird.name"),
            'extern "C" void reconstructed(void) asm("weird.name");\n'
            'extern "C" void reconstructed(void) {}\n')

    def test_a_two_instruction_body_is_not_void(self):
        self.assertIsNone(propose(body(BX_LR, BX_LR), "f"))


class ReturnConstTemplateTests(unittest.TestCase):
    def test_return_zero(self):
        self.assertEqual(
            propose(body(0xE3A00000, BX_LR), "func_6004a820"),  # mov r0, #0; bx lr
            'extern "C" int func_6004a820(void);\n'
            'extern "C" int func_6004a820(void) { return 0; }\n')

    def test_return_small_immediate(self):
        self.assertIn("return 5;", propose(body(0xE3A00005, BX_LR), "f"))

    def test_rotated_immediate_is_decoded(self):
        # mov r0, #0x100  ==  imm8=1 rotated right by 24  ==  imm12 0xC01
        self.assertIn("return 256;", propose(body(0xE3A00C01, BX_LR), "f"))

    def test_high_bit_renders_as_signed_int_literal(self):
        # mov r0, #0xFF000000 (imm8=0xFF, rotate 8) -> -16777216
        self.assertIn("return -16777216;", propose(body(0xE3A004FF, BX_LR), "f"))


class ReturnNotConstTemplateTests(unittest.TestCase):
    def test_mvn_zero_is_minus_one(self):
        self.assertEqual(
            propose(body(0xE3E00000, BX_LR), "f"),  # mvn r0, #0; bx lr
            'extern "C" int f(void);\n'
            'extern "C" int f(void) { return -1; }\n')


class MissTests(unittest.TestCase):
    def test_none_and_empty_body(self):
        self.assertIsNone(propose(None, "f"))
        self.assertIsNone(propose(b"", "f"))

    def test_plain_instruction_is_not_templated(self):
        self.assertIsNone(propose(body(0xE1A00000, BX_LR), "f"))  # mov r0,r0; bx lr

    def test_unrecognized_single_instruction(self):
        self.assertIsNone(propose(body(0xE1A00000), "f"))


class GetterSetterTemplateTests(unittest.TestCase):
    def test_word_getter_with_offset(self):
        # ldr r0, [r0, #0x10]; bx lr
        self.assertEqual(
            propose(body(0xE5900010, BX_LR), "g"),
            'extern "C" int g(char *p);\n'
            'extern "C" int g(char *p) { return *(int *)(p + 16); }\n')

    def test_byte_getter(self):
        # ldrb r0, [r0, #4]; bx lr
        self.assertEqual(
            propose(body(0xE5D00004, BX_LR), "g"),
            'extern "C" int g(unsigned char *p);\n'
            'extern "C" int g(unsigned char *p) { return p[4]; }\n')

    def test_word_setter(self):
        # str r1, [r0, #8]; bx lr
        self.assertEqual(
            propose(body(0xE5801008, BX_LR), "g"),
            'extern "C" void g(char *p, int v);\n'
            'extern "C" void g(char *p, int v) { *(int *)(p + 8) = v; }\n')

    def test_byte_setter(self):
        # strb r1, [r0]; bx lr
        self.assertEqual(
            propose(body(0xE5C01000, BX_LR), "g"),
            'extern "C" void g(unsigned char *p, unsigned char v);\n'
            'extern "C" void g(unsigned char *p, unsigned char v) { p[0] = v; }\n')

    def test_ldr_from_a_register_is_not_a_pc_pool(self):
        # ldr r0, [r1]; bx lr -- base register is not r0, not this shape.
        self.assertIsNone(propose(body(0xE5910000, BX_LR), "f"))


class ExpansionTemplateTests(unittest.TestCase):
    """The parameterized rules added from the shape report (all gate-verified)."""

    def test_add_const(self):
        # add r0, r0, #0x68; bx lr
        self.assertEqual(
            propose(body(0xE2800068, BX_LR), "f"),
            'extern "C" int f(int x);\n'
            'extern "C" int f(int x) { return x + 104; }\n')

    def test_add_register_is_not_add_const(self):
        # add r0, r0, r1; bx lr -- register form, not an immediate add.
        self.assertIsNone(propose(body(0xE0800001, BX_LR), "f"))

    def test_half_getter(self):
        # ldrh r0, [r0, #0x9c]; bx lr
        self.assertEqual(
            propose(body(0xE1D009BC, BX_LR), "g"),
            'extern "C" int g(char *p);\n'
            'extern "C" int g(char *p) { return *(unsigned short *)(p + 156); }\n')

    def test_sbyte_getter(self):
        # ldrsb r0, [r0, #3]; bx lr
        self.assertEqual(
            propose(body(0xE1D000D3, BX_LR), "g"),
            'extern "C" int g(char *p);\n'
            'extern "C" int g(char *p) { return *(signed char *)(p + 3); }\n')

    def test_negative_halfword_offset_is_not_matched(self):
        # ldrh r0, [r0, #-4] (U=0): the rules assume U=1, so this falls through safely.
        self.assertIsNone(propose(body(0xE15000B4, BX_LR), "f"))

    def test_store_const_word(self):
        # mov r1, #0; str r1, [r0, #4]; bx lr
        self.assertEqual(
            propose(body(0xE3A01000, 0xE5801004, BX_LR), "s"),
            'extern "C" void s(char *p);\n'
            'extern "C" void s(char *p) { *(int *)(p + 4) = 0; }\n')

    def test_store_const_byte(self):
        # mov r1, #0; strb r1, [r0, #0x68]; bx lr
        self.assertEqual(
            propose(body(0xE3A01000, 0xE5C01068, BX_LR), "s"),
            'extern "C" void s(unsigned char *p);\n'
            'extern "C" void s(unsigned char *p) { p[104] = 0; }\n')

    def test_far_word_getter(self):
        # movw r1, #0x1428; ldr r0, [r0, r1]; bx lr
        self.assertEqual(
            propose(body(0xE3011428, 0xE7900001, BX_LR), "g"),
            'extern "C" int g(char *p);\n'
            'extern "C" int g(char *p) { return *(int *)(p + 5160); }\n')

    def test_far_byte_getter(self):
        # movw r1, #0x1500; ldrb r0, [r0, r1]; bx lr
        self.assertEqual(
            propose(body(0xE3011500, 0xE7D00001, BX_LR), "g"),
            'extern "C" int g(unsigned char *p);\n'
            'extern "C" int g(unsigned char *p) { return p[5376]; }\n')


class ProposeRuleTests(unittest.TestCase):
    """The matched rule is reported by 1-based position and name (the driver's `rule #N`)."""

    def _rule(self, b: bytes) -> tuple[int, str, str]:
        hit = propose_rule(b, "f")
        assert hit is not None
        return hit

    def test_void_return_is_rule_1(self):
        self.assertEqual(self._rule(body(BX_LR))[:2], (1, "void-return"))

    def test_return_const_is_rule_2(self):
        self.assertEqual(self._rule(body(0xE3A00000, BX_LR))[:2], (2, "return-const"))

    def test_add_const_is_rule_8(self):
        self.assertEqual(self._rule(body(0xE2800068, BX_LR))[:2], (8, "add-const"))

    def test_store_const_byte_is_rule_12(self):
        self.assertEqual(self._rule(body(0xE3A01000, 0xE5C01068, BX_LR))[:2],
                         (12, "store-const-byte"))

    def test_far_byte_getter_is_rule_14(self):
        self.assertEqual(self._rule(body(0xE3011500, 0xE7D00001, BX_LR))[:2],
                         (14, "far-byte-getter"))

    def test_source_matches_propose(self):
        b = body(0xE2800068, BX_LR)
        self.assertEqual(self._rule(b)[2], propose(b, "f"))

    def test_unrecognized_body_has_no_rule(self):
        self.assertIsNone(propose_rule(body(0xE1A00000, BX_LR), "f"))
        self.assertIsNone(propose_rule(None, "f"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
