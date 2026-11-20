"""The byte gate: compile one reconstructed function and compare it to the original.

This is the Phase-3 per-function claim mechanism (``docs/architecture.md`` →
*Unmatched-function fallback*, Model C). It is **link-free**: it compiles a single
translation unit to an object and diffs the one function against the original bytes at its
ledger address, so matching is independent of "does the whole tree build".

Pipeline
--------
1. Look up the ``(module, addr)`` entry in the committed ledger.
2. Compile ``src/<module>/<group>.cpp`` with the pinned toolchain (``config/toolchain.json``)
   and ``-ffunction-sections``, so the function has its own section.
3. Extract that function's bytes from the ELF32 object (by its defined ``FUNC`` symbol),
   together with the relocations applied to its own section.
4. Dump the original memory blocks (``tools/ghidra/dump_blocks.sh``) and compare the compiled
   function body against the original at its offset within its block.
5. Optionally ``--update`` the ledger's ``verify`` axis on a match, together with the
   ``gate`` provenance of that verdict (``raw`` while the comparison is byte-for-byte).

Body length vs. block partition
-------------------------------
The ledger's ``size`` is the block **partition** — the bytes up to the next cut point — *not*
the function body. A partition over-covers its function whenever an unsymbolised region (a
routine the inventory missed, or an interior literal pool with no cut) sits between this
function and the next cut. ``func_601a72e4`` (``new_b`` in the PoC) is the canonical case: a
**60 B body in a 1368 B partition**, because the next cut point is 0x601a783c.

The gate requires an **authoritative extent** and compares exactly that many bytes. The loop
derives it from the inventory's instruction span and every reference PC-relative literal-load
target, including intervening alignment bytes. ``--body N`` supplies that extent directly.
The ledger partition and reference block are bounds only: a missing or out-of-bounds extent
fails closed, and a candidate whose length differs is rejected. A matching prefix is never
sufficient, whether the omitted suffix is code, padding, or a literal pool.

Scope: the gate compares generated code against the original with **relocations resolved**
(stage 2). A branch or call in an unlinked object encodes a target-independent placeholder
(``0xEAFFFFFE`` for every ``b``, ``0xEBFFFFFE`` for every ``bl``) — the callee's identity lives
only in the relocation. The gate therefore patches each ``R_ARM_CALL``/``R_ARM_JUMP24`` site
with the immediate the linker would have produced, using the callee's **original** address from
the ledger, and then compares bytes exactly. A wrong callee resolves to a different immediate
and still fails, so this is not a weaker check; it is the comparison a link would have made.

Fail-closed rule: a function may only claim a match when **every** relocation in its body was
verified. Two relocation classes are resolved:

* **branch/call** (`R_ARM_CALL`, `R_ARM_JUMP24`, …) — patched with the callee's original
  address, from the ledger or, for an import, from its PLT stub;
* **literal pool** (`R_ARM_GOT_PREL`) — patched to `GOT(symbol) + addend − P`, where the addend
  is the object's own in-place word and `GOT(symbol)` comes from the map (an import's slot, or
  an internal object's slot named by the address it holds).

Anything else — a jump table, an unnameable symbol, a symbol with no GOT slot — is reported as
`unverified-reloc` and never matches, even if the raw bytes happen to agree. A match reached
through resolved relocations records `gate=reloc` in the ledger; a purely byte-identical one
records `gate=raw` (see `docs/architecture.md` -> *Gate provenance*).

An import has no ledger address, but the image does not call it by name either: it calls a
12-byte **PLT stub** in `.text`, which jumps through the import's GOT slot. `gotmap` recovers
import -> stub from the stub's own code, so `bl <import>` resolves to the address the original
linked to (695 imports, one stub each). A call to an unresolved name is still refused.

Usage::

    tools/ledger/bytegate.py <module> <addr> [options]

Options:
    --ledger FILE   committed ledger (default config/main/ledger.tsv)
    --src-root DIR  source root (default <repo>/src)
    --build-config FILE  build layout incl. include dirs (default config/build.json)
    --ref-bin FILE  a block .bin to compare against (skips the Ghidra dump)
    --ref-dir DIR   where to dump blocks (default baserom/work/bytegate/ref)
    --nso FILE      NSO to dump (default baserom/main.nso)
    --body N        authoritative body length; requires an exact length match
    --show          print the full byte diff on mismatch
    --update        set verify=match in the ledger when the function matches
    --no-color      disable ANSI colour (also honours NO_COLOR and non-TTY output)
    --report FILE   write a machine-readable JSON result (closeness input; see gate_result)

Exit codes:
    0  match
    1  byte mismatch (compiled cleanly, bytes differ)
    2  usage/config error (no entry, no source, bad ELF, clang missing)
    3  compilation failed (distinct from a mismatch, so callers cannot confuse the two)
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

from ledgerlib import read_entries, set_fields
import gotmap

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_SRC_ROOT = REPO / "src"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"
DEFAULT_BUILD_CONFIG = REPO / "config" / "build.json"
DEFAULT_STUB_CACHE = gotmap.DEFAULT_CACHE


def include_dirs(build_config: Path) -> list[str]:
    """Include dirs from the shared build layout, so the gate and the build agree."""
    if not build_config.exists():
        return []
    raw = json.loads(build_config.read_text())
    return [f"-I{(REPO / d).resolve()}" for d in raw.get("include_dirs", [])]

_COLORS = {
    "GREEN": "\033[32m",
    "RED": "\033[31m",
    "YELLOW": "\033[33m",
    "DIM": "\033[2m",
    "BOLD": "\033[1m",
    "RESET": "\033[0m",
}
GREEN, RED, YELLOW, DIM, BOLD, RESET = _COLORS.values()


def should_color(no_color: bool, stream, env) -> bool:
    """Whether to emit ANSI colour: off for ``--no-color``, ``NO_COLOR``, or a non-TTY."""
    if no_color or "NO_COLOR" in env:
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def set_color(enabled: bool) -> None:
    """Enable/disable the module-level ANSI codes (called once from ``main``)."""
    global GREEN, RED, YELLOW, DIM, BOLD, RESET
    vals = _COLORS if enabled else {k: "" for k in _COLORS}
    GREEN, RED, YELLOW, DIM, BOLD, RESET = (vals[k] for k in _COLORS)


# --- ELF32 (ARM) ----------------------------------------------------------------------

class ElfError(Exception):
    pass


def _elf32(path: Path) -> tuple[bytes, list[dict], list[dict], dict[int, list[dict]]]:
    """Return (data, sections, symbols, symtabs) for a little-endian ELF32 object.

    ``symbols`` is every symbol flattened (the function lookup); ``symtabs`` keys a symbol-table
    section index to that table's own symbol list, which is what a relocation section's
    ``sh_link`` points at.
    """
    data = path.read_bytes()
    if data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        raise ElfError("not a little-endian ELF32 file")
    e_shoff = struct.unpack_from("<I", data, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", data, 0x2E)[0]
    e_shnum = struct.unpack_from("<H", data, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", data, 0x32)[0]

    def sh(i: int) -> dict:
        base = e_shoff + i * e_shentsize
        name, typ, flags, addr, off, size, link, info, align, entsize = \
            struct.unpack_from("<IIIIIIIIII", data, base)
        return {"index": i, "name_off": name, "type": typ, "flags": flags, "addr": addr,
                "offset": off, "size": size, "link": link, "info": info,
                "align": align, "entsize": entsize}

    sections = [sh(i) for i in range(e_shnum)]
    strtab = sections[e_shstrndx]
    strings = data[strtab["offset"]:strtab["offset"] + strtab["size"]]

    def name_at(off: int) -> str:
        end = strings.index(b"\x00", off)
        return strings[off:end].decode("utf-8", "replace")

    for s in sections:
        s["name"] = name_at(s["name_off"])

    symbols: list[dict] = []
    symtabs: dict[int, list[dict]] = {}
    for s in sections:
        if s["type"] != 2:  # SHT_SYMTAB
            continue
        symstr = sections[s["link"]]
        symdata = data[symstr["offset"]:symstr["offset"] + symstr["size"]]
        table: list[dict] = []
        for o in range(0, s["size"], 16):
            n, val, sz, info, _other, shndx = struct.unpack_from("<IIIBBH", data,
                                                                 s["offset"] + o)
            entry = {
                "name": name_at_bytes(symdata, n),
                "value": val, "size": sz, "info": info, "shndx": shndx,
                "type": info & 0xF, "bind": info >> 4,
            }
            table.append(entry)
            symbols.append(entry)
        symtabs[s["index"]] = table
    return data, sections, symbols, symtabs


def name_at_bytes(blob: bytes, off: int) -> str:
    end = blob.index(b"\x00", off)
    return blob[off:end].decode("utf-8", "replace")


def extract_function(obj: Path, names: list[str]) -> tuple[bytes, str, list[dict]]:
    """Return (bytes, symbol name, relocations) for the object's one function.

    ``names`` are candidate identities (the ledger name and group); they disambiguate the
    rare multi-function object. ``relocations`` are the ones applied to the function's own
    section (see :func:`function_relocations`). Raises if zero or an unidentifiable plurality
    of functions is found.
    """
    data, sections, symbols, symtabs = _elf32(obj)
    funcs = [s for s in symbols
             if s["type"] == 2 and s["shndx"] not in (0, 0xFFF1, 0xFFF2)]
    if not funcs:
        raise ElfError(f"{obj}: no defined function symbol")
    if len(funcs) > 1:
        chosen = [s for s in funcs if s["name"] in names]
        if len(chosen) != 1:
            listing = ", ".join(s["name"] for s in funcs)
            raise ElfError(f"{obj}: {len(funcs)} function symbols ({listing}); "
                           f"cannot identify one — one function per file expected")
        func = chosen[0]
    else:
        func = funcs[0]

    sec = sections[func["shndx"]]
    code = data[sec["offset"]:sec["offset"] + sec["size"]]
    return code, func["name"], function_relocations(data, sections, symtabs, sec)


# --- relocations ----------------------------------------------------------------------

# The A32 branch/call relocation types. ``R_ARM_PC24``/``R_ARM_PLT32`` are the older
# spellings of the same encodings as ``R_ARM_JUMP24``/``R_ARM_CALL``; clang emits the latter.
BRANCH_RELOCS = {1: "R_ARM_PC24", 27: "R_ARM_PLT32", 28: "R_ARM_CALL", 29: "R_ARM_JUMP24"}

# Literal-pool relocations: the word names a GOT slot, and the linker writes
# ``GOT(symbol) + addend - P`` where the addend is the object's in-place word.
POOL_RELOCS = {96: "R_ARM_GOT_PREL"}


def function_relocations(data: bytes, sections: list[dict], symtabs: dict[int, list[dict]],
                         sec: dict) -> list[dict]:
    """The relocations applied to ``sec`` (the function's own section), in offset order.

    Only relocations that patch *this* section count. The ``.ARM.exidx`` entry of every
    function in this image carries an ``R_ARM_PREL31`` against the exidx section, so it is
    excluded by construction rather than by type. Each entry is
    ``{offset, type, symbol, addend}``.
    """
    out: list[dict] = []
    for s in sections:
        if s["type"] not in (4, 9) or s["info"] != sec["index"]:  # SHT_RELA / SHT_REL
            continue
        table = symtabs.get(s["link"], [])
        entsize = s["entsize"] or (8 if s["type"] == 9 else 12)
        for o in range(0, s["size"], entsize):
            r_off, r_info = struct.unpack_from("<II", data, s["offset"] + o)
            addend = (struct.unpack_from("<i", data, s["offset"] + o + 8)[0]
                      if entsize >= 12 else 0)
            idx = r_info >> 8
            out.append({
                "offset": r_off, "type": r_info & 0xFF,
                "symbol": table[idx]["name"] if idx < len(table) else "",
                "addend": addend,
            })
    out.sort(key=lambda r: r["offset"])
    return out


def ledger_addresses(entries: list[dict]) -> dict[str, int]:
    """Symbol name -> image address for every addressed ledger entry.

    Ledger addresses are unique, so this is a bijection and a symbol's identity is its name;
    aliases cannot collide. Externals have no address and are deliberately absent — their
    calls resolve through a PLT stub instead (see :func:`branch_addresses`).
    """
    return {e["name"]: int(e["addr"], 16) for e in entries if e["addr"]}


def branch_addresses(relocs: list[dict], entries: list[dict], nso: Path,
                     stub_cache: Path | None) -> tuple[dict[str, int], int]:
    """Symbol -> address for branch resolution, and how many sites used a PLT stub.

    The ledger names every defined function. An import has no ledger address, but the image
    calls it through a 12-byte PLT stub in ``.text``; ``gotmap`` recovers import -> stub from
    the stub's own code and the GOT relocations. Ledger names win on any collision, and an
    unavailable stub map is a warning (the site then stays ``unverified-reloc``, as before).
    """
    ledger = ledger_addresses(entries)
    stubs: dict[str, int] = {}
    if any(r["symbol"] not in ledger for r in relocs):
        try:
            stubs = gotmap.symbol_stubs(nso, stub_cache)
        except (gotmap.GotError, OSError, ValueError) as e:
            print(f"warning: PLT stub map unavailable ({e}); import calls stay unverified",
                  file=sys.stderr)
    via_stub = sum(1 for r in relocs
                   if r["symbol"] in stubs and r["symbol"] not in ledger)
    return {**stubs, **ledger}, via_stub


def resolve_branches(cand: bytes, relocs: list[dict], insn_base: int,
                     addresses: dict[str, int]) -> tuple[bytes, list[tuple[int, str]]]:
    """Rewrite branch/call immediates to the value the linker would have produced.

    The unresolved object carries this image's defining fact: an unlinked branch encodes the
    target-independent placeholder ``0xEAFFFFFE``/``0xEBFFFFFE``, so only the relocation names
    the callee. Patching the site with the callee's *original* address restores the exact byte
    comparison — a wrong callee resolves to a different immediate and still fails.

    Returns ``(patched, unresolved)``; each unresolved item is ``(offset, reason)``. The caller
    must fail closed on a non-empty list: an unverified site means the comparison cannot be
    trusted, not that the code is wrong.
    """
    buf = bytearray(cand)
    unresolved: list[tuple[int, str]] = []
    for r in relocs:
        off = r["offset"]
        site = f"+0x{off:x}"
        name = BRANCH_RELOCS.get(r["type"])
        if name is None:
            unresolved.append((off, f"{site}: relocation type {r['type']} is not a verified "
                                    f"branch/call"))
            continue
        target = addresses.get(r["symbol"])
        if target is None:
            unresolved.append((off, f"{site}: {r['symbol'] or '<no symbol>'} has no ledger "
                                    f"address"))
            continue
        if off % 4 or off + 4 > len(buf):
            unresolved.append((off, f"{site}: not an aligned instruction inside the body"))
            continue
        word = struct.unpack_from("<I", buf, off)[0]
        if (word >> 25) & 0x7 != 0b101 or (word >> 28) == 0xF:
            unresolved.append((off, f"{site}: {name} but the word is not an A32 branch"))
            continue
        delta = target + r["addend"] - (insn_base + off + 8)
        if delta % 4 or not (-(1 << 25) <= delta < (1 << 25)):
            unresolved.append((off, f"{site}: target {target:08x} is out of branch range"))
            continue
        struct.pack_into("<I", buf, off, (word & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
    return bytes(buf), unresolved


def resolve_pools(cand: bytes, relocs: list[dict], insn_base: int,
                  slots: dict[str, int]) -> tuple[bytes, list[tuple[int, str]]]:
    """Rewrite literal-pool words to the value the linker would have produced.

    For ``R_ARM_GOT_PREL`` the in-place word is the *addend* ``A``; the linked value is
    ``GOT(symbol) + A - P``, with ``P`` the word's address in the original. ``slots`` maps a
    symbol to the slot the original assigned it (an import from the relocation table, an
    internal object from the slot contents), so a wrong symbol resolves to a different slot
    and still fails the byte comparison.
    """
    buf = bytearray(cand)
    unresolved: list[tuple[int, str]] = []
    for r in relocs:
        off = r["offset"]
        site = f"+0x{off:x}"
        slot = slots.get(r["symbol"])
        if slot is None:
            unresolved.append((off, f"{site}: {r['symbol'] or '<no symbol>'} has no GOT slot"))
            continue
        if off % 4 or off + 4 > len(buf):
            unresolved.append((off, f"{site}: not an aligned word inside the body"))
            continue
        addend = struct.unpack_from("<I", buf, off)[0]
        word = (slot + addend - (insn_base + off)) & 0xFFFFFFFF
        struct.pack_into("<I", buf, off, word)
    return bytes(buf), unresolved


def resolve_relocations(cand: bytes, relocs: list[dict], insn_base: int,
                        addresses: dict[str, int], slots: dict[str, int]
                        ) -> tuple[bytes, list[tuple[int, str]]]:
    """Resolve every relocation the gate understands; anything else fails closed."""
    patched, unresolved = cand, []
    branches = [r for r in relocs if r["type"] in BRANCH_RELOCS]
    pools = [r for r in relocs if r["type"] in POOL_RELOCS]
    for r in relocs:
        if r["type"] not in BRANCH_RELOCS and r["type"] not in POOL_RELOCS:
            unresolved.append((r["offset"], f"+0x{r['offset']:x}: relocation type {r['type']} "
                                              f"is not verified"))
    if branches:
        patched, problems = resolve_branches(patched, branches, insn_base, addresses)
        unresolved += problems
    if pools:
        patched, problems = resolve_pools(patched, pools, insn_base, slots)
        unresolved += problems
    return patched, unresolved


def pool_slots(entries: list[dict], payload: dict) -> dict[str, int]:
    """``symbol -> GOT slot`` for literal-pool resolution.

    Two sources, because the image has two kinds of slot: an **import** is named by the
    dynamic relocation that fills it, while an **internal** object is resolved by the static
    link and is therefore named by nothing — but its slot *holds its address*, so the address
    names it as ``D_<addr>``. The ledger defines which addresses are data, so only those are
    offered; anything else stays unresolvable and fails closed.
    """
    out: dict[str, int] = {}
    named: set[int] = set()
    for slot_hex, info in payload.get("slots", {}).items():
        slot = int(slot_hex, 16)
        named.add(slot)
        if info.get("symbol"):
            out[info["symbol"]] = slot
    blocks = sorted((int(e["addr"], 16), int(e["addr"], 16) + int(e["size"]))
                    for e in entries if e["kind"] == "data" and e["addr"])
    starts = [lo for lo, _hi in blocks]
    for slot_hex, value in payload.get("values", {}).items():
        slot = int(slot_hex, 16)
        if slot in named:
            continue
        i = bisect.bisect_right(starts, value) - 1
        if i >= 0 and blocks[i][0] <= value < blocks[i][1]:
            out.setdefault(f"D_{value:08x}", slot)
    return out


# --- reference bytes ------------------------------------------------------------------

def block_bin(ref_dir: Path, block: str) -> Path:
    """Locate ``<block>_<startHex>.bin`` (the ledger stores no block start)."""
    matches = [p for p in ref_dir.iterdir()
               if p.name.startswith(block + "_") and p.suffix == ".bin"]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{ref_dir}: expected exactly one {block}_*.bin, found {len(matches)}")
    return matches[0]


def block_start(bin_path: Path) -> int:
    return int(bin_path.stem.rsplit("_", 1)[-1], 16)


def dump_blocks_ref(nso: Path, ref_dir: Path) -> None:
    script = REPO / "tools" / "ghidra" / "dump_blocks.sh"
    subprocess.run(["bash", str(script), str(nso), str(ref_dir)], check=True)


# --- diff -----------------------------------------------------------------------------

def print_diff(cand: bytes, ref: bytes, show: bool) -> None:
    n = max(len(cand), len(ref))
    print(f"    compiled {len(cand)} B, original {len(ref)} B")
    bad = [i for i in range(min(len(cand), len(ref))) if cand[i] != ref[i]]
    print(f"    {len(bad)} differing byte(s)"
          + (f"; first at +0x{bad[0]:x}" if bad else ""))
    if not show:
        return
    words = (n + 3) // 4
    for w in range(words):
        a = cand[4 * w:4 * w + 4]
        b = ref[4 * w:4 * w + 4]
        mark = "  " if a == b else "! "
        col = RESET if a == b else RED
        print(f"    {col}{mark}+0x{4*w:04x}  got {a.hex(' '):11}  want {b.hex(' '):11}{RESET}")


DIFF_WORD_LIMIT = 16


def diff_words(cand: bytes, ref: bytes, limit: int = DIFF_WORD_LIMIT) -> list[dict]:
    """The differing 4-byte words over the compared span, aligned to A32 words.

    Each entry is ``{"offset": <byte offset>, "got": <candidate hex>, "want": <reference hex>}``.
    A32 is fixed-width, so a divergence is normally one whole instruction: this turns the gate's
    opaque byte count (``3 differing byte(s); first at +0x0``) into the exact instruction pair an
    author — or a retry loop — can act on. Bounded to ``limit`` words so a wildly different body
    cannot bloat the report; a candidate whose length differs still yields words up to the shorter
    span.
    """
    span = min(len(cand), len(ref))
    out: list[dict] = []
    for off in range(0, span, 4):
        a, b = cand[off:off + 4], ref[off:off + 4]
        if a != b:
            out.append({"offset": off, "got": a.hex(), "want": b.hex()})
            if len(out) >= limit:
                break
    return out


# --- the comparison rule --------------------------------------------------------------

def compare_body(cand: bytes, block: bytes, off: int, partition: int,
                 body: int | None) -> tuple[bool, bytes, str]:
    """Compare exactly ``body`` reference bytes; return ``(ok, ref, status)``.

    ``body`` is the authoritative instruction-plus-pool extent. The ledger partition and
    reference block are bounds, never comparison lengths. A missing or inconsistent extent
    fails closed rather than accepting a candidate-sized prefix.

    Status values:

    * ``match``          — the complete body matches;
    * ``missing-body``   — no authoritative extent was supplied;
    * ``invalid-extent`` — the extent is outside the partition or reference block;
    * ``empty-body``     — the object defined a zero-length function;
    * ``body-length``    — the compiled length differs from the authoritative extent;
    * ``mismatch``       — the lengths agree but the bytes differ.
    """
    if body is None:
        return False, b"", "missing-body"
    ref = block[off:off + body] if off >= 0 and body > 0 else b""
    if body <= 0 or body > partition or off < 0 or off + body > len(block):
        return False, ref, "invalid-extent"
    if not cand:
        return False, ref, "empty-body"
    if len(cand) != body:
        return False, ref, "body-length"
    return (cand == ref), ref, ("match" if cand == ref else "mismatch")


def gate_result(module: str, addr: str, name: str, cand: bytes, ref: bytes, ok: bool,
                status: str, body: int | None, partition: int,
                has_reloc: bool, gate: str = "raw",
                relocs: dict | None = None) -> dict:
    """The machine-readable result of one gate run (the near-miss bank's closeness input).

    Pure, so it is unit-tested and stable: ``diff_count`` is the divergence count over the
    compared span, and ``body`` is the authoritative extent when one was asserted. ``diff_words``
    carries the differing instructions themselves (see :func:`diff_words`) so a caller can act on
    a mismatch without re-deriving the comparison. ``gate`` is the provenance a match was
    recorded with, and ``relocs`` the counts/reasons behind it.
    """
    span = min(len(cand), len(ref))
    diff_count = sum(1 for i in range(span) if cand[i] != ref[i])
    first_diff = next((i for i in range(span) if cand[i] != ref[i]), None)
    return {
        "module": module, "addr": addr, "name": name,
        "ok": ok, "status": status,
        "body": body, "partition": partition,
        "cand_len": len(cand), "ref_len": len(ref),
        "diff_count": diff_count, "first_diff": first_diff,
        "diff_words": diff_words(cand, ref),
        "has_reloc": has_reloc, "gate": gate,
        "relocs": relocs or {"total": 0, "unresolved": []},
    }


def print_status(status: str, cand_len: int, partition: int,
                 body: int | None) -> None:
    """Explain a non-plain-mismatch status on its own line."""
    if status == "missing-body":
        print(f"  {RED}reason: no authoritative instruction-plus-pool extent was supplied; "
              f"refusing to compare a candidate-sized prefix{RESET}")
    elif status == "invalid-extent":
        print(f"  {RED}reason: extent {body} B is outside the {partition} B partition or "
              f"the reference block{RESET}")
    elif status == "empty-body":
        print(f"  {RED}reason: compiled function is empty (0 B); the ledger entry is "
              f"{partition} B{RESET}")
    elif status == "body-length":
        print(f"  {RED}reason: compiled body {cand_len} B != asserted --body {body} B{RESET}")
    elif status == "unverified-reloc":
        print(f"  {RED}reason: a relocation site could not be verified (see the list "
              f"above); refusing to claim a match{RESET}")


# --- main -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module")
    ap.add_argument("addr")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--src-root", type=Path, default=DEFAULT_SRC_ROOT)
    ap.add_argument("--ref-bin", type=Path, default=None)
    ap.add_argument("--ref-dir", type=Path, default=REPO / "baserom" / "work" / "bytegate" / "ref")
    ap.add_argument("--nso", type=Path, default=REPO / "baserom" / "main.nso")
    ap.add_argument("--toolchain", type=Path, default=DEFAULT_TOOLCHAIN)
    ap.add_argument("--build-config", type=Path, default=DEFAULT_BUILD_CONFIG)
    ap.add_argument("--build-dir", type=Path, default=REPO / "baserom" / "work" / "bytegate")
    ap.add_argument("--stub-cache", type=Path, default=DEFAULT_STUB_CACHE,
                    help="cached GOT/PLT map (default under baserom/work; built on first use)")
    ap.add_argument("--body", type=int, default=None,
                    help="authoritative body length in bytes; requires an exact length match")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--no-color", action="store_true",
                    help="disable ANSI colour (also honours NO_COLOR and non-TTY output)")
    ap.add_argument("--report", type=Path, default=None,
                    help="write a machine-readable JSON result (see gate_result) here")
    args = ap.parse_args(argv)

    set_color(should_color(args.no_color, sys.stdout, os.environ))

    addr = args.addr.lower().removeprefix("0x").zfill(8)
    entries = read_entries(args.ledger)
    entry = next((e for e in entries
                  if e["module"] == args.module and e["addr"] == addr), None)
    if entry is None:
        print(f"error: no ledger entry ({args.module}, {addr})", file=sys.stderr)
        return 2
    if entry["kind"] != "function":
        print(f"error: ({args.module}, {addr}) is kind {entry['kind']!r}, not a function",
              file=sys.stderr)
        return 2

    size = int(entry["size"])
    src = args.src_root / args.module / f"{entry['group']}.cpp"
    if not src.exists():
        print(f"error: no source at {src}\n"
              f"  create it as the reconstruction of {entry['name']} ({entry['block']}, "
              f"{size} B)", file=sys.stderr)
        return 2

    tc = json.loads(args.toolchain.read_text())
    clang = tc.get("clang", "clang")
    if not args.build_config.exists():
        print(f"warning: build config {args.build_config} not found — compiling with no "
              f"include dirs", file=sys.stderr)
    cflags = (list(tc["cflags"]) + list(tc.get("section_flags", []))
              + include_dirs(args.build_config))

    args.build_dir.mkdir(parents=True, exist_ok=True)
    obj = args.build_dir / f"{entry['name']}.o"
    cmd = [clang, *cflags, "-c", str(src), "-o", str(obj)]
    print(f"compile: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"error: clang not found ({clang}); run inside the devcontainer", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"error: compilation failed (clang exit {e.returncode}); see the compiler output "
              f"above", file=sys.stderr)
        return 3

    try:
        cand, sym, relocs = extract_function(obj, [entry["name"], entry["group"]])
    except ElfError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"function: {entry['name']}  (object symbol {sym})")
    patched, unresolved = cand, []
    via_stub = 0
    via_pool = 0
    if relocs:
        addresses, via_stub = branch_addresses(relocs, entries, args.nso, args.stub_cache)
        slots: dict[str, int] = {}
        if any(r["type"] in POOL_RELOCS for r in relocs):
            try:
                slots = pool_slots(entries,
                                   gotmap.load_or_build(args.nso, args.stub_cache))
            except (gotmap.GotError, OSError, ValueError) as e:
                print(f"warning: GOT map unavailable ({e}); pool words stay unverified",
                      file=sys.stderr)
            via_pool = sum(1 for r in relocs
                           if r["type"] in POOL_RELOCS and r["symbol"] in slots)
        patched, unresolved = resolve_relocations(cand, relocs, int(addr, 16),
                                                  addresses, slots)
        resolved = len(relocs) - len(unresolved)
        via = ""
        if via_stub:
            via += f", {via_stub} via PLT stub"
        if via_pool:
            via += f", {via_pool} via GOT slot"
        if unresolved:
            print(f"  {YELLOW}relocations: {resolved}/{len(relocs)} resolved{via} — "
                  f"{len(unresolved)} cannot be verified{RESET}")
            for _off, why in unresolved:
                print(f"    {YELLOW}{why}{RESET}")
        else:
            print(f"  {DIM}relocations: {resolved}/{len(relocs)} resolved "
                  f"(branch/call{via}){RESET}")

    if args.ref_bin is not None:
        ref_bin = args.ref_bin
    else:
        print(f"reference: dumping blocks -> {args.ref_dir}")
        try:
            dump_blocks_ref(args.nso, args.ref_dir)
            ref_bin = block_bin(args.ref_dir, entry["block"])
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"error: could not obtain reference blocks from {args.nso}: {e}",
                  file=sys.stderr)
            return 2

    block = ref_bin.read_bytes()
    off = int(addr, 16) - block_start(ref_bin)
    ok, ref, status = compare_body(patched, block, off, size, args.body)

    # Provenance: ``reloc`` only when every relocation in the body was resolved. A single
    # unverified site makes the verdict untrustworthy, so a raw-looking match is refused.
    gate = "reloc" if relocs and not unresolved else "raw"
    if unresolved and status != "body-length":
        unverified = {site for site, _why in unresolved}
        diverging = {w["offset"] for w in diff_words(patched, ref)}
        if ok or diverging <= unverified:
            ok, status = False, "unverified-reloc"

    if args.report is not None:
        result = gate_result(args.module, addr, entry["name"], patched, ref, ok, status,
                             args.body, size, bool(relocs), gate,
                             {"total": len(relocs), "via_stub": via_stub,
                              "via_pool": via_pool,
                              "unresolved": [why for _off, why in unresolved]})
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    where = f"{entry['addr']} in {entry['block']}"
    print()
    if ok:
        print(f"{GREEN}{BOLD}>>> MATCH{RESET}  {entry['name']}  "
              f"({len(cand)} B at {where})")
    else:
        print(f"{RED}{BOLD}>>> MISMATCH{RESET}  {entry['name']}  ({where})")
        print_status(status, len(cand), size, args.body)
        print_diff(patched, ref, args.show)

    if ok and args.update:
        changed = set_fields(args.ledger, (args.module, addr),
                             {"verify": "match", "gate": gate})
        print(f"ledger: {entry['name']} verify=match gate={gate}"
              f"{' (unchanged)' if not changed else ''}")
    elif args.update and not ok:
        print("ledger: not updated (no match)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
