"""Export the committed ledger as an **objdiff report** — decomp.dev's progress format.

decomp.dev (``encounter/decomp.dev``) does not scrape source: its bot downloads a GitHub
Actions artifact named ``<version>_report`` and parses the ``report.json`` inside it with
``objdiff_core::bindings::report::Report`` (the protobuf-derived schema in
``objdiff-core/protos/report.proto``, current ``REPORT_VERSION = 2``). This tool renders the
committed ledger as exactly that document, so the published number is derived from the one
shared predicate (``ledgerlib``) — never hand-authored. See ``docs/architecture.md`` →
*Progress metrics*.

Mapping (every field is the predicate in ``ledgerlib``; nothing is invented)
---------------------------------------------------------------------------
The site's two figures are *decompiled* (``matched_code``) and *fully linked*
(``complete_code``); both are code-byte percentages.

* ``matched_code`` / ``matched_functions`` ← ``decompiled(e)`` (``verify = match``).
* ``complete_code`` / ``complete_data`` ← ``done(e)``: decompiled **and** linked. The link
  build decides linked (``tools/build/linkcheck.py --report``); without one, the axis falls
  back to ``enroll = complete``, the ledger-expressible stand-in. ``reloc`` is by design
  derived rather than stored (see *Status layer & the shared "matched" predicate*).
* code = ``kind = function``; data = ``kind = data`` (literal pools living in ``.text`` stay
  data, because the entry's *kind*, not its block, decides).
* ``fuzzy_match_percent`` is the code match percent: an entry is byte-identical or it is not,
  so the ledger has no partial credit to report.
* Total bytes are ledger partitions; matched/complete bytes are exact verified extents. The
  CLI derives function extents from the NSO plus inventory, and data extents from inventory
  or its gap export. Missing/inconsistent extents fail rather than claiming partition padding.

Categories are the ledger's ``module`` (one bar per module); the top-level ``measures`` are
what decomp.dev publishes. Per-unit detail (``units``, grouped by ``group``) is **omitted by
default**: the ledger's one-function-per-file default makes ``group`` one-per-function, so
emitting every unit inflates the artifact to hundreds of MB (267k groups / ~245 MB on the
seed) for detail decomp.dev does not surface. ``--units`` includes it for local inspection.

Usage::

    python3 tools/ledger/report.py                     # report for the committed ledger -> stdout
    python3 tools/ledger/report.py --out report.json   # write the artifact body
    python3 tools/ledger/report.py --link-report build/link.json   # real Linked metric
    python3 tools/ledger/report.py --units             # include per-group unit detail
    python3 tools/ledger/report.py --ledger FILE --nso FILE --inventory FILE --gaps FILE

Exit codes::

    0  report emitted
    2  usage error (missing ledger/extent input, or an inconsistent extent)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import complexity
from ledgerlib import counted, decompiled, entry_key, read_entries

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_INVENTORY = REPO / "baserom" / "work" / "inventory" / "inventory.tsv"
DEFAULT_GAPS = REPO / "baserom" / "work" / "inventory" / "inventory.gaps.tsv"

# objdiff REPORT_VERSION (objdiff-core/src/bindings/report.rs). v2 is emitted fully formed, so
# decomp.dev's Report::migrate() is a no-op (v0/v1 migration would otherwise recompute these).
REPORT_VERSION = 2

_COUNT_KEYS = (
    "total_code", "matched_code",
    "total_data", "matched_data",
    "total_functions", "matched_functions",
    "complete_code", "complete_data",
    "total_units", "complete_units",
)


def is_complete(e: dict, linked: set[tuple[str, str]] | None = None) -> bool:
    """In the denominator and linked: verified by the image check, or enrolled as ours.

    With a link result (``linkcheck.py --report``), the *Linked* axis is the build's verdict:
    a matched entry whose bytes the assembled image reproduced. Without one it falls back to
    the ledger's ``enroll`` axis, which is the hand-expressible approximation.
    """
    if linked is not None:
        return counted(e) and decompiled(e) and (e["module"], e["addr"]) in linked
    return counted(e) and e["enroll"] == "complete"


def linked_entries(path: Path) -> set[tuple[str, str]]:
    """Read ``linkcheck.py --report`` and return the entries whose bytes it verified."""
    payload = json.loads(Path(path).read_text())
    keys: set[tuple[str, str]] = set()
    for item in payload.get("linked", []):
        module, sep, addr = str(item).partition(":")
        if not sep or not module or not addr:
            raise ValueError(f"{path}: linked entry {item!r} is not 'module:addr'")
        keys.add((module, addr))
    return keys


def read_extent_inputs(inventory_path: Path, gaps_path: Path
                       ) -> tuple[dict[str, tuple[str, int]], set[str]]:
    """Read exact inventory body extents and the addresses of materialized gap rows."""
    import csv

    with Path(inventory_path).open(newline="") as f:
        inventory = {
            r["addr"]: (r["kind"], int(r["size"]))
            for r in csv.DictReader(f, delimiter="\t")
            if r["class"] == "content" and r["kind"] in ("function", "data")
        }
    with Path(gaps_path).open(newline="") as f:
        gaps = {r["addr"] for r in csv.DictReader(f, delimiter="\t")
                if r["class"] == "content"}
    return inventory, gaps


def verified_extents(entries: list[dict], text: bytes | None,
                     inventory: dict[str, tuple[str, int]], gaps: set[str]
                     ) -> dict[tuple[str, str], int]:
    """Derive the exact extent behind every matched ledger entry.

    Function extents include instructions, alignment, and referenced literal-pool words. Data
    cut points use their inventory extent; a ledger row materialized from an inventory gap is
    already the exact gap, so its partition and verified extent are identical. Anything else
    fails closed instead of turning a partition into evidence of matched coverage.
    """
    extents: dict[tuple[str, str], int] = {}
    for e in entries:
        if not decompiled(e):
            continue
        partition = int(e["size"])
        record = inventory.get(e["addr"])
        try:
            if e["kind"] == "function":
                if record is None or record[0] != "function":
                    raise ValueError("no function instruction extent in the inventory")
                body = complexity.body_of(text, e["addr"], record[1])
                extent = complexity.function_extent(body, partition)
            else:
                if record is not None:
                    if record[0] != "data":
                        raise ValueError(f"inventory kind is {record[0]}, not data")
                    extent = record[1]
                elif e["addr"] in gaps:
                    extent = partition
                else:
                    raise ValueError("no data extent in the inventory or gap export")
            if not 0 < extent <= partition:
                raise ValueError(f"extent {extent} does not fit partition {partition}")
        except ValueError as exc:
            raise ValueError(f"{e['module']}:{e['addr']} ({e['name']}): {exc}") from exc
        extents[entry_key(e)] = extent
    return extents


def load_verified_extents(entries: list[dict], nso: Path, inventory_path: Path,
                          gaps_path: Path) -> dict[tuple[str, str], int]:
    """Load report extent inputs without invoking Ghidra."""
    if not any(decompiled(e) for e in entries):
        return {}
    inventory, gaps = read_extent_inputs(inventory_path, gaps_path)
    text = None
    if any(decompiled(e) and e["kind"] == "function" for e in entries):
        text = complexity.load_text(nso)
        if text is None:
            raise ValueError(f"cannot read reference .text from {nso}")
    return verified_extents(entries, text, inventory, gaps)


def _pct(numerator: float, denominator: float) -> float:
    """objdiff's convention: an empty denominator is 100%, not a division by zero."""
    return 100.0 if denominator == 0 else numerator / denominator * 100.0


