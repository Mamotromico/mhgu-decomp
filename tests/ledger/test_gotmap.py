"""Tests for the GOT map: dynamic parsing, symbols, slots, and the extent.

The fixture is a synthetic image — a ``MOD0`` header, a dynamic table, a symbol table, and
two REL tables — so these run without the NSO or Ghidra. Run with::

    python3 tests/ledger/test_gotmap.py
"""

from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import gotmap
from gotmap import (
    BASE,
    Image,
    GotError,
    build,
    check,
    dynamic_entries,
    got_extent,
    got_ranges,
    got_slots,
    mod0_address,
    read_relocations,
    read_symbols,
    symbol_slots,
)

TEXT = BASE
DATA = BASE + 0x1000
SYMTAB, STRTAB, HASH = 0x1100, 0x1140, 0x1180
REL, JMPREL, PLTGOT, INIT_ARRAY = 0x1200, 0x1220, 0x1300, 0x1400

DYNAMIC = [
    (gotmap.DT_SYMTAB, SYMTAB),
    (gotmap.DT_STRTAB, STRTAB),
    (gotmap.DT_SYMENT, 16),
    (gotmap.DT_HASH, HASH),
    (gotmap.DT_REL, REL),
    (gotmap.DT_RELSZ, 16),
    (gotmap.DT_RELENT, 8),
    (gotmap.DT_JMPREL, JMPREL),
    (gotmap.DT_PLTRELSZ, 8),
    (gotmap.DT_PLTGOT, PLTGOT),
    (gotmap.DT_INIT_ARRAY, INIT_ARRAY),
    (gotmap.DT_NULL, 0),
]


def sym(name_off: int, info: int = 0x12, shndx: int = 0, value: int = 0) -> bytes:
    return struct.pack("<IIIBBH", name_off, value, 0, info, 0, shndx)


def rel(offset: int, type_: int, index: int) -> bytes:
    return struct.pack("<II", offset, (index << 8) | type_)


def fixture() -> Image:
    strings = b"\x00sym_a\x00sym_b\x00sym_c\x00"
    offsets = {b"sym_a": 1, b"sym_b": 7, b"sym_c": 13}

    data = bytearray(0x500)

    def put(addr: int, blob: bytes) -> None:
        """Write at a module-relative address (``DATA`` is this section's start)."""
        off = addr - (DATA - BASE)
        data[off:off + len(blob)] = blob

    for i, (tag, value) in enumerate(DYNAMIC):
        struct.pack_into("<iI", data, i * 8, tag, value)
    # .dynsym: null, sym_a, sym_b, sym_c — then .dynstr immediately after (0x1140).
    put(SYMTAB, sym(0) + sym(offsets[b"sym_a"]) + sym(offsets[b"sym_b"], 0x11)
        + sym(offsets[b"sym_c"]))
    put(STRTAB, strings)
    put(HASH, struct.pack("<II", 1, 4))               # nbucket, nchain (# symbols)
    put(REL, rel(PLTGOT + 0x10, gotmap.R_ARM_GLOB_DAT, 1)      # sym_a -> slot
        + rel(PLTGOT + 0x30, gotmap.R_ARM_ABS32, 2))           # sym_b: a data word
    put(JMPREL, rel(PLTGOT + 0x0C, gotmap.R_ARM_JUMP_SLOT, 3))  # sym_c
    # Loader stubs: outside every image section, as the real file's import slots are.
    put(PLTGOT + 0x0C, struct.pack("<I", 0x70000000))
    put(PLTGOT + 0x10, struct.pack("<I", 0x70001000))

    text = bytearray(0x400)
    text[4:8] = b"MOD0"
    struct.pack_into("<I", text, 8, DATA - (TEXT + 4))   # dynamic offset from MOD0
    # A PLT stub at .text+0x310: r12 = (stub+8) + 0 + 0, then jump through r12 + 0xFF4,
    # which is module-relative 0x130C — sym_c's JUMP_SLOT slot.
    struct.pack_into("<III", text, 0x310, 0xE28FC000, 0xE28CC000, 0xE5BCFFF4)
    return Image({"text": (TEXT, bytes(text)), "data": (DATA, bytes(data))})


class ImageTests(unittest.TestCase):
    def test_reads_by_address(self):
        image = fixture()
        self.assertTrue(image.contains(DATA + 0x100))
        self.assertEqual(image.read(DATA, 4), image.read(DATA, 4))
        self.assertFalse(image.contains(0x70000000))

    def test_unreadable_span_raises(self):
        with self.assertRaises(GotError):
            fixture().read(0x70000000)

    def test_mod0_address(self):
        self.assertEqual(mod0_address(fixture()), TEXT + 4)


class DynamicTests(unittest.TestCase):
    def test_parses_tag_value_pairs_until_null(self):
        dynamic = dynamic_entries(fixture())
        self.assertEqual(dynamic[gotmap.DT_SYMTAB], SYMTAB)
        self.assertEqual(dynamic[gotmap.DT_PLTGOT], PLTGOT)
        self.assertNotIn(gotmap.DT_NULL, dynamic)


class SymbolTests(unittest.TestCase):
    def test_symbols_are_indexed_and_named(self):
        image = fixture()
        symbols = read_symbols(image, dynamic_entries(image))
        self.assertEqual([s["name"] for s in symbols], ["", "sym_a", "sym_b", "sym_c"])
        self.assertFalse(symbols[1]["defined"])


