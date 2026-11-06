"""The image's GOT: which imported symbol each slot belongs to.

Stage 3 of the relocation-aware gate (see ``baserom/work/reloc-gate-plan.txt`` and
``docs/architecture.md`` -> *Gate provenance*). The gate resolves branch/call relocations
today; a literal-pool word (``R_ARM_GOT_PREL``) names a **GOT slot**, so verifying one needs
this map: slot address -> symbol.

Where the data comes from
-------------------------
The NSO carries no ELF section headers. ``MOD0`` (magic at ``.text + 8``) gives the
``.dynamic`` offset, and the dynamic table gives everything else: ``DT_REL``/``DT_RELSZ``,
``DT_JMPREL``/``DT_PLTRELSZ``, ``DT_SYMTAB``, ``DT_STRTAB``, ``DT_SYMENT``, ``DT_PLTGOT``,
``DT_INIT_ARRAY``. Every address in those tables is **module-relative** (an offset from the
``0x60000000`` image base), which is the same space as the ledger — so no conversion is
needed beyond adding the base.

Only two relocation types name a GOT slot:

* ``R_ARM_GLOB_DAT`` and ``R_ARM_JUMP_SLOT`` — the slot holds the symbol's address;
* ``R_ARM_ABS32`` (1,345 here) always targets a **data word** (vtables, typeinfo), not a
  slot; ``R_ARM_RELATIVE`` (171,058) carries no symbol at all.

So the map is small: 706 slots for the image's 761 imports.

**The slot contents are not the answer.** In the file, an import slot holds a loader stub
(page-aligned, outside every image block), so ``ldr rd, [pc, #imm]`` cannot be resolved by
reading the slot — the relocation is the only record of what it means. Internal symbols take
the other path: their slots are resolved statically, are absent from the dynamic tables, and
*do* hold the symbol's address.

The GOT's extent is reproducible without the loader: ``.got.plt`` starts at ``DT_PLTGOT`` and
holds three reserved words plus one per ``JUMP_SLOT``; ``.got`` runs from there to
``DT_INIT_ARRAY`` — exactly the range the Switch loader constructs (``0x1838AE8``-``0x1848900``
module-relative).

Imports are also called through **12-byte PLT stubs in ``.text``** (``add r12, pc, #hi``;
``add r12, r12, #lo``; ``ldr pc, [r12, #off]!``), one per import, and each stub's computed
address is a GOT slot. Decoding the idioms therefore yields import -> stub, which is how a
compiled ``bl <import>`` resolves to the address the original linked to.

**Raw file vs. loaded image.** This module reads the *raw* NSO, whose ``.data`` pointers are
**module-relative** (e.g. a GOT slot holding ``0x0184ad78`` means ``0x6184ad78``). The Ghidra
block dumps the gate compares against are *post-load* (base added, import slots patched to
trampolines). Slot **addresses** are identical in both, which is what a pool site needs; only
the slot *contents* differ, so do not mix the two when comparing values.

Usage::

    python3 tools/ledger/gotmap.py                    # summary + the GOT extent
    python3 tools/ledger/gotmap.py --symbol _ZN...    # the slot address(es) for a symbol
    python3 tools/ledger/gotmap.py --slot 0x6183800c  # the symbol a slot belongs to
    python3 tools/ledger/gotmap.py --check            # self-consistency checks
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_CACHE = REPO / "baserom" / "work" / "gotmap" / "gotmap.json"

BASE = 0x60000000

DT_NULL = 0
DT_PLTRELSZ = 2
DT_PLTGOT = 3
DT_HASH = 4
DT_STRTAB = 5
DT_SYMTAB = 6
DT_SYMENT = 11
DT_REL = 17
DT_RELSZ = 18
DT_RELENT = 19
DT_INIT_ARRAY = 25
DT_JMPREL = 23

R_ARM_ABS32 = 2
R_ARM_GLOB_DAT = 21
R_ARM_JUMP_SLOT = 22
R_ARM_RELATIVE = 23

# The only relocations that fill a GOT slot with a symbol's address.
GOT_RELOCS = (R_ARM_GLOB_DAT, R_ARM_JUMP_SLOT)

# Three reserved words precede the JUMP_SLOT entries in .got.plt.
GOT_PLT_RESERVED = 3


class GotError(Exception):
    pass


# --- the image ------------------------------------------------------------------------

class Image:
    """Address-addressable view over the decompressed NSO sections."""

    def __init__(self, sections: dict[str, tuple[int, bytes]]):
        """``sections`` maps a name to ``(loaded address, bytes)``."""
        self.sections = sections
        self.spans = sorted((addr, addr + len(blob), name)
                            for name, (addr, blob) in sections.items())

    @classmethod
    def from_nso(cls, path: Path) -> "Image":
        sys.path.insert(0, str(REPO / "tools" / "nso"))
        import nso_extract

        extracted = nso_extract.extract(Path(path))
        sections = {}
        for s in extracted["sections"]:
            sections[s["name"]] = (BASE + s["memory_offset"],
                                   extracted["data"][s["name"]])
        return cls(sections)

    def located(self, addr: int, size: int = 4) -> tuple[str, int] | None:
        """``(section name, offset)`` for a readable span, or ``None``."""
        for start, end, name in self.spans:
            if start <= addr and addr + size <= end:
                return name, addr - start
        return None

    def contains(self, addr: int, size: int = 4) -> bool:
        return self.located(addr, size) is not None

    def read(self, addr: int, size: int = 4) -> bytes:
        found = self.located(addr, size)
        if found is None:
            raise GotError(f"address 0x{addr:08x}+{size} is not in any image section")
        name, offset = found
        return self.sections[name][1][offset:offset + size]

    def u32(self, addr: int) -> int:
        return struct.unpack("<I", self.read(addr))[0]


# --- ELF dynamic metadata -------------------------------------------------------------

def mod0_address(image: Image) -> int:
    """The address of the ``MOD0`` header (magic at ``.text + 8`` in this image)."""
    text = image.sections.get("text")
    if text is None:
        raise GotError("image has no .text section")
    base, blob = text
    off = blob.find(b"MOD0")
    if off < 0:
        raise GotError("no MOD0 header found in .text")
    return base + off


def dynamic_entries(image: Image, limit: int = 0x1000) -> dict[int, int]:
    """The ``.dynamic`` table as ``tag -> value`` (first value wins; ``DT_NULL`` ends it)."""
    mod0 = mod0_address(image)
    dynamic = mod0 + image.u32(mod0 + 4)
    entries: dict[int, int] = {}
    for off in range(0, limit, 8):
        tag, value = struct.unpack("<iI", image.read(dynamic + off, 8))
        if tag == DT_NULL:
            break
        entries.setdefault(tag & 0xFFFFFFFF, value)
    if not entries:
        raise GotError("empty .dynamic table")
    return entries


def dynamic_address(dynamic: dict[int, int], tag: int, name: str) -> int:
    try:
        return BASE + dynamic[tag]
    except KeyError:
        raise GotError(f"the dynamic table has no {name} entry") from None


def _cstring(blob: bytes, offset: int) -> str:
    if offset >= len(blob):
        raise GotError(f"string offset {offset} is outside .dynstr")
    end = blob.find(b"\x00", offset)
    if end < 0:
        raise GotError(f"unterminated string at .dynstr+{offset}")
    return blob[offset:end].decode("utf-8", "replace")


def read_symbols(image: Image, dynamic: dict[int, int]) -> list[dict]:
    """The dynamic symbol table, in index order (relocations index into it)."""
    symtab = dynamic_address(dynamic, DT_SYMTAB, "DT_SYMTAB")
    strtab = dynamic_address(dynamic, DT_STRTAB, "DT_STRTAB")
    syment = dynamic.get(DT_SYMENT, 16)
    if syment < 16:
        raise GotError(f"unexpected DT_SYMENT {syment}")
    if DT_HASH in dynamic:
        # .hash: nbucket, nchain — nchain is the symbol count.
        count = image.u32(dynamic_address(dynamic, DT_HASH, "DT_HASH") + 4)
    else:
        # .dynsym is contiguous with and immediately precedes .dynstr in this image.
        count = (strtab - symtab) // syment
    strings = image.sections[image.located(strtab)[0]][1]
    strings = strings[strtab - image.sections[image.located(strtab)[0]][0]:]
    symbols = []
    for index in range(count):
        name_off, value, size, info, _other, shndx = struct.unpack(
            "<IIIBBH", image.read(symtab + index * syment, 16))
        symbols.append({
            "index": index,
            "name": _cstring(strings, name_off) if name_off else "",
            "value": value & 0x7FFFFFFF,
            "size": size,
            "type": info & 0xF,
            "bind": info >> 4,
            "shndx": shndx,
            "defined": shndx not in (0, 0xFFF1, 0xFFF2),
        })
    return symbols


def read_relocations(image: Image, addr: int, size: int, entsize: int = 8) -> list[tuple[int, int]]:
    """``(r_offset, r_info)`` pairs of a REL table, in table order."""
    if size % entsize:
        raise GotError(f"relocation table size {size} is not a multiple of {entsize}")
    out = []
    for off in range(0, size, entsize):
        out.append(struct.unpack("<II", image.read(addr + off, 8)))
    return out


def _tables(image: Image, dynamic: dict[int, int]) -> list[tuple[str, list[tuple[int, int]]]]:
    """The image's REL tables as ``(name, entries)``."""
    tables = []
    if DT_REL in dynamic:
        tables.append(("rel.dyn", read_relocations(
            image, dynamic_address(dynamic, DT_REL, "DT_REL"),
            dynamic.get(DT_RELSZ, 0), dynamic.get(DT_RELENT, 8))))
    if DT_JMPREL in dynamic:
        tables.append(("rel.plt", read_relocations(
            image, dynamic_address(dynamic, DT_JMPREL, "DT_JMPREL"),
            dynamic.get(DT_PLTRELSZ, 0), 8)))
    return tables