def _extent(e: dict, extents: dict[tuple[str, str], int]) -> int:
    """The exact verified extent, or the partition for an unmatched denominator row."""
    partition = int(e["size"])
    if not decompiled(e):
        return partition
    try:
        extent = extents[entry_key(e)]
    except KeyError:
        raise ValueError(f"missing verified extent for {e['module']}:{e['addr']}") from None
    if not 0 < extent <= partition:
        raise ValueError(f"verified extent {extent} does not fit partition {partition} "
                         f"for {e['module']}:{e['addr']}")
    return extent


def _counts(entries: list[dict], linked: set[tuple[str, str]] | None,
            extents: dict[tuple[str, str], int]) -> dict:
    """Accumulate byte/count totals; only denominators use whole partitions."""
    c = {k: 0 for k in _COUNT_KEYS}
    for e in entries:
        partition = int(e["size"])
        extent = _extent(e, extents)
        if e["kind"] == "function":
            c["total_code"] += partition
            c["total_functions"] += 1
            if decompiled(e):
                c["matched_code"] += extent
                c["matched_functions"] += 1
        else:  # data
            c["total_data"] += partition
            if decompiled(e):
                c["matched_data"] += extent
        if is_complete(e, linked):
            c["complete_code" if e["kind"] == "function" else "complete_data"] += extent
    return c


def _finalize(c: dict) -> dict:
    """Turn raw counts into an objdiff ``Measures`` object (field order mirrors the proto)."""
    total_code, total_data = c["total_code"], c["total_data"]
    return {
        "fuzzy_match_percent": _pct(c["matched_code"], total_code),
        "total_code": total_code,
        "matched_code": c["matched_code"],
        "matched_code_percent": _pct(c["matched_code"], total_code),
        "total_data": total_data,
        "matched_data": c["matched_data"],
        "matched_data_percent": _pct(c["matched_data"], total_data),
        "total_functions": c["total_functions"],
        "matched_functions": c["matched_functions"],
        "matched_functions_percent": _pct(c["matched_functions"], c["total_functions"]),
        "complete_code": c["complete_code"],
        "complete_code_percent": _pct(c["complete_code"], total_code),
        "complete_data": c["complete_data"],
        "complete_data_percent": _pct(c["complete_data"], total_data),
        "total_units": c["total_units"],
        "complete_units": c["complete_units"],
    }