class SlotTests(unittest.TestCase):
    def setUp(self):
        self.image = fixture()
        self.dynamic = dynamic_entries(self.image)
        self.symbols = read_symbols(self.image, self.dynamic)
        self.slots = got_slots(self.image, self.dynamic, self.symbols)

    def test_only_got_filling_relocations_count(self):
        # GLOB_DAT and JUMP_SLOT yes; ABS32 (a data word) and RELATIVE no.
        self.assertEqual(sorted(info["symbol"] for info in self.slots.values()),
                         ["sym_a", "sym_c"])

    def test_slot_address_is_base_plus_r_offset(self):
        self.assertIn(BASE + PLTGOT + 0x10, self.slots)
        self.assertIn(BASE + PLTGOT + 0x0C, self.slots)

    def test_symbol_slots_lookup(self):
        self.assertEqual(symbol_slots(self.slots, "sym_c"), [BASE + PLTGOT + 0x0C])
        self.assertEqual(symbol_slots(self.slots, "nope"), [])

    def test_extent_spans_got_plt_and_got(self):
        self.assertEqual(got_extent(self.image, self.dynamic),
                         (BASE + PLTGOT, BASE + INIT_ARRAY))

    def test_ranges_split_got_plt_from_got(self):
        ranges = got_ranges(self.image, self.dynamic)
        self.assertEqual([name for name, _lo, _hi in ranges], [".got.plt", ".got"])
        self.assertEqual(ranges[0][1], BASE + PLTGOT)
        self.assertEqual(ranges[0][2], ranges[1][1])   # contiguous
        self.assertEqual(ranges[1][2], BASE + INIT_ARRAY)

    def test_check_passes_on_the_fixture(self):
        self.assertEqual(check(self.image), [])

    def test_check_reports_a_slot_outside_the_extent(self):
        model = build(self.image)
        model["slots"][BASE + 0x2000] = {"symbol": "stray", "table": "rel.dyn",
                                         "type": gotmap.R_ARM_JUMP_SLOT, "index": 0}
        self.assertTrue(any("outside the GOT" in p for p in check(self.image, model)))


class RelocationTests(unittest.TestCase):
    def test_rejects_a_partial_entry(self):
        with self.assertRaises(GotError):
            read_relocations(fixture(), BASE + REL, 12)

    def test_reads_offsets_and_info(self):
        entries = read_relocations(fixture(), BASE + REL, 16)
        self.assertEqual(entries[0][0], PLTGOT + 0x10)
        self.assertEqual(entries[1][1] & 0xFF, gotmap.R_ARM_ABS32)


class StubTests(unittest.TestCase):
    """PLT stubs: import calls land on a 12-byte idiom in .text that jumps through the GOT."""

    def setUp(self):
        self.image = fixture()
        self.model = build(self.image)
        self.stub = TEXT + 0x310
        self.slot = BASE + PLTGOT + 0x0C          # sym_c's JUMP_SLOT slot

    def test_decodes_the_stub_to_its_slot(self):
        self.assertEqual(gotmap.plt_stubs(self.image), {self.stub: self.slot})

    def test_inverts_through_the_got_to_name_the_import(self):
        self.assertEqual(gotmap.import_stubs(self.image, self.model),
                         {"sym_c": self.stub})

    def test_build_exposes_stubs_and_imports(self):
        self.assertEqual(self.model["stubs"], {self.stub: self.slot})
        self.assertEqual(self.model["imports"], {"sym_c": self.stub})

    def test_check_accepts_the_stub(self):
        self.assertEqual(check(self.image, self.model), [])

    def test_a_stub_jumping_through_an_unmapped_slot_is_reported(self):
        model = build(self.image)
        model["stubs"][TEXT + 0x320] = BASE + PLTGOT + 0x400   # no relocation names it
        self.assertTrue(any("which no relocation names" in p
                            for p in check(self.image, model)))


class CacheTests(unittest.TestCase):
    def test_a_current_cache_is_used_without_touching_the_image(self):
        with tempfile.TemporaryDirectory() as d:
            nso = Path(d) / "main.nso"
            nso.write_bytes(b"x" * 10)
            cache = Path(d) / "gotmap.json"
            cache.write_text(json.dumps({
                "version": gotmap.CACHE_VERSION,
                "nso": {"path": str(nso), "size": 10,
                        "mtime_ns": nso.stat().st_mtime_ns},
                "ranges": [], "slots": {}, "stubs": {},
                "imports": {"an_import": 0x613EFD58},
            }))
            self.assertEqual(gotmap.symbol_stubs(nso, cache),
                             {"an_import": 0x613EFD58})

    def test_a_stale_cache_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as d:
            nso = Path(d) / "main.nso"
            nso.write_bytes(b"x" * 10)
            cache = Path(d) / "gotmap.json"
            cache.write_text(json.dumps({"version": gotmap.CACHE_VERSION,
                                         "nso": {"size": 1, "mtime_ns": 0},
                                         "imports": {"stale": 1}}))
            # A rebuild is attempted, and a 10-byte "NSO" cannot be one.
            with self.assertRaises(Exception):
                gotmap.symbol_stubs(nso, cache)

    def test_stub_names_maps_address_to_import(self):
        with tempfile.TemporaryDirectory() as d:
            nso = Path(d) / "main.nso"
            nso.write_bytes(b"x" * 10)
            cache = Path(d) / "gotmap.json"
            cache.write_text(json.dumps({
                "version": gotmap.CACHE_VERSION,
                "nso": {"size": 10, "mtime_ns": nso.stat().st_mtime_ns},
                "ranges": [], "slots": {"6183800c": {"symbol": "sym_c"}},
                "stubs": {"613efd58": "6183800c"}, "imports": {"sym_c": 0x613EFD58},
            }))
            self.assertEqual(gotmap.stub_names(nso, cache), {"613efd58": "sym_c"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
