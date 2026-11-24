"""Regression tests for the A32 decode helper (plan 3.1 aligned feedback).

The decoder shells out to devkitARM ``arm-none-eabi-objdump``; every test here is hermetic —
the runner is faked, or ``find_objdump``/``disassemble`` are patched — so no tool install is
needed. Run with::

    python3 tests/ledger/test_disasm.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path
from unittest import mock

# The ledger tools are plain scripts (no package), so put their directory on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import disasm


class _Proc:
    """A ``subprocess.CompletedProcess`` stand-in for the fake runner."""

    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


GNU_SAMPLE = """\
t.bin:     file format binary


Disassembly of section .data:

00000000 <.data>:
   0:	fe300a81 	vselgt.f32	s0, s1, s2
   4:	92800001 	addls	r0, r0, #1
   8:	0a000001 	beq	0x14
   c:	ed1f2a01 	vldr	s4, [pc, #-4]	@ 0x10
  10:	00000000 	andeq	r0, r0, r0
  14:	e12fff1e 	bx	lr
"""


class ClassifyTests(unittest.TestCase):
    def test_plain_and_conditional_branches(self):
        self.assertEqual(disasm.classify("b"), "br")
        self.assertEqual(disasm.classify("beq"), "cond-br")
        self.assertEqual(disasm.classify("bgt"), "cond-br")

    def test_ble_is_branch_le_bleq_is_conditional_call(self):
        # The bl+cond form must be checked before b+cond, or ``ble`` is misread.
        self.assertEqual(disasm.classify("ble"), "cond-br")
        self.assertEqual(disasm.classify("bleq"), "call")

    def test_calls(self):
        self.assertEqual(disasm.classify("bl"), "call")
        self.assertEqual(disasm.classify("blx"), "call")
        self.assertEqual(disasm.classify("blne"), "call")

    def test_cbz_cbnz_are_conditional(self):
        self.assertEqual(disasm.classify("cbz"), "cond-br")
        self.assertEqual(disasm.classify("cbnz"), "cond-br")

    def test_computational_mnemonics_are_not_control_flow(self):
        for m in ("add", "addls", "ldr", "vldr", "bx", "cmp", "push", "pop"):
            self.assertIsNone(disasm.classify(m), m)


class ParseObjdumpTests(unittest.TestCase):
    def test_only_body_lines_are_kept(self):
        out = disasm.parse_objdump(GNU_SAMPLE)
        self.assertEqual(out[0x0], "vselgt.f32 s0, s1, s2")
        self.assertEqual(out[0x4], "addls r0, r0, #1")
        self.assertEqual(out[0x14], "bx lr")

    def test_header_and_banner_lines_are_ignored(self):
        out = disasm.parse_objdump("t.bin:     file format binary\n"
                                   "Disassembly of section .data:\n")
        self.assertEqual(out, {})

    def test_operandless_instruction(self):
        out = disasm.parse_objdump("   0:	e1a00000 	nop\n")
        self.assertEqual(out[0], "nop")


class StructureTests(unittest.TestCase):
    LINES = {0x0: "vselgt.f32 s0, s1, s2", 0x4: "addls r0, r0, #1",
             0x8: "beq 0x14", 0xC: "vldr s4, [pc, #-4]	@ 0x10",
             0x10: "andeq r0, r0, r0"}

    def test_pool_word_is_excluded_from_the_counts(self):
        s = disasm.structure(self.LINES)
        self.assertEqual(s["insns"], 4)
        self.assertEqual(s["pool_words"], 1)
        self.assertEqual(s["pool_loads"], 1)
        self.assertEqual(s["cond_br"], 1)
        self.assertEqual(s["br"], 0)
        self.assertEqual(s["calls"], 0)
        self.assertEqual(s["branches"], ["+0x8  beq 0x14"])

    def test_pool_load_targets_beyond_the_body_are_not_pool_words(self):
        s = disasm.structure({0: "ldr r0, [pc, #1024]"})
        self.assertEqual(s["pool_words"], 0)
        self.assertEqual(s["pool_loads"], 1)

    def test_branch_list_is_capped_with_a_tail_marker(self):
        lines = {4 * i: "beq 0x100" for i in range(15)}
        s = disasm.structure(lines)
        self.assertEqual(s["cond_br"], 15)
        self.assertEqual(len(s["branches"]), disasm.BRANCH_LIST_LIMIT + 1)
        self.assertEqual(s["branches"][-1], "+3 more")


class DisassembleTests(unittest.TestCase):
    def test_runner_is_called_with_the_raw_binary_flags(self):
        seen = []

        def fake(argv, **kw):
            seen.append((argv, kw))
            return _Proc(GNU_SAMPLE)

        out = disasm.disassemble(struct.pack("<I", 0xE12FFF1E), exe="/fake/objdump",
                                 runner=fake)
        (argv, kw), = seen
        self.assertEqual(argv[1:], ["-b", "binary", "-m", "arm", "-M", "reg-names-std",
                                    "-D", argv[-1]])
        self.assertEqual(kw["capture_output"], True)
        self.assertEqual(out[0x14], "bx lr")

    def test_nonzero_exit_yields_none(self):
        out = disasm.disassemble(b"\x00" * 4, exe="/fake/objdump",
                                 runner=lambda argv, **kw: _Proc("boom", returncode=1))
        self.assertIsNone(out)

    def test_empty_buffer_yields_none(self):
        self.assertIsNone(disasm.disassemble(b"", exe="/fake/objdump"))


class CompareTests(unittest.TestCase):
    CAND = {0: "addcc r0, r0, #1", 4: "mov r0, #0"}
    REF = {0: "addls r0, r0, #1", 4: "mov r0, #1"}

    def test_sites_and_structures_are_assembled(self):
        with mock.patch.object(disasm, "find_objdump", return_value="/fake/objdump"), \
                mock.patch.object(disasm, "disassemble",
                                  side_effect=lambda buf, exe=None: self.CAND if buf == b"c"
                                  else self.REF):
            out = disasm.compare(b"c", b"r", [0, 4, 8])
        self.assertTrue(out["available"])
        self.assertEqual(out["sites"]["0"], {"got": "addcc r0, r0, #1",
                                             "want": "addls r0, r0, #1"})
        self.assertEqual(out["sites"]["4"]["got"], "mov r0, #0")
        self.assertNotIn("8", out["sites"])          # beyond the decode: omitted
        self.assertIn("insns", out["cand"])

    def test_missing_tool_reports_unavailable(self):
        with mock.patch.object(disasm, "find_objdump", return_value=None):
            out = disasm.compare(b"c", b"r", [0])
        self.assertFalse(out["available"])
        self.assertIn("objdump", out["reason"])

    def test_a_decode_error_never_raises(self):
        with mock.patch.object(disasm, "find_objdump", return_value="/fake/objdump"), \
                mock.patch.object(disasm, "disassemble", side_effect=RuntimeError("bang")):
            out = disasm.compare(b"c", b"r", [0])
        self.assertFalse(out["available"])
        self.assertIn("RuntimeError", out["reason"])


if __name__ == "__main__":
    unittest.main()
