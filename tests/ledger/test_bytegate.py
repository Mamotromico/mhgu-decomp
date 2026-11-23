"""Regression tests for the byte gate's comparison rule.

The rule this pins down is the fix for the partition-vs-body defect: the ledger's ``size``
is the block *partition* (bytes to the next cut point), which over-covers a function whose
trailing region was never cut (``func_601a72e4``/``new_b``: a 60 B body in a 1368 B
partition). ``compare_body`` requires the authoritative instruction-plus-pool extent, treats the
partition and reference block as bounds, and rejects truncated or omitted-pool candidates.

Pure-function tests only — no clang, no Ghidra, no ledger, no binary. Run with::

    python3 tests/ledger/test_bytegate.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path
from unittest import mock

# The ledger tools are plain scripts (no package), so put their directory on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import bytegate
import gotmap
import refcache
from bytegate import (
    branch_addresses,
    compare_body,
    function_relocations,
    gate_result,
    ledger_addresses,
    pool_slots,
    resolve_branches,
    resolve_pools,
    resolve_relocations,
    resolve_ref_bin,
    should_color,
)


class CompareBodyTests(unittest.TestCase):
    # A synthetic block; the "function" lives at offset 0x10. Bytes are arbitrary but
    # deterministic so a wrong slice is easy to spot.
    BLOCK = bytes((0xA0 + i) & 0xFF for i in range(0x1000))
    OFF = 0x10

    def original(self, n: int) -> bytes:
        return self.BLOCK[self.OFF:self.OFF + n]

    def test_exact_body_filling_partition_matches(self):
        body = self.original(0x40)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 0x40, 0x40)
        self.assertTrue(ok)
        self.assertEqual(ref, body)
        self.assertEqual(status, "match")

    def test_exact_body_in_over_covering_partition_matches(self):
        # new_b's shape: a 60 B body in a 1368 B partition.
        body = self.original(60)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, 60)
        self.assertTrue(ok)
        self.assertEqual(ref, body)
        self.assertEqual(status, "match")

    def test_wrong_bytes_are_a_mismatch(self):
        body = bytearray(self.original(60))
        body[10] ^= 0xFF
        ok, ref, status = compare_body(bytes(body), self.BLOCK, self.OFF, 1368, 60)
        self.assertFalse(ok)
        self.assertEqual(len(ref), 60)
        self.assertEqual(status, "mismatch")

    def test_candidate_longer_than_partition_is_a_length_mismatch(self):
        body = self.original(200)
        ok, _ref, status = compare_body(body, self.BLOCK, self.OFF, 100, 100)
        self.assertFalse(ok)
        self.assertEqual(status, "body-length")

    def test_empty_candidate_is_rejected(self):
        ok, ref, status = compare_body(b"", self.BLOCK, self.OFF, 1368, 60)
        self.assertFalse(ok)
        self.assertEqual(ref, self.original(60))
        self.assertEqual(status, "empty-body")

    def test_missing_extent_rejects_even_a_complete_match(self):
        body = self.original(60)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, None)
        self.assertFalse(ok)
        self.assertEqual(ref, b"")
        self.assertEqual(status, "missing-body")

    def test_truncated_matching_prefix_is_rejected(self):
        body = self.original(40)
        ok, ref, status = compare_body(body, self.BLOCK, self.OFF, 1368, 60)
        self.assertFalse(ok)
        self.assertEqual(len(ref), 60)
        self.assertEqual(status, "body-length")

    def test_extent_outside_partition_is_rejected(self):
        body = self.original(80)
        ok, _ref, status = compare_body(body, self.BLOCK, self.OFF, 60, 80)
        self.assertFalse(ok)
        self.assertEqual(status, "invalid-extent")

    def test_extent_outside_reference_block_is_rejected(self):
        block = self.original(60)
        ok, _ref, status = compare_body(block, block, 0, 100, 80)
        self.assertFalse(ok)
        self.assertEqual(status, "invalid-extent")

    def test_pool_instructions_padding_and_word_match(self):
        from complexity import function_extent

        instructions = struct.pack("<II", 0xE59F0004, 0xE12FFF1E)
        original = instructions + bytes(4) + struct.pack("<I", 0x12345678)
        extent = function_extent(instructions, len(original))
        ok, ref, status = compare_body(original, original, 0, len(original), extent)
        self.assertTrue(ok)
        self.assertEqual(ref, original)
        self.assertEqual(status, "match")

    def test_omitted_pool_is_a_length_mismatch(self):
        from complexity import function_extent

        instructions = struct.pack("<II", 0xE59F0004, 0xE12FFF1E)
        original = instructions + bytes(4) + struct.pack("<I", 0x12345678)
        extent = function_extent(instructions, len(original))
        ok, ref, status = compare_body(instructions, original, 0, len(original), extent)
        self.assertFalse(ok)
        self.assertEqual(ref, original)
        self.assertEqual(status, "body-length")


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

    def test_gate_provenance_is_reported(self):
        # The ledger records it with verify=match; the loop copies it into the attempt log.
        raw = self.result(b"abcd", b"abcd")
        self.assertEqual(raw["gate"], "raw")
        reloc = gate_result("main", "601a72e4", "func_601a72e4", b"abcd", b"abcd",
                            True, "match", 60, 1368, has_reloc=True, gate="reloc")
        self.assertEqual(reloc["gate"], "reloc")

    def test_carries_status_and_identity(self):
        r = self.result(b"abcd", b"abce", ok=False, status="mismatch")
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "mismatch")
        self.assertEqual(r["name"], "func_601a72e4")

    def test_reports_the_differing_words(self):
        # The softfp/hardfp shape: one instruction differs in 3 bytes, the next matches.
        cand = bytes.fromhex("5c1080e51eff2fe1")
        ref = bytes.fromhex("170a80ed1eff2fe1")
        r = self.result(cand, ref, ok=False, status="mismatch")
        self.assertEqual(r["diff_words"],
                         [{"offset": 0, "got": "5c1080e5", "want": "170a80ed"}])

    def test_no_diff_words_on_a_match(self):
        self.assertEqual(self.result(b"abcd", b"abcd")["diff_words"], [])

    def test_diff_words_are_capped(self):
        cand = bytes(4 * 32)
        ref = bytes([0xFF]) * (4 * 32)
        r = self.result(cand, ref, ok=False, status="mismatch")
        self.assertEqual(len(r["diff_words"]), 16)
        self.assertEqual(r["diff_words"][0], {"offset": 0, "got": "00000000",
                                              "want": "ffffffff"})


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


class ResolveBranchesTests(unittest.TestCase):
    """The relocation-aware compare: patch the site, then byte-compare.

    The worked example is a real one: ``60000298`` is a 4 B thunk whose body is the single
    branch ``b __nnDetailNintendoSdkRuntimeObjectFile``. Unlinked it is ``0xEAFFFFFE``; the
    original (linked) word is ``0xEAFFFFFF``.
    """

    BASE = 0x60000298
    TARGET = 0x6000029c

    def reloc(self, offset: int = 0, type_: int = 29, symbol: str = "callee") -> dict:
        return {"offset": offset, "type": type_, "symbol": symbol, "addend": 0}

    def test_a_tail_branch_patches_to_the_linked_word(self):
        patched, unresolved = resolve_branches(
            struct.pack("<I", 0xEAFFFFFE), [self.reloc()], self.BASE,
            {"callee": self.TARGET})
        self.assertEqual(unresolved, [])
        self.assertEqual(patched, struct.pack("<I", 0xEAFFFFFF))

    def test_a_call_preserves_its_opcode(self):
        patched, _ = resolve_branches(struct.pack("<I", 0xEBFFFFFE), [self.reloc(type_=28)],
                                      self.BASE, {"callee": self.TARGET})
        self.assertEqual(struct.unpack("<I", patched)[0], 0xEBFFFFFF)

    def test_a_conditional_branch_keeps_its_condition(self):
        patched, _ = resolve_branches(struct.pack("<I", 0x0AFFFFFE), [self.reloc()],
                                      self.BASE, {"callee": self.TARGET})
        self.assertEqual(struct.unpack("<I", patched)[0], 0x0AFFFFFF)

    def test_a_backward_target_patches_negative(self):
        patched, _ = resolve_branches(struct.pack("<I", 0xEAFFFFFE), [self.reloc()],
                                      self.BASE, {"callee": self.BASE - 0x10})
        # delta = (BASE-0x10) - (BASE+8) = -0x18 -> imm24 = -6
        self.assertEqual(struct.unpack("<I", patched)[0], 0xEA000000 | ((-6) & 0xFFFFFF))

    def test_an_unverified_relocation_type_fails_closed(self):
        patched, unresolved = resolve_branches(struct.pack("<I", 0xEAFFFFFE),
                                               [self.reloc(type_=96)], self.BASE,
                                               {"callee": self.TARGET})
        self.assertEqual(patched, struct.pack("<I", 0xEAFFFFFE))
        self.assertEqual(len(unresolved), 1)
        self.assertIn("not a verified branch/call", unresolved[0][1])

    def test_a_symbol_without_a_ledger_address_fails_closed(self):
        _patched, unresolved = resolve_branches(struct.pack("<I", 0xEAFFFFFE),
                                                [self.reloc()], self.BASE, {})
        self.assertEqual(len(unresolved), 1)
        self.assertIn("no ledger address", unresolved[0][1])

    def test_a_non_branch_word_at_a_branch_site_fails_closed(self):
        _patched, unresolved = resolve_branches(struct.pack("<I", 0xE1A00000),
                                                [self.reloc()], self.BASE,
                                                {"callee": self.TARGET})
        self.assertEqual(len(unresolved), 1)
        self.assertIn("not an A32 branch", unresolved[0][1])

    def test_an_out_of_range_target_fails_closed(self):
        _patched, unresolved = resolve_branches(struct.pack("<I", 0xEAFFFFFE),
                                                [self.reloc()], self.BASE,
                                                {"callee": 0x70000000})
        self.assertEqual(len(unresolved), 1)
        self.assertIn("out of branch range", unresolved[0][1])


class FunctionRelocationsTests(unittest.TestCase):
    """Relocation parsing is scoped to the function's own section."""

    SEC = {"index": 5}

    def rel_section(self, index: int, info: int, size: int = 16) -> dict:
        return {"index": index, "type": 9, "info": info, "offset": 0, "size": size,
                "link": 1, "entsize": 8}

    def test_only_relocations_against_this_section_are_returned(self):
        data = (struct.pack("<II", 4, (0 << 8) | 29)
                + struct.pack("<II", 0, (1 << 8) | 96))
        sections = [self.rel_section(2, 5), self.rel_section(3, 6, size=8)]
        symtabs = {1: [{"name": "callee"}, {"name": "g_data"}]}
        relocs = function_relocations(data, sections, symtabs, self.SEC)
        self.assertEqual(relocs, [
            {"offset": 0, "type": 96, "symbol": "g_data", "addend": 0},
            {"offset": 4, "type": 29, "symbol": "callee", "addend": 0},
        ])

    def test_exidx_relocations_never_reach_the_body(self):
        # Info 6 is the .ARM.exidx section, not the function's section 5.
        sections = [self.rel_section(3, 6)]
        self.assertEqual(function_relocations(b"\0" * 16, sections, {}, self.SEC), [])

    def test_an_unknown_symbol_index_yields_an_empty_name(self):
        data = struct.pack("<II", 0, (9 << 8) | 29)
        relocs = function_relocations(data, [self.rel_section(2, 5, size=8)], {1: []},
                                      self.SEC)
        self.assertEqual(relocs[0]["symbol"], "")


