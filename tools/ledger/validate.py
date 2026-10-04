#!/usr/bin/env python3
"""Validate the committed symbol ledger's invariants (the CI gate).

The ledger is a *frozen, hand-owned* artifact: it is seeded once from the Ghidra
inventory export (``tools/ledger/gen_ledger.py``) and then edited in place, carrying
authored status. There is therefore no regeneration to compare against — instead this
validator proves the ledger still satisfies the structural invariants that make it a
sound denominator and a sound partition. See ``docs/architecture.md`` → *Symbol ledger*
and *Ledger — concrete schema*.

Invariants checked
------------------
* **Schema** — the header is exactly the shared ``LEDGER_COLUMNS``; every row has the
  same field count.
* **Field domains** — ``kind``, ``name_class``, ``verify``, ``review``, ``enroll``,
  ``guess`` are within their declared sets; addresses are 8-hex lowercase; non-externals
  carry a block and a positive integer size; externals carry no address/block/size/group.
* **Naming** — a ``generated`` name is exactly ``func_<addr>`` (function) / ``D_<addr>``
  (data); a ``discovered`` name is reproduced verbatim.
* **Key uniqueness** — no duplicate ``(module, addr)`` (non-externals) or ``(module,
  name)`` (externals).
* **Order** — addressed entries ascending by ``(module, addr)``; externals last, by
  ``(module, name)``.
* **Partition** — within each ``(module, block)`` consecutive entries are adjacent
  (``next.addr == addr + size``): no overlaps and no holes.
* **(optional) Block bounds** — with ``--blocks`` (an ``inventory.blocks.tsv``), the
  first entry of each block starts at the block start and the last ends at the block end,
  closing the partition against the true extent.

Usage::

    python3 tools/ledger/validate.py                    # the committed ledger
    python3 tools/ledger/validate.py --blocks FILE      # also close the partition
    python3 tools/ledger/validate.py --ledger FILE
"""

from __future__ import annotations

import argparse
import csv
import itertools
import re
from pathlib import Path

from ledgerlib import (
    ENROLL_VALUES,
    KINDS,
    LEDGER_COLUMNS,
    NAMING_CLASSES,
    REVIEW_VALUES,
    VERIFY_VALUES,
    read_entries,
)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"

ADDR_RE = re.compile(r"^[0-9a-f]{8}$")
GEN_NAME_RE = re.compile(r"^(func|D)_([0-9a-f]{8})$")
BINDS = ("LOCAL", "GLOBAL", "WEAK")


def _read_header(path: Path) -> list[str]:
    with path.open(newline="") as f:
        return next(csv.reader(f, delimiter="\t"))


