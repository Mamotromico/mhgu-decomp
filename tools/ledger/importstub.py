"""Derive the linker-generated GOT import stubs from the GOT map, retype and gate them.

The end of ``.text`` (``0x613efd58``-``0x613f1de0``) holds one 12-byte stub per imported
symbol. **No C source produces them**: the three words are the linker's own encoding of
"call the import that owns this GOT slot", and the slot's *contents* are a load-time fact
about another module. Under the per-function byte gate they could therefore never match —
they were 3,209 model attempts (20 % of the attempt budget) at a 0 % ceiling (see
``AGENTS.md`` -> *Linker veneers are not functions*).

What this tool does instead
---------------------------
Treats a stub as what it is: **link output**, like a relocation. Given only the stub's own
address and the GOT slot it jumps through, :func:`encodings` re-derives the 12 bytes and
compares them with the reference::

    add  r12, pc, #hi      ; r12 = (stub + 8) + hi    (a 4 MB page step)
    add  r12, r12, #lo     ; r12 += lo                (the offset within the page)
    ldr  pc, [r12, #off]!  ; jump through the slot at r12 + off

The split of ``slot - (stub + 8)`` into ``(hi, lo, off)`` is the *linker's* convention, not
a fact the bytes reveal: several splits encode the same address. This tool therefore
enumerates a small set of splits (:data:`SPLITS`) and accepts a stub as **derived** only
when one of them reproduces the reference bytes exactly. Ambiguity is resolved by the
reference, never assumed — and a stub no split reproduces stays unverified and is reported.

A verified stub is a real, checked statement: *"this body is exactly what a linker emits to
reach GOT slot X at address A"*. It is **not** a decompilation, so it is kept out of the
denominator (``kind=import-stub``), carries the ``link`` gate provenance, and is reported
separately (``ledgerlib.built_stub``).

Usage::

    python3 tools/ledger/importstub.py --check          # survey every stub, write nothing
    python3 tools/ledger/importstub.py --check --json   # machine-readable survey
    python3 tools/ledger/importstub.py --apply          # retype + stamp the derived ones

``--apply`` is idempotent: it writes only the rows whose fields actually change, one pass
over the file, so no other row is reformatted and no status is lost. Re-run it after a
re-seed **or a reconcile**: a re-partition regenerates the rows it replaces as
``func_``/``D_``, so a region containing stubs needs the retype again.

Exit codes::

    0  every stub in the ledger is derived and matches the reference
    1  a stub is unencodable, differs, or is missing from the GOT map (see the report)
    2  usage error (missing ledger / image)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import complexity  # noqa: E402
import gotmap  # noqa: E402
from ledgerlib import read_entries  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"

STUB_SIZE = 12

# ``(hi mask, mid mask, lo mask)`` — disjoint, and their union is all 32 bits. The first is
# the convention observed throughout this image (4 MB page step / page offset / low byte);
# the others are the plausible alternatives, tried in order. Which one was used is decided
# by whether it reproduces the reference bytes.
SPLITS = (
    (0xFFC00000, 0x003FFF00, 0x000000FF),
    (0xFFC00000, 0x003FF000, 0x00000FFF),
    (0x0FFFFF00, 0x00000000, 0x000000FF),
    (0x0FFFF000, 0x00000000, 0x00000FFF),
)

# A32 encodings of the three instructions with an unset immediate:
# ``add r12, pc, #imm``, ``add r12, r12, #imm``, ``ldr pc, [r12, #imm]!``.
ADD_PC = 0xE28FC000
ADD_R12 = 0xE28CC000
LDR_PC = 0xE5BCF000


def imm8_rot(value: int) -> list[int]:
    """Every 12-bit field encoding ``value`` as ``imm8 ROR (2*rot)``; empty if none.

    The field is ``rot[11:8]`` and ``imm8[7:0]``, and only 8-bit patterns rotated right by an
    even amount are representable. A value usually has **several** encodings (``2^22`` is
    ``1 ROR 10``, ``4 ROR 12``, ``0x10 ROR 14``, …), and *which* one the linker picked is not
    recoverable from the value — so all of them are returned and the reference bytes choose.
    """
    out: list[int] = []
    value &= 0xFFFFFFFF
    for rot in range(16):
        shift = 2 * rot
        if not shift:
            if value < 0x100:
                out.append(value)
            continue
        imm8 = ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF
        if imm8 < 0x100:
            out.append((rot << 8) | imm8)
    return out


def encodings(stub: int, slot: int) -> list[bytes]:
    """Every stub body this tool can derive from ``(stub address, GOT slot address)``.

    The distance ``slot - (stub + 8)`` is split per :data:`SPLITS` and each field is encoded in
    every valid modified-immediate form, so the result is the full set of bodies that reach
    **exactly that slot** with the linker's ``add/add/ldr pc`` shape. Which member the linker
    emitted is decided by comparing with the reference; an empty list means no split encodes
    the distance (a different idiom).
    """
    delta = (slot - (stub + 8)) & 0xFFFFFFFF
    out: list[bytes] = []
    for hi_mask, mid_mask, lo_mask in SPLITS:
        hi = delta & hi_mask
        mid = delta & mid_mask
        low = delta & lo_mask
        if (hi | mid | low) != delta or low > 0xFFF:
            continue
        for e_hi in imm8_rot(hi):
            for e_mid in imm8_rot(mid):
                body = b"".join(word.to_bytes(4, "little") for word in
                                (ADD_PC | e_hi, ADD_R12 | e_mid, LDR_PC | low))
                if body not in out:
                    out.append(body)
    return out


def survey(entries: list[dict], text: bytes | None,
           stubs: dict[int, int]) -> list[dict]:
    """Classify every ledger row that is (or looks like) an import stub.

    ``stubs`` is ``stub address -> GOT slot address`` (``gotmap.plt_stubs``). A row is
    reported when it is already ``kind=import-stub`` or when its body is one
    (:func:`complexity.is_veneer`) — so a mis-typed row cannot hide.

    Each result carries ``status``, one of:

    ``derived``        one of :func:`encodings` reproduces the reference body exactly
    ``mismatch``       derivable, but none of the candidates equals the reference
    ``unencodable``    no split encodes the distance (a different linker idiom)
    ``not-in-gotmap``  the body is a stub but the GOT map has no stub at that address
    ``typed-not-stub`` the ledger says ``import-stub`` but the body is not one
    """
    out: list[dict] = []
    if text is None:
        return out
    for e in entries:
        if not e.get("addr") or e.get("kind") == "external":
            continue
        # A stub is exactly 12 bytes; a longer row that merely *starts* with the idiom is a
        # real function (or a merge) and must not be retyped.
        try:
            if int(e.get("size") or 0) != STUB_SIZE:
                continue
            body = complexity.body_of(text, e["addr"], STUB_SIZE)
        except ValueError:
            continue
        looks = complexity.is_veneer(body)
        typed = e.get("kind") == "import-stub"
        if not looks and not typed:
            continue
        addr = int(e["addr"], 16)
        rec = {"addr": e["addr"], "kind": e["kind"], "verify": e.get("verify", ""),
               "gate": e.get("gate", "")}
        if typed and not looks:
            rec["status"] = "typed-not-stub"
        elif addr not in stubs:
            rec["status"] = "not-in-gotmap"
        else:
            slot = stubs[addr]
            candidates = encodings(addr, slot)
            rec["slot"] = f"{slot:08x}"
            if not candidates:
                rec["status"] = "unencodable"
            elif body in candidates:
                rec["status"] = "derived"
            else:
                rec["status"] = "mismatch"
        out.append(rec)
    return out


def stub_fields(addr: str) -> dict[str, str]:
    """The ledger fields of a derived import stub: link output, never source-enrolled."""
    name = f"plt_{addr}"
    return {
        "kind": "import-stub",
        "name": name,
        "name_class": "generated",
        "group": name,
        "enroll": "",
        "verify": "match",
        "gate": "link",
    }


def apply(ledger: Path, records: list[dict]) -> int:
    """Write the derived rows; return how many rows changed. Idempotent.

    One pass over the file rather than one write per row: the ledger is ~24 MB and there are
    ~670 stubs, so a per-row rewrite would copy the whole file 670 times. The edit is still
    line-surgical — only the targeted lines are re-joined, every other line is copied
    verbatim — which is the property that keeps the write from disturbing authored status.
    """
    wanted = {rec["addr"]: stub_fields(rec["addr"])
              for rec in records if rec["status"] == "derived"}
    if not wanted:
        return 0
    lines = ledger.read_text().splitlines(keepends=True)
    header = lines[0].rstrip("\n").split("\t")
    columns = next(iter(wanted.values())).keys()
    try:
        idx = {c: header.index(c) for c in columns}
    except ValueError as exc:
        raise ValueError(f"{ledger}: {exc}")
    changed = 0
    for i, line in enumerate(lines[1:], start=1):
        fields = line.rstrip("\n").split("\t")
        if len(fields) <= max(idx.values()):
            continue
        want = wanted.get(fields[1])
        if want is None or fields[0] != "main":
            continue
        if all(fields[idx[c]] == want[c] for c in want):
            continue
        for c, value in want.items():
            fields[idx[c]] = value
        lines[i] = "\t".join(fields) + "\n"
        changed += 1
    if changed:
        ledger.write_text("".join(lines))
    return changed


def summarize(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--check", action="store_true",
                    help="report only, write nothing (the default)")
    ap.add_argument("--apply", action="store_true",
                    help="retype + stamp the derived rows")
    ap.add_argument("--json", action="store_true", help="machine-readable survey")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: {args.ledger}: does not exist", file=sys.stderr)
        return 2
    if not args.nso.exists():
        print(f"error: {args.nso}: does not exist", file=sys.stderr)
        return 2

    text = complexity.load_text(args.nso)
    if text is None:
        print(f"error: cannot read {args.nso}", file=sys.stderr)
        return 2

    image = gotmap.Image.from_nso(args.nso)
    stubs = gotmap.plt_stubs(image)
    entries = read_entries(args.ledger)
    records = survey(entries, text, stubs)
    counts = summarize(records)

    if args.apply:
        changed = apply(args.ledger, records)
        print(f"importstub: retyped/stamped {changed} row(s)")

    if args.json:
        print(json.dumps({"counts": counts, "records": records}, indent=1, sort_keys=True))
    else:
        print(f"importstub: {len(records)} stub row(s) in {args.ledger}")
        for status in ("derived", "mismatch", "unencodable", "not-in-gotmap",
                       "typed-not-stub"):
            if counts.get(status):
                print(f"  {status:<14} {counts[status]}")
        bad = [r for r in records if r["status"] != "derived"]
        for rec in bad[:20]:
            print(f"  - {rec['addr']}  {rec['status']}  (kind={rec['kind']})")
        if len(bad) > 20:
            print(f"  ... and {len(bad) - 20} more")

    return 0 if counts.get("derived", 0) == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