class PoolTests(unittest.TestCase):
    """Literal-pool resolution: patch the word to ``GOT(symbol) + addend - P``."""

    def test_patches_the_word_to_the_linked_value(self):
        cand = struct.pack("<I", 8)                    # the object's in-place addend
        patched, unresolved = resolve_pools(cand, [{"offset": 0, "type": 96,
                                                    "symbol": "D_1", "addend": 0}],
                                           0x2000, {"D_1": 0x1000})
        self.assertEqual(unresolved, [])
        self.assertEqual(struct.unpack("<I", patched)[0],
                         (0x1000 + 8 - 0x2000) & 0xFFFFFFFF)

    def test_a_symbol_without_a_slot_fails_closed(self):
        _patched, unresolved = resolve_pools(struct.pack("<I", 8),
                                             [{"offset": 0, "type": 96,
                                               "symbol": "unknown", "addend": 0}],
                                             0x2000, {})
        self.assertEqual(len(unresolved), 1)
        self.assertIn("no GOT slot", unresolved[0][1])

    def test_the_dispatcher_rejects_an_unsupported_type(self):
        _patched, unresolved = resolve_relocations(
            struct.pack("<II", 0, 0),
            [{"offset": 0, "type": 2, "symbol": "D_1", "addend": 0}],
            0x2000, {}, {})
        self.assertEqual(len(unresolved), 1)
        self.assertIn("not verified", unresolved[0][1])