def got_slots(image: Image, dynamic: dict[int, int],
              symbols: list[dict]) -> dict[int, dict]:
    """``slot address -> {symbol, table, type}`` for every GOT-filling relocation.

    Slot addresses are module-relative targets made absolute (``r_offset + BASE``), i.e. the
    addresses the ledger and the code use. ``R_ARM_ABS32`` entries are deliberately excluded:
    they patch data words (vtables), not slots.
    """
    slots: dict[int, dict] = {}
    for table, entries in _tables(image, dynamic):
        for r_offset, r_info in entries:
            r_type = r_info & 0xFF
            if r_type not in GOT_RELOCS:
                continue
            index = r_info >> 8
            symbol = symbols[index]["name"] if index < len(symbols) else ""
            slot = BASE + r_offset
            slots[slot] = {"symbol": symbol, "table": table, "type": r_type,
                           "index": index}
    return slots


def got_ranges(image: Image, dynamic: dict[int, int]) -> list[tuple[str, int, int]]:
    """The GOT split into ``(.got.plt, .got)`` address ranges.

    ``.got.plt`` starts at ``DT_PLTGOT`` and holds three reserved words plus one per
    ``JUMP_SLOT``; ``.got`` follows immediately, up to the initializer array. This reproduces
    the range the loader constructs without consulting it (module-relative
    ``0x1838AE8``-``0x1848900`` for ``.got`` in this image).
    """
    plt_start = dynamic_address(dynamic, DT_PLTGOT, "DT_PLTGOT")
    plt_slots = dynamic.get(DT_PLTRELSZ, 0) // 8 + GOT_PLT_RESERVED
    plt_end = plt_start + plt_slots * 4
    if DT_INIT_ARRAY not in dynamic:
        raise GotError("the dynamic table has no DT_INIT_ARRAY entry (GOT end unknown)")
    return [(".got.plt", plt_start, plt_end),
            (".got", plt_end, BASE + dynamic[DT_INIT_ARRAY])]