def _item(e: dict, extents: dict[tuple[str, str], int]) -> dict:
    """One ``ReportItem`` (a function or a data section)."""
    item = {
        "name": e["name"],
        "size": _extent(e, extents),
        "fuzzy_match_percent": 100.0 if decompiled(e) else 0.0,
    }
    if e["addr"]:
        item["metadata"] = {"virtual_address": int(e["addr"], 16)}
    return item


def build(entries: list[dict], include_units: bool = False,
          linked: set[tuple[str, str]] | None = None,
          extents: dict[tuple[str, str], int] | None = None) -> dict:
    """Render ledger entries as an objdiff ``Report`` (v2) document.

    ``include_units`` adds per-``group`` unit detail; it is off by default because the ledger's
    one-function-per-file default makes that detail enormous (see the module docstring).
    ``linked`` is the link build's verified set; without it the Linked axis uses ``enroll``.
    ``extents`` is mandatory for matched rows: verified numerators never use partition sizes.
    """
    extents = {} if extents is None else extents
    counted_entries = [e for e in entries if counted(e)]

    # Group by (module, group): the unit is a translation unit, its category is the module.
    groups: dict[tuple[str, str], list[dict]] = {}
    for e in counted_entries:
        groups.setdefault((e["module"], e["group"]), []).append(e)

    units = []
    complete_by_module: dict[str, list[int]] = {}  # module -> [total, complete]
    for (module, group), es in sorted(groups.items()):
        complete = all(is_complete(e, linked) for e in es)
        tally = complete_by_module.setdefault(module, [0, 0])
        tally[0] += 1
        tally[1] += 1 if complete else 0
        if include_units:
            c = _counts(es, linked, extents)
            c["total_units"] = 1
            c["complete_units"] = 1 if complete else 0
            unit = {"name": group, "measures": _finalize(c)}
            functions = [_item(e, extents) for e in es if e["kind"] == "function"]
            sections = [_item(e, extents) for e in es if e["kind"] == "data"]
            if functions:
                unit["functions"] = functions
            if sections:
                unit["sections"] = sections
            unit["metadata"] = {"complete": complete, "progress_categories": [module]}
            units.append(unit)

    measures = _counts(counted_entries, linked, extents)
    measures["total_units"] = sum(t for t, _c in complete_by_module.values())
    measures["complete_units"] = sum(c for _t, c in complete_by_module.values())

    # One category per module, aggregated from that module's units.
    by_module: dict[str, list[dict]] = {}
    for (module, _group), es in sorted(groups.items()):
        by_module.setdefault(module, []).extend(es)
    categories = []
    for module, es in sorted(by_module.items()):
        c = _counts(es, linked, extents)
        c["total_units"], c["complete_units"] = complete_by_module[module]
        categories.append({"id": module, "name": module, "measures": _finalize(c)})

    report = {"measures": _finalize(measures), "version": REPORT_VERSION,
              "categories": categories}
    if include_units:
        report["units"] = units
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help="committed ledger (default config/main/ledger.tsv)")
    ap.add_argument("--out", type=Path, default=None,
                    help="write the report here (default: stdout)")
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO,
                    help="reference NSO for matched function extents")
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY,
                    help="inventory.tsv supplying exact instruction/data extents")
    ap.add_argument("--gaps", type=Path, default=DEFAULT_GAPS,
                    help="inventory.gaps.tsv identifying exact materialized data gaps")
    ap.add_argument("--link-report", type=Path, default=None,
                    help="linkcheck.py --report output; makes the Linked axis the build's "
                         "verdict instead of the ledger's enroll axis")
    ap.add_argument("--units", action="store_true",
                    help="include per-group unit detail (large; omitted by default)")
    ap.add_argument("--compact", action="store_true",
                    help="emit compact JSON (no indentation)")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: {args.ledger}: does not exist", file=sys.stderr)
        return 2

    entries = read_entries(args.ledger)
    linked = None
    try:
        if args.link_report is not None:
            linked = linked_entries(args.link_report)
        extents = load_verified_extents(entries, args.nso, args.inventory, args.gaps)
        report = build(entries, include_units=args.units, linked=linked, extents=extents)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.compact:
        text = json.dumps(report, separators=(",", ":"))
    else:
        text = json.dumps(report, indent=2)
    text += "\n"

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        m = report["measures"]
        print(f"report: {args.out}  "
              f"decompiled {m['matched_code_percent']:.2f}%  "
              f"linked {m['complete_code_percent']:.2f}%", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