class PoolSlotsTests(unittest.TestCase):
    """``symbol -> slot``: imports by relocation, internal objects by slot contents."""

    ENTRIES = [{"kind": "data", "addr": "6172f000", "size": "16"},
               {"kind": "function", "addr": "60000000", "size": "4"}]
    PAYLOAD = {
        "slots": {"6183800c": {"symbol": "sqrtf"}},
        "values": {"61838010": 0x6172F004,     # inside the data entry
                   "61838014": 0x99999999},    # inside no data entry
    }

    def test_imports_come_from_the_relocation(self):
        self.assertEqual(pool_slots(self.ENTRIES, self.PAYLOAD)["sqrtf"], 0x6183800C)

    def test_an_internal_slot_is_named_by_the_address_it_holds(self):
        self.assertEqual(pool_slots(self.ENTRIES, self.PAYLOAD)["D_6172f004"], 0x61838010)

    def test_an_address_outside_any_data_entry_is_not_named(self):
        self.assertNotIn("D_99999999", pool_slots(self.ENTRIES, self.PAYLOAD))

    def test_a_relocation_named_slot_is_not_renamed_from_contents(self):
        payload = {"slots": {"61838010": {"symbol": "an_import"}},
                   "values": {"61838010": 0x6172F004}}
        slots = pool_slots(self.ENTRIES, payload)
        self.assertEqual(slots["an_import"], 0x61838010)
        self.assertNotIn("D_6172f004", slots)