def got_extent(image: Image, dynamic: dict[int, int]) -> tuple[int, int]:
    """``(start, end)`` of the whole GOT (``.got.plt`` through ``.got``)."""
    ranges = got_ranges(image, dynamic)
    return ranges[0][1], ranges[-1][2]


# --- PLT stubs ------------------------------------------------------------------------

def _imm32(imm12: int) -> int:
    """The immediate of an A32 data-processing instruction (an 8-bit value rotated right)."""
    rotate = (imm12 >> 8) & 0xF
    value = imm12 & 0xFF
    shift = 2 * rotate
    if not shift:
        return value
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF


def _is_add_pc(word: int) -> bool:
    return (word >> 16) == 0xE28F and ((word >> 12) & 0xF) == 0xC


def _is_add_r12(word: int) -> bool:
    return (word >> 16) == 0xE28C and ((word >> 12) & 0xF) == 0xC


def _is_ldr_pc(word: int) -> bool:
    return (word >> 16) == 0xE5BC and ((word >> 12) & 0xF) == 0xF


def plt_stubs(image: Image) -> dict[int, int]:
    """``stub address -> GOT slot address`` for every A32 PLT stub in ``.text``.

    The image calls an import through a 12-byte stub (one per import)::

        add  r12, pc, #hi        ; r12 = (stub + 8) + hi
        add  r12, r12, #lo       ; r12 += lo
        ldr  pc, [r12, #off]!    ; jump through the GOT slot at r12 + off

    The three immediates are chosen by the linker so that the sum lands on the slot; the sum
    wraps modulo 2^32, which is why it must not be range-checked. Anything that is not exactly
    this idiom is ignored.
    """
    text = image.sections.get("text")
    if text is None:
        raise GotError("image has no .text section")
    base, blob = text
    stubs: dict[int, int] = {}
    for off in range(0, len(blob) - 11, 4):
        w0, w1, w2 = struct.unpack_from("<III", blob, off)
        if not (_is_add_pc(w0) and _is_add_r12(w1) and _is_ldr_pc(w2)):
            continue
        r12 = (base + off + 8 + _imm32(w0 & 0xFFF)) & 0xFFFFFFFF
        r12 = (r12 + _imm32(w1 & 0xFFF)) & 0xFFFFFFFF
        stubs[base + off] = (r12 + (w2 & 0xFFF)) & 0xFFFFFFFF
    return stubs


