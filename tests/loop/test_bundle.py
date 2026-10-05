"""Tests for the context-bundle generator's pure helpers (no Ghidra, no binary).

The impure Ghidra runner is not exercised here; everything it feeds — extent resolution,
disassembly parsing, annotation, rendering — is. Run with::

    python3 tests/loop/test_bundle.py
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from bundle import (
    Blocks,
    BundleError,
    annotate,
    callees,
    format_insn,
    hex_words,
    is_call,
    literal_slots,
    name_table,
    parse_disasm,
    parse_inventory,
    render,
    resolve_body,
    target_name,
)


def entry(addr="601a72e4", name="func_601a72e4", module="main", block=".text",
          group=None, size="1368", kind="function") -> dict:
    return {"module": module, "addr": addr, "name": name, "block": block,
            "group": group or name, "size": size, "kind": kind}


class ParseInventoryTests(unittest.TestCase):
    TEXT = ("addr\tkind\tsize\tname\n"
            "60000024\tfunction\t384\t_init\n"
            "60000000\tdata\t36\tD_60000000\n"
            "601a72e4\tfunction\t60\tFUN_601a72e4\n")

    def test_keeps_only_function_rows(self):
        sizes = parse_inventory(self.TEXT)
        self.assertEqual(sizes, {"60000024": 384, "601a72e4": 60})

    def test_ignores_comments_and_short_rows(self):
        self.assertEqual(parse_inventory("# c\n\nbad\n"), {})

    def test_bad_size_is_skipped(self):
        self.assertEqual(parse_inventory("a\tfunction\tnotanint\n"), {})


class ResolveBodyTests(unittest.TestCase):
    SIZES: ClassVar[dict] = {"601a72e4": 60}

    def test_override_wins(self):
        self.assertEqual(resolve_body(entry(), self.SIZES, 42), (42, "override"))

    def test_inventory_used_when_present(self):
        self.assertEqual(resolve_body(entry(), self.SIZES), (60, "inventory"))

    def test_missing_extent_raises_never_partition(self):
        with self.assertRaises(BundleError) as ctx:
            resolve_body(entry(addr="60000f8c"), self.SIZES)
        self.assertIn("no body extent", str(ctx.exception))

    def test_non_positive_override_rejected(self):
        with self.assertRaises(BundleError):
            resolve_body(entry(), self.SIZES, 0)


class NameTableTests(unittest.TestCase):
    def test_only_addressed_entries_of_the_module(self):
        entries = [
            {"module": "main", "addr": "60000024", "name": "func_60000024"},
            {"module": "other", "addr": "60000024", "name": "func_other"},
            {"module": "main", "addr": "", "name": "_ZN2nn3fooEv"},
        ]
        self.assertEqual(name_table(entries, "main"), {"60000024": "func_60000024"})

    def test_target_name_falls_back_to_loc(self):
        self.assertEqual(target_name("60000024", {"60000024": "f"}), "f")
        self.assertEqual(target_name("60000024", {}), "loc_60000024")


class ParseDisasmTests(unittest.TestCase):
    def test_parses_columns_and_flows(self):
        text = ("601a72e4\t00482de9\tstmdb\tsp!,{r11,lr}\t\n"
                "601a7314\tf6ffff1a\tbne\t0x601a72f4\t601a72f4\n")
        ins = parse_disasm(text)
        self.assertEqual(len(ins), 2)
        self.assertEqual(ins[0]["mnemonic"], "stmdb")
        self.assertEqual(ins[0]["flows"], [])
        self.assertEqual(ins[1]["flows"], ["601a72f4"])

    def test_skips_comments_and_malformed(self):
        self.assertEqual(parse_disasm(";; note\nshort\trow\n"), [])

    def test_tolerates_undisassembled_row(self):
        ins = parse_disasm("60001158\t-\t<null>\t\t\n")
        self.assertEqual(ins[0]["mnemonic"], "<null>")
        self.assertEqual(ins[0]["operands"], "")


class LiteralSlotTests(unittest.TestCase):
    def test_absolute_operand(self):
        self.assertEqual(literal_slots("r0, [0x60001058]"), [0x60001058])

    def test_register_forms_are_ignored(self):
        self.assertEqual(literal_slots("r0, [r1, #0x4]"), [])
        self.assertEqual(literal_slots("r0, [pc, r1]"), [])

    def test_multiple_absolute(self):
        self.assertEqual(literal_slots("[0x60001058], [0x60001060]"),
                         [0x60001058, 0x60001060])


class AnnotateTests(unittest.TestCase):
    NAMES: ClassVar[dict] = {"601a72f4": "loc_target", "60001058": "g_thing"}

    def read_word(self, addr):
        return {0x60001058: 0x60001060, 0x4: 0xDEADBEEF}.get(addr)

    def test_flow_names_resolved(self):
        ins = parse_disasm("601a7314\tf6ffff1a\tbne\t0x601a72f4\t601a72f4\n")
        out = annotate(ins, self.NAMES, self.read_word)
        self.assertEqual(out[0]["flow_names"], ["loc_target"])

    def test_literal_value_and_pointed_name(self):
        ins = parse_disasm("6000104c\t04009fe5\tldr\tr0, [0x60001058]\t\n")
        out = annotate(ins, self.NAMES, self.read_word)
        self.assertEqual(out[0]["literals"], [
            {"slot": "60001058", "value": 0x60001060}])

    def test_literal_without_known_target_has_no_name(self):
        ins = parse_disasm("x\tdeadbeef\tldr\tr0, [0x4]\t\n")
        out = annotate(ins, self.NAMES, self.read_word)
        self.assertEqual(out[0]["literals"], [{"slot": "00000004", "value": 0xDEADBEEF}])

    def test_unreadable_literal_is_dropped(self):
        ins = parse_disasm("x\tdeadbeef\tldr\tr0, [0x99]\t\n")
        out = annotate(ins, self.NAMES, lambda a: None)
        self.assertEqual(out[0]["literals"], [])

    def test_input_not_mutated(self):
        ins = parse_disasm("601a7314\tf6ffff1a\tbne\t0x601a72f4\t601a72f4\n")
        annotate(ins, self.NAMES, self.read_word)
        self.assertNotIn("flow_names", ins[0])


class CalleesTests(unittest.TestCase):
    def test_only_calls_deduped_in_order(self):
        ins = [
            {"mnemonic": "bl", "flows": ["60000690"]},
            {"mnemonic": "bne", "flows": ["601a72f4"]},
            {"mnemonic": "bl", "flows": ["607aedcc"]},
            {"mnemonic": "blx", "flows": ["60000690"]},
        ]
        self.assertEqual(callees(ins, {"60000690": "func_60000690"}),
                         [("60000690", "func_60000690"), ("607aedcc", "loc_607aedcc")])

    def test_conditional_branches_are_not_calls(self):
        ins = [
            {"mnemonic": "ble", "flows": ["601a72f4"]},
            {"mnemonic": "blt", "flows": ["601a72f8"]},
            {"mnemonic": "bls", "flows": ["601a72fc"]},
            {"mnemonic": "blo", "flows": ["601a7300"]},
        ]
        self.assertEqual(callees(ins, {}), [])

    def test_conditional_branch_with_link_is_a_call(self):
        ins = [
            {"mnemonic": "bleq", "flows": ["60000690"]},
            {"mnemonic": "blls", "flows": ["60000694"]},
        ]
        self.assertEqual(callees(ins, {}),
                         [("60000690", "loc_60000690"), ("60000694", "loc_60000694")])

    def test_is_call(self):
        for mnemonic in ("bl", "blx", "bleq", "blxne", "blls", "bl.w", "blxgt"):
            self.assertTrue(is_call(mnemonic), mnemonic)
        for mnemonic in ("ble", "blt", "bls", "blo", "b", "bne", "ldr", "<null>"):
            self.assertFalse(is_call(mnemonic), mnemonic)


class HexWordsTests(unittest.TestCase):
    def test_grouping_and_padding(self):
        self.assertEqual(hex_words(bytes.fromhex("00482de90020a0e3")),
                         "00482de9 0020a0e3")

    def test_partial_tail(self):
        self.assertEqual(hex_words(b"\x01\x02\x03\x04\x05"), "01020304 05")


class FormatInsnTests(unittest.TestCase):
    def test_flow_and_literal_notes(self):
        ins = {"addr": "6000104c", "bytes": "04009fe5", "mnemonic": "ldr",
               "operands": "r0, [0x60001058]", "flow_names": [],
               "literals": [{"slot": "60001058", "value": 0x1837B18, "name": "g_x"}]}
        self.assertIn("; = 0x01837b18 (g_x)", format_insn(ins))

    def test_no_notes_has_no_semicolon(self):
        ins = {"addr": "601a72e4", "bytes": "00482de9", "mnemonic": "stmdb",
               "operands": "sp!,{r11,lr}", "flow_names": [], "literals": []}
        self.assertNotIn(";", format_insn(ins))


class RenderTests(unittest.TestCase):
    META: ClassVar[dict] = {"name": "func_601a72e4", "module": "main", "addr": "601a72e4",
                          "block": ".text", "group": "func_601a72e4", "kind": "function",
                          "body": 60, "extent_source": "inventory", "partition": 1368,
                          "body_hex": "00482de9 0020a0e3", "callees": []}

    def test_deterministic(self):
        ins = parse_disasm("601a72e4\t00482de9\tstmdb\tsp!,{r11,lr}\t\n")
        self.assertEqual(render(self.META, ins), render(self.META, ins))

    def test_carries_extent_and_partition(self):
        text = render(self.META, [])
        self.assertIn("body      60 B  (source: inventory)", text)
        self.assertIn("partition 1368 B", text)

    def test_no_calls_placeholder(self):
        self.assertIn("## calls\n\n    (none)", render(self.META, []))

    def test_calls_listed(self):
        meta = dict(self.META, callees=[("60000690", "func_60000690")])
        self.assertIn("    60000690  func_60000690", render(meta, []))


class BlocksTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.dir = Path(self._dir.name)
        (self.dir / ".text_60000000.bin").write_bytes(
            bytes.fromhex("00482de9") + struct.pack("<I", 0x60001058) + b"\xaa\xbb")

    def tearDown(self):
        self._dir.cleanup()

    def test_read_word(self):
        self.assertEqual(Blocks(self.dir).read_word(0x60000004), 0x60001058)

    def test_read_word_out_of_range(self):
        self.assertIsNone(Blocks(self.dir).read_word(0x60000009))

    def test_read_word_unknown_address(self):
        self.assertIsNone(Blocks(self.dir).read_word(0x70000000))

    def test_bytes_at(self):
        self.assertEqual(Blocks(self.dir).bytes_at(0x60000000, 4), bytes.fromhex("00482de9"))

    def test_bytes_at_truncates_at_block_end(self):
        self.assertEqual(Blocks(self.dir).bytes_at(0x60000008, 8), b"\xaa\xbb")


if __name__ == "__main__":
    unittest.main(verbosity=2)
