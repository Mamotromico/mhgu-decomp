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
3. Extract that function's bytes from the ELF32 object (by its defined ``FUNC`` symbol) and
   note whether it carries relocations.
4. Dump the original memory blocks (``tools/ghidra/dump_blocks.sh``) and compare the compiled
   function body against the original at its offset within its block.
5. Optionally ``--update`` the ledger's ``verify`` axis on a match.

Body length vs. block partition
-------------------------------
The ledger's ``size`` is the block **partition** — the bytes up to the next cut point — *not*
the function body. A partition over-covers its function whenever an unsymbolised region (a
routine the inventory missed, or an interior literal pool with no cut) sits between this
function and the next cut. ``func_601a72e4`` (``new_b`` in the PoC) is the canonical case: a
**60 B body in a 1368 B partition**, because the next cut point is 0x601a783c.

The gate therefore compares the **compiled body** against the original, using the compiled
length as the compared span, and treats ``size`` as an **upper bound**:
``0 < len(body) <= size`` and ``body == original[addr : addr+len(body)]``. An entry whose
partition over-covers is reported explicitly, never silently. ``--body N`` supplies an
authoritative extent (the PoC regression fixtures use it); with it the compiled length must
match ``N`` exactly instead of merely fitting the partition.

Residual risk, documented rather than hidden: under the default rule a *truncated*
reconstruction that happens to compile to the original's prefix would match. Disambiguating
that needs a disassembly-derived function extent (a later milestone); ``--body`` is the escape
hatch until it lands.

Scope: the gate currently compares raw bytes (stage 1). That is exactly correct for a
**relocation-free leaf** (nothing in it depends on where it is placed). A function whose
object carries relocations is reported and the raw compare still runs, but a clean match for
non-leaves needs the address-agnostic, relocation-aware diff (a later milestone).

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
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

from ledgerlib import read_entries, set_field

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_SRC_ROOT = REPO / "src"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"
DEFAULT_BUILD_CONFIG = REPO / "config" / "build.json"


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


def _elf32(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (sections, symbols) for a little-endian ELF32 object."""
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
    for s in sections:
        if s["type"] != 2:  # SHT_SYMTAB
            continue
        symstr = sections[s["link"]]
        symdata = data[symstr["offset"]:symstr["offset"] + symstr["size"]]
        for o in range(0, s["size"], 16):
            n, val, sz, info, _other, shndx = struct.unpack_from("<IIIBBH", data,
                                                                 s["offset"] + o)
            symbols.append({
                "name": name_at_bytes(symdata, n),
                "value": val, "size": sz, "info": info, "shndx": shndx,
                "type": info & 0xF, "bind": info >> 4,
            })
    return sections, symbols


def name_at_bytes(blob: bytes, off: int) -> str:
    end = blob.index(b"\x00", off)
    return blob[off:end].decode("utf-8", "replace")


def extract_function(obj: Path, names: list[str]) -> tuple[bytes, str, bool]:
    """Return (bytes, symbol name, has_relocations) for the object's one function.

    ``names`` are candidate identities (the ledger name and group); they disambiguate the
    rare multi-function object. Raises if zero or an unidentifiable plurality is found.
    """
    data = obj.read_bytes()
    sections, symbols = _elf32(obj)
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

    has_reloc = any(s["type"] in (4, 9) and s["info"] == sec["index"]  # SHT_RELA/SHT_REL
                    for s in sections)
    return code, func["name"], has_reloc


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
    """Compare a compiled function body against the original; return ``(ok, ref, status)``.

    ``partition`` is the ledger's ``size`` (an upper bound, not the body length). ``body`` is
    the optional authoritative extent. ``ref`` is the original slice compared against, or a
    best-effort slice for the diagnostics of a length failure.

    Status values:

    * ``match``       — the body matches the original over its length and fills the partition;
    * ``short-body``  — matches, but the partition over-covers the body (still a match);
    * ``empty-body``  — the object defined a zero-length function;
    * ``too-long``    — the body is larger than its partition and cannot fit this slot;
    * ``body-length`` — ``--body`` was given and the compiled length differs from it;
    * ``mismatch``    — the lengths agree but the bytes differ.
    """
    if body is not None:
        ref = block[off:off + body]
        if len(cand) != body:
            return False, ref, "body-length"
        return (cand == ref), ref, ("match" if cand == ref else "mismatch")

    n = len(cand)
    if n == 0:
        return False, b"", "empty-body"
    if n > partition:
        return False, block[off:off + n], "too-long"
    ref = block[off:off + n]
    if cand != ref:
        return False, ref, "mismatch"
    return True, ref, ("short-body" if n < partition else "match")


def gate_result(module: str, addr: str, name: str, cand: bytes, ref: bytes, ok: bool,
                status: str, body: int | None, partition: int,
                has_reloc: bool) -> dict:
    """The machine-readable result of one gate run (the near-miss bank's closeness input).

    Pure, so it is unit-tested and stable: ``diff_count`` is the divergence count over the
    compared span, and ``body`` is the authoritative extent when one was asserted. ``diff_words``
    carries the differing instructions themselves (see :func:`diff_words`) so a caller can act on
    a mismatch without re-deriving the comparison.
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
        "has_reloc": has_reloc,
    }


def print_status(status: str, cand_len: int, partition: int,
                 body: int | None) -> None:
    """Explain a non-plain-mismatch status on its own line."""
    if status == "empty-body":
        print(f"  {RED}reason: compiled function is empty (0 B); the ledger entry is "
              f"{partition} B{RESET}")
    elif status == "too-long":
        print(f"  {RED}reason: compiled body {cand_len} B > partition {partition} B — "
              f"cannot fit this slot (wrong function?){RESET}")
    elif status == "body-length":
        print(f"  {RED}reason: compiled body {cand_len} B != asserted --body {body} B{RESET}")


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
        cand, sym, has_reloc = extract_function(obj, [entry["name"], entry["group"]])
    except ElfError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"function: {entry['name']}  (object symbol {sym})")
    if has_reloc:
        print(f"  {DIM}note: object carries relocations — the gate compares raw bytes for "
              f"now; a clean match for non-leaves needs the relocation-aware diff{RESET}")

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
    ok, ref, status = compare_body(cand, block, off, size, args.body)

    if args.report is not None:
        result = gate_result(args.module, addr, entry["name"], cand, ref, ok, status,
                             args.body, size, has_reloc)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    where = f"{entry['addr']} in {entry['block']}"
    print()
    if ok:
        print(f"{GREEN}{BOLD}>>> MATCH{RESET}  {entry['name']}  "
              f"({len(cand)} B at {where})")
        if status == "short-body":
            print(f"  {YELLOW}note: body {len(cand)} B < partition {size} B — the entry "
                  f"over-covers; compared over the body, not the partition{RESET}")
    else:
        print(f"{RED}{BOLD}>>> MISMATCH{RESET}  {entry['name']}  ({where})")
        print_status(status, len(cand), size, args.body)
        print_diff(cand, ref, args.show)

    if ok and args.update:
        changed = set_field(args.ledger, (args.module, addr), "verify", "match")
        print(f"ledger: {entry['name']} verify={'match' if changed else 'match (unchanged)'}")
    elif args.update and not ok:
        print("ledger: not updated (no match)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