class LedgerAddressesTests(unittest.TestCase):
    def test_externals_have_no_address(self):
        entries = [{"name": "func_60000000", "addr": "60000000"},
                   {"name": "_ZN2nn2fs4InitEv", "addr": ""}]
        self.assertEqual(ledger_addresses(entries), {"func_60000000": 0x60000000})


class BranchAddressesTests(unittest.TestCase):
    """Import calls resolve through their PLT stub; ledger names always win."""

    ENTRIES = [{"name": "func_60000000", "addr": "60000000"},
               {"name": "sqrtf", "addr": ""}]

    def test_an_import_resolves_through_the_stub_map(self):
        with mock.patch.object(gotmap, "symbol_stubs",
                               return_value={"sqrtf": 0x613EFD58}):
            addresses, via = branch_addresses([{"symbol": "sqrtf"}], self.ENTRIES,
                                              Path("/nso"), None)
        self.assertEqual(addresses["sqrtf"], 0x613EFD58)
        self.assertEqual(addresses["func_60000000"], 0x60000000)
        self.assertEqual(via, 1)

    def test_a_ledger_name_beats_the_stub_map(self):
        with mock.patch.object(gotmap, "symbol_stubs",
                               return_value={"func_60000000": 0x1}):
            addresses, via = branch_addresses([{"symbol": "func_60000000"}],
                                              self.ENTRIES, Path("/nso"), None)
        self.assertEqual(addresses["func_60000000"], 0x60000000)
        self.assertEqual(via, 0)

    def test_a_symbol_in_neither_map_stays_unresolved(self):
        with mock.patch.object(gotmap, "symbol_stubs", return_value={}):
            addresses, via = branch_addresses([{"symbol": "unknown"}], self.ENTRIES,
                                              Path("/nso"), None)
        self.assertNotIn("unknown", addresses)
        self.assertEqual(via, 0)

    def test_an_unavailable_map_does_not_break_resolution(self):
        with mock.patch.object(gotmap, "symbol_stubs",
                               side_effect=gotmap.GotError("no image")):
            addresses, via = branch_addresses([{"symbol": "sqrtf"}], self.ENTRIES,
                                              Path("/nope"), None)
        self.assertNotIn("sqrtf", addresses)
        self.assertEqual(via, 0)

    def test_the_map_is_not_loaded_when_every_symbol_is_known(self):
        with mock.patch.object(gotmap, "symbol_stubs",
                               side_effect=AssertionError("must not be called")):
            _addresses, via = branch_addresses([{"symbol": "func_60000000"}],
                                               self.ENTRIES, Path("/nso"), None)
        self.assertEqual(via, 0)