def validate(path: Path, blocks: Path | None) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"{path}: does not exist"]

    header = _read_header(path)
    if header != LEDGER_COLUMNS:
        errors.append(
            f"header mismatch:\n    got  {header}\n    want {LEDGER_COLUMNS}")

    entries = read_entries(path)
    seen_keys: set[tuple[str, str]] = set()
    seen_ext: set[tuple[str, str]] = set()
    last_addressed: tuple[str, int] | None = None
    seen_external = False
    prev_external_name: tuple[str, str] | None = None

    per_block: dict[tuple[str, str], list[dict]] = {}

    for lineno, e in enumerate(entries, start=2):
        where = f"line {lineno} ({e.get('module','?')},{e.get('addr','')})"

        if len(e) != len(LEDGER_COLUMNS):
            errors.append(f"{where}: {len(e)} fields, expected {len(LEDGER_COLUMNS)}")
            continue

        kind = e["kind"]
        if kind not in KINDS:
            errors.append(f"{where}: bad kind {kind!r}")

        if e["name_class"] not in NAMING_CLASSES:
            errors.append(f"{where}: bad name_class {e['name_class']!r}")
        elif e["name_class"] == "generated" and kind != "external":
            m = GEN_NAME_RE.match(e["name"])
            if not m:
                errors.append(f"{where}: generated name {e['name']!r} is not "
                              f"func_/D_<addr>")
            else:
                prefix, naddr = m.group(1), m.group(2)
                if prefix == "func" and kind != "function":
                    errors.append(f"{where}: func_ name on kind {kind!r}")
                if prefix == "D" and kind != "data":
                    errors.append(f"{where}: D_ name on kind {kind!r}")
                if naddr != e["addr"]:
                    errors.append(f"{where}: generated name address {naddr} != "
                                  f"row addr {e['addr']}")

        if e["verify"] not in VERIFY_VALUES:
            errors.append(f"{where}: bad verify {e['verify']!r}")
        if e["review"] not in REVIEW_VALUES:
            errors.append(f"{where}: bad review {e['review']!r}")
        if e["guess"] not in ("0", "1"):
            errors.append(f"{where}: bad guess {e['guess']!r}")

        if kind == "external":
            seen_external = True
            if e["enroll"] != "":
                errors.append(f"{where}: external must have empty enroll")
            if e["addr"] or e["block"] or e["size"] or e["group"]:
                errors.append(f"{where}: external must have empty addr/block/size/group")
            if e["bind"] not in BINDS:
                errors.append(f"{where}: bad bind {e['bind']!r}")
            nk = (e["module"], e["name"])
            if nk in seen_ext:
                errors.append(f"{where}: duplicate external name {e['name']!r}")
            seen_ext.add(nk)
            if prev_external_name is not None and nk < prev_external_name:
                errors.append(f"{where}: externals out of order")
            prev_external_name = nk
            continue

        # --- addressed (function / data) --------------------------------------------------
        if seen_external:
            errors.append(f"{where}: addressed entry after externals")
        if not ADDR_RE.match(e["addr"]):
            errors.append(f"{where}: addr {e['addr']!r} is not 8-hex lowercase")
        else:
            a = int(e["addr"], 16)
            if last_addressed is not None:
                lm, la = last_addressed
                if (e["module"], a) < (lm, la):
                    errors.append(f"{where}: addressed entries out of order")
            last_addressed = (e["module"], a)
            key = (e["module"], e["addr"])
            if key in seen_keys:
                errors.append(f"{where}: duplicate (module,addr) {key}")
            seen_keys.add(key)

        if not e["block"]:
            errors.append(f"{where}: missing block")
        if e["enroll"] not in ENROLL_VALUES:
            errors.append(f"{where}: bad enroll {e['enroll']!r}")
        try:
            if int(e["size"]) <= 0:
                errors.append(f"{where}: size must be positive")
        except ValueError:
            errors.append(f"{where}: size {e['size']!r} is not an integer")

        per_block.setdefault((e["module"], e["block"]), []).append(e)

    # --- partition: adjacency within each block ------------------------------------------
    for (module, block), rows in sorted(per_block.items()):
        rows.sort(key=lambda x: int(x["addr"], 16))
        for prev, nxt in itertools.pairwise(rows):
            end = int(prev["addr"], 16) + int(prev["size"])
            if int(nxt["addr"], 16) != end:
                errors.append(
                    f"{module}:{block}: {prev['addr']}+{prev['size']} = {end:08x} "
                    f"but next is {nxt['addr']} (hole or overlap)")
            if nxt["module"] != module:
                errors.append(f"{nxt['addr']}: module changed within block")

    # --- optional: close the partition against true block bounds -------------------------
    if blocks is not None:
        extents = {}
        with Path(blocks).open(newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["class"] == "content":
                    extents[r["block"]] = (int(r["addr"], 16), int(r["size"]))
        for (module, block), rows in sorted(per_block.items()):
            if block not in extents:
                continue
            start, size = extents[block]
            if int(rows[0]["addr"], 16) != start:
                errors.append(f"{module}:{block}: first entry {rows[0]['addr']} != "
                              f"block start {start:08x}")
            last = rows[-1]
            end = int(last["addr"], 16) + int(last["size"])
            if end != start + size:
                errors.append(f"{module}:{block}: last entry ends {end:08x} != "
                              f"block end {start + size:08x}")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--blocks", type=Path, default=None,
                    help="optional inventory.blocks.tsv to close the partition")
    args = ap.parse_args(argv)

    errors = validate(args.ledger, args.blocks)
    entries = read_entries(args.ledger) if args.ledger.exists() else []
    counted = sum(1 for e in entries if e["kind"] != "external")
    print(f"validate: {args.ledger}")
    print(f"  entries           {len(entries)}")
    print(f"  counted (non-ext) {counted}")
    if errors:
        print(f"  FAIL: {len(errors)} invariant violation(s)")
        for err in errors[:50]:
            print(f"    - {err}")
        if len(errors) > 50:
            print(f"    ... and {len(errors) - 50} more")
        return 1
    print("  OK: all invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
