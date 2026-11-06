"""The whole-image check: assemble the reconstructed image and compare it to the original.

This is the *Linked* metric's gate (``docs/architecture.md`` -> *Progress metrics*), the
per-function byte gate's whole-image counterpart. Model B (``docs/architecture.md`` ->
*Unmatched-function fallback*): unmatched regions keep the original bytes, matched functions
contribute their compiled bytes, and the result is compared against the image at every address.

Why substitution and not ``ld``
-------------------------------
A literal link cannot reproduce this image. It is position-independent, so a compiled
function's ``R_ARM_GOT_PREL`` makes the *linker* allocate a GOT entry — at an address the
linker chooses. Measured: ``arm-none-eabi-ld -T script`` places ``.got.plt`` immediately after
``.text`` (``0x60000028``), where the original has it at ``0x61838000``. Neither GNU ld nor lld
exposes the original's slot assignment, so a byte-identical image is unreachable by linking.

Substitution instead applies the *same* resolution the per-function gate applies — the ledger
address for an internal symbol, the PLT stub for an import, the GOT slot for a pool word — and
writes the resulting bytes at the function's original address. A resolution that would differ
from the original therefore shows up as a differing byte here, with the entry that owns it.

Usage::

    python3 tools/build/linkcheck.py                 # every matched function with a source
    python3 tools/build/linkcheck.py --limit 20      # a quick pass
    python3 tools/build/linkcheck.py --show 20       # more mismatches listed
    python3 tools/build/linkcheck.py --json          # machine-readable summary
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "nso"))

import bytegate  # noqa: E402
import gotmap  # noqa: E402
from ledgerlib import read_entries  # noqa: E402

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_SRC_ROOT = REPO / "src"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"
DEFAULT_BUILD_CONFIG = REPO / "config" / "build.json"


# --- pure helpers ---------------------------------------------------------------------

def first_mismatch(candidate: bytes, reference: bytes, base: int = 0) -> int | None:
    """The address of the first differing byte, or ``None`` when the images are equal."""
    span = min(len(candidate), len(reference))
    for i in range(span):
        if candidate[i] != reference[i]:
            return base + i
    return base + span if len(candidate) != len(reference) else None


def substitute(image: bytearray, base: int, spans: list[tuple[int, bytes]]) -> list[str]:
    """Write ``(address, bytes)`` spans into ``image``; return the problems found.

    A span must lie inside the image and must not overlap another span — an overlap would mean
    two claims on the same bytes, which the ledger's partition is supposed to prevent. Every
    other byte is left exactly as the original had it.
    """
    problems: list[str] = []
    claimed: list[tuple[int, int]] = []
    for address, data in sorted(spans):
        lo, hi = address - base, address - base + len(data)
        if lo < 0 or hi > len(image):
            problems.append(f"0x{address:08x}: span {len(data)} B is outside the image")
            continue
        i = bisect.bisect_right([a for a, _b in claimed], lo)
        if i > 0 and claimed[i - 1][1] > lo:
            problems.append(f"0x{address:08x}: overlaps the span at "
                            f"0x{claimed[i - 1][0] + base:08x}")
            continue
        claimed.insert(i, (lo, hi))
        image[lo:hi] = data
    return problems


def owner(address: int, entries: list[dict]) -> dict | None:
    """The ledger entry whose partition contains ``address``."""
    starts = [int(e["addr"], 16) for e in entries if e["addr"]]
    i = bisect.bisect_right(starts, address) - 1
    if i < 0:
        return None
    e = entries[i]
    if address < int(e["addr"], 16) + int(e["size"]):
        return e
    return None


# --- the reconstructed image ----------------------------------------------------------

def matched_sources(entries: list[dict], src_root: Path) -> list[dict]:
    """Matched function entries that have a source file to contribute."""
    out = []
    for e in entries:
        if e["kind"] != "function" or e["verify"] != "match":
            continue
        if not (src_root / e["module"] / f"{e['group']}.cpp").exists():
            continue
        out.append(e)
    return out


def compile_and_resolve(entry: dict, *, src_root: Path, tc: dict, flags: list[str],
                        entries: list[dict], nso: Path, stub_cache: Path | None,
                        build_dir: Path) -> tuple[int, bytes, int] | str:
    """Compile one function and resolve its relocations.

    Returns ``(address, bytes, relocation count)``, or a reason string when the function cannot
    contribute (a compile error, an ELF problem, or a relocation the gate cannot resolve).
    """
    src = src_root / entry["module"] / f"{entry['group']}.cpp"
    obj = build_dir / f"{entry['name']}.o"
    cmd = [tc.get("clang", "clang"), *flags, "-c", str(src), "-o", str(obj)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode:
        return f"compile failed ({run.returncode})"
    try:
        code, _sym, relocs = bytegate.extract_function(obj, [entry["name"], entry["group"]])
    except bytegate.ElfError as e:
        return f"elf: {e}"
    address = int(entry["addr"], 16)
    if not relocs:
        return address, code, 0
    addresses, _via_stub = bytegate.branch_addresses(relocs, entries, nso, stub_cache)
    slots: dict[str, int] = {}
    if any(r["type"] in bytegate.POOL_RELOCS for r in relocs):
        try:
            slots = bytegate.pool_slots(entries, gotmap.load_or_build(nso, stub_cache))
        except (gotmap.GotError, OSError, ValueError) as e:
            return f"got map: {e}"
    patched, unresolved = bytegate.resolve_relocations(code, relocs, address, addresses, slots)
    if unresolved:
        return "; ".join(why for _off, why in unresolved)
    return address, patched, len(relocs)


def build_image(image: gotmap.Image,
                contributions: list[tuple[int, bytes]]) -> tuple[bytearray, list[str]]:
    """The reconstructed image: original bytes everywhere, contributions where they land."""
    problems: list[str] = []
    sections = image.sections
    base = min(addr for addr, _blob in sections.values())
    top = max(addr + len(blob) for addr, blob in sections.values())
    merged = bytearray(top - base)
    for addr, blob in sections.values():
        merged[addr - base:addr - base + len(blob)] = blob
    problems += substitute(merged, base, contributions)
    return merged, problems


def verified_keys(contributions: list[tuple[dict, int, bytes]], candidate: bytes,
                  reference: bytes, base: int) -> list[str]:
    """``module:addr`` for every contribution whose own bytes the image reproduced.

    Per-entry rather than per-image: substitution makes each contribution independent, so a
    mismatch in one entry does not disqualify another. This is the set ``report.py
    --link-report`` consumes to publish the Linked metric.
    """
    out = []
    for entry, address, data in contributions:
        lo = address - base
        if candidate[lo:lo + len(data)] == reference[lo:lo + len(data)]:
            out.append(f"{entry['module']}:{entry['addr']}")
    return out


def describe(address: int, entries: list[dict]) -> str:
    e = owner(address, entries)
    if e is None:
        return "(no ledger entry)"
    return (f"{e['name']} ({e['kind']}, {e['block']}, 0x{e['addr']} +"
            f"0x{address - int(e['addr'], 16):x})")


# --- CLI ------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--src-root", type=Path, default=DEFAULT_SRC_ROOT)
    ap.add_argument("--toolchain", type=Path, default=DEFAULT_TOOLCHAIN)
    ap.add_argument("--build-config", type=Path, default=DEFAULT_BUILD_CONFIG)
    ap.add_argument("--stub-cache", type=Path, default=gotmap.DEFAULT_CACHE)
    ap.add_argument("--build-dir", type=Path, default=REPO / "baserom" / "work" / "linkcheck")
    ap.add_argument("--limit", type=int, default=None,
                    help="only the first N matched functions (a quick pass)")
    ap.add_argument("--show", type=int, default=10, help="how many mismatches to list")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", type=Path, default=None,
                    help="write the machine-readable link result (what report.py --link-report "
                         "consumes) here")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: missing ledger {args.ledger}", file=sys.stderr)
        return 2
    entries = read_entries(args.ledger)
    targets = matched_sources(entries, args.src_root)
    if args.limit is not None:
        targets = targets[:args.limit]

    tc = json.loads(args.toolchain.read_text())
    flags = (list(tc["cflags"]) + list(tc.get("section_flags", []))
             + bytegate.include_dirs(args.build_config))
    args.build_dir.mkdir(parents=True, exist_ok=True)

    print(f"link check: {len(targets)} matched function(s) from {args.src_root}")
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(
            lambda e: compile_and_resolve(e, src_root=args.src_root, tc=tc, flags=flags,
                                          entries=entries, nso=args.nso,
                                          stub_cache=args.stub_cache,
                                          build_dir=args.build_dir),
            targets))

    contributions: list[tuple[dict, int, bytes]] = []
    errors: list[tuple[dict, str]] = []
    relocated = 0
    for entry, result in zip(targets, results):
        if isinstance(result, str):
            errors.append((entry, result))
        else:
            address, data, count = result
            contributions.append((entry, address, data))
            relocated += count > 0

    if errors:
        print(f"  {len(errors)} function(s) could not contribute:")
        for entry, why in errors[:args.show]:
            print(f"    {entry['addr']} {entry['name']}: {why}")

    try:
        image = gotmap.Image.from_nso(args.nso)
    except (gotmap.GotError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    base = min(a for a, _b in image.sections.values())
    reference, problems = build_image(image, [])
    candidate, more = build_image(image, [(addr, data) for _e, addr, data in contributions])
    for p in problems + more:
        print(f"  problem: {p}")

    # An entry is linked when its own bytes are what the original has at that address — a
    # mismatch anywhere else does not disqualify it, and a mismatch inside it does.
    linked = verified_keys(contributions, candidate, reference, base)
    mismatch = first_mismatch(candidate, reference, base)
    payload = {
        "ok": mismatch is None and not errors,
        "matched": len(targets),
        "contributed": len(contributions),
        "relocated": relocated,
        "failed": [{"module": e["module"], "addr": e["addr"], "name": e["name"],
                    "why": why} for e, why in errors],
        "bytes": len(reference),
        "first_mismatch": f"0x{mismatch:08x}" if mismatch is not None else None,
        "owner": describe(mismatch, entries) if mismatch is not None else None,
        "linked": linked,
    }
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"  contributed {len(contributions)} of {len(targets)} "
              f"({relocated} with relocations resolved, {len(reference)} bytes compared)")
        if mismatch is None:
            print(f"  OK: the assembled image is byte-identical to the original "
                  f"({len(linked)} entr{'y' if len(linked) == 1 else 'ies'} linked)")
        else:
            print(f"  MISMATCH first at 0x{mismatch:08x}: {payload['owner']}")
            offset = mismatch - base
            shown = 0
            while shown < args.show and offset < len(reference):
                if candidate[offset] != reference[offset]:
                    print(f"    0x{base + offset:08x}: got {candidate[offset]:02x} "
                          f"want {reference[offset]:02x}")
                    shown += 1
                offset += 1
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
