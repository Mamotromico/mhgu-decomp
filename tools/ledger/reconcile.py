"""Apply reviewed boundary corrections to the committed ledger (a *reconcile*, not a re-seed).

The ledger is seeded once from the Ghidra inventory export (``gen_ledger.py``) and then
hand-owned: it carries authored status, so it is a **frozen seed** and must never be
regenerated wholesale. The Ghidra draft, however, sometimes invents *interior* cut points —
it promotes a branch/jump-table target inside a real function to a ``function`` entry (or
leaves the bytes as a ``D_<addr>`` gap). Such a fragment reads registers set by the
preceding instructions and can never be reconstructed standalone, so it wastes the loop.

This tool applies a checked-in, reviewable list of **overrides** — declarative boundary
corrections — to the existing ledger in place:

* the *decision* (which addresses are real function boundaries) is human, taken from the
  disassembly; it is never auto-derived, because the draft is the thing that is wrong;
* the *edit* is mechanical and this tool performs it, so the partition stays adjacent and
  authored status survives on every kept row.

Because the ledger round-trips byte-identically through ``gen_ledger.serialize``, the result
is a diff that shows **exactly** the re-partitioned region and nothing else.

Override file (TSV, ``#`` comment lines and blank lines ignored)::

    module  block   start       end         cuts
    main    .text   60c49cb8    60c4a1c0    60c49cb8:function,60c49f1c:function

One row re-partitions ``[start, end)`` in ``(module, block)``. Requirements:

* ``start`` and ``end`` are the addresses of **existing** ledger entries in the same block;
  ``start < end``. The entry at ``end`` is the fixed right edge and is left untouched, so
  you cannot re-partition past a block's last entry (add a boundary first if you need to).
* ``cuts`` is a comma-separated ``addr:kind`` list (``kind`` is ``function`` or ``data``),
  strictly increasing, all within ``[start, end)``, and the **first cut must equal
  ``start``** (the left edge is fixed by the preceding entry).
* a cut whose address already exists in the replaced region **keeps that row** verbatim
  (its ``name``/``name_class``/``bind``/``group`` and its ``verify``/``review``/``enroll``
  status), only its ``size`` is recomputed; a new cut gets a generated ``func_``/``D_``
  name and the seed status defaults.
* replacing a row whose ``verify`` is not ``none`` when its address is not among the cuts
  would **drop authored status** and is refused unless ``--force``.

The tool is a **preview by default**: it prints the changes and a unified diff and writes
nothing until ``--apply``. On ``--apply`` it validates the result against the ledger's
invariants (``validate.py``) and refuses to write an invalid ledger.

Usage::

    python3 tools/ledger/reconcile.py                          # preview the committed ledger
    python3 tools/ledger/reconcile.py --apply                  # write it
    python3 tools/ledger/reconcile.py --overrides FILE --apply

Exit codes: 0 ok (or preview), 1 an override is invalid / the result violates invariants,
2 usage error.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import io
import itertools
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ledgerlib import STATUS_DEFAULTS, read_entries
from validate import validate

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_OVERRIDES = REPO / "config" / "main" / "ledger.overrides.tsv"

OVERRIDE_COLUMNS = ("module", "block", "start", "end", "cuts")
KINDS = ("function", "data")


class ReconcileError(Exception):
    """An override is malformed or cannot be applied to the ledger."""


@dataclass(frozen=True)
class Override:
    """One reviewed re-partition of ``[start, end)`` in ``(module, block)``."""

    module: str
    block: str
    start: int
    end: int
    cuts: tuple[tuple[int, str], ...]   # (addr, kind), strictly increasing, cuts[0] == start


# --- parsing --------------------------------------------------------------------------

def read_overrides(path: Path) -> list[Override]:
    """Parse the override TSV. A missing file is an empty override list (a no-op)."""
    path = Path(path)
    if not path.exists():
        return []
    # Strip ``#`` comments and blank lines so the file can carry a documented example.
    kept = [ln for ln in path.read_text().splitlines(keepends=True)
            if ln.strip() and not ln.lstrip().startswith("#")]
    if not kept:
        return []
    reader = csv.DictReader(kept, delimiter="\t")
    if reader.fieldnames != list(OVERRIDE_COLUMNS):
        raise ReconcileError(f"{path}: header must be {list(OVERRIDE_COLUMNS)}, "
                             f"got {reader.fieldnames}")
    overrides = []
    for lineno, r in enumerate(reader, start=2):
        where = f"{path}:{lineno}"
        try:
            start, end = int(r["start"], 16), int(r["end"], 16)
        except (TypeError, ValueError):
            raise ReconcileError(f"{where}: start/end must be hex addresses")
        module, block = r["module"].strip(), r["block"].strip()
        cuts: list[tuple[int, str]] = []
        for tok in (r["cuts"] or "").split(","):
            tok = tok.strip()
            if not tok:
                continue
            try:
                a_str, kind = tok.split(":")
                cuts.append((int(a_str, 16), kind.strip()))
            except ValueError:
                raise ReconcileError(f"{where}: bad cut {tok!r} (want addr:kind)")
        if not module or not block:
            raise ReconcileError(f"{where}: module and block are required")
        if start >= end:
            raise ReconcileError(f"{where}: start must be < end")
        if not cuts:
            raise ReconcileError(f"{where}: at least one cut is required")
        for a, kind in cuts:
            if kind not in KINDS:
                raise ReconcileError(f"{where}: bad kind {kind!r} (want function|data)")
            if not start <= a < end:
                raise ReconcileError(f"{where}: cut {a:08x} outside [{start:08x}, {end:08x})")
        if cuts[0][0] != start:
            raise ReconcileError(f"{where}: first cut must equal start ({start:08x})")
        if any(b[0] <= a[0] for a, b in itertools.pairwise(cuts)):
            raise ReconcileError(f"{where}: cuts must be strictly increasing")
        overrides.append(Override(module, block, start, end, tuple(cuts)))
    return overrides


# --- application ----------------------------------------------------------------------

def _new_entry(module: str, block: str, addr: int, kind: str, size: int) -> dict:
    name = f"{'func' if kind == 'function' else 'D'}_{addr:08x}"
    return {
        "module": module, "addr": f"{addr:08x}", "kind": kind, "name": name,
        "block": block, "group": name, "size": str(size), "name_class": "generated",
        "bind": "", "guess": "0", **STATUS_DEFAULTS,
    }


def _sort(entries: list[dict]) -> list[dict]:
    addressed = [e for e in entries if e["kind"] != "external"]
    externals = [e for e in entries if e["kind"] == "external"]
    addressed.sort(key=lambda e: (e["module"], int(e["addr"], 16)))
    externals.sort(key=lambda e: (e["module"], e["name"]))
    return addressed + externals


def apply_overrides(entries: list[dict], overrides: list[Override], *,
                    force: bool = False) -> tuple[list[dict], list[dict]]:
    """Return ``(new_entries, changes)``. Raises ``ReconcileError`` on an invalid override.

    ``entries`` is one dict per ledger row (as ``ledgerlib.read_entries`` returns); the input
    is not mutated. ``changes`` is one report dict per override (removed/added/carried).
    """
    working = [dict(e) for e in entries]
    changes: list[dict] = []

    for ov in overrides:
        where = f"{ov.module}:{ov.block} [{ov.start:08x}, {ov.end:08x})"
        block_rows = [e for e in working
                      if e["module"] == ov.module and e["block"] == ov.block]
        by_addr = {int(e["addr"], 16) for e in block_rows}
        if ov.start not in by_addr:
            raise ReconcileError(f"{where}: start {ov.start:08x} is not an existing entry")
        if ov.end not in by_addr:
            raise ReconcileError(f"{where}: end {ov.end:08x} is not an existing entry "
                                 "(the right edge must be a committed boundary)")

        region = sorted((e for e in block_rows if ov.start <= int(e["addr"], 16) < ov.end),
                        key=lambda e: int(e["addr"], 16))
        if not region:
            raise ReconcileError(f"{where}: no entries in range")
        preserved = {int(e["addr"], 16): e for e in region}
        cut_addrs = {a for a, _ in ov.cuts}

        # Refuse to silently discard a row that carries authored status (§ status is precious).
        if not force:
            dropped = [e for e in region
                       if int(e["addr"], 16) not in cut_addrs
                       and e.get("verify", "none") not in ("", "none")]
            if dropped:
                addrs = ", ".join(e["addr"] for e in dropped)
                raise ReconcileError(
                    f"{where}: would drop authored status (verify!=none) at {addrs}; "
                    f"pass --force to proceed deliberately")

        new_rows: list[dict] = []
        carried: list[str] = []
        added: list[str] = []
        for i, (a, kind) in enumerate(ov.cuts):
            nxt = ov.cuts[i + 1][0] if i + 1 < len(ov.cuts) else ov.end
            size = nxt - a
            old = preserved.get(a)
            if old is not None:
                if old["kind"] != kind:
                    raise ReconcileError(f"{where}: cut {a:08x} kind {kind} != existing "
                                         f"kind {old['kind']}")
                row = dict(old)
                row["size"] = str(size)
                carried.append(f"{a:08x}")
            else:
                row = _new_entry(ov.module, ov.block, a, kind, size)
                added.append(f"{a:08x}")
            new_rows.append(row)

        # Drop the replaced rows, splice in the new ones, and report.
        removed = {id(e) for e in region}
        working = [e for e in working if id(e) not in removed] + new_rows
        changes.append({
            "module": ov.module, "block": ov.block,
            "start": f"{ov.start:08x}", "end": f"{ov.end:08x}",
            "removed": [e["addr"] for e in region],
            "added": added, "carried": carried,
        })

    return _sort(working), changes


# --- serialization / reporting --------------------------------------------------------

def serialize(entries: list[dict]) -> str:
    """The ledger text (identical formatting to ``gen_ledger.serialize``)."""
    from ledgerlib import LEDGER_COLUMNS
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LEDGER_COLUMNS, delimiter="\t", lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    w.writerows(entries)
    return buf.getvalue()


def _diff(old: str, new: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile="ledger.tsv (before)", tofile="ledger.tsv (after)")) or "(no change)\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    ap.add_argument("--blocks", type=Path, default=None,
                    help="optional inventory.blocks.tsv to also check block bounds")
    ap.add_argument("--apply", action="store_true",
                    help="write the reconciled ledger (default: preview only)")
    ap.add_argument("--force", action="store_true",
                    help="allow an override that would drop a row with authored status")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: missing ledger {args.ledger}", file=sys.stderr)
        return 2
    try:
        overrides = read_overrides(args.overrides)
    except ReconcileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if not overrides:
        print(f"reconcile: no overrides ({args.overrides}); nothing to do")
        return 0

    old_text = args.ledger.read_text()
    try:
        new_entries, changes = apply_overrides(read_entries(args.ledger), overrides,
                                               force=args.force)
    except ReconcileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    new_text = serialize(new_entries)

    # Validate the *result* against the ledger's invariants; never write an invalid ledger.
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as fh:
        fh.write(new_text)
        tmp = Path(fh.name)
    try:
        errors = validate(tmp, args.blocks)
    finally:
        tmp.unlink(missing_ok=True)
    if errors:
        print("error: reconciled ledger violates invariants; not written:", file=sys.stderr)
        for err in errors[:20]:
            print(f"  - {err}", file=sys.stderr)
        return 1

    for c in changes:
        print(f"region {c['module']}:{c['block']} [{c['start']}, {c['end']})")
        print(f"  removed {len(c['removed'])}: {' '.join(c['removed'])}")
        if c["carried"]:
            print(f"  carried {len(c['carried'])}: {' '.join(c['carried'])}")
        if c["added"]:
            print(f"  added   {len(c['added'])}: {' '.join(c['added'])}")
    if old_text == new_text:
        print("reconcile: overrides already applied; no change")
        return 0

    print()
    print(_diff(old_text, new_text))
    if not args.apply:
        print("preview only — re-run with --apply to write")
        return 0
    args.ledger.write_text(new_text)
    print(f"wrote {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