def import_stubs(image: Image, model: dict | None = None) -> dict[str, int]:
    """``import symbol -> stub address``: the inverse of :func:`plt_stubs` via the GOT."""
    model = model or build(image)
    return dict(model["imports"])


# --- cache ----------------------------------------------------------------------------
#
# The map is a function of the NSO only, and rebuilding it costs ~2.4 s (pure-Python LZ4 over
# the whole image), so it is cached as JSON next to the other git-ignored work products. The
# fingerprint is the image's size and mtime: a different file rebuilds, an identical one loads.
# v2 adds ``values`` (slot contents), which the pool resolver needs.
CACHE_VERSION = 2


def _fingerprint(path: Path) -> dict:
    stat = Path(path).stat()
    return {"path": str(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def to_json(model: dict, nso: Path) -> dict:
    """The JSON payload written to the cache (addresses as 8-hex strings, for readability)."""
    return {
        "version": CACHE_VERSION,
        "nso": _fingerprint(nso),
        "ranges": [[name, lo, hi] for name, lo, hi in model["ranges"]],
        "slots": {f"{slot:08x}": {"symbol": info["symbol"], "table": info["table"]}
                  for slot, info in model["slots"].items()},
        "stubs": {f"{stub:08x}": f"{slot:08x}" for stub, slot in model["stubs"].items()},
        "imports": {name: stub for name, stub in model["imports"].items()},
        "values": {f"{slot:08x}": value for slot, value in model["values"].items()},
    }


def load_or_build(nso: Path = DEFAULT_NSO, cache: Path | None = DEFAULT_CACHE) -> dict:
    """The map payload, from ``cache`` when it is current, else built from ``nso``."""
    stamp = _fingerprint(nso)
    if cache is not None and Path(cache).exists():
        try:
            payload = json.loads(Path(cache).read_text())
        except (json.JSONDecodeError, OSError):
            payload = None
        if (payload and payload.get("version") == CACHE_VERSION
                and payload.get("nso", {}).get("size") == stamp["size"]
                and payload.get("nso", {}).get("mtime_ns") == stamp["mtime_ns"]):
            return payload
    payload = to_json(build(Image.from_nso(nso)), nso)
    if cache is not None:
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return payload


def symbol_stubs(nso: Path = DEFAULT_NSO,
                 cache: Path | None = DEFAULT_CACHE) -> dict[str, int]:
    """``import symbol -> stub address`` from the cached map (built on first use)."""
    return {name: int(addr) for name, addr in load_or_build(nso, cache)["imports"].items()}


def stub_names(nso: Path = DEFAULT_NSO,
               cache: Path | None = DEFAULT_CACHE) -> dict[str, str]:
    """``stub address (8-hex) -> import name``, for annotating a bundle."""
    payload = load_or_build(nso, cache)
    slots = payload.get("slots", {})
    return {stub: slots[slot]["symbol"] for stub, slot in payload.get("stubs", {}).items()
            if slot in slots}


def slot_targets(nso: Path = DEFAULT_NSO,
                 cache: Path | None = DEFAULT_CACHE) -> dict[int, str]:
    """``GOT slot -> a name for what it points at``, for a pool reference's target.

    An import slot is named by its symbol. Any other slot holds an address, which a caller can
    name from the ledger — so the raw payload's ``values`` is what this exposes, and the naming
    (``D_<addr>``) is the caller's business.
    """
    payload = load_or_build(nso, cache)
    named = {int(slot, 16): info["symbol"] for slot, info in payload.get("slots", {}).items()}
    for slot, value in payload.get("values", {}).items():
        named.setdefault(int(slot, 16), f"D_{int(value):08x}")
    return named


def slot_values(image: Image, ranges: list[tuple[str, int, int]]) -> dict[int, int]:
    """``GOT slot -> the address it holds``, in the ledger's address space.

    The raw NSO stores module-relative values, so the image base is added. A zero slot is an
    import the loader has not patched yet and is omitted. For an internal symbol the slot is
    what makes it reachable at all: the static link resolved it, so no relocation names it.
    """
    out: dict[int, int] = {}
    for _name, lo, hi in ranges:
        for slot in range(lo, hi, 4):
            try:
                value = image.u32(slot)
            except GotError:
                continue
            if value:
                out[slot] = value + BASE if value < BASE else value
    return out


def build(image: Image) -> dict:
    """Everything the map is derived from, in one pass."""
    dynamic = dynamic_entries(image)
    symbols = read_symbols(image, dynamic)
    slots = got_slots(image, dynamic, symbols)
    ranges = got_ranges(image, dynamic)
    stubs = plt_stubs(image)
    imports: dict[str, int] = {}
    for stub, slot in stubs.items():
        info = slots.get(slot)
        if info and info["symbol"]:
            imports[info["symbol"]] = stub
    return {"dynamic": dynamic, "symbols": symbols, "slots": slots,
            "ranges": ranges, "extent": (ranges[0][1], ranges[-1][2]),
            "stubs": stubs, "imports": imports,
            "values": slot_values(image, ranges)}


def symbol_slots(slots: dict[int, dict], name: str) -> list[int]:
    """The slot address(es) assigned to ``name``."""
    return sorted(slot for slot, info in slots.items() if info["symbol"] == name)


def check(image: Image, model: dict | None = None) -> list[str]:
    """Self-consistency checks; an empty list means the map is coherent."""
    model = model or build(image)
    slots, (start, end) = model["slots"], model["extent"]
    ranges = model["ranges"]
    problems = []
    if start >= end:
        problems.append(f"empty GOT extent 0x{start:08x}..0x{end:08x}")
    seen: dict[str, int] = {}
    for slot, info in sorted(slots.items()):
        if not any(lo <= slot < hi for _name, lo, hi in ranges):
            problems.append(f"slot 0x{slot:08x} ({info['symbol']}) is outside the GOT")
        if not image.contains(slot):
            problems.append(f"slot 0x{slot:08x} is not readable")
            continue
        value = image.u32(slot)
        if image.contains(value):
            # An internal symbol the static link resolved — fine, but it must not be an
            # import reloc, whose slot is a loader stub until load time.
            if not info["symbol"]:
                problems.append(f"slot 0x{slot:08x} has an address but no symbol")
        if info["symbol"]:
            if info["symbol"] in seen:
                problems.append(f"symbol {info['symbol']} has two slots: "
                                f"0x{seen[info['symbol']]:08x} and 0x{slot:08x}")
            seen[info["symbol"]] = slot
    for stub, slot in sorted(model.get("stubs", {}).items()):
        if not image.contains(stub):
            problems.append(f"stub 0x{stub:08x} is not inside .text")
        if slot not in slots:
            problems.append(f"stub 0x{stub:08x} jumps through slot 0x{slot:08x}, which no "
                            f"relocation names")
    return problems


# --- CLI ------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--symbol", default=None, help="print the slot(s) for this symbol")
    ap.add_argument("--slot", default=None, help="print the symbol for this slot (hex)")
    ap.add_argument("--stub", default=None, help="print the import a .text stub jumps to (hex)")
    ap.add_argument("--check", action="store_true", help="run the self-consistency checks")
    args = ap.parse_args(argv)

    try:
        image = Image.from_nso(args.nso)
        model = build(image)
    except (GotError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    slots = model["slots"]
    start, end = model["extent"]

    if args.symbol:
        found = symbol_slots(slots, args.symbol)
        if not found:
            print(f"no GOT slot for {args.symbol!r}")
            return 1
        for slot in found:
            print(f"0x{slot:08x}  {slots[slot]['table']}  {args.symbol}")
        return 0

    if args.slot:
        try:
            slot = int(args.slot, 0)
        except ValueError:
            print(f"error: bad slot {args.slot!r}", file=sys.stderr)
            return 2
        info = slots.get(slot)
        print(f"0x{slot:08x}  {info['symbol']}" if info else
              f"0x{slot:08x}  (not a GOT-filling relocation)")
        return 0 if info else 1

    if args.stub:
        try:
            stub = int(args.stub, 0)
        except ValueError:
            print(f"error: bad stub {args.stub!r}", file=sys.stderr)
            return 2
        slot = model["stubs"].get(stub)
        if slot is None:
            print(f"0x{stub:08x}  (no PLT stub at this address)")
            return 1
        info = slots.get(slot)
        print(f"0x{stub:08x} -> 0x{slot:08x}  {info['symbol'] if info else '?'}")
        return 0

    print(f"image      {args.nso}")
    print(f"symbols    {len(model['symbols'])} dynamic symbols")
    for name, lo, hi in model["ranges"]:
        print(f"GOT        {name:<8} 0x{lo:08x}..0x{hi:08x} ({(hi - lo) // 4} slot(s))")
    by_table: dict[str, int] = {}
    for info in slots.values():
        by_table[info["table"]] = by_table.get(info["table"], 0) + 1
    print(f"slots      {len(slots)} named by relocation "
          f"({', '.join(f'{k}: {v}' for k, v in sorted(by_table.items()))})")
    symbols = {info["symbol"] for info in slots.values()}
    print(f"symbols    {len(symbols)} distinct import(s) with a slot")
    print(f"stubs      {len(model['stubs'])} PLT stub(s) in .text, "
          f"{len(model['imports'])} import(s) resolvable")

    if args.check:
        problems = check(image, model)
        print()
        if problems:
            print(f"FAIL: {len(problems)} problem(s)")
            for p in problems[:20]:
                print(f"  - {p}")
            return 1
        print("OK: slots are inside the GOT, readable, and one slot per symbol")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