class ResolveRefBinTests(unittest.TestCase):
    """Reference-source selection: cached direct extraction, with the Ghidra dump as
    the explicit fallback (uncacheable block, cache failure, or --ghidra-ref)."""

    NSO = Path("/nso/main.nso")
    REF_DIR = Path("/ref")
    CACHE = Path("/cache")
    TEXT_BIN = CACHE / ".text_60000000.bin"

    def resolve(self, block, **kwargs):
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with contextlib.redirect_stdout(io.StringIO()):
                path, src = resolve_ref_bin(self.NSO, block, self.REF_DIR, self.CACHE,
                                            **kwargs)
        return path, src, err.getvalue()

    def test_a_text_block_is_served_from_the_cache(self):
        with mock.patch.object(refcache, "ref_bin_for_block",
                               return_value=self.TEXT_BIN) as cache:
            with mock.patch.object(bytegate, "dump_blocks_ref",
                                   side_effect=AssertionError("no dump wanted")):
                path, src, _ = self.resolve(".text")
        self.assertEqual((path, src), (self.TEXT_BIN, "cache"))
        cache.assert_called_once_with(self.NSO, ".text", self.CACHE, refresh=False)

    def test_an_uncacheable_block_falls_back_to_the_dump(self):
        with mock.patch.object(refcache, "ref_bin_for_block", return_value=None):
            with mock.patch.object(bytegate, "dump_blocks_ref") as dump:
                with mock.patch.object(bytegate, "block_bin",
                                       return_value=self.REF_DIR / ".data_6172f000.bin"
                                       ) as block_bin:
                    path, src, _ = self.resolve(".data")
        self.assertEqual((path, src),
                         (self.REF_DIR / ".data_6172f000.bin", "ghidra"))
        dump.assert_called_once_with(self.NSO, self.REF_DIR)
        block_bin.assert_called_once_with(self.REF_DIR, ".data")

    def test_a_cache_failure_falls_back_to_the_dump_with_a_warning(self):
        with mock.patch.object(refcache, "ref_bin_for_block",
                               side_effect=refcache.RefError("no image")):
            with mock.patch.object(bytegate, "dump_blocks_ref"):
                with mock.patch.object(bytegate, "block_bin",
                                       return_value=self.TEXT_BIN):
                    _path, src, err = self.resolve(".text")
        self.assertEqual(src, "ghidra")
        self.assertIn("falling back to Ghidra", err)

    def test_force_ghidra_skips_the_cache(self):
        with mock.patch.object(refcache, "ref_bin_for_block",
                               side_effect=AssertionError("cache must not be touched")):
            with mock.patch.object(bytegate, "dump_blocks_ref") as dump:
                with mock.patch.object(bytegate, "block_bin",
                                       return_value=self.TEXT_BIN):
                    _path, src, _ = self.resolve(".text", force_ghidra=True)
        self.assertEqual(src, "ghidra")
        dump.assert_called_once()

    def test_refresh_is_passed_through_to_the_cache(self):
        with mock.patch.object(refcache, "ref_bin_for_block",
                               return_value=self.TEXT_BIN) as cache:
            with mock.patch.object(bytegate, "dump_blocks_ref",
                                   side_effect=AssertionError("no dump wanted")):
                self.resolve(".text", refresh=True)
        cache.assert_called_once_with(self.NSO, ".text", self.CACHE, refresh=True)

    def test_a_dump_failure_propagates_to_the_caller(self):
        # The pre-cache behaviour is preserved: no block file at all is a setup error,
        # not a silently skipped comparison.
        with mock.patch.object(refcache, "ref_bin_for_block", return_value=None):
            with mock.patch.object(bytegate, "dump_blocks_ref",
                                   side_effect=FileNotFoundError("no ghidra")):
                with self.assertRaises(FileNotFoundError):
                    self.resolve(".data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
